"""
Service d'extraction de texte (OCR) avec EasyOCR.

Fonctions :
    - extract_text(image_path) : extrait le texte brut de l'image
    - extract_fields(image_path) : extrait et structure les 6 champs
                                    (fournisseur, n° facture, date, HT, TVA, TTC)

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
# EXTRACTION DU TEXTE BRUT
# ==================================================
def extract_text(image_path: str) -> str:
    """Extrait le texte brut d'une image avec EasyOCR."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image introuvable : {image_path}")

    reader = _load_reader()

    try:
        results = reader.readtext(image_path, detail=1)
    except Exception as e:
        raise ValueError(f"Erreur EasyOCR : {e}")

    if not results:
        return ""

    lines = []
    for item in results:
        if len(item) >= 2:
            text = item[1]
            if text and text.strip():
                lines.append(text.strip())

    return "\n".join(lines)


# ==================================================
# PARSING DES VALEURS
# ==================================================
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


def _extract_amount_after_label(text: str, labels: list[str]) -> float | None:
    """
    Cherche un montant au format XX.XX ou XX,XX après un libellé.
    Tolère les sauts de ligne et les caractères parasites entre le libellé
    et le montant (ex: 'Toid HT\n2231.68 MAD').
    """
    for label in labels:
        # Cherche : label, puis jusqu'à 50 caractères quelconques (y compris \n),
        # puis capture un montant au format X.XX ou X,XX
        pattern = rf"{label}[\s\S]{{0,50}}?(\d+[.,]\d{{2}})"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount = _parse_amount(match.group(1))
            if amount is not None:
                return amount
    return None


# ==================================================
# EXTRACTION STRUCTURÉE
# ==================================================
def extract_fields(image_path: str) -> dict:
    """Extrait et structure les 6 champs d'une facture."""
    raw_text = extract_text(image_path)

    if not raw_text:
        return {
            "supplier": None, "invoice_number": None, "date": None,
            "total_ht": None, "vat": None, "total_ttc": None, "raw_text": "",
        }

    # ===== Fournisseur =====
    supplier = None
    match = re.search(
        r"(?:fournisseur|vendeur|émetteur|emetteur)\s*[:\-]\s*([A-Za-zÀ-ÿ0-9\s\.\-&']+)",
        raw_text, re.IGNORECASE,
    )
    if match:
        supplier = match.group(1).strip()[:255]
    else:
        first_line = raw_text.split("\n")[0].strip()
        if (
            first_line
            and len(first_line) < 60
            and not re.search(r"\d{3,}", first_line)
            and len(first_line) > 2
        ):
            supplier = first_line

    # ===== Numéro de facture =====
    invoice_number = None
    patterns_num = [
        r"(?:facture|fact|invoice)\s*(?:n[°o]?|num[eé]ro|#)?\s*[:\-]?\s*([A-Z0-9\-/]{3,30})",
        r"n[°o]\s*(?:facture|fact)?\s*[:\-]?\s*([A-Z0-9\-/]{3,30})",
        r"\b(FAC[\-/]?\d{3,10})\b",
        r"\b(F[AC]T[\-/]?\d{3,10})\b",
        r"\b(VTE[\-/]?\d{3,10})\b",
    ]
    for pat in patterns_num:
        m = re.search(pat, raw_text, re.IGNORECASE)
        if m:
            invoice_number = m.group(1).strip()
            break

    # ===== Date =====
    date = None
    # D'abord chercher explicitement après "date"
    m = re.search(
        r"(?:date\s*(?:de\s*)?(?:facture)?)\s*[:\-]?\s*([\d]{1,2}\s*[/\-\.vV]\s*[\d]{1,2}\s*[/\-\.vV]\s*[\d]{4})",
        raw_text, re.IGNORECASE,
    )
    if m:
        date = _parse_date(m.group(1))
    # Sinon, première date trouvée dans le texte
    if not date:
        date = _parse_date(raw_text)

    # ===== Montant HT =====
    # Tolère "Total HT" ou "Toid HT" (erreur OCR courante T→i)
    total_ht = _extract_amount_after_label(raw_text, [
        r"total\s*h\.?\s*t\.?",    # Total HT
        r"to[il]d\s*h\.?\s*t\.?",  # Toid HT (erreur OCR)
        r"hors\s*taxe[s]?",        # Hors taxes
    ])

    # ===== TVA =====
    # Tolère "TVA (20%)" ou "TvA {203)" (erreurs OCR courantes)
    vat = _extract_amount_after_label(raw_text, [
        r"t\.?\s*v\.?\s*a\.?",     # TVA (avec points optionnels)
    ])

    # ===== Montant TTC =====
    total_ttc = _extract_amount_after_label(raw_text, [
        r"total\s*t\.?\s*t\.?\s*c\.?",   # Total TTC
        r"toutes\s*taxes?\s*comprises?", # Toutes taxes comprises
    ])

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