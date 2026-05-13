# database/repositories/watchlist.py
# Repository per la tabella watchlist.
# Contiene TUTTE le operazioni di lettura e scrittura sulla watchlist.
# Nessun altro file del progetto scriverà query su questa tabella.

import yfinance as yf
from database.connection import get_connection, get_cursor


def get_watchlist():
    """
    Restituisce tutti i ticker presenti nella watchlist
    ordinati per data di aggiunta più recente.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT ticker, nome, data_aggiunta, note
        FROM watchlist
        ORDER BY data_aggiunta DESC
    """)

    righe = cursor.fetchall()
    cursor.close()
    conn.close()

    # Converte da RealDictRow a lista di dizionari standard
    return [dict(r) for r in righe]


def aggiungi_ticker(ticker: str, nome: str = "", note: str = "") -> bool:
    """
    Verifica che il ticker esista su Yahoo Finance poi lo salva.
    Restituisce True se aggiunto, False se non valido o già presente.
    Il nome viene recuperato automaticamente se non fornito.
    """
    ticker = ticker.upper().strip()
    print(f"🔍 Verifico {ticker} su Yahoo Finance...")

    try:
        titolo = yf.Ticker(ticker)
        info = titolo.info

        prezzo  = info.get("currentPrice") or info.get("regularMarketPrice")
        simbolo = info.get("symbol")

        if not prezzo and not simbolo:
            print(f"⚠️  Ticker '{ticker}' non trovato.")
            return False

        if not nome:
            nome = info.get("longName") or info.get("shortName") or ticker
            print(f"   Nome rilevato: {nome}")

    except Exception as e:
        print(f"⚠️  Impossibile verificare '{ticker}': {e}")
        return False

    conn = get_connection()
    cursor = get_cursor(conn)

    try:
        # ON CONFLICT DO NOTHING evita l'errore se il ticker esiste già
        # e restituisce 0 righe inserite invece di sollevare un'eccezione
        cursor.execute("""
            INSERT INTO watchlist (ticker, nome, note)
            VALUES (%s, %s, %s)
            ON CONFLICT (ticker) DO NOTHING
        """, (ticker, nome, note))

        # rowcount = 0 significa che il ticker era già presente
        if cursor.rowcount == 0:
            print(f"⚠️  {ticker} già presente nella watchlist.")
            conn.rollback()
            return False

        conn.commit()
        print(f"✅ {ticker} ({nome}) aggiunto.")
        return True

    except Exception as e:
        conn.rollback()
        print(f"⚠️  Errore inserimento {ticker}: {e}")
        return False

    finally:
        cursor.close()
        conn.close()


def rimuovi_ticker(ticker: str):
    """
    Rimuove il ticker dalla watchlist e tutto il suo storico
    (prezzi, notizie, segnali) in una singola transazione.
    Se una delle DELETE fallisce, viene fatto rollback di tutto.
    """
    ticker = ticker.upper()
    conn = get_connection()
    cursor = get_cursor(conn)

    try:
        # Elimina prima i dati collegati poi il ticker
        # L'ordine è importante — prima i figli poi il padre
        cursor.execute("DELETE FROM prezzi   WHERE ticker = %s", (ticker,))
        cursor.execute("DELETE FROM notizie  WHERE ticker = %s", (ticker,))
        cursor.execute("DELETE FROM segnali  WHERE ticker = %s", (ticker,))
        cursor.execute("DELETE FROM watchlist WHERE ticker = %s", (ticker,))

        conn.commit()
        print(f"🗑️  {ticker} rimosso da watchlist e storico.")

    except Exception as e:
        conn.rollback()
        print(f"⚠️  Errore rimozione {ticker}: {e}")

    finally:
        cursor.close()
        conn.close()


def cerca_ticker(query: str) -> list:
    """
    Cerca ticker su Yahoo Finance per nome o simbolo parziale.
    Restituisce una lista di risultati con ticker, nome, tipo e borsa.
    """
    try:
        risultati = yf.Search(query, max_results=6)
        quotes = risultati.quotes

        tipi_supportati = {
            "EQUITY":         "Azione",
            "ETF":            "ETF",
            "CRYPTOCURRENCY": "Crypto",
            "FUTURE":         "Futures",
            "INDEX":          "Indice",
            "CURRENCY":       "Valuta",
            "MUTUALFUND":     "Fondo"
        }

        return [
            {
                "ticker": q.get("symbol", ""),
                "nome":   q.get("longname") or q.get("shortname", ""),
                "tipo":   tipi_supportati.get(q.get("quoteType", ""), q.get("quoteType", "")),
                "borsa":  q.get("exchange", "")
            }
            for q in quotes
            if q.get("quoteType") in tipi_supportati
        ]

    except Exception as e:
        print(f"⚠️  Errore ricerca: {e}")
        return []