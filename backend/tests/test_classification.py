"""
Tests du module classification_service.

À exécuter : python -m tests.test_classification
"""
import os
from services.classification_service import predict, predict_proba, CLASSES


AI_DATASET = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "ai", "dataset", "test"
)


def test_predictions_on_dataset():
    """Teste le CNN sur une image de chaque classe du dataset test."""
    print("=" * 60)
    print("TESTS DU MODULE CLASSIFICATION_SERVICE")
    print("=" * 60)

    total = 0
    correct = 0

    for expected_class in CLASSES:
        class_dir = os.path.join(AI_DATASET, expected_class)
        if not os.path.exists(class_dir):
            print(f"\n⚠️  Dossier introuvable : {class_dir}")
            continue

        # Prendre les 3 premières images de chaque classe
        images = sorted(os.listdir(class_dir))[:3]
        print(f"\n[TEST] Classe '{expected_class}' ({len(images)} images)")

        for img_file in images:
            img_path = os.path.join(class_dir, img_file)
            pred_label, conf = predict(img_path)
            is_correct = pred_label == expected_class

            total += 1
            if is_correct:
                correct += 1

            status = "✅" if is_correct else "❌"
            print(f"  {status} {img_file:30s} → {pred_label:15s} ({conf*100:.1f}%)")

    accuracy = (correct / total * 100) if total > 0 else 0
    print(f"\n{'=' * 60}")
    print(f"RÉSULTAT : {correct}/{total} corrects ({accuracy:.1f}%)")
    print("=" * 60)

    return accuracy


def test_proba_format():
    """Vérifie que predict_proba retourne un dict conforme."""
    print("\n[TEST] Format de predict_proba")

    class_dir = os.path.join(AI_DATASET, "facture_achat")
    if not os.path.exists(class_dir):
        print("  ⚠️  Dossier introuvable, test ignoré")
        return

    img_path = os.path.join(class_dir, os.listdir(class_dir)[0])
    probs = predict_proba(img_path)

    assert isinstance(probs, dict), "predict_proba doit retourner un dict"
    assert set(probs.keys()) == set(CLASSES), f"Clés attendues : {CLASSES}"
    assert abs(sum(probs.values()) - 1.0) < 0.01, "La somme des probas doit être ~1.0"

    print(f"  ✅ Dict conforme : {list(probs.keys())}")
    print(f"  ✅ Somme des probas : {sum(probs.values()):.4f}")


def run_all_tests():
    accuracy = test_predictions_on_dataset()
    test_proba_format()

    print("\n" + "=" * 60)
    if accuracy >= 80:
        print(f"🎉 TESTS RÉUSSIS (accuracy: {accuracy:.1f}%)")
    else:
        print(f"⚠️  Accuracy faible ({accuracy:.1f}%) — vérifier le modèle")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()