"""
Tests fonctionnels automatisés (T01 → T11).

Ces tests couvrent les cas du rapport :
    T01 : Importer une image valide
    T02 : Importer un fichier non autorisé
    T03 : Importer un PDF valide
    T04 : Détecter une image floue
    T05 : Classifier une facture d'achat
    T06 : Classifier une facture de vente
    T07 : Classifier un autre document
    T08 : Extraire les informations
    T09 : Corriger un champ
    T10 : Détecter un doublon potentiel
    T11 : Consulter l'historique

À exécuter : python -m tests.test_functional
"""
import os
import io
import json
import time
import requests
import numpy as np
from PIL import Image

BASE_URL = "http://localhost:5000"
AI_DATASET = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "ai", "dataset", "test"
)

# Compteurs globaux
results = {"pass": 0, "fail": 0, "details": []}


def log_result(test_id: str, name: str, success: bool, message: str = ""):
    """Enregistre le résultat d'un test."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"  {status} | {test_id} : {name}")
    if message:
        print(f"         → {message}")
    results["details"].append({
        "test_id": test_id,
        "name": name,
        "success": success,
        "message": message,
    })
    if success:
        results["pass"] += 1
    else:
        results["fail"] += 1


def create_test_image(color: str = "white", size=(800, 600), text: str = "") -> bytes:
    """Crée une image de test en mémoire."""
    img = Image.new("RGB", size, color)
    if text:
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.text((50, 50), text, fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def get_dataset_image(cls: str, index: int = 0) -> str | None:
    """Récupère le chemin d'une image du dataset."""
    class_dir = os.path.join(AI_DATASET, cls)
    if not os.path.exists(class_dir):
        return None
    files = sorted([f for f in os.listdir(class_dir) if f.endswith(".png")])
    if index >= len(files):
        return None
    return os.path.join(class_dir, files[index])


# ==================================================
# TESTS
# ==================================================
def test_T01_valid_image():
    """T01 : Importer une image valide."""
    print("\n[T01] Importer une image valide")
    img_path = get_dataset_image("facture_achat", 0)
    if not img_path:
        log_result("T01", "Importer une image valide", False, "Image de test introuvable")
        return

    with open(img_path, "rb") as f:
        files = {"file": ("test.png", f, "image/png")}
        r = requests.post(f"{BASE_URL}/api/invoices/upload", files=files)

    success = r.status_code == 200 and "id" in r.json()
    log_result("T01", "Importer une image valide", success,
               f"HTTP {r.status_code}, id={r.json().get('id') if success else 'N/A'}")
    return r.json().get("id") if success else None


def test_T02_invalid_format():
    """T02 : Importer un fichier non autorisé (.txt)."""
    print("\n[T02] Importer un fichier non autorisé")
    buf = io.BytesIO(b"fake content")
    files = {"file": ("test.txt", buf, "text/plain")}
    r = requests.post(f"{BASE_URL}/api/invoices/upload", files=files)

    success = r.status_code == 415 and r.json().get("error", {}).get("code") == "INVALID_FORMAT"
    log_result("T02", "Importer un fichier non autorisé", success,
               f"HTTP {r.status_code} (attendu: 415)")


def test_T03_valid_pdf():
    """T03 : Importer un PDF valide."""
    print("\n[T03] Importer un PDF valide")
    # Créer un PDF minimal (juste l'en-tête, pas un vrai PDF lisible par OCR)
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF"
    files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    r = requests.post(f"{BASE_URL}/api/invoices/upload", files=files)

    success = r.status_code == 200 and "id" in r.json()
    log_result("T03", "Importer un PDF valide", success, f"HTTP {r.status_code}")


def test_T04_blurry_image():
    """T04 : Détecter une image floue."""
    print("\n[T04] Détecter une image floue")
    # Créer une image floue synthétique
    from PIL import ImageFilter
    img = Image.new("RGB", (800, 600), "white")
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.text((50, 50), "FACTURE TEST", fill="black")
    img = img.filter(ImageFilter.GaussianBlur(radius=20))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    files = {"file": ("blurry.png", buf, "image/png")}
    r = requests.post(f"{BASE_URL}/api/invoices/upload", files=files)

    if r.status_code != 200:
        log_result("T04", "Détecter une image floue", False, f"HTTP {r.status_code}")
        return

    warnings = r.json().get("validation", {}).get("warnings", [])
    success = "BLURRY_IMAGE" in warnings
    log_result("T04", "Détecter une image floue", success,
               f"Warnings: {warnings}")


def test_T05_to_T07_classification():
    """T05, T06, T07 : Tester la classification sur les 3 classes."""
    print("\n[T05-T07] Classification des 3 classes")
    expected_classes = [
        ("T05", "facture_achat", "Classifier une facture d'achat"),
        ("T06", "facture_vente", "Classifier une facture de vente"),
        ("T07", "autre", "Classifier un autre document"),
    ]

    for test_id, cls, name in expected_classes:
        print(f"\n  [{test_id}] {name}")
        img_path = get_dataset_image(cls, 0)
        if not img_path:
            log_result(test_id, name, False, "Image de test introuvable")
            continue

        with open(img_path, "rb") as f:
            files = {"file": ("test.png", f, "image/png")}
            r = requests.post(f"{BASE_URL}/api/invoices/upload", files=files)

        if r.status_code != 200:
            log_result(test_id, name, False, f"HTTP {r.status_code}")
            continue

        data = r.json()
        predicted = data["classification"]["label"]
        success = predicted == cls
        log_result(test_id, name, success,
                   f"Prédit: {predicted} (attendu: {cls})")


