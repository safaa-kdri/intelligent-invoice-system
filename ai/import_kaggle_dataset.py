"""
Import du dataset Kaggle (factures PFE TNS).

Ce script :
    1. Convertit les PDF en images PNG (résolution 224x224)
    2. Copie les images dans le dataset d'entraînement
    3. Répartit en train/val (80/20)

Structure source :
    D:/Downloads/factures_pfe/
    ├── facture achat/*.pdf
    └── facture vente/*.pdf

Structure cible :
    ai/dataset/train/facture_achat/*.png
    ai/dataset/train/facture_vente/*.png
    ai/dataset/val/facture_achat/*.png
    ai/dataset/val/facture_vente/*.png

À exécuter : python import_kaggle_dataset.py
"""
import os
import random
import shutil
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image


# ==================================================
# CONFIGURATION
# ==================================================
KAGGLE_DIR = "D:/Downloads/factures_pfe"  # ← À ADAPTER
DATASET_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "dataset"
)

# Ratio train/val
TRAIN_RATIO = 0.80

# Taille des images (MobileNetV2)
IMG_SIZE = (224, 224)

# Correspondance dossiers Kaggle → classes
CLASS_MAP = {
    "facture achat": "facture_achat",
    "facture vente": "facture_vente",
}

# Seed pour la reproductibilité
random.seed(42)


def convert_pdf_to_png(pdf_path: str, output_dir: str, prefix: str) -> int:
    """
    Convertit un PDF en image(s) PNG.
    Retourne le nombre d'images générées.
    """
    try:
        # Convertir la première page uniquement (les factures sont sur 1 page)
        pages = convert_from_path(pdf_path, dpi=150, first_page=1, last_page=1)
        if not pages:
            return 0

        # Prendre la première page
        img = pages[0]

        # Redimensionner à 224×224
        img = img.resize(IMG_SIZE, Image.LANCZOS)

        # Nom de sortie
        base_name = Path(pdf_path).stem  # ex. "ACHAT00149"
        output_path = os.path.join(output_dir, f"{prefix}_{base_name}.png")

        # Sauvegarder
        img.save(output_path, "PNG", optimize=True)
        return 1
    except Exception as e:
        print(f"  ❌ Erreur {Path(pdf_path).name} : {e}")
        return 0


def process_class(class_folder: str, class_name: str):
    """Traite une classe (dossier source Kaggle)."""
    source_dir = os.path.join(KAGGLE_DIR, class_folder)
    if not os.path.exists(source_dir):
        print(f"⚠️  Dossier introuvable : {source_dir}")
        return

    # Lister les PDF
    pdf_files = sorted([f for f in os.listdir(source_dir) if f.lower().endswith(".pdf")])
    print(f"\n[{class_name}] {len(pdf_files)} PDF trouvés")

    # Mélanger pour la répartition
    random.shuffle(pdf_files)

    # Séparer train/val
    n_train = int(len(pdf_files) * TRAIN_RATIO)
    train_files = pdf_files[:n_train]
    val_files = pdf_files[n_train:]

    # Créer les dossiers
    for split in ["train", "val"]:
        os.makedirs(os.path.join(DATASET_DIR, split, class_name), exist_ok=True)

    # Traiter train
    print(f"  Train : {len(train_files)} fichiers...")
    train_count = 0
    for i, pdf_file in enumerate(train_files, 1):
        n = convert_pdf_to_png(
            os.path.join(source_dir, pdf_file),
            os.path.join(DATASET_DIR, "train", class_name),
            prefix="kaggle",
        )
        train_count += n
        if i % 20 == 0:
            print(f"    {i}/{len(train_files)}...")

    # Traiter val
    print(f"  Val   : {len(val_files)} fichiers...")
    val_count = 0
    for i, pdf_file in enumerate(val_files, 1):
        n = convert_pdf_to_png(
            os.path.join(source_dir, pdf_file),
            os.path.join(DATASET_DIR, "val", class_name),
            prefix="kaggle",
        )
        val_count += n
        if i % 20 == 0:
            print(f"    {i}/{len(val_files)}...")

    print(f"  ✅ {class_name} : {train_count} train, {val_count} val")


def main():
    print("=" * 60)
    print("IMPORT DU DATASET KAGGLE (Factures PFE TNS)")
    print("=" * 60)
    print(f"Source  : {KAGGLE_DIR}")
    print(f"Cible   : {DATASET_DIR}")
    print(f"Train   : {TRAIN_RATIO*100:.0f}%")
    print(f"Val     : {(1-TRAIN_RATIO)*100:.0f}%")
    print()

    if not os.path.exists(KAGGLE_DIR):
        print(f"❌ Dossier source introuvable : {KAGGLE_DIR}")
        print("   Modifiez la variable KAGGLE_DIR dans le script.")
        print()
        print("   Exemple :")
        print('   KAGGLE_DIR = "D:/Downloads/factures_pfe"')
        return

    # Traiter chaque classe
    for kaggle_folder, class_name in CLASS_MAP.items():
        process_class(kaggle_folder, class_name)

    # ===== Résumé =====
    print("\n" + "=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)

    for split in ["train", "val", "test"]:
        print(f"\n[{split}]")
        total = 0
        for cls in ["facture_achat", "facture_vente", "autre"]:
            d = os.path.join(DATASET_DIR, split, cls)
            if os.path.exists(d):
                # Compter uniquement les PNG
                n = len([f for f in os.listdir(d) if f.endswith(".png")])
                print(f"  {cls:15s} : {n:4d}")
                total += n
        print(f"  {'TOTAL':15s} : {total:4d}")

    print("\n🎉 Import terminé !")
    print("\n⚠️  Prochaine étape : réentraîner le modèle avec :")
    print("   cd ../ai && python train.py")


if __name__ == "__main__":
    main()