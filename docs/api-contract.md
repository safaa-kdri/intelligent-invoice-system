# Contrat d'API — Système intelligent de traitement des factures

**Version** : 1.0
**Date** : 2026-11-11
**Validé par** : Safaa El Kadouri + Aya Nahal
**Statut** : Référence absolue — ne pas modifier sans accord des deux

---

## 1. Conventions générales

### 1.1 Base URL

| Environnement | URL |
|---|---|
| Développement local | `http://localhost:5000` |
| (production — plus tard) | *à définir* |

### 1.2 Format des échanges

- **Requêtes** : `multipart/form-data` pour l'upload, `application/json` pour les autres
- **Réponses** : toujours `application/json` (UTF-8)
- **Encodage** : UTF-8

### 1.3 Codes HTTP utilisés

| Code | Signification | Quand l'utiliser |
|---|---|---|
| `200 OK` | Succès | Requête traitée correctement |
| `201 Created` | Création réussie | Facture créée |
| `400 Bad Request` | Requête invalide | Fichier manquant, format non supporté, données invalides |
| `404 Not Found` | Ressource introuvable | ID inexistant |
| `413 Payload Too Large` | Fichier trop volumineux | Taille > 10 Mo |
| `415 Unsupported Media Type` | Format non supporté | Extension non autorisée |
| `422 Unprocessable Entity` | Données incohérentes | Champs invalides en base |
| `500 Internal Server Error` | Erreur serveur | Exception non gérée |
| `503 Service Unavailable` | Service indisponible | Module IA non chargé |

### 1.4 Format d'erreur standard

Toute erreur (code ≥ 400) **doit** renvoyer ce format :

```json
{
  "error": {
    "code": "STRING_CODE",
    "message": "Message lisible par l'utilisateur en français",
    "details": "Optionnel — détails techniques"
  }
}
```

**Codes d'erreur internes** :

| Code interne | Signification |
|---|---|
| `NO_FILE` | Aucun fichier dans la requête |
| `INVALID_FORMAT` | Extension non autorisée |
| `FILE_TOO_LARGE` | Fichier > 10 Mo |
| `EMPTY_FILE` | Fichier vide (0 octet) |
| `CLASSIFICATION_FAILED` | Le CNN n'a pas pu classifier |
| `OCR_FAILED` | PaddleOCR a échoué |
| `DB_ERROR` | Erreur MySQL |
| `NOT_FOUND` | Facture introuvable |
| `INVALID_INPUT` | Données envoyées invalides |

### 1.5 Formats de données figés

- **Dates** : `YYYY-MM-DD` (ISO 8601, ex. `2026-10-15`)
- **Datetimes** : `YYYY-MM-DDTHH:MM:SS` (ex. `2026-10-15T14:30:00`)
- **Montants** : nombres décimaux avec point (ex. `1234.56`), **jamais** de chaînes, **jamais** de virgule
- **Labels de classification** : exactement `facture_achat`, `facture_vente`, `autre` (minuscules, underscores)
- **Confiance** : nombre flottant entre `0.0` et `1.0`

### 1.6 Contraintes fichiers

| Contrainte | Valeur |
|---|---|
| Extensions autorisées | `.pdf`, `.jpg`, `.jpeg`, `.png` (insensible à la casse) |
| Taille maximale | **10 Mo** |
| Taille minimale | 1 Ko |
| Nombre de fichiers par requête | **1** (une facture à la fois) |

---

## 2. Endpoints

### 2.1 `GET /api/health`

**Description** : vérifier que le serveur Flask est opérationnel.

**Paramètres** : aucun.

**Réponse 200** :
```json
{
  "status": "ok",
  "version": "1.0",
  "timestamp": "2026-11-11T10:00:00"
}
```

**Usage** : test rapide après démarrage du backend.

---

### 2.2 `POST /api/invoices/upload` ⭐ (endpoint principal)

**Description** : uploader une facture et lancer **tout le pipeline** (OpenCV → CNN → OCR → validation → MySQL).

**Requête** :
- **Content-Type** : `multipart/form-data`
- **Champ** : `file` (le fichier)

**Exemple cURL** :
```bash
curl -X POST http://localhost:5000/api/invoices/upload \
  -F "file=@ma_facture.jpg"
```

