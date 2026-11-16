"""
Service de contrôle qualité d'image avec OpenCV.

Détecte 4 types de problèmes :
    1. Flou (variance du Laplacien)
    2. Luminosité insuffisante (moyenne des pixels)
    3. Inclinaison (transformée de Hough)
    4. Mauvais cadrage (analyse des contours)

Retourne un dict structuré conforme au contrat d'API.
"""
import cv2
import numpy as np
import os


# ==================================================
# SEUILS (à ajuster selon les tests réels)
# ==================================================
# Variance du Laplacien : en dessous = flou
# Valeurs typiques : net > 500, acceptable > 100, flou < 100
BLUR_THRESHOLD = 100.0

# Luminosité moyenne : 0 (noir) à 255 (blanc)
# < 50 = trop sombre, > 220 = surexposé
BRIGHTNESS_MIN = 50.0
BRIGHTNESS_MAX = 220.0

# Angle d'inclinaison (en degrés) au-delà duquel on considère mal orienté
SKEW_THRESHOLD_DEG = 5.0

# Pourcentage de marge minimale attendue autour du document (cadrage)
# Si le document occupe moins de 60% de l'image, on considère mal cadré
MIN_DOCUMENT_AREA_RATIO = 0.60


# ==================================================
# 1. DÉTECTION DU FLOU
# ==================================================
def detect_blur(image_gray: np.ndarray) -> dict:
    """
    Détecte le flou via la variance du Laplacien.

    Principe :
        - Un Laplacien calcule les gradients (changements brusques d'intensité).
        - Sur une image nette, les contours sont marqués → variance élevée.
        - Sur une image floue, les contours sont adoucis → variance faible.
    """
    laplacian = cv2.Laplacian(image_gray, cv2.CV_64F)
    variance = float(laplacian.var())

    return {
        "is_blurry": variance < BLUR_THRESHOLD,
        "blur_variance": round(variance, 2),
    }


# ==================================================
# 2. DÉTECTION DE LA LUMINOSITÉ
# ==================================================
def detect_brightness(image_gray: np.ndarray) -> dict:
    """
    Détecte une luminosité insuffisante ou excessive.

    Principe :
        - Moyenne des intensités de tous les pixels.
        - Trop basse → image sombre (illisible pour l'OCR).
        - Trop haute → image surexposée (perte d'information).
    """
    mean = float(np.mean(image_gray))

    return {
        "is_dark": mean < BRIGHTNESS_MIN,
        "is_overexposed": mean > BRIGHTNESS_MAX,
        "brightness_mean": round(mean, 2),
    }


# ==================================================
# 3. DÉTECTION DE L'INCLINAISON
# ==================================================
def detect_skew(image_gray: np.ndarray) -> dict:
    """
    Détecte l'inclinaison via la transformée de Hough.

    Principe :
        - On détecte les lignes droites dans l'image (bords du document).
        - On calcule leur angle par rapport à l'horizontale.
        - La médiane des angles donne l'inclinaison globale.

    Note : pour une image sans lignes détectées, on retourne 0°.
    """
    # Détection des contours
    edges = cv2.Canny(image_gray, 50, 150, apertureSize=3)

    # Transformée de Hough pour détecter les lignes
    lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=200)

    if lines is None:
        # Aucune ligne détectée → pas d'inclinaison mesurable
        return {
            "is_skewed": False,
            "skew_angle": 0.0,
        }

    # Calculer l'angle de chaque ligne
    angles = []
    for line in lines[:20]:  # on limite aux 20 premières pour la performance
        rho, theta = line[0]
        # theta est en radians (0 à π). On le convertit en degrés relatifs à l'horizontale.
        angle_deg = (theta * 180.0 / np.pi) - 90.0
        # On ne garde que les angles proches de l'horizontale (< 45°)
        if abs(angle_deg) < 45:
            angles.append(angle_deg)

    if not angles:
        return {
            "is_skewed": False,
            "skew_angle": 0.0,
        }

    # Médiane des angles (plus robuste que la moyenne)
    median_angle = float(np.median(angles))

    return {
        "is_skewed": abs(median_angle) > SKEW_THRESHOLD_DEG,
        "skew_angle": round(median_angle, 2),
    }


