"""
Compte les images par catégorie dans le dataset.

À exécuter : python count_images.py
"""
import os

DATASET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset")


def count_images(directory):
    """Compte les images dans un dossier."""
    if not os.path.exists(directory):
        return 0, 0, 0
    files = [f for f in os.listdir(directory) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    synth = [f for f in files if not f.startswith("kaggle_")]
    kaggle = [f for f in files if f.startswith("kaggle_")]
    return len(synth), len(kaggle), len(files)


def main():
    print("=" * 60)
    print("DISTRIBUTION DES IMAGES PAR CATÉGORIE")
    print("=" * 60)

    total_general = 0

    for split in ["train", "val", "test"]:
        print(f"\n[{split.upper()}]")
        total_split = 0

        for cls in ["facture_achat", "facture_vente", "autre"]:
            d = os.path.join(DATASET_DIR, split, cls)
            synth, kaggle, total = count_images(d)
            print(f"  {cls:15s} : {synth:3d} synthétiques + {kaggle:3d} réelles = {total:3d} total")
            total_split += total

        print(f"  {'TOTAL':15s} : {total_split:3d}")
        total_general += total_split

    print("=" * 60)
    print(f"TOTAL GÉNÉRAL : {total_general} images")
    print("=" * 60)


if __name__ == "__main__":
    main()