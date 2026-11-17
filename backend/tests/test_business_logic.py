"""
Tests du module business_logic_service.

À exécuter : python -m tests.test_business_logic
"""
from services.business_logic_service import detect_ocr_hint, refine_classification


def test_detect_hint():
    print("\n[TEST] Détection des indices OCR")
    cases = [
        ("Client : Marjane", "vente"),
        ("Fournisseur : Inwi", "achat"),
        ("FACTURE CLIENT", "vente"),
        ("FACTURE FOURNISSEUR", "achat"),
        ("Destinataire : Sté ABC", "vente"),
        ("Émetteur : Sté XYZ", "achat"),
        ("Document divers", "indetermine"),
        ("", "indetermine"),
    ]

    for text, expected in cases:
        result = detect_ocr_hint(text)
        status = "✅" if result["hint"] == expected else "❌"
        print(f"  {status} '{text[:40]:40s}' → {result['hint']:15s} (attendu: {expected})")
        assert result["hint"] == expected, f"Attendu {expected}, obtenu {result['hint']}"

    print("  ✅ Tous les cas OK")


def test_refine_correction():
    print("\n[TEST] Correction CNN par OCR")

    # Cas 1 : CNN dit vente, OCR dit achat → correction
    ocr_achat = {"raw_text": "Fournisseur : Inwi\nFACTURE\nTOTAL TTC : 1000.00 MAD"}
    result = refine_classification("facture_vente", 0.85, ocr_achat)
    print(f"  CNN 'vente' + OCR 'achat' → {result['final_label']} (corrigé: {result['corrected']})")
    assert result["final_label"] == "facture_achat"
    assert result["corrected"] is True

    # Cas 2 : CNN dit achat, OCR dit vente → correction
    ocr_vente = {"raw_text": "Client : Marjane\nFACTURE CLIENT\nTOTAL TTC : 1000.00 MAD"}
    result = refine_classification("facture_achat", 0.85, ocr_vente)
    print(f"  CNN 'achat' + OCR 'vente' → {result['final_label']} (corrigé: {result['corrected']})")
    assert result["final_label"] == "facture_vente"
    assert result["corrected"] is True

    # Cas 3 : CNN dit achat, OCR dit achat → pas de correction
    result = refine_classification("facture_achat", 0.90, ocr_achat)
    print(f"  CNN 'achat' + OCR 'achat' → {result['final_label']} (corrigé: {result['corrected']})")
    assert result["final_label"] == "facture_achat"
    assert result["corrected"] is False

    # Cas 4 : CNN dit "autre" → jamais corrigé
    result = refine_classification("autre", 0.80, ocr_achat)
    print(f"  CNN 'autre' + OCR 'achat' → {result['final_label']} (corrigé: {result['corrected']})")
    assert result["final_label"] == "autre"
    assert result["corrected"] is False

    print("  ✅ Tous les cas OK")


def run_all_tests():
    print("=" * 60)
    print("TESTS DU MODULE BUSINESS_LOGIC_SERVICE")
    print("=" * 60)

    test_detect_hint()
    test_refine_correction()

    print("\n" + "=" * 60)
    print("🎉 TOUS LES TESTS SONT PASSÉS")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()