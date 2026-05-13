# tests/test_indicators.py
# Testa il calcolo degli indicatori tecnici.
# Questi test non richiedono database né chiamate API —
# lavorano solo su dati numerici generati internamente.

import pytest
import pandas as pd
import numpy as np
from modules.indicators import (
    _get_storico, _analizza_rsi,
    _analizza_macd, _analizza_sma,
    _analizza_bollinger
)


# ─────────────────────────────────────────────
# FIXTURE — dati storici simulati
# ─────────────────────────────────────────────

@pytest.fixture
def dati_crescenti():
    """
    Crea un DataFrame con 60 giorni di prezzi crescenti.
    Simula un titolo in forte trend rialzista — RSI dovrebbe
    essere alto (ipercomprato).
    """
    date = pd.date_range("2024-01-01", periods=60, freq="D")
    prezzi = [100 + i * 2 for i in range(60)]  # Prezzi da 100 a 218

    df = pd.DataFrame({
        "Open":   [p - 1 for p in prezzi],
        "High":   [p + 2 for p in prezzi],
        "Low":    [p - 2 for p in prezzi],
        "Close":  prezzi,
        "Volume": [1000000] * 60
    }, index=date)

    return df


@pytest.fixture
def dati_decrescenti():
    """
    Crea un DataFrame con 60 giorni di prezzi decrescenti.
    Simula un titolo in forte trend ribassista — RSI dovrebbe
    essere basso (ipervenduto).
    """
    date = pd.date_range("2024-01-01", periods=60, freq="D")
    prezzi = [200 - i * 2 for i in range(60)]  # Prezzi da 200 a 82

    df = pd.DataFrame({
        "Open":   [p + 1 for p in prezzi],
        "High":   [p + 2 for p in prezzi],
        "Low":    [p - 2 for p in prezzi],
        "Close":  prezzi,
        "Volume": [1000000] * 60
    }, index=date)

    return df


@pytest.fixture
def dati_pochi():
    """
    Crea un DataFrame con solo 5 giorni di dati.
    Simula un titolo appena quotato — gli indicatori
    non dovrebbero essere calcolabili.
    """
    date = pd.date_range("2024-01-01", periods=5, freq="D")
    prezzi = [100, 102, 101, 103, 105]

    df = pd.DataFrame({
        "Open":   [p - 1 for p in prezzi],
        "High":   [p + 1 for p in prezzi],
        "Low":    [p - 1 for p in prezzi],
        "Close":  prezzi,
        "Volume": [500000] * 5
    }, index=date)

    return df


# ─────────────────────────────────────────────
# TEST RSI
# ─────────────────────────────────────────────

def test_rsi_ipercomprato(dati_crescenti):
    """
    Con prezzi sempre crescenti il RSI deve essere > 70
    e il segnale deve essere IPERCOMPRATO con importanza ALTA.
    """
    segnali_salvati = []

    # Sostituiamo salva_segnale con una funzione che raccoglie i segnali
    # invece di scriverli nel database
    import modules.indicators as ind
    originale = ind.salva_segnale
    ind.salva_segnale = lambda *args: segnali_salvati.append(args)

    _analizza_rsi(dati_crescenti.copy(), "TEST")

    ind.salva_segnale = originale  # Ripristina la funzione originale

    assert len(segnali_salvati) == 1
    _, _, rsi, segnale, importanza = segnali_salvati[0]
    assert rsi > 70
    assert segnale == "IPERCOMPRATO"
    assert importanza == "ALTA"


def test_rsi_ipervenduto(dati_decrescenti):
    """
    Con prezzi sempre decrescenti il RSI deve essere < 30
    e il segnale deve essere IPERVENDUTO con importanza ALTA.
    """
    segnali_salvati = []

    import modules.indicators as ind
    originale = ind.salva_segnale
    ind.salva_segnale = lambda *args: segnali_salvati.append(args)

    _analizza_rsi(dati_decrescenti.copy(), "TEST")

    ind.salva_segnale = originale

    assert len(segnali_salvati) == 1
    _, _, rsi, segnale, importanza = segnali_salvati[0]
    assert rsi < 30
    assert segnale == "IPERVENDUTO"
    assert importanza == "ALTA"


