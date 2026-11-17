"""
Routes pour la gestion des factures.
Blueprint Flask monté sur /api/invoices

Pipeline complet :
    1. Upload + validation fichier
    2. Contrôle qualité (OpenCV)
    3. Classification (MobileNetV2)
    4. Extraction OCR (EasyOCR)
    5. Raffinement métier (business_logic) ← NOUVEAU
    6. Insertion MySQL
    7. Réponse JSON
"""
import os
import uuid
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

from services import persistence_service
from services.quality_service import analyze_quality
from services.classification_service import predict as classify_image
from services.ocr_service import extract_fields as extract_ocr_fields
from services.business_logic_service import refine_classification


invoices_bp = Blueprint("invoices", __name__)


UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 Mo
IMAGE_EXTENSIONS = {"jpg", "jpeg", "png"}
AMOUNT_TOLERANCE = 0.01


os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ==================================================
# POST /api/invoices/upload
# ==================================================
@invoices_bp.route("/upload", methods=["POST"])
def upload():
    """
    Upload + pipeline complet :
    OpenCV → CNN → EasyOCR → Logique métier → MySQL
    """

    # ===== 1. Vérifier la présence d'un fichier =====
    if "file" not in request.files:
        return jsonify({
            "error": {
                "code": "NO_FILE",
                "message": "Aucun fichier n'a été fourni dans la requête."
            }
        }), 400

    f = request.files["file"]
    if f.filename == "":
        return jsonify({
            "error": {
                "code": "NO_FILE",
                "message": "Le fichier fourni n'a pas de nom."
            }
        }), 400

    # ===== 2. Vérifier l'extension =====
    if not allowed_file(f.filename):
        return jsonify({
            "error": {
                "code": "INVALID_FORMAT",
                "message": "Format non supporté. Utilisez PDF, JPG, JPEG ou PNG.",
                "details": f"Extension reçue : .{f.filename.rsplit('.', 1)[-1].lower()}"
            }
        }), 415

    # ===== 3. Vérifier la taille =====
    content = f.read()
    f.seek(0)

    if len(content) > MAX_FILE_SIZE:
        return jsonify({
            "error": {
                "code": "FILE_TOO_LARGE",
                "message": "Le fichier dépasse la taille maximale de 10 Mo.",
                "details": f"Taille reçue : {len(content) / (1024 * 1024):.2f} Mo"
            }
        }), 413

    if len(content) == 0:
        return jsonify({
            "error": {
                "code": "EMPTY_FILE",
                "message": "Le fichier est vide (0 octet)."
            }
        }), 400

    # ===== 4. Sauvegarder avec un nom unique =====
    original_name = secure_filename(f.filename)
    ext = original_name.rsplit(".", 1)[1].lower() if "." in original_name else ""
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(UPLOAD_FOLDER, unique_name)
    f.save(save_path)

    # ===== 5. Contrôle qualité (OpenCV) =====
    quality_result = None
    quality_error = None

    if ext in IMAGE_EXTENSIONS:
        try:
            quality_result = analyze_quality(save_path)
        except Exception as e:
            quality_error = str(e)
    else:
        quality_result = {
            "is_blurry": False, "is_dark": False,
            "is_skewed": False, "is_badly_framed": False,
            "quality_status": "good",
            "scores": {
                "blur_variance": 0.0, "brightness_mean": 0.0,
                "skew_angle": 0.0, "document_area_ratio": 0.0,
            },
            "issues": ["PDF_QUALITY_NOT_ANALYZED"],
        }

    # ===== 6. Classification CNN =====
    cnn_label = None
    cnn_confidence = 0.0
    classification_error = None

    if ext in IMAGE_EXTENSIONS:
        try:
            cnn_label, cnn_confidence = classify_image(save_path)
        except Exception as e:
            classification_error = str(e)
    else:
        classification_error = "PDF_CLASSIFICATION_NOT_SUPPORTED"

    # ===== 7. Extraction OCR (EasyOCR) =====
    ocr_result = None
    ocr_error = None

    if ext in IMAGE_EXTENSIONS:
        try:
            ocr_result = extract_ocr_fields(save_path)
        except Exception as e:
            ocr_error = str(e)

    # ===== 8. Raffinement métier (NOUVEAU) =====
    refined = refine_classification(
        cnn_label=cnn_label or "autre",
        cnn_confidence=cnn_confidence,
        ocr_result=ocr_result,
    )
    final_label = refined["final_label"]

    # ===== 9. Construire les warnings =====
    warnings = []

    # Qualité
    if quality_result:
        warnings.extend(quality_result.get("issues", []))
    if quality_error:
        warnings.append(f"QUALITY_ANALYSIS_FAILED:{quality_error}")

    # Classification
    if classification_error:
        warnings.append(f"CLASSIFICATION_FAILED:{classification_error}")
    if cnn_label is not None and cnn_confidence < 0.6:
        warnings.append("LOW_CONFIDENCE")

    # Si l'OCR a corrigé le CNN → warning explicite
    if refined["corrected"]:
        warnings.append("CNN_OVERRIDDEN_BY_OCR")

    # Si indéterminé → warning
    if refined["ocr_hint"]["hint"] == "indetermine" and cnn_label in (
        "facture_achat", "facture_vente"
    ):
        warnings.append("INVOICE_TYPE_UNDETERMINED")

    # OCR : champs manquants
    if ocr_error:
        warnings.append(f"OCR_FAILED:{ocr_error}")
    if ocr_result:
        for field in ["supplier", "invoice_number", "date", "total_ht", "vat", "total_ttc"]:
            if ocr_result.get(field) is None:
                warnings.append(f"MISSING_FIELD:{field}")

        # Cohérence HT + TVA = TTC
        ht = ocr_result.get("total_ht")
        vat = ocr_result.get("vat")
        ttc = ocr_result.get("total_ttc")
        if all(v is not None for v in [ht, vat, ttc]):
            if abs((ht + vat) - ttc) > AMOUNT_TOLERANCE:
                warnings.append("AMOUNT_MISMATCH")

    # ===== 10. Insérer dans MySQL =====
    try:
        facture_id = persistence_service.create_facture(
            nom_fichier=unique_name,
            chemin_fichier=save_path,
        )

        persistence_service.create_resultat_analyse(
            facture_id=facture_id,
            confiance=cnn_confidence,
            qualite=quality_result["quality_status"] if quality_result else "unknown",
            texte_ocr=ocr_result.get("raw_text", "") if ocr_result else "",
        )

        for warning in warnings:
            persistence_service.create_anomalie(
                facture_id=facture_id,
                type_anomalie=warning,
                description="Avertissement détecté lors du traitement.",
            )

        persistence_service.create_donnee_extraite(
            facture_id=facture_id,
            fournisseur=ocr_result.get("supplier") if ocr_result else None,
            numero_facture=ocr_result.get("invoice_number") if ocr_result else None,
            date_facture=ocr_result.get("date") if ocr_result else None,
            montant_ht=ocr_result.get("total_ht") if ocr_result else None,
            montant_tva=ocr_result.get("vat") if ocr_result else None,
            montant_ttc=ocr_result.get("total_ttc") if ocr_result else None,
        )

        final_status = "warning" if warnings else "processed"
        persistence_service.update_facture_status(
            facture_id=facture_id,
            type_document=final_label,
            statut=final_status,
        )

        facture_row = persistence_service.get_facture_by_id(facture_id)
        created_at = (
            facture_row["date_importation"].isoformat()
            if facture_row and facture_row["date_importation"]
            else None
        )

        # ===== 11. Réponse JSON =====
        return jsonify({
            "id": facture_id,
            "filename": unique_name,
            "status": final_status,
            "classification": {
                "label": final_label,
                "confidence": cnn_confidence,
                "cnn_label": cnn_label,
                "corrected": refined["corrected"],
                "correction_reason": refined["reason"] if refined["corrected"] else None,
                "ocr_hint": refined["ocr_hint"]["hint"],
                "ocr_matches": {
                    "achat": refined["ocr_hint"]["achat_matches"][:3],
                    "vente": refined["ocr_hint"]["vente_matches"][:3],
                },
            },
            "quality": {
                "is_blurry": quality_result["is_blurry"] if quality_result else False,
                "is_dark": quality_result["is_dark"] if quality_result else False,
                "is_skewed": quality_result["is_skewed"] if quality_result else False,
                "is_badly_framed": quality_result["is_badly_framed"] if quality_result else False,
                "quality_status": quality_result["quality_status"] if quality_result else "unknown",
                "scores": quality_result["scores"] if quality_result else {
                    "blur_variance": 0.0, "brightness_mean": 0.0, "skew_angle": 0.0,
                },
            },
            "extracted": {
                "supplier": ocr_result.get("supplier") if ocr_result else None,
                "invoice_number": ocr_result.get("invoice_number") if ocr_result else None,
                "date": ocr_result.get("date") if ocr_result else None,
                "total_ht": ocr_result.get("total_ht") if ocr_result else None,
                "vat": ocr_result.get("vat") if ocr_result else None,
                "total_ttc": ocr_result.get("total_ttc") if ocr_result else None,
            },
            "validation": {
                "is_valid": len(warnings) == 0,
                "warnings": warnings,
            },
            "ocr_text": ocr_result.get("raw_text", "") if ocr_result else "",
            "created_at": created_at,
        }), 200

    except Exception as e:
        try:
            if os.path.exists(save_path):
                os.remove(save_path)
        except Exception:
            pass

        return jsonify({
            "error": {
                "code": "DB_ERROR",
                "message": "Impossible d'enregistrer la facture.",
                "details": str(e),
            }
        }), 500


# ==================================================
# GET /api/invoices — liste paginée
# ==================================================
@invoices_bp.route("", methods=["GET"])
def list_invoices():
    try:
        page = max(1, int(request.args.get("page", 1)))
        limit = min(100, max(1, int(request.args.get("limit", 20))))
    except ValueError:
        return jsonify({
            "error": {
                "code": "INVALID_INPUT",
                "message": "Les paramètres 'page' et 'limit' doivent être des entiers."
            }
        }), 400

    status = request.args.get("status")
    label = request.args.get("label")

    invoices, total = persistence_service.get_all_factures(
        page=page, limit=limit, status=status, label=label
    )

    return jsonify({
        "total": total, "page": page, "limit": limit, "invoices": invoices,
    }), 200


# ==================================================
# GET /api/invoices/<id>
# ==================================================
@invoices_bp.route("/<int:facture_id>", methods=["GET"])
def get_invoice(facture_id: int):
    row = persistence_service.get_facture_by_id(facture_id)
    if row is None:
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": f"Aucune facture trouvée avec l'identifiant {facture_id}."
            }
        }), 404

    anomalies = persistence_service.get_anomalies_by_facture_id(facture_id)

    return jsonify({
        "id": row["id"],
        "filename": row["nom_fichier"],
        "status": row["statut"],
        "classification": {
            "label": row["type_document"] or "autre",
            "confidence": row["confiance"] or 0.0,
        },
        "quality": {
            "is_blurry": any(a["type_anomalie"] == "BLURRY_IMAGE" for a in anomalies),
            "is_dark": any(a["type_anomalie"] == "DARK_IMAGE" for a in anomalies),
            "is_skewed": any(a["type_anomalie"] == "SKEWED_IMAGE" for a in anomalies),
            "is_badly_framed": any(a["type_anomalie"] == "BAD_FRAMING" for a in anomalies),
            "quality_status": row["qualite"] or "good",
            "scores": {"blur_variance": 0.0, "brightness_mean": 0.0, "skew_angle": 0.0},
        },
        "extracted": {
            "supplier": row["fournisseur"],
            "invoice_number": row["numero_facture"],
            "date": row["date_facture"].isoformat() if row["date_facture"] else None,
            "total_ht": float(row["montant_ht"]) if row["montant_ht"] is not None else None,
            "vat": float(row["montant_tva"]) if row["montant_tva"] is not None else None,
            "total_ttc": float(row["montant_ttc"]) if row["montant_ttc"] is not None else None,
        },
        "validation": {
            "is_valid": len(anomalies) == 0,
            "warnings": [a["type_anomalie"] for a in anomalies],
        },
        "ocr_text": row["texte_ocr"] or "",
        "created_at": row["date_importation"].isoformat() if row["date_importation"] else None,
    }), 200


