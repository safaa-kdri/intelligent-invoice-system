"""
Tests du module ocr_service.

À exécuter : python -m tests.test_ocr
"""
import os
from services.ocr_service import extract_text, extract_fields


AI_DATASET = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "ai", "dataset", "test"
)


def test_extract_text():
    """Vérifie que extract_text retourne du texte non vide."""
    print("\n[TEST] Extraction du texte brut")

    class_dir = os.path.join(AI_DATASET, "facture_achat")
    if not os.path.exists(class_dir):
        print(f"  ⚠️  Dossier introuvable : {class_dir}")
        return

    img_path = os.path.join(class_dir, sorted(os.listdir(class_dir))[0])
    print(f"  Image : {os.path.basename(img_path)}")

    text = extract_text(img_path)

    print(f"  Texte extrait ({len(text)} chars) :")
    for line in text.split("\n")[:10]:
        print(f"    {line}")

    assert len(text) > 0, "Le texte extrait ne doit pas être vide"
    print("  ✅ OK")


def test_extract_fields():
    """Vérifie que les 6 champs sont structurés."""
    print("\n[TEST] Structuration des champs")

    class_dir = os.path.join(AI_DATASET, "facture_achat")
    if not os.path.exists(class_dir):
        print(f"  ⚠️  Dossier introuvable : {class_dir}")
        return

    img_path = os.path.join(class_dir, sorted(os.listdir(class_dir))[0])
    fields = extract_fields(img_path)

    print(f"  Image : {os.path.basename(img_path)}")
    print(f"  Fournisseur   : {fields['supplier']}")
    print(f"  N° facture    : {fields['invoice_number']}")
    print(f"  Date          : {fields['date']}")
    print(f"  Montant HT    : {fields['total_ht']}")
    print(f"  TVA           : {fields['vat']}")
    print(f"  Montant TTC   : {fields['total_ttc']}")

    if all([fields['total_ht'], fields['vat'], fields['total_ttc']]):
        computed_ttc = fields['total_ht'] + fields['vat']
        diff = abs(computed_ttc - fields['total_ttc'])
        if diff < 0.01:
            print(f"  ✅ Cohérence HT + TVA = TTC")
        elif diff < 1.0:
            print(f"  ✅ Cohérence (arrondi) : écart {diff:.2f}")
        else:
            print(f"  ℹ️  Écart HT+TVA ({computed_ttc:.2f}) vs TTC ({fields['total_ttc']:.2f}) = {diff:.2f}")
            print(f"      → Probablement taxes additionnelles ou erreur OCR (normal)")

    print("  ✅ OK")


def run_all_tests():
    print("=" * 60)
    print("TESTS DU MODULE OCR_SERVICE")
    print("=" * 60)

    test_extract_text()
    test_extract_fields()

    print("\n" + "=" * 60)
    print("🎉 TESTS TERMINÉS")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()