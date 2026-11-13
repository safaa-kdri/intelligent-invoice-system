"""
Routes pour la gestion des factures.
Blueprint Flask monté sur /api/invoices
"""
import os
import uuid
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename


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
    Reçoit un fichier, le valide, le sauvegarde et retourne un JSON structuré.
    Pipeline IA (OpenCV + CNN + OCR) pas encore branché.
    """
    # 1. Vérifier la présence d'un fichier
    if "file" not in request.files:
        return jsonify({
            "error": {
                "code": "NO_FILE",
                "message": "Aucun fichier n'a été fourni dans la requête."
            }
        }), 400

    f = request.files["file"]

    # 2. Vérifier qu'un fichier est bien nommé
    if f.filename == "":
        return jsonify({
            "error": {
                "code": "NO_FILE",
                "message": "Le fichier fourni n'a pas de nom."
            }
        }), 400

    # 3. Vérifier l'extension
    if not allowed_file(f.filename):
        return jsonify({
            "error": {
                "code": "INVALID_FORMAT",
                "message": "Format non supporté. Utilisez PDF, JPG, JPEG ou PNG.",
                "details": f"Extension reçue : .{f.filename.rsplit('.', 1)[-1].lower()}"
            }
        }), 415

    # 4. Vérifier la taille (en lisant dans un flux temporaire)
    # On lit tout le contenu pour connaître la taille
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

    # 5. Sauvegarder avec un nom unique (UUID + nom sécurisé)
    original_name = secure_filename(f.filename)
    ext = original_name.rsplit(".", 1)[1].lower() if "." in original_name else ""
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(UPLOAD_FOLDER, unique_name)
    f.save(save_path)

    # 6. TODO : insérer dans MySQL + appeler modules IA
    # Pour l'instant : réponse factice conforme au contrat d'API

    return jsonify({
        "id": 0,
        "filename": unique_name,
        "status": "processed",
        "classification": {
            "label": "facture_achat",
            "confidence": 0.0
        },
        "quality": {
            "is_blurry": False,
            "is_dark": False,
            "is_skewed": False,
            "is_badly_framed": False,
            "quality_status": "good",
            "scores": {
                "blur_variance": 0.0,
                "brightness_mean": 0.0,
                "skew_angle": 0.0
            }
        },
        "extracted": {
            "supplier": None,
            "invoice_number": None,
            "date": None,
            "total_ht": None,
            "vat": None,
            "total_ttc": None
        },
        "validation": {
            "is_valid": False,
            "warnings": ["PIPELINE_IA_NOT_CONNECTED"]
        },
        "ocr_text": "",
        "created_at": None
    }), 200