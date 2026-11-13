"""
Module de connexion à MySQL.
Charge les paramètres depuis .env et fournit une connexion réutilisable.
"""
import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Charge le fichier .env situé à la racine du backend
load_dotenv()


def get_connection():
    """
    Retourne une nouvelle connexion MySQL.
    Lève une exception si la connexion échoue.
    """
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "invoice_db"),
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci",
        )
        return connection
    except Error as e:
        raise ConnectionError(f"Impossible de se connecter à MySQL : {e}")


def test_connection():
    """
    Test rapide de la connexion.
    Retourne True si OK, False sinon.
    """
    try:
        conn = get_connection()
        if conn.is_connected():
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION();")
            version = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s;",
                           (os.getenv("DB_NAME", "invoice_db"),))
            nb_tables = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            print(f"✅ Connexion MySQL OK — version {version} — {nb_tables} table(s) dans la base.")
            return True
    except Exception as e:
        print(f"❌ Échec de connexion : {e}")
        return False


def count_rows(table_name):
    """
    Retourne le nombre de lignes d'une table.
    Utile pour vérifier manuellement les inserts.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count


if __name__ == "__main__":
    test_connection()