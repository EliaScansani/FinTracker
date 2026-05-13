# main.py
# Script di utilità da terminale per FinTracker.
# Permette di eseguire operazioni manualmente senza aprire il browser.
# Utile per debug e manutenzione.

import argparse
from database.migrations import esegui_migrazioni
from modules.market_data import aggiorna_prezzi
from modules.news import aggiorna_notizie
from modules.indicators import analizza_watchlist
from modules.telegram_bot import invia_riepilogo
from database.repositories import (
    get_watchlist, aggiungi_ticker,
    rimuovi_ticker, get_ultimi_prezzi,
    get_notizie, get_segnali
)


def cmd_watchlist():
    """Mostra i ticker in watchlist."""
    righe = get_watchlist()
    if not righe:
        print("📭 Watchlist vuota.")
        return
    print(f"\n{'TICKER':<10} {'NOME':<30} {'AGGIUNTO IL':<15}")
    print("-" * 55)
    for r in righe:
        print(f"{r['ticker']:<10} {r['nome'] or '':<30} {str(r['data_aggiunta']):<15}")


def cmd_aggiungi(ticker, note=""):
    """Aggiunge un ticker alla watchlist."""
    aggiungi_ticker(ticker, note=note)


def cmd_rimuovi(ticker):
    """Rimuove un ticker dalla watchlist."""
    rimuovi_ticker(ticker)


def cmd_prezzi():
    """Mostra gli ultimi prezzi salvati."""
    prezzi = get_ultimi_prezzi()
    if not prezzi:
        print("📭 Nessun prezzo. Esegui: python main.py --aggiorna-prezzi")
        return
    print(f"\n{'TICKER':<8} {'PREZZO':>10} {'VAR%':>8} {'VOLUME':>12}")
    print("-" * 42)
    for p in prezzi:
        var = f"{round(p['variazione_pct'], 2)}%" if p['variazione_pct'] else "N/D"
        print(f"{p['ticker']:<8} ${str(p['prezzo']):>9} {var:>8} {str(p['volume'] or ''):>12}")


def main():
    parser = argparse.ArgumentParser(description="FinTracker CLI")

    parser.add_argument("--migra",           action="store_true", help="Esegui migrazioni database")
    parser.add_argument("--watchlist",        action="store_true", help="Mostra watchlist")
    parser.add_argument("--aggiungi",         metavar="TICKER",    help="Aggiungi ticker")
    parser.add_argument("--rimuovi",          metavar="TICKER",    help="Rimuovi ticker")
    parser.add_argument("--prezzi",           action="store_true", help="Mostra ultimi prezzi")
    parser.add_argument("--aggiorna-prezzi",  action="store_true", help="Aggiorna prezzi da Yahoo Finance")
    parser.add_argument("--aggiorna-notizie", action="store_true", help="Aggiorna notizie da NewsAPI")
    parser.add_argument("--analisi",          action="store_true", help="Esegui analisi tecnica")
    parser.add_argument("--telegram",         action="store_true", help="Invia riepilogo Telegram")
    parser.add_argument("--note",             metavar="NOTE",      help="Note per --aggiungi", default="")

    args = parser.parse_args()

    if args.migra:           esegui_migrazioni()
    elif args.watchlist:     cmd_watchlist()
    elif args.aggiungi:      cmd_aggiungi(args.aggiungi, args.note)
    elif args.rimuovi:       cmd_rimuovi(args.rimuovi)
    elif args.prezzi:        cmd_prezzi()
    elif args.aggiorna_prezzi:  aggiorna_prezzi()
    elif args.aggiorna_notizie: aggiorna_notizie()
    elif args.analisi:       analizza_watchlist()
    elif args.telegram:      invia_riepilogo()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()