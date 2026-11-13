"""
Point d'entrée Flask — Système intelligent de traitement des factures.
Lance le serveur sur http://localhost:5000
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Charge les variables d'environnement (.env)
load_dotenv()

# Import des blueprints
from routes.invoices import invoices_bp


def create_app():
    """Factory Flask — crée et configure l'application."""
    app = Flask(__name__)

    # Active CORS pour autoriser http://localhost:3000 (Next.js)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Configuration
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 Mo
    app.config["UPLOAD_FOLDER"] = os.path.join(
        os.path.dirname(__file__), "uploads"
    )

    # Enregistrement des blueprints
    app.register_blueprint(invoices_bp, url_prefix="/api/invoices")

    # Route de santé
    @app.route("/api/health")
    def health():
        return jsonify({
            "status": "ok",
            "service": "intelligent-invoice-system",
            "version": "1.0"
        })

    # Gestionnaire d'erreur 413 (fichier trop volumineux)
    @app.errorhandler(413)
    def request_entity_too_large(e):
        return jsonify({
            "error": {
                "code": "FILE_TOO_LARGE",
                "message": "Le fichier dépasse la taille maximale de 10 Mo."
            }
        }), 413

    # Gestionnaire d'erreur 404
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": "Route introuvable."
            }
        }), 404

    # Gestionnaire d'erreur 500
    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Erreur interne du serveur."
            }
        }), 500

    return app


# Création de l'application (utilisée par flask run et python app.py)
app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    print(f"🚀 Démarrage du serveur Flask sur http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)