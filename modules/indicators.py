# modules/indicators.py
# Questo modulo calcola gli indicatori tecnici sui dati storici di ogni ticker.
# Gli indicatori analizzano l'andamento passato del titolo per generare
# segnali utili a capire se un titolo è in trend positivo, negativo,
# ipercomprato o ipervenduto.
# Utilizza pandas-ta che estende pandas con funzioni di analisi tecnica.

import yfinance as yf        # Per scaricare i dati storici
import pandas as pd          # Per manipolare i dati in DataFrame
import pandas_ta as ta       # Libreria di indicatori tecnici
try:
    from database.repositories import get_watchlist, salva_segnale  # Funzioni per interagire con il database
except Exception:  # pragma: no cover - fallback for test environments without DB
    def get_watchlist():
        return []

    def salva_segnale(*args, **kwargs):
        # No-op fallback for environments without a database (tests/mock)
        return None


# ─────────────────────────────────────────────
# FUNZIONE PRINCIPALE: analizza tutti i ticker
# ─────────────────────────────────────────────

def analizza_watchlist():
    """
    Per ogni ticker in watchlist scarica i dati storici,
    calcola RSI, MACD, SMA e Bande di Bollinger e salva i segnali.
    """
    watchlist = get_watchlist()
    if not watchlist:
        print("📭 La watchlist è vuota.")
        return

    for riga in watchlist:
        ticker = riga["ticker"]
        print(f"\n📊 Analisi tecnica: {ticker}")
        print("─" * 40)

        try:
            df = _get_storico(ticker)
            if df.empty:
                print(f"  ⚠️  Nessun dato storico per {ticker}")
                continue

            prezzo = round(df["Close"].iloc[-1], 2)
            print(f"  💰 Prezzo attuale: ${prezzo}")

            _analizza_rsi(df, ticker)
            _analizza_macd(df, ticker)
            _analizza_sma(df, ticker, prezzo)
            _analizza_bollinger(df, ticker, prezzo)

        except Exception as e:
            print(f"  ⚠️  Errore per {ticker}: {e}")

    print("\n✅ Analisi tecnica completata.")


def _get_storico(ticker, periodo="6mo"):
    titolo = yf.Ticker(ticker)
    return titolo.history(period=periodo, interval="1d")

def _analizza_rsi(df, ticker):
    rsi_result = df.ta.rsi(length=14)
    
    if rsi_result is None or rsi_result.empty:
        return

    valore = rsi_result.iloc[-1]
    
    try:
        valore_float = float(valore)
    except (TypeError, ValueError):
        return

    if pd.isna(valore_float):
        return

    rsi = round(valore_float, 2)

    if rsi > 70: 
        segnale, importanza = "IPERCOMPRATO", "ALTA"
    elif rsi < 30: 
        segnale, importanza = "IPERVENDUTO", "ALTA"
    elif rsi > 60:
        segnale, importanza = "TENDENZA RIALZISTA", "MEDIA"
    elif rsi < 40:  
        segnale, importanza = "TENDENZA RIBASSISTA", "MEDIA"
    else:          
        segnale, importanza = "NEUTRO", "BASSA"

    print(f"  📈 RSI ({rsi}): {segnale}")
    salva_segnale(ticker, "RSI", rsi, segnale, importanza)


def _analizza_macd(df, ticker):
    macd_result = df.ta.macd(fast=12, slow=26, signal=9)
    
    if macd_result is None:
        return
    
    try:
        m = macd_result["MACD_12_26_9"].iloc[-1]
        s = macd_result["MACDs_12_26_9"].iloc[-1]
        h = macd_result["MACDh_12_26_9"].iloc[-1]
    except KeyError:
        return

    if pd.isna(m) or pd.isna(s) or pd.isna(h): 
        return

    macd   = round(float(m), 4)
    signal = round(float(s), 4)
    hist   = round(float(h), 4)

    segnale    = "MOMENTUM POSITIVO" if macd > signal else "MOMENTUM NEGATIVO"
    print(f"  📉 MACD ({macd}): {segnale}")
    salva_segnale(ticker, "MACD", hist, segnale, "MEDIA")


def _analizza_sma(df, ticker, prezzo):
    for periodo in [20, 50, 200]:
        if len(df) < periodo:
            continue
        df.ta.sma(length=periodo, append=True)
        colonna = f"SMA_{periodo}"
        if colonna not in df.columns:
            continue

        valore_raw = df[colonna].iloc[-1]
        if pd.isna(valore_raw):  # ← salta se NaN
            continue

        valore  = round(float(valore_raw), 2)
        segnale = f"PREZZO {'SOPRA' if prezzo > valore else 'SOTTO'} SMA{periodo}"

        print(f"  📊 SMA{periodo} ({valore}): {segnale}")
        salva_segnale(ticker, f"SMA{periodo}", valore, segnale, "BASSA")


def _analizza_bollinger(df, ticker, prezzo):
    bbands =df.ta.bbands(length=20, std=2)
    
    if bbands is None:
        return
    
    try:
        col_upper = [c for c in bbands.columns if c.startswith("BBU")][0]
        col_lower = [c for c in bbands.columns if c.startswith("BBL")][0]
        col_mid   = [c for c in bbands.columns if c.startswith("BBM")][0]
    
        upper = round(float(bbands[col_upper].iloc[-1]), 2)
        lower = round(float(bbands[col_lower].iloc[-1]), 2)
        mid = round(float(bbands[col_mid].iloc[-1]), 2)
    except (KeyError, TypeError):
        return

    if any(pd.isna(v) for v in [upper, lower, mid]):
        return
    
    larghezza = round(((upper - lower) / mid) * 100, 2)

    if prezzo >= upper:    
        segnale, importanza = "PREZZO A BANDA SUPERIORE", "ALTA"
    elif prezzo <= lower:  
        segnale, importanza = "PREZZO A BANDA INFERIORE", "ALTA"
    else:                  
        segnale, importanza = "PREZZO DENTRO LE BANDE", "BASSA"

    print(f"  🎯 Bollinger ({lower}/${upper}): {segnale}")
    salva_segnale(ticker, "BOLLINGER", larghezza, segnale, importanza)
