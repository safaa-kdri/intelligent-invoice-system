"""
Service de persistance MySQL.
Regroupe toutes les opérations d'écriture/lecture liées aux factures.

Chaque fonction ouvre et ferme sa propre connexion pour éviter
les problèmes de concurrence (simple et sûr pour un projet pédagogique).
"""
from database.db import get_connection


def create_facture(nom_fichier: str, chemin_fichier: str) -> int:
    """
    Insère une nouvelle ligne dans la table `facture` avec statut 'pending'.
    Retourne l'ID auto-généré par MySQL.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO facture (nom_fichier, chemin_fichier, statut) "
            "VALUES (%s, %s, %s);",
            (nom_fichier, chemin_fichier, "pending"),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()


def update_facture_status(
    facture_id: int, type_document: str, statut: str
) -> None:
    """
    Met à jour le type_document (label CNN) et le statut de la facture.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE facture SET type_document = %s, statut = %s WHERE id = %s;",
            (type_document, statut, facture_id),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def create_resultat_analyse(
    facture_id: int,
    confiance: float,
    qualite: str,
    texte_ocr: str = "",
) -> int:
    """
    Insère une ligne dans `resultat_analyse` (résultats IA).
    Retourne l'ID auto-généré.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO resultat_analyse "
            "(facture_id, confiance, qualite, texte_ocr) "
            "VALUES (%s, %s, %s, %s);",
            (facture_id, confiance, qualite, texte_ocr),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()


def create_anomalie(
    facture_id: int, type_anomalie: str, description: str
) -> int:
    """
    Insère une ligne dans `anomalie`.
    Retourne l'ID auto-généré.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO anomalie (facture_id, type_anomalie, description) "
            "VALUES (%s, %s, %s);",
            (facture_id, type_anomalie, description),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()


def create_donnee_extraite(
    facture_id: int,
    fournisseur: str | None = None,
    numero_facture: str | None = None,
    date_facture: str | None = None,
    montant_ht: float | None = None,
    montant_tva: float | None = None,
    montant_ttc: float | None = None,
) -> int:
    """
    Insère une ligne dans `donnee_extraite`.
    Les champs peuvent être None si l'OCR n'a rien trouvé.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO donnee_extraite "
            "(facture_id, fournisseur, numero_facture, date_facture, "
            "montant_ht, montant_tva, montant_ttc) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s);",
            (
                facture_id,
                fournisseur,
                numero_facture,
                date_facture,
                montant_ht,
                montant_tva,
                montant_ttc,
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()


def get_facture_by_id(facture_id: int) -> dict | None:
    """
    Récupère une facture complète (facture + donnee_extraite + resultat_analyse).
    Retourne un dict ou None si introuvable.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT f.id, f.nom_fichier, f.chemin_fichier, f.type_document, "
            "f.statut, f.date_importation, "
            "r.confiance, r.qualite, r.texte_ocr, r.date_analyse, "
            "d.fournisseur, d.numero_facture, d.date_facture, "
            "d.montant_ht, d.montant_tva, d.montant_ttc "
            "FROM facture f "
            "LEFT JOIN resultat_analyse r ON r.facture_id = f.id "
            "LEFT JOIN donnee_extraite d ON d.facture_id = f.id "
            "WHERE f.id = %s;",
            (facture_id,),
        )
        row = cursor.fetchone()
        return row
    finally:
        cursor.close()
        conn.close()


def get_anomalies_by_facture_id(facture_id: int) -> list[dict]:
    """
    Récupère toutes les anomalies d'une facture.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, type_anomalie, description, date_detection "
            "FROM anomalie WHERE facture_id = %s ORDER BY date_detection ASC;",
            (facture_id,),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def get_all_factures(
    page: int = 1,
    limit: int = 20,
    status: str | None = None,
    label: str | None = None,
) -> tuple[list[dict], int]:
    """
    Récupère la liste paginée des factures, avec filtres optionnels.
    Retourne (liste_factures, total_count).
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Construire la clause WHERE dynamiquement
        where_clauses = []
        params = []

        if status:
            where_clauses.append("statut = %s")
            params.append(status)
        if label:
            where_clauses.append("type_document = %s")
            params.append(label)

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        # Compter le total
        cursor.execute(f"SELECT COUNT(*) AS total FROM facture {where_sql};", params)
        total = cursor.fetchone()["total"]

        # Récupérer la page
        offset = (page - 1) * limit
        cursor.execute(
            f"SELECT id, nom_fichier, type_document, statut, date_importation "
            f"FROM facture {where_sql} "
            f"ORDER BY date_importation DESC "
            f"LIMIT %s OFFSET %s;",
            params + [limit, offset],
        )
        rows = cursor.fetchall()

        # Convertir les datetime en string ISO
        for row in rows:
            if row.get("date_importation"):
                row["date_importation"] = row["date_importation"].isoformat()

        return rows, total
    finally:
        cursor.close()
        conn.close()


def delete_facture(facture_id: int) -> bool:
    """
    Supprime une facture (et ses données associées par CASCADE).
    Retourne True si une ligne a été supprimée, False sinon.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM facture WHERE id = %s;", (facture_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()


def facture_exists(facture_id: int) -> bool:
    """
    Vérifie si une facture existe.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM facture WHERE id = %s;", (facture_id,))
        return cursor.fetchone()[0] > 0
    finally:
        cursor.close()
        conn.close()