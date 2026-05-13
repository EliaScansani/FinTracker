# backend/routes/segnali.py
# Gestisce la lettura dei segnali tecnici e l'avvio dell'analisi.

from fastapi import APIRouter, HTTPException, status
from database.repositories import get_segnali
from modules.indicators import analizza_watchlist

router = APIRouter()


@router.get("/")
def leggi_segnali(solo_oggi: bool = True, solo_importanti: bool = False):
    """
    Restituisce i segnali tecnici salvati nel database.
    - solo_oggi: True = solo oggi, False = ultimi 30 giorni
    - solo_importanti: True = solo importanza ALTA
    """
    return get_segnali(solo_oggi=solo_oggi, solo_importanti=solo_importanti)

@router.post("/analisi")
def avvia_analisi():
    """
    Avvia l'analisi tecnica completa su tutti i ticker in watchlist.
    Calcola RSI, MACD, SMA e Bande di Bollinger e salva i segnali nel DB.
    """
    try:
        analizza_watchlist()
        return {"messaggio": "Analisi tecnica completata."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )