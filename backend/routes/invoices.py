"""
Routes pour la gestion des factures.
Blueprint Flask monté sur /api/invoices
"""
import os
import uuid
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

from services import persistence_service


# Création du blueprint
invoices_bp = Blueprint("invoices", __name__)


# Constantes de configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 Mo


# S'assurer que le dossier uploads existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename: str) -> bool:
    """Vérifie que l'extension du fichier est autorisée."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@invoices_bp.route("/upload", methods=["POST"])
def upload():
    """
    Reçoit un fichier, le valide, le sauvegarde, l'enregistre dans MySQL
    et retourne un JSON structuré conforme au contrat d'API.

    Le pipeline IA (OpenCV + CNN + OCR) sera branché à l'étape suivante.
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

    # ===== 3. Vérifier la taille et la vacuité =====
    content = f.read()
    f.seek(0)  # remettre le curseur au début pour la sauvegarde

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

    # ===== 5. Insérer dans MySQL =====
    try:
        # 5a. Créer la facture avec statut 'pending'
        facture_id = persistence_service.create_facture(
            nom_fichier=unique_name,
            chemin_fichier=save_path,
        )

        # 5b. Résultats IA factices (le vrai pipeline viendra à l'étape suivante)
        classification_label = "facture_achat"
        classification_confidence = 0.0
        quality_status = "good"
        ocr_text = ""
        warnings = ["PIPELINE_IA_NOT_CONNECTED"]

        # 5c. Insérer le résultat d'analyse
        persistence_service.create_resultat_analyse(
            facture_id=facture_id,
            confiance=classification_confidence,
            qualite=quality_status,
            texte_ocr=ocr_text,
        )

        # 5d. Insérer les warnings dans la table anomalie
        for warning in warnings:
            persistence_service.create_anomalie(
                facture_id=facture_id,
                type_anomalie=warning,
                description="Avertissement généré par le pipeline (factice pour l'instant).",
            )

        # 5e. Insérer les données extraites (vides pour l'instant)
        persistence_service.create_donnee_extraite(
            facture_id=facture_id,
            fournisseur=None,
            numero_facture=None,
            date_facture=None,
            montant_ht=None,
            montant_tva=None,
            montant_ttc=None,
        )

        # 5f. Mettre à jour la facture avec le label et le statut final
        final_status = "processed" if not warnings else "warning"
        persistence_service.update_facture_status(
            facture_id=facture_id,
            type_document=classification_label,
            statut=final_status,
        )

        # 5g. Récupérer la date d'insertion depuis MySQL
        facture_row = persistence_service.get_facture_by_id(facture_id)
        created_at = (
            facture_row["date_importation"].isoformat()
            if facture_row and facture_row["date_importation"]
            else None
        )

        # ===== 6. Retourner le JSON conforme au contrat d'API =====
        return jsonify({
            "id": facture_id,
            "filename": unique_name,
            "status": final_status,
            "classification": {
                "label": classification_label,
                "confidence": classification_confidence,
            },
            "quality": {
                "is_blurry": False,
                "is_dark": False,
                "is_skewed": False,
                "is_badly_framed": False,
                "quality_status": quality_status,
                "scores": {
                    "blur_variance": 0.0,
                    "brightness_mean": 0.0,
                    "skew_angle": 0.0,
                },
            },
            "extracted": {
                "supplier": None,
                "invoice_number": None,
                "date": None,
                "total_ht": None,
                "vat": None,
                "total_ttc": None,
            },
            "validation": {
                "is_valid": len(warnings) == 0,
                "warnings": warnings,
            },
            "ocr_text": ocr_text,
            "created_at": created_at,
        }), 200

    except Exception as e:
        # En cas d'erreur MySQL, on supprime le fichier déjà sauvegardé
        # et on retourne une erreur 500 conforme au contrat
        try:
            if os.path.exists(save_path):
                os.remove(save_path)
        except Exception:
            pass

        return jsonify({
            "error": {
                "code": "DB_ERROR",
                "message": "Impossible d'enregistrer la facture en base de données.",
                "details": str(e),
            }
        }), 500


# ==================================================
# GET /api/invoices — liste paginée
# ==================================================
@invoices_bp.route("", methods=["GET"])
def list_invoices():
    """
    Retourne la liste paginée des factures.
    Query params :
        - page (int, défaut 1)
        - limit (int, défaut 20, max 100)
        - status (processed | warning | failed)
        - label (facture_achat | facture_vente | autre)
    """
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
        "total": total,
        "page": page,
        "limit": limit,
        "invoices": invoices,
    }), 200


# ==================================================
# GET /api/invoices/<id> — détail d'une facture
# ==================================================
@invoices_bp.route("/<int:facture_id>", methods=["GET"])
def get_invoice(facture_id: int):
    """
    Retourne le détail complet d'une facture (facture + analyse + extrait).
    """
    row = persistence_service.get_facture_by_id(facture_id)
    if row is None:
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": f"Aucune facture trouvée avec l'identifiant {facture_id}."
            }
        }), 404

    anomalies = persistence_service.get_anomalies_by_facture_id(facture_id)

    # Construire la réponse conforme au contrat d'API
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
            "scores": {
                "blur_variance": 0.0,
                "brightness_mean": 0.0,
                "skew_angle": 0.0,
            },
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
# DELETE /api/invoices/<id> — supprimer une facture
# ==================================================
@invoices_bp.route("/<int:facture_id>", methods=["DELETE"])
def delete_invoice(facture_id: int):
    """
    Supprime une facture et toutes ses données associées (CASCADE).
    """
    if not persistence_service.facture_exists(facture_id):
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": f"Aucune facture trouvée avec l'identifiant {facture_id}."
            }
        }), 404

    # Supprimer le fichier physique
    row = persistence_service.get_facture_by_id(facture_id)
    if row and row.get("chemin_fichier"):
        try:
            if os.path.exists(row["chemin_fichier"]):
                os.remove(row["chemin_fichier"])
        except Exception:
            pass  # on ignore si le fichier ne peut pas être supprimé

    # Supprimer en base (CASCADE supprime les tables liées)
    persistence_service.delete_facture(facture_id)

    return jsonify({"id": facture_id, "status": "deleted"}), 200


# ==================================================
# GET /api/invoices/<id>/export — téléchargement JSON
# ==================================================
@invoices_bp.route("/<int:facture_id>/export", methods=["GET"])
def export_invoice(facture_id: int):
    """
    Retourne le détail d'une facture en JSON téléchargeable.
    """
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