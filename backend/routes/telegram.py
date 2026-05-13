# backend/routes/telegram.py
# Route per l'invio del riepilogo Telegram direttamente dalla dashboard.

from fastapi import APIRouter, HTTPException, status
from modules.telegram_bot import invia_riepilogo

router = APIRouter()


@router.post("/riepilogo")
def invia():
    """
    Invia il riepilogo giornaliero su Telegram.
    Assembla prezzi, segnali e notizie in un unico messaggio.
    """
    try:
        invia_riepilogo()
        return {"messaggio": "Riepilogo inviato su Telegram."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )