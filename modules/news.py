# modules/news.py
# Questo modulo si occupa di recuperare notizie finanziarie aggiornate
# per ogni ticker presente nella watchlist, utilizzando NewsAPI.
# Le notizie vengono sia stampate nel terminale che salvate nel database
# per poterle consultare in seguito.

import requests
from database.connection import get_connection 
from database.repositories import get_watchlist, salva_notizia  # Funzioni per interagire con il database
from config import NEWS_API_KEY                          # Chiave API caricata dal file .env

# ─────────────────────────────────────────────
# COSTANTI DI CONFIGURAZIONE
# ─────────────────────────────────────────────

# URL base delle API di NewsAPI — tutti i parametri vengono aggiunti dopo
NEWS_API_URL = "https://newsapi.org/v2/everything"

# Numero massimo di notizie da recuperare per ogni ticker
MAX_NOTIZIE = 5


# ─────────────────────────────────────────────
# SETUP DATABASE: aggiunge la tabella notizie
# ─────────────────────────────────────────────

def inizializza_tabella_notizie():
    """
    Crea la tabella 'notizie' nel database se non esiste già.
    Viene chiamata all'avvio del programma insieme a inizializza_db().
    Separata da database.py per mantenere ogni modulo indipendente.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notizie (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            titolo TEXT,
            fonte TEXT,
            url TEXT,
            pubblicata_il TEXT,
            salvata_il TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# FUNZIONE PRINCIPALE: scarica e salva notizie
# ─────────────────────────────────────────────

def aggiorna_notizie():
    """
    Per ogni ticker in watchlist cerca notizie pertinenti su NewsAPI
    e le salva nel database tramite il repository.
    """
    if not NEWS_API_KEY:
        print("⚠️  NEWS_API_KEY mancante nel file .env")
        return

    watchlist = get_watchlist()
    if not watchlist:
        print("📭 La watchlist è vuota.")
        return

    for riga in watchlist:
        ticker = riga["ticker"]
        nome   = riga["nome"]
        query  = _costruisci_query(ticker, nome)

        print(f"📰 Cercando notizie per {ticker} (query: '{query}')...")

        try:
            risposta = requests.get(NEWS_API_URL, params={
                "q":        query,
                "language": "en",
                "sortBy":   "publishedAt",
                "pageSize": MAX_NOTIZIE,
                "apiKey":   NEWS_API_KEY
            })

            dati = risposta.json()
            if dati.get("status") != "ok":
                print(f"  ⚠️  Errore API: {dati.get('message')}")
                continue

            salvati = 0
            for articolo in dati.get("articles", []):
                titolo     = articolo.get("title", "")      or ""
                descrizione= articolo.get("description", "") or ""
                fonte      = articolo.get("source", {}).get("name", "")
                url        = articolo.get("url", "")
                pubblicata = articolo.get("publishedAt", "")

                if not _e_rilevante(titolo, descrizione, ticker, nome):
                    continue

                if salva_notizia(ticker, titolo, fonte, url, pubblicata):
                    salvati += 1
                    print(f"  📌 {titolo[:70]}...")

            if salvati == 0:
                print(f"  📭 Nessuna notizia rilevante per {ticker}.")
            else:
                print(f"  ✅ {salvati} notizie salvate per {ticker}.")

        except Exception as e:
            print(f"  ⚠️  Errore per {ticker}: {e}")

    print("\n✅ Aggiornamento notizie completato.")


def _costruisci_query(ticker, nome):
    """
    Costruisce una query di ricerca specifica per il ticker.
    Gestisce casi particolari come futures e indici che hanno
    ticker con caratteri speciali (GC=F, CL=F, ^GSPC ecc.)
    """
    # Dizionario di parole chiave per ticker speciali comuni
    ticker_speciali = {
        "GC=F":  "gold price futures",
        "CL=F":  "crude oil price futures",
        "SI=F":  "silver price futures",
        "ES=F":  "S&P 500 futures",
        "NQ=F":  "Nasdaq futures",
        "BTC-USD": "Bitcoin price",
        "ETH-USD": "Ethereum price",
        "^GSPC": "S&P 500 index",
        "^DJI":  "Dow Jones index",
        "^IXIC": "Nasdaq composite",
    }

    if ticker in ticker_speciali:
        return ticker_speciali[ticker]

    # Per ticker normali usa il nome azienda se disponibile
    # altrimenti usa il ticker stesso tra virgolette per ricerca esatta
    if nome and len(nome) > 2:
        # Prende le prime due parole del nome — più specifico
        parole = nome.split()[:2]
        return " ".join(parole)

    return f'"{ticker}"'


def _e_rilevante(titolo, descrizione, ticker, nome):
    """
    Verifica che un articolo sia effettivamente rilevante per il ticker.
    Controlla che almeno uno dei termini chiave compaia nel titolo
    o nella descrizione — evita articoli generici non pertinenti.
    Restituisce True se l'articolo è rilevante, False altrimenti.
    """
    testo = (titolo + " " + descrizione).lower()

    # Termini rilevanti per questo ticker
    termini = []

    # Aggiunge il ticker pulito (senza caratteri speciali)
    ticker_pulito = ticker.replace("=F", "").replace("-USD", "").replace("^", "")
    if len(ticker_pulito) > 1:
        termini.append(ticker_pulito.lower())

    # Aggiunge le parole del nome azienda (almeno 4 caratteri)
    if nome:
        for parola in nome.split():
            if len(parola) >= 4:
                termini.append(parola.lower())

    # Termini speciali per ticker di futures/indici
    termini_speciali = {
        "GC=F":    ["gold", "oro"],
        "CL=F":    ["oil", "crude", "petrolio"],
        "SI=F":    ["silver", "argento"],
        "BTC-USD": ["bitcoin", "btc", "crypto"],
        "ETH-USD": ["ethereum", "eth", "crypto"],
        "^GSPC":   ["s&p", "s&p 500", "sp500"],
        "^DJI":    ["dow jones", "djia"],
        "^IXIC":   ["nasdaq"],
        "DRS":     ["Leonardo DRS", "Leonardo", "DRS"],
    }

    if ticker in termini_speciali:
        termini.extend(termini_speciali[ticker])

    # Basta che almeno un termine sia presente nel testo
    return any(termine in testo for termine in termini)
