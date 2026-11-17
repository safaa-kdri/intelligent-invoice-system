"""
Évaluation de l'OCR (Character Error Rate + Word Error Rate).

Prend un échantillon d'images du dataset et calcule :
    - CER (Character Error Rate) : erreurs au niveau caractère
    - WER (Word Error Rate) : erreurs au niveau mot

Formules :
    CER = (S + D + I) / N_chars
    WER = (S + D + I) / N_words

où S = substitutions, D = deletions, I = insertions, N = nombre de référence.

À exécuter : python evaluate_ocr.py
"""
import os
import sys

# Ajouter le chemin backend pour importer le service OCR
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from services.ocr_service import extract_text


def levenshtein(a, b):
    """
    Calcule la distance de Levenshtein entre deux séquences.
    Fonctionne avec des chaînes (caractères) ou des listes (mots).
    """
    if len(a) < len(b):
        a, b = b, a

    if len(b) == 0:
        return len(a)

    previous_row = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current_row = [i]
        for j, cb in enumerate(b, 1):
            insertions = previous_row[j] + 1
            deletions = current_row[j - 1] + 1
            substitutions = previous_row[j - 1] + (ca != cb)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def cer(reference: str, hypothesis: str) -> float:
    """Character Error Rate."""
    if not reference:
        return 0.0 if not hypothesis else 1.0
    dist = levenshtein(reference, hypothesis)
    return dist / len(reference)


def wer(reference: str, hypothesis: str) -> float:
    """Word Error Rate (basé sur les mots)."""
    ref_words = reference.lower().split()
    hyp_words = hypothesis.lower().split()
    if not ref_words:
        return 0.0 if not hyp_words else 1.0
    dist = levenshtein(ref_words, hyp_words)
    return dist / len(ref_words)


def main():
    print("=" * 60)
    print("ÉVALUATION DE L'OCR (CER / WER)")
    print("=" * 60)

    # ⚠️ Références annotées manuellement à partir des images réelles.
    # Chaque "reference" correspond au texte EXACT contenu dans l'image.
    eval_set = [
        {
            "image": "dataset/test/facture_achat/facture_achat_0000.png",
            "reference": (
                "Inwi\n"
                "FACTURE\n"
                "N° FAC-2933\n"
                "Date : 11/10/2024\n"
                "Total HT : 2331.69 MAD\n"
                "TVA (20%) : 466.34 MAD\n"
                "TOTAL TTC : 2798.03 MAD\n"
                "Merci de votre confiance"
            ),
        },
        # Vous pouvez ajouter d'autres images annotées ici :
        # {
        #     "image": "dataset/test/facture_vente/facture_vente_0000.png",
        #     "reference": "...",
        # },
        # {
        #     "image": "dataset/test/autre/autre_0000.png",
        #     "reference": "...",
        # },
    ]

    if not eval_set:
        print("\n⚠️  Aucune image annotée. Ajoutez des entrées dans eval_set.")
        return

    total_cer = 0.0
    total_wer = 0.0
    valid_count = 0

    for i, item in enumerate(eval_set, 1):
        img_path = os.path.join(os.path.dirname(__file__), item["image"])
        if not os.path.exists(img_path):
            print(f"\n[{i}] ⚠️  Image introuvable : {img_path}")
            continue

        print(f"\n[{i}] {os.path.basename(item['image'])}")
        print("-" * 60)

        # Extraction OCR
        hypothesis = extract_text(img_path)
        reference = item["reference"]

        # Calcul des métriques
        c = cer(reference, hypothesis)
        w = wer(reference, hypothesis)

        print(f"Référence ({len(reference)} chars) :")
        print(f"  {reference[:120]}{'...' if len(reference) > 120 else ''}")
        print(f"Extrait ({len(hypothesis)} chars) :")
        print(f"  {hypothesis[:120]}{'...' if len(hypothesis) > 120 else ''}")
        print(f"\n  CER : {c*100:.2f}%")
        print(f"  WER : {w*100:.2f}%")

        total_cer += c
        total_wer += w
        valid_count += 1

    if valid_count == 0:
        print("\n❌ Aucune image valide évaluée.")
        return

    avg_cer = total_cer / valid_count
    avg_wer = total_wer / valid_count

    print("\n" + "=" * 60)
    print("RÉSULTATS MOYENS")
    print("=" * 60)
    print(f"Images évaluées : {valid_count}")
    print(f"CER moyen       : {avg_cer*100:.2f}%")
    print(f"WER moyen       : {avg_wer*100:.2f}%")
    print("\n📄 À reporter dans le rapport (section 4.4.3)")
    print()
    print("💡 Interprétation :")
    if avg_cer < 0.15:
        print("   ✅ CER < 15% : OCR de bonne qualité")
    elif avg_cer < 0.30:
        print("   ⚠️  CER 15-30% : OCR acceptable, corrections nécessaires")
    else:
        print("   ❌ CER > 30% : OCR faible, correction manuelle indispensable")


if __name__ == "__main__":
    main()