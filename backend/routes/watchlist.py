# backend/routes/watchlist.py
# Route per la gestione della watchlist.
# Espone API REST per leggere, aggiungere, rimuovere ticker.

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from database.repositories import (
    get_watchlist, aggiungi_ticker,
    rimuovi_ticker, cerca_ticker
)

router = APIRouter()


class AggiungiTickerRequest(BaseModel):
    note: str = ""


@router.get("/")
def leggi_watchlist():
    """Restituisce tutti i ticker presenti nella watchlist."""
    return get_watchlist()


@router.get("/cerca/{query}")
def cerca(query: str):
    """
    Cerca ticker su Yahoo Finance per nome o simbolo parziale.
    Es: /api/watchlist/cerca/Amazon → restituisce AMZN con dettagli.
    """
    risultati = cerca_ticker(query)
    return {"risultati": risultati}


@router.post("/{ticker}", status_code=status.HTTP_201_CREATED)
def aggiungi(ticker: str, body: AggiungiTickerRequest = AggiungiTickerRequest()):
    """
    Aggiunge un ticker alla watchlist dopo averlo validato su Yahoo Finance.
    Restituisce 400 se il ticker non esiste o è già presente.
    """
    successo = aggiungi_ticker(ticker.upper(), note=body.note)
    if not successo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ticker '{ticker.upper()}' non valido o già presente."
        )
    return {"messaggio": f"{ticker.upper()} aggiunto alla watchlist."}


@router.delete("/{ticker}")
def rimuovi(ticker: str):
    """Rimuove un ticker dalla watchlist e tutto il suo storico."""
    rimuovi_ticker(ticker.upper())
    return {"messaggio": f"{ticker.upper()} rimosso dalla watchlist."}