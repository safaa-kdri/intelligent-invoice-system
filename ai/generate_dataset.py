"""
Génère un dataset synthétique de 300 images réparties en 3 classes :
    - facture_achat  (100 images)
    - facture_vente  (100 images)
    - autre          (100 images)

Répartition :
    - train : 70 images par classe
    - val   : 15 images par classe
    - test  : 15 images par classe

Chaque image est de taille 224x224 (taille attendue par MobileNetV2).
"""
import os
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import shutil


# Configuration
IMG_SIZE = 224
N_PER_CLASS = 100
SPLIT = {"train": 0.70, "val": 0.15, "test": 0.15}

DATASET_DIR = os.path.join(os.path.dirname(__file__), "dataset")
CLASSES = ["facture_achat", "facture_vente", "autre"]


# Couleurs et styles
COLORS_BG = [
    (255, 255, 255),  # blanc
    (245, 245, 220),  # beige
    (240, 248, 255),  # bleu très clair
    (255, 250, 240),  # floral white
]

COLORS_TEXT = [(0, 0, 0), (30, 30, 30), (50, 50, 50)]

COLORS_ACCENT = [
    (0, 102, 204),    # bleu
    (204, 0, 0),      # rouge
    (0, 153, 76),     # vert
    (255, 102, 0),    # orange
    (102, 0, 153),    # violet
]


# Noms d'entreprises pour les factures
SUPPLIERS_ACHAT = [
    "ABC SARL", "XYZ Corp", "Marjane", "Total Energie", "Inwi",
    "Lydec", "Cosumar", "Lesieur", "Centrale Danone", "Nestlé Maroc",
]

SUPPLIERS_VENTE = [
    "Mon Entreprise SARL", "Client Alpha", "Client Beta", "Sté Gamma",
    "Sté Delta", "Client Epsilon", "Sté Zeta", "Client Eta",
]

OTHER_TITLES = [
    "REÇU DE PAIEMENT", "BON DE COMMANDE", "TICKET DE CAISSE",
    "BON DE LIVRAISON", "DEVIS", "NOTE D'HONORAIRES",
    "ATTESTATION", "CERTIFICAT", "FACTURE PROFORMA",
]


def get_font(size: int, bold: bool = False):
    """Retourne une police, ou la police par défaut si non disponible."""
    try:
        # Windows
        if bold:
            return ImageFont.truetype("arialbd.ttf", size)
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        try:
            return ImageFont.load_default(size)
        except Exception:
            return ImageFont.load_default()


def random_amount():
    """Génère un montant aléatoire cohérent (HT, TVA 20%, TTC)."""
    ht = round(random.uniform(50, 5000), 2)
    tva = round(ht * 0.20, 2)
    ttc = round(ht + tva, 2)
    return ht, tva, ttc


def generate_facture_achat() -> Image.Image:
    """Génère une image de facture d'achat (fournisseur → entreprise)."""
    img = Image.new("RGB", (IMG_SIZE, IMG_SIZE), random.choice(COLORS_BG))
    draw = ImageDraw.Draw(img)

    # Bordure
    accent = random.choice(COLORS_ACCENT)
    draw.rectangle([5, 5, IMG_SIZE - 5, IMG_SIZE - 5], outline=accent, width=2)

    # En-tête fournisseur
    supplier = random.choice(SUPPLIERS_ACHAT)
    draw.text((15, 15), supplier, fill=accent, font=get_font(14, bold=True))

    # Titre "FACTURE"
    draw.text((15, 45), "FACTURE", fill=random.choice(COLORS_TEXT), font=get_font(12, bold=True))

    # Numéro et date
    num = f"N° FAC-{random.randint(1000, 9999)}"
    date = f"{random.randint(1, 28):02d}/{random.randint(1, 12):02d}/{random.randint(2020, 2026)}"
    draw.text((15, 70), num, fill=random.choice(COLORS_TEXT), font=get_font(9))
    draw.text((15, 85), f"Date : {date}", fill=random.choice(COLORS_TEXT), font=get_font(9))

    # Montants
    ht, tva, ttc = random_amount()
    draw.text((15, 120), f"Total HT : {ht:.2f} MAD", fill=random.choice(COLORS_TEXT), font=get_font(9))
    draw.text((15, 135), f"TVA (20%) : {tva:.2f} MAD", fill=random.choice(COLORS_TEXT), font=get_font(9))
    draw.text((15, 150), f"TOTAL TTC : {ttc:.2f} MAD", fill=accent, font=get_font(10, bold=True))

    # Mention bas de page
    draw.text((15, 195), "Merci de votre confiance", fill=random.choice(COLORS_TEXT), font=get_font(8))

    return img