**Réponse 200 (succès)** :
```json
{
  "id": 1,
  "filename": "facture_001.jpg",
  "status": "processed",
  "classification": {
    "label": "facture_achat",
    "confidence": 0.94
  },
  "quality": {
    "is_blurry": false,
    "is_dark": false,
    "is_skewed": false,
    "is_badly_framed": false,
    "quality_status": "good",
    "scores": {
      "blur_variance": 245.3,
      "brightness_mean": 142.7,
      "skew_angle": 1.2
    }
  },
  "extracted": {
    "supplier": "ABC SARL",
    "invoice_number": "FAC-2026-001",
    "date": "2026-10-15",
    "total_ht": 1000.00,
    "vat": 200.00,
    "total_ttc": 1200.00
  },
  "validation": {
    "is_valid": true,
    "warnings": []
  },
  "ocr_text": "ABC SARL\nFacture N° FAC-2026-001\nDate : 15/10/2026\n...",
  "created_at": "2026-11-11T10:15:32"
}
```

**Champs de la réponse** :

| Champ | Type | Description |
|---|---|---|
| `id` | int | ID de la facture en base |
| `filename` | string | Nom du fichier sauvegardé |
| `status` | string | `processed`, `warning`, `failed` |
| `classification.label` | string | `facture_achat`, `facture_vente`, ou `autre` |
| `classification.confidence` | float | Score entre 0.0 et 1.0 |
| `quality.is_blurry` | bool | Image floue ? |
| `quality.is_dark` | bool | Image trop sombre ? |
| `quality.is_skewed` | bool | Inclinaison > 5° ? |
| `quality.is_badly_framed` | bool | Cadrage incorrect ? |
| `quality.quality_status` | string | `good`, `warning`, `bad` |
| `quality.scores` | object | Valeurs numériques (debug) |
| `extracted.supplier` | string \| null | Nom du fournisseur |
| `extracted.invoice_number` | string \| null | Numéro de facture |
| `extracted.date` | string \| null | Format `YYYY-MM-DD` |
| `extracted.total_ht` | float \| null | Montant HT |
| `extracted.vat` | float \| null | Montant TVA |
| `extracted.total_ttc` | float \| null | Montant TTC |
| `validation.is_valid` | bool | Toutes les règles OK ? |
| `validation.warnings` | array of string | Liste des avertissements |
| `ocr_text` | string | Texte brut extrait (pour debug) |
| `created_at` | string | Date d'insertion en base |

**Règles sur `status`** :

| `status` | Signification |
|---|---|
| `processed` | Tout s'est bien passé |
| `warning` | Traitement OK mais anomalies détectées (qualité, incohérence montants, doublon) |
| `failed` | Erreur bloquante (OCR a échoué, classification impossible) |

**Warnings possibles** (dans `validation.warnings`) :

| Warning | Signification |
|---|---|
| `BLURRY_IMAGE` | Image floue |
| `DARK_IMAGE` | Image trop sombre |
| `SKEWED_IMAGE` | Image inclinée |
| `BAD_FRAMING` | Cadrage incorrect |
| `MISSING_FIELD:<nom>` | Champ manquant (ex. `MISSING_FIELD:supplier`) |
| `AMOUNT_MISMATCH` | HT + TVA ≠ TTC |
| `INVALID_DATE` | Date non interprétable |
| `POTENTIAL_DUPLICATE` | Doublon potentiel détecté |
| `LOW_CONFIDENCE` | Confiance CNN < 0.6 |

**Réponses d'erreur** :

- **400 `NO_FILE`** :
  ```json
  {
    "error": {
      "code": "NO_FILE",
      "message": "Aucun fichier n'a été fourni dans la requête."
    }
  }
  ```

- **415 `INVALID_FORMAT`** :
  ```json
  {
    "error": {
      "code": "INVALID_FORMAT",
      "message": "Format non supporté. Utilisez PDF, JPG, JPEG ou PNG.",
      "details": "Extension reçue : .docx"
    }
  }
  ```

- **413 `FILE_TOO_LARGE`** :
  ```json
  {
    "error": {
      "code": "FILE_TOO_LARGE",
      "message": "Le fichier dépasse la taille maximale de 10 Mo.",
      "details": "Taille reçue : 15.3 Mo"
    }
  }
  ```

