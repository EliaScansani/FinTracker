# scheduler.py
# Script di esecuzione automatica giornaliera.
# Viene lanciato dal Task Scheduler di Windows ogni mattina.

import logging
import os
from datetime import datetime

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(
            f"logs/fintracker_{datetime.now().strftime('%Y%m%d')}.log",
            encoding="utf-8"
        ),
        logging.StreamHandler()
    ]
)

log = logging.getLogger(__name__)


def esegui(nome, funzione):
    log.info(f"▶ Avvio: {nome}")
    try:
        funzione()
        log.info(f"✅ Completato: {nome}")
    except Exception as e:
        log.error(f"❌ Errore in {nome}: {e}", exc_info=True)


def routine_mattutina():
    log.info("=" * 50)
    log.info("🤖 FinTracker — Routine mattutina")
    log.info(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    log.info("=" * 50)

    from database.migrations import esegui_migrazioni
    from modules.market_data import aggiorna_prezzi
    from modules.news import aggiorna_notizie
    from modules.indicators import analizza_watchlist
    from modules.telegram_bot import invia_riepilogo

    esegui("Migrazioni database",      esegui_migrazioni)
    esegui("Aggiornamento prezzi",      aggiorna_prezzi)
    esegui("Aggiornamento notizie",     aggiorna_notizie)
    esegui("Analisi tecnica",           analizza_watchlist)
    esegui("Invio riepilogo Telegram",  invia_riepilogo)

    log.info("=" * 50)
    log.info("🏁 Routine mattutina completata")
    log.info("=" * 50)


if __name__ == "__main__":
    routine_mattutina()