# database/migrations.py
# Crea tutte le tabelle del database se non esistono già.
# Viene eseguito automaticamente all'avvio dell'applicazione.
# Usa sintassi PostgreSQL nativa:
# - SERIAL al posto di INTEGER AUTOINCREMENT
# - NOW() al posto di datetime('now')
# - BOOLEAN al posto di INTEGER per i valori true/false

from database.connection import get_connection, get_cursor


def esegui_migrazioni():
    """
    Esegue tutte le migrazioni in sequenza.
    Ogni tabella viene creata solo se non esiste già —
    sicuro da eseguire ad ogni avvio senza perdere dati.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    print("🔄 Esecuzione migrazioni database...")

    # ── Tabella watchlist ──────────────────────────
    # Contiene i ticker che l'utente vuole monitorare.
    # UNIQUE su ticker evita duplicati a livello database.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id           SERIAL PRIMARY KEY,
            ticker       TEXT NOT NULL UNIQUE,
            nome         TEXT,
            data_aggiunta DATE DEFAULT CURRENT_DATE,
            note         TEXT
        )
    """)

    # ── Tabella prezzi ─────────────────────────────
    # Storico dei prezzi scaricati da Yahoo Finance.
    # Un record per ogni aggiornamento di ogni ticker.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prezzi (
            id             SERIAL PRIMARY KEY,
            ticker         TEXT NOT NULL,
            timestamp      TIMESTAMPTZ DEFAULT NOW(),
            prezzo         NUMERIC(12, 4),
            variazione_pct NUMERIC(8, 4),
            volume         BIGINT,
            max_52w        NUMERIC(12, 4),
            min_52w        NUMERIC(12, 4)
        )
    """)

    # ── Tabella notizie ────────────────────────────
    # Articoli scaricati da NewsAPI per ogni ticker.
    # UNIQUE su url evita di salvare lo stesso articolo due volte.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notizie (
            id           SERIAL PRIMARY KEY,
            ticker       TEXT NOT NULL,
            titolo       TEXT,
            fonte        TEXT,
            url          TEXT UNIQUE,
            pubblicata_il TIMESTAMPTZ,
            salvata_il   TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # ── Tabella segnali ────────────────────────────
    # Segnali tecnici generati dall'analisi RSI, MACD ecc.
    # importanza può essere: ALTA, MEDIA, BASSA
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS segnali (
            id         SERIAL PRIMARY KEY,
            ticker     TEXT NOT NULL,
            indicatore TEXT NOT NULL,
            valore     NUMERIC(12, 4),
            segnale    TEXT,
            importanza TEXT,
            timestamp  TIMESTAMP DEFAULT NOW()
        )
    """)

    # Indice UNIQUE per evitare duplicati segnali stesso giorno
    # Permette ON CONFLICT su ticker + indicatore + data
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_segnali_unici
        ON segnali (ticker, indicatore, DATE(timestamp))
    """)
    
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Migrazioni completate.")


if __name__ == "__main__":
    esegui_migrazioni()