# ==================================================
# DELETE /api/invoices/<id>
# ==================================================
@invoices_bp.route("/<int:facture_id>", methods=["DELETE"])
def delete_invoice(facture_id: int):
    if not persistence_service.facture_exists(facture_id):
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": f"Aucune facture trouvée avec l'identifiant {facture_id}."
            }
        }), 404

    row = persistence_service.get_facture_by_id(facture_id)
    if row and row.get("chemin_fichier"):
        try:
            if os.path.exists(row["chemin_fichier"]):
                os.remove(row["chemin_fichier"])
        except Exception:
            pass

    persistence_service.delete_facture(facture_id)
    return jsonify({"id": facture_id, "status": "deleted"}), 200


# ==================================================
# GET /api/invoices/<id>/export
# ==================================================
@invoices_bp.route("/<int:facture_id>/export", methods=["GET"])
def export_invoice(facture_id: int):
    row = persistence_service.get_facture_by_id(facture_id)
    if row is None:
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": f"Aucune facture trouvée avec l'identifiant {facture_id}."
            }
        }), 404

    anomalies = persistence_service.get_anomalies_by_facture_id(facture_id)

    data = {
        "id": row["id"],
        "filename": row["nom_fichier"],
        "status": row["statut"],
        "classification": {
            "label": row["type_document"] or "autre",
            "confidence": row["confiance"] or 0.0,
        },
        "extracted": {
            "supplier": row["fournisseur"],
            "invoice_number": row["numero_facture"],
            "date": row["date_facture"].isoformat() if row["date_facture"] else None,
            "total_ht": float(row["montant_ht"]) if row["montant_ht"] is not None else None,
            "vat": float(row["montant_tva"]) if row["montant_tva"] is not None else None,
            "total_ttc": float(row["montant_ttc"]) if row["montant_ttc"] is not None else None,
        },
        "validation": {
            "is_valid": len(anomalies) == 0,
            "warnings": [a["type_anomalie"] for a in anomalies],
        },
        "ocr_text": row["texte_ocr"] or "",
        "created_at": row["date_importation"].isoformat() if row["date_importation"] else None,
    }

    response = jsonify(data)
    response.headers["Content-Disposition"] = f'attachment; filename="facture_{facture_id}.json"'
    return response, 200