def test_T08_extraction():
    """T08 : Extraire les informations."""
    print("\n[T08] Extraire les informations")
    img_path = get_dataset_image("facture_achat", 0)
    if not img_path:
        log_result("T08", "Extraire les informations", False, "Image introuvable")
        return

    with open(img_path, "rb") as f:
        files = {"file": ("test.png", f, "image/png")}
        r = requests.post(f"{BASE_URL}/api/invoices/upload", files=files)

    if r.status_code != 200:
        log_result("T08", "Extraire les informations", False, f"HTTP {r.status_code}")
        return

    data = r.json()
    extracted = data.get("extracted", {})
    nb_filled = sum(1 for v in extracted.values() if v is not None)
    success = nb_filled >= 3  # Au moins 3 champs sur 6
    log_result("T08", "Extraire les informations", success,
               f"{nb_filled}/6 champs extraits : {list(k for k,v in extracted.items() if v is not None)}")


def test_T09_correction():
    """T09 : Corriger un champ."""
    print("\n[T09] Corriger un champ")
    # D'abord uploader
    img_path = get_dataset_image("facture_achat", 0)
    if not img_path:
        log_result("T09", "Corriger un champ", False, "Image introuvable")
        return

    with open(img_path, "rb") as f:
        files = {"file": ("test.png", f, "image/png")}
        r = requests.post(f"{BASE_URL}/api/invoices/upload", files=files)

    if r.status_code != 200:
        log_result("T09", "Corriger un champ", False, "Upload échoué")
        return

    facture_id = r.json()["id"]

    # Ensuite corriger
    correction = {"supplier": "Test Supplier SARL", "total_ht": 1000.00}
    r = requests.put(f"{BASE_URL}/api/invoices/{facture_id}", json=correction)

    if r.status_code != 200:
        log_result("T09", "Corriger un champ", False, f"PUT HTTP {r.status_code}")
        return

    updated = r.json()
    success = (
        updated["extracted"]["supplier"] == "Test Supplier SARL"
        and updated["extracted"]["total_ht"] == 1000.00
    )
    log_result("T09", "Corriger un champ", success,
               f"Fournisseur: {updated['extracted']['supplier']}")


def test_T10_duplicate_detection():
    """T10 : Détecter un doublon potentiel."""
    print("\n[T10] Détecter un doublon potentiel")
    # Uploader deux fois la même image
    img_path = get_dataset_image("facture_achat", 0)
    if not img_path:
        log_result("T10", "Détecter un doublon", False, "Image introuvable")
        return

    # Upload 1
    with open(img_path, "rb") as f:
        files = {"file": ("test.png", f, "image/png")}
        r1 = requests.post(f"{BASE_URL}/api/invoices/upload", files=files)

    # Upload 2 (même fichier)
    with open(img_path, "rb") as f:
        files = {"file": ("test.png", f, "image/png")}
        r2 = requests.post(f"{BASE_URL}/api/invoices/upload", files=files)

    if r1.status_code != 200 or r2.status_code != 200:
        log_result("T10", "Détecter un doublon", False, "Upload échoué")
        return

    warnings2 = r2.json().get("validation", {}).get("warnings", [])
    success = "POTENTIAL_DUPLICATE" in warnings2
    log_result("T10", "Détecter un doublon potentiel", success,
               f"Warnings: {warnings2}")
    # Note : cette fonctionnalité n'est pas encore implémentée, on documente


def test_T11_history():
    """T11 : Consulter l'historique."""
    print("\n[T11] Consulter l'historique")
    r = requests.get(f"{BASE_URL}/api/invoices?limit=5")

    if r.status_code != 200:
        log_result("T11", "Consulter l'historique", False, f"HTTP {r.status_code}")
        return

    data = r.json()
    success = "invoices" in data and data.get("total", 0) >= 0
    log_result("T11", "Consulter l'historique", success,
               f"{data.get('total', 0)} factures, {len(data.get('invoices', []))} retournées")


# ==================================================
# MAIN
# ==================================================
def run_all_tests():
    print("=" * 70)
    print("TESTS FONCTIONNELS (T01 → T11)")
    print("=" * 70)
    print(f"Backend : {BASE_URL}")
    print(f"Dataset : {AI_DATASET}\n")

    # Vérifier que le backend est accessible
    try:
        r = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if r.status_code != 200:
            print("❌ Backend non accessible. Lancez `python app.py` dans un autre terminal.")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Backend non accessible. Lancez `python app.py` dans un autre terminal.")
        return

    start_time = time.time()

    # Exécuter les tests
    test_T01_valid_image()
    test_T02_invalid_format()
    test_T03_valid_pdf()
    test_T04_blurry_image()
    test_T05_to_T07_classification()
    test_T08_extraction()
    test_T09_correction()
    test_T10_duplicate_detection()
    test_T11_history()

    elapsed = time.time() - start_time

    # Résumé
    print("\n" + "=" * 70)
    print("RÉSUMÉ")
    print("=" * 70)
    total = results["pass"] + results["fail"]
    print(f"✅ Réussis : {results['pass']}/{total}")
    print(f"❌ Échoués : {results['fail']}/{total}")
    print(f"⏱️  Durée   : {elapsed:.1f}s")

    # Sauvegarder les résultats en JSON
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "docs", "test-results.json"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n📄 Résultats sauvegardés : {output_path}")


if __name__ == "__main__":
    run_all_tests()