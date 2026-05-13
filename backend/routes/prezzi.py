# backend/routes/prezzi.py
# Gestisce la lettura e l'aggiornamento dei prezzi di mercato.

from fastapi import APIRouter, HTTPException, status
from database.repositories import get_ultimi_prezzi
from modules.market_data import aggiorna_prezzi as _aggiorna_prezzi

router = APIRouter()


@router.get("/")
def leggi_prezzi():
    """
    Restituisce l'ultimo prezzo salvato per ogni ticker in watchlist.
    Usa DISTINCT ON di PostgreSQL per prendere il record più recente.
    """
    return get_ultimi_prezzi()

@router.post("/aggiorna")
def aggiorna():
    """
    Forza l'aggiornamento dei prezzi per tutti i ticker in watchlist.
    Può richiedere qualche secondo in base al numero di ticker.
    """
    try:
        _aggiorna_prezzi()
        return {"messaggio": "Prezzi aggiornati con successo."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )