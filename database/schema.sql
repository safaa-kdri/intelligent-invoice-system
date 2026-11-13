-- ==================================================
-- Base de données : Système intelligent de traitement des factures
-- Version : 1.0
-- Date : 2026-11-11
-- Auteur : Safaa El Kadouri
-- ==================================================

-- Création de la base
CREATE DATABASE IF NOT EXISTS invoice_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE invoice_db;

-- ==================================================
-- Table : facture
-- Stocke les métadonnées de chaque fichier uploadé
-- ==================================================
CREATE TABLE IF NOT EXISTS facture (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom_fichier VARCHAR(255) NOT NULL,
    chemin_fichier VARCHAR(500) NOT NULL,
    type_document VARCHAR(50),
    statut VARCHAR(50) DEFAULT 'pending',
    date_importation DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_type_document (type_document),
    INDEX idx_statut (statut),
    INDEX idx_date_importation (date_importation)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==================================================
-- Table : donnee_extraite
-- Stocke les 6 champs extraits par OCR
-- ==================================================
CREATE TABLE IF NOT EXISTS donnee_extraite (
    id INT AUTO_INCREMENT PRIMARY KEY,
    facture_id INT NOT NULL,
    fournisseur VARCHAR(255),
    numero_facture VARCHAR(100),
    date_facture DATE,
    montant_ht DECIMAL(12,2),
    montant_tva DECIMAL(12,2),
    montant_ttc DECIMAL(12,2),

    CONSTRAINT fk_donnee_facture
        FOREIGN KEY (facture_id) REFERENCES facture(id)
        ON DELETE CASCADE,

    INDEX idx_facture_id (facture_id),
    INDEX idx_numero_facture (numero_facture),
    INDEX idx_fournisseur (fournisseur),
    INDEX idx_date_facture (date_facture)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==================================================
-- Table : resultat_analyse
-- Stocke les résultats de classification + qualité
-- ==================================================
CREATE TABLE IF NOT EXISTS resultat_analyse (
    id INT AUTO_INCREMENT PRIMARY KEY,
    facture_id INT NOT NULL,
    confiance FLOAT,
    qualite VARCHAR(50),
    texte_ocr LONGTEXT,
    date_analyse DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_analyse_facture
        FOREIGN KEY (facture_id) REFERENCES facture(id)
        ON DELETE CASCADE,

    INDEX idx_facture_id_analyse (facture_id),
    INDEX idx_qualite (qualite),
    INDEX idx_confiance (confiance)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==================================================
-- Table : anomalie
-- Stocke les warnings détectés (qualité, cohérence, doublons)
-- ==================================================
CREATE TABLE IF NOT EXISTS anomalie (
    id INT AUTO_INCREMENT PRIMARY KEY,
    facture_id INT NOT NULL,
    type_anomalie VARCHAR(100),
    description TEXT,
    date_detection DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_anomalie_facture
        FOREIGN KEY (facture_id) REFERENCES facture(id)
        ON DELETE CASCADE,

    INDEX idx_facture_id_anomalie (facture_id),
    INDEX idx_type_anomalie (type_anomalie)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==================================================
-- Message de confirmation
-- ==================================================
SELECT 'Base invoice_db créée avec succès ✅' AS message;