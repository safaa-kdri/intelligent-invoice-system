"""
Tests du module quality_service.
Génère des images synthétiques pour valider chaque détection.

À exécuter : python -m tests.test_quality
"""
import os
import cv2
import numpy as np
from services.quality_service import analyze_quality


TMP_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads", "_test_quality")
os.makedirs(TMP_DIR, exist_ok=True)


def create_test_image(name: str, transform) -> str:
    """Crée une image de test avec une transformation donnée."""
    # Base : image blanche avec un rectangle noir (simule un document)
    img = np.ones((600, 800, 3), dtype=np.uint8) * 255
    cv2.rectangle(img, (100, 100), (700, 500), (0, 0, 0), 2)
    cv2.putText(img, "FACTURE TEST", (200, 250),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 3)
    cv2.putText(img, "Total: 1200.00 MAD", (200, 350),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

    img = transform(img)
    path = os.path.join(TMP_DIR, name)
    cv2.imwrite(path, img)
    return path


def test_blur():
    """Vérifie la détection du flou."""
    print("\n[TEST] Détection du flou")

    # Image nette (référence)
    def identity(img): return img
    path_net = create_test_image("net.png", identity)
    result_net = analyze_quality(path_net)
    print(f"  Net     : blur_variance = {result_net['scores']['blur_variance']:.1f}, "
          f"is_blurry = {result_net['is_blurry']}")

    # Image floue (flou gaussien)
    def apply_blur(img): return cv2.GaussianBlur(img, (31, 31), 0)
    path_flou = create_test_image("flou.png", apply_blur)
    result_flou = analyze_quality(path_flou)
    print(f"  Flou    : blur_variance = {result_flou['scores']['blur_variance']:.1f}, "
          f"is_blurry = {result_flou['is_blurry']}")

    assert not result_net["is_blurry"], "Une image nette ne doit pas être détectée comme floue"
    assert result_flou["is_blurry"], "Une image floue doit être détectée comme floue"
    print("  ✅ OK")


def test_dark():
    """Vérifie la détection de luminosité insuffisante."""
    print("\n[TEST] Détection de la luminosité")

    # Image lumineuse (référence)
    def identity(img): return img
    path_lum = create_test_image("lumineux.png", identity)
    result_lum = analyze_quality(path_lum)
    print(f"  Lumineux : brightness_mean = {result_lum['scores']['brightness_mean']:.1f}, "
          f"is_dark = {result_lum['is_dark']}")

    # Image sombre
    def apply_dark(img): return (img * 0.15).astype(np.uint8)
    path_sombre = create_test_image("sombre.png", apply_dark)
    result_sombre = analyze_quality(path_sombre)
    print(f"  Sombre   : brightness_mean = {result_sombre['scores']['brightness_mean']:.1f}, "
          f"is_dark = {result_sombre['is_dark']}")

    assert not result_lum["is_dark"], "Une image lumineuse ne doit pas être détectée comme sombre"
    assert result_sombre["is_dark"], "Une image sombre doit être détectée comme sombre"
    print("  ✅ OK")


def test_skew():
    """Vérifie la détection d'inclinaison."""
    print("\n[TEST] Détection de l'inclinaison")

    # Image droite (référence)
    def identity(img): return img
    path_droite = create_test_image("droite.png", identity)
    result_droite = analyze_quality(path_droite)
    print(f"  Droite    : skew_angle = {result_droite['scores']['skew_angle']:.2f}°, "
          f"is_skewed = {result_droite['is_skewed']}")

    # Image inclinée à 15°
    def apply_rotation(img):
        h, w = img.shape[:2]
        M = cv2.getRotationMatrix2D((w // 2, h // 2), 15, 1.0)
        return cv2.warpAffine(img, M, (w, h), borderValue=(255, 255, 255))
    path_inclinee = create_test_image("inclinee.png", apply_rotation)
    result_inclinee = analyze_quality(path_inclinee)
    print(f"  Inclinée  : skew_angle = {result_inclinee['scores']['skew_angle']:.2f}°, "
          f"is_skewed = {result_inclinee['is_skewed']}")

    # Note : Hough peut donner un angle inversé, on vérifie juste la valeur absolue
    assert not result_droite["is_skewed"], "Une image droite ne doit pas être détectée comme inclinée"
    assert result_inclinee["is_skewed"], "Une image inclinée doit être détectée comme inclinée"
    print("  ✅ OK")


def test_quality_status():
    """Vérifie le calcul du statut global."""
    print("\n[TEST] Statut global")

    # Image nette et lumineuse → devrait être "good"
    def identity(img): return img
    path_good = create_test_image("good.png", identity)
    result_good = analyze_quality(path_good)
    print(f"  Image saine   : quality_status = {result_good['quality_status']}, "
          f"issues = {result_good['issues']}")

    # Image très dégradée → devrait être "bad"
    def apply_bad(img):
        img = cv2.GaussianBlur(img, (51, 51), 0)
        img = (img * 0.1).astype(np.uint8)
        return img
    path_bad = create_test_image("bad.png", apply_bad)
    result_bad = analyze_quality(path_bad)
    print(f"  Image dégradée : quality_status = {result_bad['quality_status']}, "
          f"issues = {result_bad['issues']}")

    assert result_good["quality_status"] in ("good", "warning")
    assert result_bad["quality_status"] == "bad", \
        f"Une image très dégradée doit être 'bad', pas '{result_bad['quality_status']}'"
    print("  ✅ OK")


def run_all_tests():
    print("=" * 60)
    print("TESTS DU MODULE QUALITY_SERVICE")
    print("=" * 60)

    test_blur()
    test_dark()
    test_skew()
    test_quality_status()

    print("\n" + "=" * 60)
    print("🎉 TOUS LES TESTS SONT PASSÉS")
    print("=" * 60)
    print(f"\nImages de test conservées dans : {TMP_DIR}")


if __name__ == "__main__":
    run_all_tests()