# ==================================================
# 4. DÉTECTION DU MAUVAIS CADRAGE
# ==================================================
def detect_bad_framing(image_gray: np.ndarray) -> dict:
    """
    Détecte un mauvais cadrage.

    Principe :
        - On détecte le plus grand contour rectangulaire (le document).
        - On calcule sa surface relative à l'image totale.
        - Si le document occupe < 60% → mal cadré (trop de marge).
        - Si le contour touche les bords → bords coupés.
    """
    # Binarisation adaptative (robuste aux variations de luminosité)
    binary = cv2.adaptiveThreshold(
        image_gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=11,
        C=2,
    )

    # Détection des contours
    contours, _ = cv2.findContours(
        binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return {
            "is_badly_framed": True,
            "document_area_ratio": 0.0,
        }

    # Prendre le plus grand contour
    largest = max(contours, key=cv2.contourArea)
    doc_area = float(cv2.contourArea(largest))
    total_area = float(image_gray.shape[0] * image_gray.shape[1])

    if total_area == 0:
        return {
            "is_badly_framed": True,
            "document_area_ratio": 0.0,
        }

    ratio = doc_area / total_area

    # Bords coupés : le plus grand contour touche un bord de l'image
    x, y, w, h = cv2.boundingRect(largest)
    img_h, img_w = image_gray.shape
    touches_edge = (
        x <= 5
        or y <= 5
        or (x + w) >= (img_w - 5)
        or (y + h) >= (img_h - 5)
    )

    is_badly_framed = (ratio < MIN_DOCUMENT_AREA_RATIO) or touches_edge

    return {
        "is_badly_framed": is_badly_framed,
        "document_area_ratio": round(ratio, 3),
    }


# ==================================================
# 5. FONCTION PRINCIPALE
# ==================================================
def analyze_quality(image_path: str) -> dict:
    """
    Analyse complète de la qualité d'une image.

    Retourne un dict conforme au contrat d'API :
        {
            "is_blurry": bool,
            "is_dark": bool,
            "is_skewed": bool,
            "is_badly_framed": bool,
            "quality_status": "good" | "warning" | "bad",
            "scores": {
                "blur_variance": float,
                "brightness_mean": float,
                "skew_angle": float,
                "document_area_ratio": float,
            }
        }

    Lève FileNotFoundError si l'image n'existe pas.
    Lève ValueError si l'image ne peut pas être lue.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image introuvable : {image_path}")

    # Lire l'image en niveaux de gris
    image_gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    if image_gray is None:
        raise ValueError(f"Impossible de lire l'image : {image_path}")

    # Appliquer les 4 détections
    blur = detect_blur(image_gray)
    brightness = detect_brightness(image_gray)
    skew = detect_skew(image_gray)
    framing = detect_bad_framing(image_gray)

    # Décider du statut global
    issues = []
    if blur["is_blurry"]:
        issues.append("BLURRY_IMAGE")
    if brightness["is_dark"]:
        issues.append("DARK_IMAGE")
    if brightness["is_overexposed"]:
        issues.append("OVEREXPOSED_IMAGE")
    if skew["is_skewed"]:
        issues.append("SKEWED_IMAGE")
    if framing["is_badly_framed"]:
        issues.append("BAD_FRAMING")

    # Statut :
    #   - "good"    : aucun problème
    #   - "warning" : 1 ou 2 problèmes (traitement possible mais risqué)
    #   - "bad"     : 3+ problèmes (traitement déconseillé)
    if len(issues) == 0:
        quality_status = "good"
    elif len(issues) <= 2:
        quality_status = "warning"
    else:
        quality_status = "bad"

    return {
        "is_blurry": blur["is_blurry"],
        "is_dark": brightness["is_dark"],
        "is_skewed": skew["is_skewed"],
        "is_badly_framed": framing["is_badly_framed"],
        "quality_status": quality_status,
        "scores": {
            "blur_variance": blur["blur_variance"],
            "brightness_mean": brightness["brightness_mean"],
            "skew_angle": skew["skew_angle"],
            "document_area_ratio": framing["document_area_ratio"],
        },
        "issues": issues,
    }