def generate_facture_vente() -> Image.Image:
    """Génère une image de facture de vente (entreprise → client)."""
    img = Image.new("RGB", (IMG_SIZE, IMG_SIZE), random.choice(COLORS_BG))
    draw = ImageDraw.Draw(img)

    # Bordure
    accent = random.choice(COLORS_ACCENT)
    draw.rectangle([5, 5, IMG_SIZE - 5, IMG_SIZE - 5], outline=accent, width=2)

    # En-tête entreprise
    draw.text((15, 15), "MON ENTREPRISE SARL", fill=accent, font=get_font(14, bold=True))

    # Titre "FACTURE CLIENT"
    draw.text((15, 45), "FACTURE CLIENT", fill=random.choice(COLORS_TEXT), font=get_font(12, bold=True))

    # Client
    client = random.choice(SUPPLIERS_VENTE[1:])
    draw.text((15, 70), f"Client : {client}", fill=random.choice(COLORS_TEXT), font=get_font(9))

    # Numéro et date
    num = f"N° VTE-{random.randint(1000, 9999)}"
    date = f"{random.randint(1, 28):02d}/{random.randint(1, 12):02d}/{random.randint(2020, 2026)}"
    draw.text((15, 90), num, fill=random.choice(COLORS_TEXT), font=get_font(9))
    draw.text((15, 105), f"Date : {date}", fill=random.choice(COLORS_TEXT), font=get_font(9))

    # Montants
    ht, tva, ttc = random_amount()
    draw.text((15, 140), f"Total HT : {ht:.2f} MAD", fill=random.choice(COLORS_TEXT), font=get_font(9))
    draw.text((15, 155), f"TVA (20%) : {tva:.2f} MAD", fill=random.choice(COLORS_TEXT), font=get_font(9))
    draw.text((15, 170), f"TOTAL TTC : {ttc:.2f} MAD", fill=accent, font=get_font(10, bold=True))

    # Mention bas de page
    draw.text((15, 195), "Paiement à réception", fill=random.choice(COLORS_TEXT), font=get_font(8))

    return img


def generate_autre() -> Image.Image:
    """Génère une image d'un autre type de document (reçu, bon, etc.)."""
    img = Image.new("RGB", (IMG_SIZE, IMG_SIZE), random.choice(COLORS_BG))
    draw = ImageDraw.Draw(img)

    # Bordure (parfois absente)
    accent = random.choice(COLORS_ACCENT)
    if random.random() > 0.3:
        draw.rectangle([5, 5, IMG_SIZE - 5, IMG_SIZE - 5], outline=accent, width=1)

    # Titre du document
    title = random.choice(OTHER_TITLES)
    draw.text((15, 20), title, fill=accent, font=get_font(13, bold=True))

    # Lignes de contenu aléatoires
    y = 55
    for _ in range(random.randint(3, 6)):
        if random.random() > 0.3:
            text = f"Article {random.randint(1, 99)} - {random.randint(1, 10)} x {random.uniform(10, 500):.2f} MAD"
            draw.text((15, y), text, fill=random.choice(COLORS_TEXT), font=get_font(8))
            y += 20

    # Total
    draw.line([(15, y + 5), (IMG_SIZE - 15, y + 5)], fill=accent, width=1)
    draw.text((15, y + 12), f"TOTAL : {random.uniform(50, 2000):.2f} MAD",
              fill=accent, font=get_font(10, bold=True))

    return img


def add_noise(img: Image.Image, intensity: int = 5) -> Image.Image:
    """Ajoute du bruit aléatoire à une image."""
    arr = np.array(img).astype(np.int32)
    noise = np.random.randint(-intensity, intensity + 1, arr.shape, dtype=np.int32)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def split_dataset(images: list, seed: int = 42):
    """Répartit les images en train/val/test."""
    random.seed(seed)
    random.shuffle(images)

    n_train = int(len(images) * SPLIT["train"])
    n_val = int(len(images) * SPLIT["val"])

    return {
        "train": images[:n_train],
        "val": images[n_train:n_train + n_val],
        "test": images[n_train + n_val:],
    }


def main():
    print("=" * 60)
    print("GÉNÉRATION DU DATASET SYNTHÉTIQUE")
    print("=" * 60)

    # Nettoyer les anciens dossiers
    if os.path.exists(DATASET_DIR):
        print(f"Suppression de l'ancien dataset : {DATASET_DIR}")
        shutil.rmtree(DATASET_DIR)

    # Créer la structure
    for split in ["train", "val", "test"]:
        for cls in CLASSES:
            os.makedirs(os.path.join(DATASET_DIR, split, cls), exist_ok=True)

    generators = {
        "facture_achat": generate_facture_achat,
        "facture_vente": generate_facture_vente,
        "autre": generate_autre,
    }

    # Générer les images par classe
    for cls, generator in generators.items():
        print(f"\nGénération de {N_PER_CLASS} images pour '{cls}'...")
        images = []
        for i in range(N_PER_CLASS):
            img = generator()
            # Ajouter des variations : bruit, légère rotation
            if random.random() > 0.5:
                img = add_noise(img, intensity=random.randint(2, 8))
            images.append(img)

        # Répartir en train/val/test
        splits = split_dataset(images)

        for split_name, split_images in splits.items():
            for i, img in enumerate(split_images):
                path = os.path.join(DATASET_DIR, split_name, cls, f"{cls}_{i:04d}.png")
                img.save(path)

            print(f"  {split_name:5s} : {len(split_images)} images → {os.path.join(DATASET_DIR, split_name, cls)}")

    # Résumé
    print("\n" + "=" * 60)
    print("RÉSUMÉ DU DATASET")
    print("=" * 60)
    for split in ["train", "val", "test"]:
        total = 0
        for cls in CLASSES:
            count = len(os.listdir(os.path.join(DATASET_DIR, split, cls)))
            print(f"  {split:5s} / {cls:15s} : {count} images")
            total += count
        print(f"  {split:5s} TOTAL           : {total} images")
        print()

    print("🎉 Dataset généré avec succès !")
    print(f"📁 Emplacement : {DATASET_DIR}")


if __name__ == "__main__":
    main()