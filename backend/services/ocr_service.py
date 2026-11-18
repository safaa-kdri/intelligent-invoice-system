"""
Service d'extraction de texte (OCR) avec EasyOCR + analyse spatiale.

Amélioration : utilise les bounding boxes d'EasyOCR pour mieux extraire
les champs sur les factures à mise en page complexe (colonnes, tableaux).

Stratégie :
    1. Extraire tous les textes + positions
    2. Identifier les zones : haut/bas, gauche/droite
    3. Chercher le fournisseur en haut à droite (zone FROM)
    4. Chercher le client en haut à gauche (zone TO)
    5. Chercher les montants dans la partie basse (totaux)

Supporte les factures en français ET en anglais.
Compatible EasyOCR 1.7.x
"""
import os
import re
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")


# ==================================================
# CHARGEMENT D'EASYOCR (une seule fois)
# ==================================================
_reader = None


def _load_reader():
    """Charge EasyOCR une seule fois (lazy loading)."""
    global _reader
    if _reader is not None:
        return _reader

    print("Chargement d'EasyOCR...")
    import easyocr

    _reader = easyocr.Reader(["fr", "en"], gpu=False, verbose=False)
    print("✅ EasyOCR chargé")
    return _reader


# ==================================================
# EXTRACTION AVEC POSITIONS
# ==================================================
def extract_text_with_positions(image_path: str) -> list[dict]:
    """
    Extrait tous les textes avec leurs positions.

    Returns:
        Liste de dicts : [
            {"text": "BigCo", "x": 450, "y": 50, "conf": 0.95},
            {"text": "Inc.",  "x": 470, "y": 80, "conf": 0.92},
            ...
        ]
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image introuvable : {image_path}")

    reader = _load_reader()

    try:
        results = reader.readtext(image_path, detail=1)
    except Exception as e:
        raise ValueError(f"Erreur EasyOCR : {e}")

    if not results:
        return []

    items = []
    for item in results:
        if len(item) < 2:
            continue

        bbox = item[0]  # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
        text = item[1].strip()
        confidence = item[2] if len(item) >= 3 else 1.0

        if not text:
            continue

        # Calculer le centre du bounding box
        x_coords = [p[0] for p in bbox]
        y_coords = [p[1] for p in bbox]
        center_x = sum(x_coords) / 4
        center_y = sum(y_coords) / 4

        items.append({
            "text": text,
            "x": center_x,
            "y": center_y,
            "x_min": min(x_coords),
            "x_max": max(x_coords),
            "y_min": min(y_coords),
            "y_max": max(y_coords),
            "conf": confidence,
        })

    return items


def extract_text(image_path: str) -> str:
    """Extrait le texte brut (pour compatibilité)."""
    items = extract_text_with_positions(image_path)
    return "\n".join(item["text"] for item in items)


# ==================================================
# UTILITAIRES
# ==================================================
def _get_image_size(image_path: str) -> tuple[int, int]:
    """Retourne (largeur, hauteur) de l'image."""
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            return img.width, img.height
    except Exception:
        return 1000, 1000  # fallback


def _parse_amount(text: str) -> float | None:
    """Convertit '1 234,56' ou '1234.56' en float."""
    if not text:
        return None
    try:
        cleaned = text.replace(" ", "").replace("\u00a0", "")
        cleaned = cleaned.replace(",", ".")
        cleaned = re.sub(r"[^0-9.]", "", cleaned)
        if not cleaned or cleaned.count(".") > 1:
            parts = cleaned.rsplit(".", 1)
            if len(parts) == 2 and len(parts[1]) <= 2:
                cleaned = parts[0].replace(".", "") + "." + parts[1]
            else:
                return None
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


def _parse_date(text: str) -> str | None:
    """Convertit une date en format YYYY-MM-DD (tolérant)."""
    if not text:
        return None

    patterns = [
        (r"(\d{1,2})\s*[/\-\.vV]\s*(\d{1,2})\s*[/\-\.vV]\s*(\d{4})", "DMY"),
        (r"(\d{4})\s*[/\-\.vV]\s*(\d{1,2})\s*[/\-\.vV]\s*(\d{1,2})", "YMD"),
        (r"(\d{1,2})\s*[/\-\.]\s*(\d{1,2})\s*[/\-\.]\s*(\d{2})\b", "DMY2"),
    ]

    for pattern, order in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                if order == "DMY":
                    d, m, y = match.groups()
                elif order == "DMY2":
                    d, m, y = match.groups()
                    y = "20" + y
                else:
                    y, m, d = match.groups()

                d_int, m_int, y_int = int(d), int(m), int(y)
                if not (1 <= m_int <= 12 and 1 <= d_int <= 31):
                    continue
                if not (2000 <= y_int <= 2100):
                    continue

                dt = datetime(y_int, m_int, d_int)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
    return None


