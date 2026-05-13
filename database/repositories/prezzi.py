# database/repositories/prezzi.py
# Repository per la tabella prezzi.
# Gestisce il salvataggio dello storico prezzi e la lettura
# dell'ultimo prezzo disponibile per ogni ticker.

from database.connection import get_connection, get_cursor


def salva_prezzo(ticker: str, prezzo: float, variazione_pct: float,
                 volume: int, max_52w: float, min_52w: float):
    """
    Inserisce un nuovo record nella tabella prezzi.
    Il timestamp viene impostato automaticamente dal database con NOW().
    Ogni chiamata aggiunge un record — lo storico viene mantenuto completo.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    try:
        cursor.execute("""
            INSERT INTO prezzi (ticker, prezzo, variazione_pct, volume, max_52w, min_52w)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (ticker, prezzo, variazione_pct, volume, max_52w, min_52w))

        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"⚠️  Errore salvataggio prezzo {ticker}: {e}")

    finally:
        cursor.close()
        conn.close()


def get_ultimi_prezzi() -> list:
    """
    Restituisce l'ultimo prezzo registrato per ogni ticker.
    Usa una subquery per selezionare solo il record più recente
    per ogni ticker — DISTINCT ON è una funzionalità PostgreSQL
    che non esiste in SQLite e rende la query molto più efficiente.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    # DISTINCT ON (ticker) prende una sola riga per ticker
    # ORDER BY ticker, timestamp DESC garantisce che sia la più recente
    cursor.execute("""
        SELECT DISTINCT ON (ticker)
            ticker, prezzo, variazione_pct,
            volume, max_52w, min_52w, timestamp
        FROM prezzi
        ORDER BY ticker, timestamp DESC
    """)

    righe = cursor.fetchall()
    cursor.close()
    conn.close()

    return [dict(r) for r in righe]


def get_storico_ticker(ticker: str, limite: int = 100) -> list:
    """
    Restituisce lo storico completo dei prezzi per un ticker specifico.
    Ordinato dal più recente al più vecchio, limitato a N record.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT ticker, prezzo, variazione_pct, volume, timestamp
        FROM prezzi
        WHERE ticker = %s
        ORDER BY timestamp DESC
        LIMIT %s
    """, (ticker, limite))

    righe = cursor.fetchall()
    cursor.close()
    conn.close()

    return [dict(r) for r in righe]