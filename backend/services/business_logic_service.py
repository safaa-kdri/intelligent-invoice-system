"""
Service de logique métier pour la distinction achat/vente.

Problème : une facture d'achat et une facture de vente peuvent être
visuellement identiques (même document, seul le point de vue change).

Solution : analyser les indices textuels du document (mentions "Client",
"Fournisseur", etc.) pour vérifier et corriger la prédiction du CNN.

Fonction principale :
    refine_classification(cnn_label, cnn_confidence, ocr_result)
        → retourne un dict avec :
            - final_label : la classe finale (peut être différente du CNN)
            - corrected : True si l'OCR a corrigé le CNN
            - reason : explication de la décision
            - ocr_hint : l'indice détecté ('achat', 'vente', 'indetermine')
"""
import re


# ==================================================
# MOTS-CLÉS INDICATEURS
# ==================================================

# Indices forts d'une FACTURE DE VENTE (vous êtes le vendeur, le client est destinataire)
VENTE_KEYWORDS = [
    r"facture\s*(?:client|client[e]?)",         # "Facture client"
    r"client\s*[:\-]",                           # "Client :"
    r"acheteur",                                  # "Acheteur"
    r"destinataire",                             # "Destinataire"
    r"factur[eé]\s*à",                            # "Facturé à"
    r"vendu\s*à",                                 # "Vendu à"
]

# Indices forts d'une FACTURE D'ACHAT (vous êtes l'acheteur, le fournisseur est émetteur)
ACHAT_KEYWORDS = [
    r"facture\s*(?:fournisseur|fourniss[a-z]+)",  # "Facture fournisseur"
    r"fournisseur\s*[:\-]",                       # "Fournisseur :"
    r"vendeur\s*[:\-]",                           # "Vendeur :"
    r"émetteur\s*[:\-]",                          # "Émetteur :"
    r"emetteur\s*[:\-]",                          # "Emetteur :"
    r"factur[eé]\s*par",                          # "Facturé par"
    r"vendu\s*par",                               # "Vendu par"
]


# ==================================================
# DÉTECTION DES INDICES
# ==================================================
def detect_ocr_hint(raw_text: str) -> dict:
    """
    Analyse le texte OCR pour détecter des indices achat/vente.

    Retourne :
        {
            "hint": "achat" | "vente" | "indetermine",
            "achat_matches": [liste des phrases détectées],
            "vente_matches": [liste des phrases détectées],
            "confidence": float,  # 0.0 à 1.0
        }
    """
    if not raw_text:
        return {
            "hint": "indetermine",
            "achat_matches": [],
            "vente_matches": [],
            "confidence": 0.0,
        }

    achat_matches = []
    vente_matches = []

    # Chercher les indices VENTE
    for keyword in VENTE_KEYWORDS:
        for match in re.finditer(keyword, raw_text, re.IGNORECASE):
            # Récupérer la ligne complète pour la traçabilité
            start = raw_text.rfind("\n", 0, match.start()) + 1
            end = raw_text.find("\n", match.end())
            if end == -1:
                end = len(raw_text)
            line = raw_text[start:end].strip()
            if line and line not in vente_matches:
                vente_matches.append(line[:100])

    # Chercher les indices ACHAT
    for keyword in ACHAT_KEYWORDS:
        for match in re.finditer(keyword, raw_text, re.IGNORECASE):
            start = raw_text.rfind("\n", 0, match.start()) + 1
            end = raw_text.find("\n", match.end())
            if end == -1:
                end = len(raw_text)
            line = raw_text[start:end].strip()
            if line and line not in achat_matches:
                achat_matches.append(line[:100])

    # Décider
    nb_achat = len(achat_matches)
    nb_vente = len(vente_matches)

    if nb_achat == 0 and nb_vente == 0:
        hint = "indetermine"
        confidence = 0.0
    elif nb_achat > nb_vente:
        hint = "achat"
        confidence = min(1.0, nb_achat * 0.4)
    elif nb_vente > nb_achat:
        hint = "vente"
        confidence = min(1.0, nb_vente * 0.4)
    else:
        # Ambigu : autant d'indices des deux côtés
        hint = "indetermine"
        confidence = 0.3

    return {
        "hint": hint,
        "achat_matches": achat_matches,
        "vente_matches": vente_matches,
        "confidence": round(confidence, 2),
    }