# ==================================================
# EXTRACTION STRUCTURÉE AVEC POSITIONS
# ==================================================
def extract_fields(image_path: str) -> dict:
    """Extrait et structure les 6 champs d'une facture (avec positions)."""
    items = extract_text_with_positions(image_path)

    if not items:
        return {
            "supplier": None, "invoice_number": None, "date": None,
            "total_ht": None, "vat": None, "total_ttc": None, "raw_text": "",
        }

    img_width, img_height = _get_image_size(image_path)
    raw_text = "\n".join(item["text"] for item in items)

    # ===== DÉFINIR LES ZONES =====
    # Top 30% = en-tête (fournisseur, client, titre)
    # Bottom 50% = totaux
    header_items = [i for i in items if i["y"] < img_height * 0.4]
    body_items = [i for i in items if i["y"] >= img_height * 0.4]
    bottom_items = [i for i in items if i["y"] >= img_height * 0.6]

    # ===== FOURNISSEUR =====
    # Stratégie 1 : chercher après "FROM", "Vendor", "Fournisseur"
    supplier = None
    from_index = None
    for idx, item in enumerate(items):
        text_upper = item["text"].upper()
        if text_upper in ("FROM", "FOURNISSEUR", "VENDOR", "SELLER", "SUPPLIER", "ÉMETTEUR", "EMETTEUR"):
            from_index = idx
            break

    if from_index is not None and from_index + 1 < len(items):
        # Chercher le texte juste après FROM (même ligne ou en dessous)
        from_item = items[from_index]
        candidates = []
        for item in items[from_index + 1:from_index + 5]:
            # Même zone (à droite du FROM ou en dessous)
            if item["y"] > from_item["y"] - 10 and item["y"] < from_item["y"] + 100:
                candidates.append(item)
        if candidates:
            # Concaténer les candidats proches
            supplier = " ".join(c["text"] for c in candidates[:3]).strip()[:255]

    # Stratégie 2 : chercher en haut à droite (zone fournisseur des factures US)
    if not supplier:
        right_top = [i for i in header_items if i["x"] > img_width * 0.5]
        if right_top:
            # Prendre le premier texte substantiel (pas un mot-clé)
            for item in right_top:
                text = item["text"].strip()
                if (len(text) > 2 
                    and text.upper() not in ("TO", "FROM", "INVOICE", "NUMBER", "DATE", "CURRENCY")
                    and not re.match(r"^\d+$", text)):
                    supplier = text[:255]
                    break

    # Stratégie 3 : chercher après un mot-clé explicite
    if not supplier:
        match = re.search(
            r"(?:fournisseur|vendeur|émetteur|emetteur)\s*[:\-]\s*([A-Za-zÀ-ÿ0-9\s\.\-&']+)"
            r"|(?:vendor|seller|supplier)\s*[:\-]\s*([A-Za-z0-9\s\.\-&'\,]+)",
            raw_text, re.IGNORECASE,
        )
        if match:
            supplier = (match.group(1) or match.group(2) or "").strip()[:255]

    # Fallback : première ligne substantielle en haut à droite
    if not supplier:
        first_line = raw_text.split("\n")[0].strip()
        if (first_line
            and len(first_line) < 60
            and not re.search(r"\d{3,}", first_line)
            and len(first_line) > 2):
            supplier = first_line

    # ===== NUMÉRO DE FACTURE =====
    invoice_number = None

    # Stratégie 1 : chercher après "INVOICE NUMBER", "Facture N°", "N°"
    for idx, item in enumerate(items):
        text_upper = item["text"].upper().replace(" ", "")
        if text_upper in ("INVOICENUMBER", "FACTURENUMBER", "INVOICE#", "INVOICENO", "FACTUREN°"):
            # Chercher le texte proche (même ligne à droite ou juste en dessous)
            keyword_item = item
            candidates = []
            for i in range(idx + 1, min(idx + 5, len(items))):
                next_item = items[i]
                # Même ligne (à droite) ou en dessous immédiat
                if (next_item["x"] > keyword_item["x"] - 20 
                    and next_item["y"] < keyword_item["y"] + 80):
                    candidates.append(next_item["text"])
            if candidates:
                invoice_number = candidates[0].strip()
                break

    # Stratégie 2 : regex sur le texte brut
    if not invoice_number:
        patterns_num = [
            r"(?:invoice\s*(?:number|num|n[°o]|#)?)\s*[:\-]?\s*([A-Z0-9\-/]{3,30})",
            r"(?:facture|fact)\s*(?:n[°o]?|num[eé]ro|#)?\s*[:\-]?\s*([A-Z0-9\-/]{3,30})",
            r"\b(FAC[\-/]?\s*\d{3,10})\b",
            r"\b(VTE[\-/]?\s*\d{3,10})\b",
            r"\b(\d{5,15})\b",  # fallback : nombre pur
        ]
        for pat in patterns_num:
            m = re.search(pat, raw_text, re.IGNORECASE)
            if m:
                candidate = m.group(1).strip()
                if candidate.upper() not in ("CLIENT", "FOURNISSEUR", "PROFORMA", "CUSTOMER", "SUPPLIER", "INVOICE"):
                    invoice_number = candidate
                    break

    # ===== DATE =====
    date = None

    # Chercher après "DATE", "ISSUE DATE", "INVOICE DATE"
    for idx, item in enumerate(items):
        text_upper = item["text"].upper()
        if any(kw in text_upper for kw in ("DATE", "ISSUE")):
            # Chercher une date proche
            for i in range(idx + 1, min(idx + 3, len(items))):
                next_text = items[i]["text"]
                parsed = _parse_date(next_text)
                if parsed:
                    date = parsed
                    break
            if date:
                break

    # Fallback : première date trouvée
    if not date:
        date = _parse_date(raw_text)

    # ===== MONTANTS (chercher dans la partie basse) =====
    def find_amount_in_zone(zone_items, keywords):
        """Cherche un montant dans une zone après un mot-clé."""
        for idx, item in enumerate(zone_items):
            text_upper = item["text"].upper()
            for kw in keywords:
                if kw in text_upper:
                    # Chercher le montant sur la même ligne ou juste après
                    for i in range(idx, min(idx + 5, len(zone_items))):
                        candidate = zone_items[i]["text"]
                        # Extraire un montant
                        amount_match = re.search(r"(\d+[.,]\d{2})", candidate)
                        if amount_match:
                            return _parse_amount(amount_match.group(1))
        return None

    # HT
    total_ht = find_amount_in_zone(
        bottom_items,
        ["SUBTOTAL", "SOUS-TOTAL", "TOTAL HT", "TOID HT", "HORS TAXE", "NET AMOUNT"]
    )

    # TVA
    vat = find_amount_in_zone(
        bottom_items,
        ["TVA", "TAX", "VAT", "SALES TAX"]
    )

    # TTC
    total_ttc = find_amount_in_zone(
        bottom_items,
        ["TOTAL TTC", "TOTAL USD", "TOTAL AMOUNT", "GRAND TOTAL", "AMOUNT DUE"]
    )

    # Fallback : chercher partout si pas trouvé
    if total_ht is None:
        m = re.search(r"(?:total\s*h\.?t\.?|subtotal|sous[- ]total)[\s\S]{0,50}?(\d+[.,]\d{2})", raw_text, re.IGNORECASE)
        if m:
            total_ht = _parse_amount(m.group(1))

    if vat is None:
        m = re.search(r"(?:tva|tax|vat)[\s\S]{0,30}?(\d+[.,]\d{2})", raw_text, re.IGNORECASE)
        if m:
            vat = _parse_amount(m.group(1))

    if total_ttc is None:
        m = re.search(r"(?:total\s*t\.?t\.?c\.?|total\s*(?:usd|eur)?|grand\s*total)[\s\S]{0,50}?(\d+[.,]\d{2})", raw_text, re.IGNORECASE)
        if m:
            total_ttc = _parse_amount(m.group(1))

    return {
        "supplier": supplier,
        "invoice_number": invoice_number,
        "date": date,
        "total_ht": total_ht,
        "vat": vat,
        "total_ttc": total_ttc,
        "raw_text": raw_text,
    }


# ==================================================
# TEST RAPIDE
# ==================================================
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage : python -m services.ocr_service <image_path>")
        sys.exit(1)
    fields = extract_fields(sys.argv[1])
    print(f"\nImage : {sys.argv[1]}\n")
    print("Texte extrait :")
    print("-" * 60)
    print(fields["raw_text"])
    print("-" * 60)
    print("\nChamps structurés :")
    for key in ["supplier", "invoice_number", "date", "total_ht", "vat", "total_ttc"]:
        print(f"  {key:15s} : {fields[key]}")