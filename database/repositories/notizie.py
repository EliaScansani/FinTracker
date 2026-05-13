# database/repositories/notizie.py
# Repository per la tabella notizie.
# Gestisce il salvataggio e la lettura delle notizie finanziarie
# con filtri per data e pertinenza al ticker.

from database.connection import get_connection, get_cursor


def salva_notizia(ticker: str, titolo: str, fonte: str,
                  url: str, pubblicata_il: str) -> bool:
    """
    Salva una notizia nel database evitando duplicati.
    La clausola ON CONFLICT ON CONSTRAINT gestisce il UNIQUE su url —
    se l'articolo esiste già non fa nulla senza sollevare errori.
    Restituisce True se salvata, False se era già presente.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    try:
        cursor.execute("""
            INSERT INTO notizie (ticker, titolo, fonte, url, pubblicata_il)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (url) DO NOTHING
        """, (ticker, titolo, fonte, url, pubblicata_il))

        salvata = cursor.rowcount > 0
        conn.commit()
        return salvata

    except Exception as e:
        conn.rollback()
        print(f"⚠️  Errore salvataggio notizia: {e}")
        return False

    finally:
        cursor.close()
        conn.close()


def get_notizie(ticker: str = None, solo_oggi: bool = True) -> list:
    """
    Restituisce le notizie salvate nel database.
    - ticker: se specificato filtra per quel titolo
    - solo_oggi: True = solo notizie di oggi
                 False = ultimi 7 giorni

    INTERVAL è la sintassi PostgreSQL per sottrarre un periodo
    dalla data corrente — equivalente a datetime('now', '-7 days') in SQLite.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    # Costruisce il filtro data in base al parametro
    if solo_oggi:
        filtro_data = "AND DATE(salvata_il) = CURRENT_DATE"
    else:
        filtro_data = "AND salvata_il >= NOW() - INTERVAL '7 days'"

    if ticker:
        cursor.execute(f"""
            SELECT ticker, titolo, fonte, url, pubblicata_il
            FROM notizie
            WHERE ticker = %s
            {filtro_data}
            ORDER BY pubblicata_il DESC
            LIMIT 10
        """, (ticker.upper(),))
    else:
        cursor.execute(f"""
            SELECT ticker, titolo, fonte, url, pubblicata_il
            FROM notizie
            WHERE 1=1
            {filtro_data}
            ORDER BY pubblicata_il DESC
            LIMIT 50
        """)

    righe = cursor.fetchall()
    cursor.close()
    conn.close()

    return [dict(r) for r in righe]


def get_notizie_recenti_per_telegram(ticker: str) -> list:
    """
    Restituisce le ultime 3 notizie delle ultime 24 ore per un ticker.
    Usata specificamente dal bot Telegram per il riepilogo mattutino.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT titolo, fonte, url, pubblicata_il
        FROM notizie
        WHERE ticker = %s
        AND salvata_il >= NOW() - INTERVAL '24 hours'
        ORDER BY pubblicata_il DESC
        LIMIT 3
    """, (ticker,))

    righe = cursor.fetchall()
    cursor.close()
    conn.close()

    return [dict(r) for r in righe]