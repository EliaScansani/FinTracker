# backend/routes/notizie.py
# Gestisce la lettura e l'aggiornamento delle notizie finanziarie.

from fastapi import APIRouter, HTTPException, status
from database.repositories import get_notizie
from modules.news import aggiorna_notizie as _aggiorna_notizie

router = APIRouter()


@router.get("/")
def leggi_notizie(ticker: str = None, solo_oggi: bool = True):
    """
    Restituisce le notizie salvate nel database.
    - ticker: filtra per ticker specifico (es. ?ticker=AAPL)
    - solo_oggi: True = solo oggi, False = ultimi 7 giorni
    """
    return get_notizie(ticker=ticker, solo_oggi=solo_oggi)



@router.post("/aggiorna")
def aggiorna():
    """Forza l'aggiornamento delle notizie per tutti i ticker in watchlist."""
    try:
        _aggiorna_notizie()
        return {"messaggio": "Notizie aggiornate con successo."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )