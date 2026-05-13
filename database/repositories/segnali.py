# database/repositories/segnali.py
# Repository per la tabella segnali.
# Gestisce il salvataggio dei segnali tecnici generati dall'analisi
# e la lettura con filtri per data e importanza.

from database.connection import get_connection, get_cursor


def salva_segnale(ticker: str, indicatore: str, valore: float,
                  segnale: str, importanza: str):
    """
    Salva un segnale tecnico nel database.
    Il timestamp viene impostato automaticamente dal database con NOW().
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    try:
        cursor.execute("""
            INSERT INTO segnali (ticker, indicatore, valore, segnale, importanza, timestamp)
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON CONFLICT (ticker, indicatore, DATE(timestamp)) 
                       DO UPDATE SET
                        valore     = EXCLUDED.valore,
                        segnale    = EXCLUDED.segnale,
                        importanza = EXCLUDED.importanza,
                        timestamp  = NOW()
        """, (ticker, indicatore, valore, segnale, importanza))

        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"⚠️  Errore salvataggio segnale {ticker}: {e}")

    finally:
        cursor.close()
        conn.close()


def get_segnali(solo_oggi: bool = True, solo_importanti: bool = False) -> list:
    """
    Restituisce i segnali tecnici salvati nel database.
    - solo_oggi: True = solo segnali di oggi
                 False = ultimi 30 giorni
    - solo_importanti: True = solo importanza ALTA

    Nota PostgreSQL: CURRENT_DATE confronta solo la parte data
    di un TIMESTAMPTZ — equivalente a date('now') in SQLite.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    if solo_oggi:
        filtro_data = "AND DATE(timestamp) = CURRENT_DATE"
    else:
        filtro_data = "AND timestamp >= NOW() - INTERVAL '30 days'"

    filtro_imp = "AND importanza = 'ALTA'" if solo_importanti else ""

    cursor.execute(f"""
        SELECT DISTINCT ON (ticker, indicatore)
                   ticker, indicatore, valore, segnale, importanza, timestamp
        FROM segnali
        WHERE 1=1
        {filtro_data}
        {filtro_imp}
        ORDER BY ticker, indicatore, timestamp DESC
    """)

    righe = cursor.fetchall()
    cursor.close()
    conn.close()

    return [dict(r) for r in righe]


def get_segnali_importanti_oggi() -> list:
    """
    Restituisce solo i segnali ALTA importanza delle ultime 24 ore.
    Usata specificamente dal bot Telegram per il riepilogo mattutino.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT DISTINCT ON (ticker, indicatore)
                   ticker, indicatore, segnale, valore
        FROM segnali
        WHERE importanza = 'ALTA'
        AND timestamp >= NOW() - INTERVAL '24 hours'
        ORDER BY ticker, indicatore, timestamp DESC
    """)

    righe = cursor.fetchall()
    cursor.close()
    conn.close()

    return [dict(r) for r in righe]