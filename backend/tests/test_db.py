"""
Test d'insertion / lecture / suppression dans MySQL.
À exécuter manuellement : python -m tests.test_db
"""
from database.db import get_connection


def test_insert_and_delete():
    conn = get_connection()
    cursor = conn.cursor()

    # INSERT facture
    cursor.execute(
        "INSERT INTO facture (nom_fichier, chemin_fichier, type_document, statut) "
        "VALUES (%s, %s, %s, %s);",
        ("test.jpg", "uploads/test.jpg", "facture_achat", "processed"),
    )
    conn.commit()
    facture_id = cursor.lastrowid
    print(f"✅ Facture insérée avec id = {facture_id}")

    # INSERT donnee_extraite
    cursor.execute(
        "INSERT INTO donnee_extraite "
        "(facture_id, fournisseur, numero_facture, date_facture, montant_ht, montant_tva, montant_ttc) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s);",
        (facture_id, "ABC SARL", "FAC-TEST-001", "2026-10-15", 1000.00, 200.00, 1200.00),
    )
    conn.commit()
    print("✅ Donnée extraite insérée")

    # SELECT avec jointure
    cursor.execute(
        "SELECT f.id, f.nom_fichier, d.fournisseur, d.montant_ttc "
        "FROM facture f JOIN donnee_extraite d ON d.facture_id = f.id "
        "WHERE f.id = %s;",
        (facture_id,),
    )
    row = cursor.fetchone()
    print(f"✅ SELECT : {row}")

    # DELETE (test ON DELETE CASCADE)
    cursor.execute("DELETE FROM facture WHERE id = %s;", (facture_id,))
    conn.commit()
    print("✅ Facture supprimée")

    # Vérifier que donnee_extraite a été supprimée (CASCADE)
    cursor.execute("SELECT COUNT(*) FROM donnee_extraite WHERE facture_id = %s;", (facture_id,))
    count = cursor.fetchone()[0]
    if count == 0:
        print("✅ CASCADE OK : donnee_extraite supprimée automatiquement")
    else:
        print(f"❌ CASCADE KO : {count} ligne(s) restante(s)")

    cursor.close()
    conn.close()
    print("\n🎉 Test terminé avec succès.")


if __name__ == "__main__":
    test_insert_and_delete()