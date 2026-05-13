# backend/routes/storico.py
# Fornisce i dati storici OHLCV per i grafici del frontend.
# I dati vengono scaricati da Yahoo Finance tramite yfinance.

from fastapi import APIRouter, HTTPException
import yfinance as yf
import pandas as pd

router = APIRouter()


@router.get("/{ticker}")
def leggi_storico(ticker: str, periodo: str = "6mo"):
    """
    Restituisce i dati storici giornalieri per un ticker.
    Parametri:
    - ticker: simbolo del titolo (es. AAPL)
    - periodo: 1mo, 3mo, 6mo, 1y, 2y (default 6mo)
    """
    periodi_validi = ["1mo", "3mo", "6mo", "1y", "2y"]
    if periodo not in periodi_validi:
        raise HTTPException(
            status_code=400,
            detail=f"Periodo non valido. Scegli tra: {periodi_validi}"
        )

    try:
        titolo = yf.Ticker(ticker.upper())
        df = titolo.history(period=periodo, interval="1d")

        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Nessun dato disponibile per {ticker.upper()}"
            )

        sma20      = df["Close"].rolling(20).mean()
        std20      = df["Close"].rolling(20).std()
        bb_upper   = sma20 + (std20 * 2)
        bb_lower   = sma20 - (std20 * 2)

        # Converte il DataFrame in una lista di dizionari
        # Le date vengono convertite in stringhe per la serializzazione JSON
        return [
            {
                "data":    str(idx.date()),
                "open":    round(row["Open"], 2),
                "high":    round(row["High"], 2),
                "low":     round(row["Low"], 2),
                "close":   round(row["Close"], 2),
                "volume":  int(row["Volume"]),
                "bb_upper": round(bb_upper[idx], 2) if not pd.isna(bb_upper[idx]) else None,
                "bb_lower": round(bb_lower[idx], 2) if not pd.isna(bb_lower[idx]) else None,
                "bb_mid":   round(sma20[idx], 2)    if not pd.isna(sma20[idx])    else None
            }
            for idx, row in df.iterrows()
        ]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))