# modules/telegram_bot.py
# Gestisce l'invio del riepilogo giornaliero via Telegram.
# Legge i dati dal database tramite i repository —
# nessuna query SQL diretta in questo modulo.

import requests
from datetime import datetime
from database.repositories import (
    get_watchlist, get_ultimi_prezzi,
    get_notizie_recenti_per_telegram,
    get_segnali_importanti_oggi
)
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, VARIAZIONE_SOGLIA


def invia_messaggio(testo: str) -> bool:
    """Invia un messaggio al bot Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Credenziali Telegram mancanti nel .env")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        risposta = requests.post(url, data={
            "chat_id":    TELEGRAM_CHAT_ID,
            "text":       testo,
            "parse_mode": "HTML"
        })
        dati = risposta.json()
        if dati.get("ok"):
            print("✅ Messaggio Telegram inviato.")
            return True
        print(f"⚠️  Errore Telegram: {dati.get('description')}")
        return False
    except Exception as e:
        print(f"⚠️  Errore invio: {e}")
        return False


def invia_riepilogo():
    """Assembla e invia il riepilogo completo su Telegram."""
    print("📤 Preparazione riepilogo Telegram...")

    ora = datetime.now().strftime("%d/%m/%Y %H:%M")
    messaggio  = f"🤖 <b>FinTracker — Riepilogo</b>\n"
    messaggio += f"📅 {ora}\n\n"
    messaggio += _blocco_prezzi()
    messaggio += _blocco_segnali()
    messaggio += _blocco_notizie()
    messaggio += "\n─────────────────────\n"
    messaggio += "⚡ <i>Generato da FinTracker</i>"

    invia_messaggio(messaggio)


def _blocco_prezzi() -> str:
    prezzi = get_ultimi_prezzi()
    if not prezzi:
        return "📭 Nessun dato prezzi disponibile.\n"

    testo  = "📊 <b>ANDAMENTO TITOLI</b>\n"
    testo += "─────────────────────\n"

    for p in prezzi:
        var = p.get("variazione_pct")
        freccia = "🟢" if var and var > 0 else "🔴" if var and var < 0 else "⚪"
        var_str = f"{round(var, 2)}%" if var else "N/D"

        testo += f"{freccia} <b>{p['ticker']}</b>: ${p['prezzo']} ({var_str})\n"
        testo += f"   📈 Max 52w: ${p['max_52w']} | Min 52w: ${p['min_52w']}\n"

        if var and abs(var) >= VARIAZIONE_SOGLIA:
            testo += f"   ⚠️  <b>Variazione significativa!</b>\n"

    return testo


def _blocco_segnali() -> str:
    segnali = get_segnali_importanti_oggi()
    if not segnali:
        return ""

    testo  = "\n🔔 <b>SEGNALI IMPORTANTI</b>\n"
    testo += "─────────────────────\n"
    for s in segnali:
        testo += f"  🔴 <b>{s['ticker']}</b> — {s['indicatore']}: {s['segnale']}\n"
    return testo


def _blocco_notizie() -> str:
    watchlist = get_watchlist()
    if not watchlist:
        return ""

    testo  = "\n📰 <b>ULTIME NOTIZIE</b>\n"
    testo += "─────────────────────\n"
    ha_notizie = False

    for riga in watchlist:
        ticker  = riga["ticker"]
        notizie = get_notizie_recenti_per_telegram(ticker)
        if not notizie:
            continue

        ha_notizie = True
        link_yahoo = f"https://finance.yahoo.com/quote/{ticker}/news"
        testo += f"\n<b>{ticker}</b> — <a href='{link_yahoo}'>Notizie Yahoo Finance</a>\n"
        
        for n in notizie:
            titolo = n["titolo"][:60] + "..." if len(n["titolo"]) > 60 else n["titolo"]
            testo += f"  • <a href='{n['url']}'>{titolo}</a>\n"
            testo += f"    {n['fonte']}\n"

    return testo if ha_notizie else ""