# ==================================================
# PUT /api/invoices/<id> — mise à jour (correction manuelle)
# ==================================================
@invoices_bp.route("/<int:facture_id>", methods=["PUT"])
def update_invoice(facture_id: int):
    """Met à jour les données extraites d'une facture (correction manuelle)."""
    if not persistence_service.facture_exists(facture_id):
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": f"Aucune facture trouvée avec l'identifiant {facture_id}."
            }
        }), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({
            "error": {
                "code": "INVALID_INPUT",
                "message": "Le corps de la requête doit être un JSON valide."
            }
        }), 400

    allowed_fields = {"supplier", "invoice_number", "date", "total_ht", "vat", "total_ttc"}
    provided_fields = set(data.keys()) & allowed_fields

    if not provided_fields:
        return jsonify({
            "error": {
                "code": "INVALID_INPUT",
                "message": f"Aucun champ valide fourni. Champs autorisés : {sorted(allowed_fields)}"
            }
        }), 400

    # Valider chaque champ
    validated = {}

    if "supplier" in data:
        val = data["supplier"]
        if val is None:
            validated["fournisseur"] = None
        elif isinstance(val, str) and len(val) <= 255:
            validated["fournisseur"] = val.strip() or None
        else:
            return jsonify({
                "error": {
                    "code": "INVALID_INPUT",
                    "message": "'supplier' doit être une chaîne ≤ 255 caractères."
                }
            }), 422

    if "invoice_number" in data:
        val = data["invoice_number"]
        if val is None:
            validated["numero_facture"] = None
        elif isinstance(val, str) and len(val) <= 100:
            validated["numero_facture"] = val.strip() or None
        else:
            return jsonify({
                "error": {
                    "code": "INVALID_INPUT",
                    "message": "'invoice_number' doit être une chaîne ≤ 100 caractères."
                }
            }), 422

    if "date" in data:
        val = data["date"]
        if val is None:
            validated["date_facture"] = None
        elif isinstance(val, str):
            try:
                from datetime import datetime as _dt
                _dt.strptime(val, "%Y-%m-%d")
                validated["date_facture"] = val
            except ValueError:
                return jsonify({
                    "error": {
                        "code": "INVALID_INPUT",
                        "message": "'date' doit être au format YYYY-MM-DD.",
                        "details": f"Valeur reçue : {val}"
                    }
                }), 422
        else:
            return jsonify({
                "error": {
                    "code": "INVALID_INPUT",
                    "message": "'date' doit être une chaîne au format YYYY-MM-DD."
                }
            }), 422

    for field, db_field in [
        ("total_ht", "montant_ht"),
        ("vat", "montant_tva"),
        ("total_ttc", "montant_ttc"),
    ]:
        if field in data:
            val = data[field]
            if val is None:
                validated[db_field] = None
            elif isinstance(val, (int, float)) and val >= 0:
                validated[db_field] = float(val)
            else:
                return jsonify({
                    "error": {
                        "code": "INVALID_INPUT",
                        "message": f"'{field}' doit être un nombre positif."
                    }
                }), 422

    try:
        # Mettre à jour
        persistence_service.update_donnee_extraite(facture_id=facture_id, **validated)

        # Recalculer les warnings
        row = persistence_service.get_facture_by_id(facture_id)

        # Supprimer les MISSING_FIELD pour les champs maintenant remplis
        for field, db_field in [
            ("supplier", "fournisseur"),
            ("invoice_number", "numero_facture"),
            ("date", "date_facture"),
            ("total_ht", "montant_ht"),
            ("vat", "montant_tva"),
            ("total_ttc", "montant_ttc"),
        ]:
            if row.get(db_field) is not None:
                persistence_service.delete_anomalies_by_type(
                    facture_id, f"MISSING_FIELD:{field}"
                )

        # Recalculer AMOUNT_MISMATCH
        ht = row.get("montant_ht")
        vat = row.get("montant_tva")
        ttc = row.get("montant_ttc")
        if all(v is not None for v in [ht, vat, ttc]):
            if abs((float(ht) + float(vat)) - float(ttc)) > AMOUNT_TOLERANCE:
                anomalies = persistence_service.get_anomalies_by_facture_id(facture_id)
                if not any(a["type_anomalie"] == "AMOUNT_MISMATCH" for a in anomalies):
                    persistence_service.create_anomalie(
                        facture_id=facture_id,
                        type_anomalie="AMOUNT_MISMATCH",
                        description="HT + TVA ≠ TTC (après correction manuelle).",
                    )
        else:
            persistence_service.delete_anomalies_by_type(facture_id, "AMOUNT_MISMATCH")

        # Recalculer le statut
        anomalies = persistence_service.get_anomalies_by_facture_id(facture_id)
        has_warnings = len(anomalies) > 0
        new_status = "warning" if has_warnings else "processed"

        row = persistence_service.get_facture_by_id(facture_id)
        persistence_service.update_facture_status(
            facture_id=facture_id,
            type_document=row["type_document"] or "autre",
            statut=new_status,
        )

        return get_invoice(facture_id)

    except Exception as e:
        return jsonify({
            "error": {
                "code": "DB_ERROR",
                "message": "Impossible de mettre à jour la facture.",
                "details": str(e),
            }
        }), 500