- **500 `DB_ERROR`** :
  ```json
  {
    "error": {
      "code": "DB_ERROR",
      "message": "Impossible d'enregistrer la facture. Réessayez plus tard."
    }
  }
  ```

---

### 2.3 `GET /api/invoices`

**Description** : récupérer la liste des factures traitées (historique).

**Paramètres query** (optionnels) :

| Param | Type | Défaut | Description |
|---|---|---|---|
| `page` | int | 1 | Numéro de page |
| `limit` | int | 20 | Nombre par page (max 100) |
| `status` | string | *(tous)* | Filtrer : `processed`, `warning`, `failed` |
| `label` | string | *(tous)* | Filtrer : `facture_achat`, `facture_vente`, `autre` |

**Réponse 200** :
```json
{
  "total": 42,
  "page": 1,
  "limit": 20,
  "invoices": [
    {
      "id": 42,
      "filename": "facture_042.jpg",
      "status": "processed",
      "label": "facture_achat",
      "confidence": 0.94,
      "created_at": "2026-11-10T14:22:00"
    },
    {
      "id": 41,
      "filename": "facture_041.pdf",
      "status": "warning",
      "label": "facture_vente",
      "confidence": 0.87,
      "created_at": "2026-11-10T11:05:00"
    }
  ]
}
```

---

### 2.4 `GET /api/invoices/{id}`

**Description** : récupérer tous les détails d'une facture.

**Paramètre** : `id` (int, dans l'URL).

**Réponse 200** : identique à la réponse de `/upload` (voir 2.2).

**Réponse 404 `NOT_FOUND`** :
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Aucune facture trouvée avec l'identifiant 999."
  }
}
```

---

### 2.5 `PUT /api/invoices/{id}`

**Description** : corriger manuellement les champs extraits (après OCR).

**Paramètre** : `id` (int).

**Body** (JSON) — tous les champs sont **optionnels**, seuls ceux envoyés sont mis à jour :

```json
{
  "supplier": "ABC SARL",
  "invoice_number": "FAC-2026-001",
  "date": "2026-10-15",
  "total_ht": 1000.00,
  "vat": 200.00,
  "total_ttc": 1200.00
}
```

**Validation** :

- `supplier` : texte ≤ 255 caractères
- `invoice_number` : texte ≤ 100 caractères
- `date` : format `YYYY-MM-DD` valide
- Montants : décimaux positifs
- Règle : `total_ttc ≈ total_ht + vat` (±0.01) → sinon warning mais enregistré

**Réponse 200** :
```json
{
  "id": 1,
  "status": "updated",
  "extracted": {
    "supplier": "ABC SARL",
    "invoice_number": "FAC-2026-001",
    "date": "2026-10-15",
    "total_ht": 1000.00,
    "vat": 200.00,
    "total_ttc": 1200.00
  },
  "validation": {
    "is_valid": true,
    "warnings": []
  },
  "updated_at": "2026-11-11T10:30:00"
}
```

**Réponse 422 `INVALID_INPUT`** :
```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "Le champ 'date' n'est pas au format YYYY-MM-DD.",
    "details": "Valeur reçue : '15/10/2026'"
  }
}
```

---

### 2.6 `DELETE /api/invoices/{id}`

**Description** : supprimer une facture et tous ses enregistrements associés (données extraites, analyse, anomalies).

**Paramètre** : `id` (int).

**Réponse 200** :
```json
{
  "id": 42,
  "status": "deleted"
}
```

**Réponse 404 `NOT_FOUND`** : même format que 2.4.

---

### 2.7 `GET /api/invoices/{id}/export`

**Description** : télécharger les résultats d'une facture au format **JSON**.

**Paramètre** : `id` (int).

**Réponse 200** :
- **Content-Type** : `application/json`
- **Content-Disposition** : `attachment; filename="facture_42.json"`
- **Body** : même structure que `/api/invoices/{id}`

**Usage** : le frontend déclenche un téléchargement.

---

## 3. Schémas JSON détaillés (TypeScript-like)

### 3.1 `Invoice` (réponse complète)

```typescript
interface Invoice {
  id: number;
  filename: string;
  status: "processed" | "warning" | "failed";
  classification: {
    label: "facture_achat" | "facture_vente" | "autre";
    confidence: number;  // 0.0 à 1.0
  };
  quality: {
    is_blurry: boolean;
    is_dark: boolean;
    is_skewed: boolean;
    is_badly_framed: boolean;
    quality_status: "good" | "warning" | "bad";
    scores: {
      blur_variance: number;
      brightness_mean: number;
      skew_angle: number;
    };
  };
  extracted: {
    supplier: string | null;
    invoice_number: string | null;
    date: string | null;          // YYYY-MM-DD
    total_ht: number | null;
    vat: number | null;
    total_ttc: number | null;
  };
  validation: {
    is_valid: boolean;
    warnings: string[];
  };
  ocr_text: string;
  created_at: string;             // ISO datetime
}
```

### 3.2 `ApiError`

```typescript
interface ApiError {
  error: {
    code: string;
    message: string;
    details?: string;
  };
}
```

---

## 4. Règles de validation métier

Appliquées **côté backend**, renvoyées dans `validation.warnings`.

### 4.1 Champs obligatoires

| Champ | Règle |
|---|---|
| `supplier` | Non vide, ≤ 255 car. |
| `invoice_number` | Non vide, ≤ 100 car. |
| `date` | Format `YYYY-MM-DD`, date valide |
| `total_ht` | ≥ 0 |
| `vat` | ≥ 0 |
| `total_ttc` | ≥ 0 |

Tout champ manquant → warning `MISSING_FIELD:<nom>`.

### 4.2 Cohérence des montants

```
|total_ttc - (total_ht + vat)| <= 0.01
```

Si non respecté → warning `AMOUNT_MISMATCH`.

### 4.3 Cohérence de la date

- La date doit être ≤ aujourd'hui + 1 jour (pas de facture dans le futur lointain)
- Si invalide → warning `INVALID_DATE`

### 4.4 Détection de doublons (signalement uniquement)

Une facture est **potentiellement dupliquée** si **au moins 3** des critères suivants matchent une facture existante :

- Même `invoice_number`
- Même `supplier`
- Même `date`
- Même `total_ttc` (±0.01)
- Même empreinte MD5 du fichier

→ warning `POTENTIAL_DUPLICATE` (ne bloque **pas** l'enregistrement).

### 4.5 Confiance de classification

Si `confidence < 0.6` → warning `LOW_CONFIDENCE`.

---

## 5. Frontend — comportement attendu

### 5.1 Page d'importation

1. `POST /api/invoices/upload` avec le fichier
2. Afficher un loader pendant le traitement (peut prendre 3-10 secondes)
3. Si `200` : afficher la carte de résultat (voir 5.2)
4. Si erreur : afficher `error.message` dans un snackbar MUI

### 5.2 Affichage des résultats

- **Bandeau qualité** : couleur selon `quality_status` (vert/orange/rouge)
- **Bloc classification** : label + pourcentage de confiance
- **Formulaire d'édition** : champs `extracted` éditables
- **Liste des warnings** : affichés en chips MUI
- **Bouton "Enregistrer les corrections"** → `PUT /api/invoices/{id}`

### 5.3 Historique

- `GET /api/invoices?page=X&limit=20`
- Pagination MUI
- Clic sur une ligne → `GET /api/invoices/{id}`

### 5.4 Export

- Bouton "Télécharger JSON" → `GET /api/invoices/{id}/export`
- Utiliser `window.open()` ou `fetch` + `Blob` pour forcer le téléchargement

---

## 6. Backend — organisation des routes

```
backend/
├── app.py                        # déclare Flask + enregistre les blueprints
├── routes/
│   ├── __init__.py
│   ├── health.py                 # GET /api/health
│   └── invoices.py               # toutes les routes /api/invoices/*
├── services/
│   ├── quality_service.py        # appelle OpenCV
│   ├── classification_service.py # appelle MobileNetV2
│   ├── ocr_service.py            # appelle PaddleOCR
│   ├── validation_service.py     # applique les règles métier
│   └── persistence_service.py    # INSERT/SELECT/UPDATE/DELETE MySQL
├── database/
│   ├── db.py                     # connexion MySQL
│   └── queries.py                # requêtes SQL préparées
├── uploads/                      # fichiers uploadés
├── .env
└── requirements.txt
```

---

## 7. Schéma de la table `facture` (rappel)

Aligné avec la base MySQL validée :

```sql
CREATE TABLE facture (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom_fichier VARCHAR(255) NOT NULL,
    chemin_fichier VARCHAR(500) NOT NULL,
    type_document VARCHAR(50),          -- 'facture_achat' | 'facture_vente' | 'autre'
    statut VARCHAR(50) DEFAULT 'processed',
    date_importation DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

> Les champs extraits vont dans `donnee_extraite`, l'analyse dans `resultat_analyse`, les warnings dans `anomalie`.

---

## 8. Exemples complets

### 8.1 Upload réussi

**Requête** :
```bash
curl -X POST http://localhost:5000/api/invoices/upload \
  -F "file=@facture_001.jpg"
```

**Réponse** :
```json
{
  "id": 1,
  "filename": "facture_001.jpg",
  "status": "processed",
  "classification": {
    "label": "facture_achat",
    "confidence": 0.94
  },
  "quality": {
    "is_blurry": false,
    "is_dark": false,
    "is_skewed": false,
    "is_badly_framed": false,
    "quality_status": "good",
    "scores": {
      "blur_variance": 245.3,
      "brightness_mean": 142.7,
      "skew_angle": 1.2
    }
  },
  "extracted": {
    "supplier": "ABC SARL",
    "invoice_number": "FAC-2026-001",
    "date": "2026-10-15",
    "total_ht": 1000.00,
    "vat": 200.00,
    "total_ttc": 1200.00
  },
  "validation": {
    "is_valid": true,
    "warnings": []
  },
  "ocr_text": "ABC SARL\nFacture N° FAC-2026-001\nDate : 15/10/2026\nTotal HT : 1000.00\nTVA : 200.00\nTotal TTC : 1200.00",
  "created_at": "2026-11-11T10:15:32"
}
```

### 8.2 Upload avec warnings

```json
{
  "id": 2,
  "filename": "photo_floue.jpg",
  "status": "warning",
  "classification": {
    "label": "facture_achat",
    "confidence": 0.72
  },
  "quality": {
    "is_blurry": true,
    "is_dark": false,
    "is_skewed": false,
    "is_badly_framed": false,
    "quality_status": "warning",
    "scores": {
      "blur_variance": 45.1,
      "brightness_mean": 130.0,
      "skew_angle": 1.0
    }
  },
  "extracted": {
    "supplier": "XYZ Corp",
    "invoice_number": "F-2026-042",
    "date": "2026-10-20",
    "total_ht": 500.00,
    "vat": 100.00,
    "total_ttc": 600.00
  },
  "validation": {
    "is_valid": true,
    "warnings": ["BLURRY_IMAGE", "POTENTIAL_DUPLICATE"]
  },
  "ocr_text": "XYZ Corp\n...",
  "created_at": "2026-11-11T10:20:00"
}
```

### 8.3 Correction manuelle

**Requête** :
```bash
curl -X PUT http://localhost:5000/api/invoices/1 \
  -H "Content-Type: application/json" \
  -d '{"supplier": "ABC SARL", "total_ttc": 1250.00}'
```

**Réponse** :
```json
{
  "id": 1,
  "status": "updated",
  "extracted": {
    "supplier": "ABC SARL",
    "invoice_number": "FAC-2026-001",
    "date": "2026-10-15",
    "total_ht": 1000.00,
    "vat": 200.00,
    "total_ttc": 1250.00
  },
  "validation": {
    "is_valid": false,
    "warnings": ["AMOUNT_MISMATCH"]
  },
  "updated_at": "2026-11-11T10:35:00"
}
```

---

## 9. Versionning et évolution

- Toute modification du contrat **doit** être discutée par les deux (Safaa + Aya)
- Incrémenter la version en haut du fichier (`1.1`, `1.2`, …)
- Documenter le changement dans une section `## 10. Historique`
- Commiter avec le message : `docs(api): modification du contrat — <raison>`

---

## 10. Historique

| Version | Date | Auteur | Changement |
|---|---|---|---|
| 1.0 | 2026-11-11 | Safaa + Aya | Version initiale validée |