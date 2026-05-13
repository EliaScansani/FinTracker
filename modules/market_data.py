# modules/market_data.py
# Questo modulo si occupa di scaricare i dati di mercato per ogni ticker
# presente nella watchlist e di salvarli nella tabella "prezzi" del database.
# Utilizza la libreria yfinance che si connette gratuitamente a Yahoo Finance.

import yfinance as yf 
from database.connection import get_connection                         # Libreria per scaricare dati finanziari da Yahoo Finance
from database.repositories import get_watchlist, salva_prezzo  # Funzioni per interagire con il database


# ─────────────────────────────────────────────
# FUNZIONE PRINCIPALE: scarica e salva i prezzi
# ─────────────────────────────────────────────

def aggiorna_prezzi():
    """
    Per ogni ticker nella watchlist scarica i dati aggiornati
    da Yahoo Finance e li salva nel database tramite il repository.
    """
    watchlist = get_watchlist()

    if not watchlist:
        print("📭 La watchlist è vuota.")
        return

    for riga in watchlist:
        ticker = riga["ticker"]
        print(f"📡 Scaricando dati per {ticker}...")

        try:
            titolo = yf.Ticker(ticker)
            info   = titolo.info

            prezzo         = info.get("currentPrice") or info.get("regularMarketPrice")
            variazione_pct = info.get("regularMarketChangePercent")
            volume         = info.get("regularMarketVolume")
            max_52w        = info.get("fiftyTwoWeekHigh")
            min_52w        = info.get("fiftyTwoWeekLow")

            if not prezzo:
                print(f"  ⚠️  Nessun prezzo disponibile per {ticker}.")
                continue

            salva_prezzo(ticker, prezzo, variazione_pct, volume, max_52w, min_52w)

            print(f"  💰 Prezzo:     ${prezzo}")
            print(f"  📈 Variazione: {round(variazione_pct, 2) if variazione_pct else 'N/D'}%")
            print(f"  📊 Volume:     {volume}")

        except Exception as e:
            print(f"  ⚠️  Errore per {ticker}: {e}")

    print("✅ Aggiornamento prezzi completato.")
