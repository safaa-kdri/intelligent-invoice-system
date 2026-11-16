"""
Service de classification d'images avec MobileNetV2.

Charge le modèle entraîné (ai/models/mobilenetv2_invoice.h5) une seule fois
au démarrage de l'application, puis expose une fonction `predict()` pour
classifier de nouvelles images.

Classes : facture_achat, facture_vente, autre
"""
import os
import numpy as np
from PIL import Image
import tensorflow as tf

# ==================================================
# CONFIGURATION
# ==================================================
IMG_SIZE = (224, 224)
CLASSES = ["facture_achat", "facture_vente", "autre"]

# Chemin vers le modèle (relatif au dossier backend/)
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(
    os.path.dirname(BACKEND_DIR), "ai", "models", "mobilenetv2_invoice.h5"
)


# ==================================================
# CHARGEMENT DU MODÈLE (une seule fois)
# ==================================================
_model = None


def _load_model():
    """Charge le modèle une seule fois (lazy loading)."""
    global _model
    if _model is not None:
        return _model

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Modèle introuvable : {MODEL_PATH}. "
            "Avez-vous lancé `python ai/train.py` ?"
        )

    print(f"Chargement du modèle CNN : {MODEL_PATH}")
    _model = tf.keras.models.load_model(MODEL_PATH)
    print("✅ Modèle chargé")
    return _model


# ==================================================
# PRÉDICTION
# ==================================================
def predict(image_path: str) -> tuple[str, float]:
    """
    Classifie une image.

    Args:
        image_path: chemin vers l'image (JPG, JPEG, PNG)

    Returns:
        (label, confidence) où :
            - label est l'une des 3 classes : facture_achat / facture_vente / autre
            - confidence est un float entre 0.0 et 1.0

    Raises:
        FileNotFoundError si l'image n'existe pas
        ValueError si l'image ne peut pas être lue
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image introuvable : {image_path}")

    model = _load_model()

    # Charger et prétraiter l'image
    try:
        img = Image.open(image_path).convert("RGB").resize(IMG_SIZE)
    except Exception as e:
        raise ValueError(f"Impossible de lire l'image : {e}")

    # Normalisation : pixels 0-255 → -1 à 1 (pré-entraînement MobileNetV2)
    arr = np.array(img, dtype=np.float32)
    arr = (arr / 127.5) - 1.0
    arr = np.expand_dims(arr, axis=0)  # ajouter la dimension batch

    # Prédiction
    probs = model.predict(arr, verbose=0)[0]
    pred_idx = int(np.argmax(probs))
    confidence = float(probs[pred_idx])
    label = CLASSES[pred_idx]

    return label, confidence


def predict_proba(image_path: str) -> dict:
    """
    Retourne les probabilités pour toutes les classes.
    Utile pour déboguer ou afficher un graphique de confiance.

    Returns:
        {"facture_achat": 0.95, "facture_vente": 0.03, "autre": 0.02}
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image introuvable : {image_path}")

    model = _load_model()

    try:
        img = Image.open(image_path).convert("RGB").resize(IMG_SIZE)
    except Exception as e:
        raise ValueError(f"Impossible de lire l'image : {e}")

    arr = np.array(img, dtype=np.float32)
    arr = (arr / 127.5) - 1.0
    arr = np.expand_dims(arr, axis=0)

    probs = model.predict(arr, verbose=0)[0]

    return {cls: float(probs[i]) for i, cls in enumerate(CLASSES)}


# ==================================================
# TEST RAPIDE (si exécuté directement)
# ==================================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage : python -m services.classification_service <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    label, conf = predict(image_path)
    print(f"\nImage     : {image_path}")
    print(f"Prédiction : {label}")
    print(f"Confiance  : {conf * 100:.2f}%")

    print("\nProbabilités par classe :")
    for cls, p in predict_proba(image_path).items():
        print(f"  {cls:15s} : {p * 100:.2f}%")