# ==================================================
# RAFFINEMENT DE LA CLASSIFICATION
# ==================================================
def refine_classification(
    cnn_label: str,
    cnn_confidence: float,
    ocr_result: dict | None,
) -> dict:
    """
    Combine la prédiction CNN avec les indices OCR pour produire
    une classification finale plus fiable.

    Args:
        cnn_label: 'facture_achat' | 'facture_vente' | 'autre'
        cnn_confidence: float (0.0 à 1.0)
        ocr_result: dict retourné par extract_fields() (avec 'raw_text')

    Returns:
        {
            "final_label": str,
            "corrected": bool,
            "reason": str,
            "ocr_hint": dict,
            "original_cnn": {"label": str, "confidence": float},
        }
    """
    result = {
        "final_label": cnn_label,
        "corrected": False,
        "reason": "CNN conservé (pas d'indice OCR contraire)",
        "ocr_hint": {
            "hint": "indetermine",
            "achat_matches": [],
            "vente_matches": [],
            "confidence": 0.0,
        },
        "original_cnn": {"label": cnn_label, "confidence": cnn_confidence},
    }

    # Si le CNN dit "autre", on ne corrige pas (l'OCR ne peut pas décider si c'est une facture)
    if cnn_label == "autre":
        result["reason"] = "CNN = autre document (pas de correction OCR)"
        return result

    # Si pas d'OCR, on garde le CNN
    if not ocr_result or not ocr_result.get("raw_text"):
        result["reason"] = "Pas de texte OCR disponible"
        return result

    # Détecter les indices
    hint = detect_ocr_hint(ocr_result["raw_text"])
    result["ocr_hint"] = hint

    # ===== Décision =====

    # Cas 1 : Indice OCR fort et clair
    if hint["hint"] == "achat" and hint["confidence"] >= 0.4:
        if cnn_label == "facture_vente":
            # CONFLIT : CNN dit vente, OCR dit achat → on corrige
            result["final_label"] = "facture_achat"
            result["corrected"] = True
            result["reason"] = (
                f"CNN dit 'vente', mais l'OCR détecte des indices d'achat : "
                f"{hint['achat_matches'][:2]}"
            )
        else:
            # CNN dit déjà achat, OCR confirme
            result["reason"] = f"CNN et OCR concordent (achat) : {hint['achat_matches'][:1]}"

    elif hint["hint"] == "vente" and hint["confidence"] >= 0.4:
        if cnn_label == "facture_achat":
            # CONFLIT : CNN dit achat, OCR dit vente → on corrige
            result["final_label"] = "facture_vente"
            result["corrected"] = True
            result["reason"] = (
                f"CNN dit 'achat', mais l'OCR détecte des indices de vente : "
                f"{hint['vente_matches'][:2]}"
            )
        else:
            result["reason"] = f"CNN et OCR concordent (vente) : {hint['vente_matches'][:1]}"

    # Cas 2 : Indice ambigu ou faible
    elif hint["hint"] == "indetermine":
        result["reason"] = "Pas d'indice OCR clair (achat/vente indéterminé)"

    # Cas 3 : Indice contraire mais faible
    elif hint["hint"] == "achat" and cnn_label == "facture_vente":
        result["reason"] = f"Indice achat faible ({hint['confidence']}), CNN conservé"

    elif hint["hint"] == "vente" and cnn_label == "facture_achat":
        result["reason"] = f"Indice vente faible ({hint['confidence']}), CNN conservé"

    return result


# ==================================================
# TEST RAPIDE
# ==================================================
if __name__ == "__main__":
    # Quelques tests basiques
    test_texts = [
        ("Client : Marjane\nFacture N° FAC-001\nTVA : 20.00", "vente"),
        ("Fournisseur : Inwi\nFacture N° FAC-002\nTVA : 30.00", "achat"),
        ("FACTURE CLIENT\nMontant : 1000", "vente"),
        ("FACTURE FOURNISSEUR\nMontant : 1000", "achat"),
        ("Document divers\nMontant : 1000", "indetermine"),
    ]

    print("=" * 60)
    print("TESTS DE DÉTECTION DES INDICES OCR")
    print("=" * 60)

    for text, expected in test_texts:
        hint = detect_ocr_hint(text)
        status = "✅" if hint["hint"] == expected else "❌"
        print(f"{status} Attendu: {expected:15s} | Détecté: {hint['hint']:15s} | Confiance: {hint['confidence']}")
        print(f"   Texte: {text[:60]}...")

    print("\n" + "=" * 60)
    print("TESTS DE RAFFINEMENT")
    print("=" * 60)

    # Test : CNN dit vente mais OCR dit achat
    ocr_result = {"raw_text": "Fournisseur : Inwi\nFACTURE\nTOTAL TTC : 1000.00 MAD"}
    refined = refine_classification("facture_vente", 0.85, ocr_result)
    print(f"\nCNN: facture_vente (0.85) → Final: {refined['final_label']}")
    print(f"Corrigé: {refined['corrected']}")
    print(f"Raison: {refined['reason']}")

    # Test : CNN dit achat et OCR dit achat
    refined2 = refine_classification("facture_achat", 0.90, ocr_result)
    print(f"\nCNN: facture_achat (0.90) → Final: {refined2['final_label']}")
    print(f"Corrigé: {refined2['corrected']}")
    print(f"Raison: {refined2['reason']}")