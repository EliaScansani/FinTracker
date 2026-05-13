# database/connection.py
# Gestisce la connessione a PostgreSQL.
# Fornisce due modalità:
# - get_connection() → connessione diretta per i repository
# - get_db()         → dipendenza FastAPI con chiusura automatica

import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """
    Connessione PostgreSQL con parametri separati.
    Più sicura dell'URL quando la password contiene caratteri speciali.
    """
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "fintracker"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD")
    )
    return conn


def get_cursor(conn):
    """
    Crea un cursore che restituisce i risultati come dizionari.
    Ogni riga sarà un dizionario con i nomi delle colonne come chiavi.
    Es: {"ticker": "AAPL", "prezzo": 182.5, ...}
    """
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def get_db():
    """
    Dipendenza FastAPI — apre la connessione, la fornisce alla route
    e la chiude automaticamente al termine, anche in caso di errore.
    Usata con Depends(get_db) nelle route FastAPI.
    """
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()