def test_rsi_dati_insufficienti(dati_pochi):
    """
    Con meno di 14 giorni di dati il RSI non è calcolabile.
    La funzione non deve salvare nessun segnale — deve terminare
    silenziosamente senza errori.
    """
    segnali_salvati = []

    import modules.indicators as ind
    originale = ind.salva_segnale
    ind.salva_segnale = lambda *args: segnali_salvati.append(args)

    _analizza_rsi(dati_pochi.copy(), "TEST")

    ind.salva_segnale = originale

    # Con pochi dati il RSI è NaN — nessun segnale deve essere salvato
    assert len(segnali_salvati) == 0


# ─────────────────────────────────────────────
# TEST SMA
# ─────────────────────────────────────────────

def test_sma_prezzo_sopra(dati_crescenti):
    """
    Con prezzi crescenti l'ultimo prezzo deve essere
    sopra tutte le medie mobili calcolabili.
    """
    segnali_salvati = []

    import modules.indicators as ind
    originale = ind.salva_segnale
    ind.salva_segnale = lambda *args: segnali_salvati.append(args)

    prezzo = float(dati_crescenti["Close"].iloc[-1])
    _analizza_sma(dati_crescenti.copy(), "TEST", prezzo)

    ind.salva_segnale = originale

    # Tutti i segnali calcolabili devono essere "SOPRA"
    for args in segnali_salvati:
        assert "SOPRA" in args[3]


def test_sma_prezzo_sotto(dati_decrescenti):
    """
    Con prezzi decrescenti l'ultimo prezzo deve essere
    sotto tutte le medie mobili calcolabili.
    """
    segnali_salvati = []

    import modules.indicators as ind
    originale = ind.salva_segnale
    ind.salva_segnale = lambda *args: segnali_salvati.append(args)

    prezzo = float(dati_decrescenti["Close"].iloc[-1])
    _analizza_sma(dati_decrescenti.copy(), "TEST", prezzo)

    ind.salva_segnale = originale

    for args in segnali_salvati:
        assert "SOTTO" in args[3]


def test_sma_dati_insufficienti(dati_pochi):
    """
    Con 5 giorni di dati nessuna SMA è calcolabile (minimo 20).
    Nessun segnale deve essere salvato.
    """
    segnali_salvati = []

    import modules.indicators as ind
    originale = ind.salva_segnale
    ind.salva_segnale = lambda *args: segnali_salvati.append(args)

    prezzo = float(dati_pochi["Close"].iloc[-1])
    _analizza_sma(dati_pochi.copy(), "TEST", prezzo)

    ind.salva_segnale = originale

    assert len(segnali_salvati) == 0


# ─────────────────────────────────────────────
# TEST BOLLINGER
# ─────────────────────────────────────────────

def test_bollinger_prezzo_dentro(dati_crescenti):
    """
    Con prezzi che crescono gradualmente il prezzo
    dovrebbe stare dentro le bande nella maggior parte dei casi.
    Il segnale deve essere calcolato senza errori.
    """
    segnali_salvati = []

    import modules.indicators as ind
    originale = ind.salva_segnale
    ind.salva_segnale = lambda *args: segnali_salvati.append(args)

    prezzo = float(dati_crescenti["Close"].iloc[-1])
    _analizza_bollinger(dati_crescenti.copy(), "TEST", prezzo)

    ind.salva_segnale = originale

    # Deve essere stato calcolato almeno un segnale Bollinger
    assert len(segnali_salvati) == 1
    # Il segnale deve essere uno dei tre validi
    assert segnali_salvati[0][3] in [
        "PREZZO DENTRO LE BANDE",
        "PREZZO A BANDA SUPERIORE",
        "PREZZO A BANDA INFERIORE"
    ]