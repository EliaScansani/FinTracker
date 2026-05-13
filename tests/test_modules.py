# tests/test_modules.py
# Testa la logica di business dei moduli principali.
# Usa mock per simulare Yahoo Finance, NewsAPI e il database —
# i test girano senza connessioni esterne.

import pytest
from unittest.mock import patch, MagicMock


# ─────────────────────────────────────────────
# TEST MARKET DATA
# ─────────────────────────────────────────────

class TestMarketData:

    @patch("modules.market_data.salva_prezzo")
    @patch("modules.market_data.get_watchlist")
    @patch("modules.market_data.yf.Ticker")
    def test_aggiorna_prezzi_successo(self, mock_yf, mock_watchlist, mock_salva):
        """
        Con un ticker valido in watchlist aggiorna_prezzi deve
        scaricare i dati e chiamare salva_prezzo una volta.
        """
        # Simula watchlist con un ticker
        mock_watchlist.return_value = [
            {"ticker": "AAPL", "nome": "Apple Inc."}
        ]

        # Simula Yahoo Finance che risponde con dati validi
        mock_yf.return_value.info = {
            "currentPrice":              182.5,
            "regularMarketChangePercent": 1.25,
            "regularMarketVolume":        50000000,
            "fiftyTwoWeekHigh":           198.0,
            "fiftyTwoWeekLow":            155.0
        }

        from modules.market_data import aggiorna_prezzi
        aggiorna_prezzi()

        # salva_prezzo deve essere stato chiamato esattamente una volta
        mock_salva.assert_called_once_with(
            "AAPL", 182.5, 1.25, 50000000, 198.0, 155.0
        )


    @patch("modules.market_data.salva_prezzo")
    @patch("modules.market_data.get_watchlist")
    def test_aggiorna_prezzi_watchlist_vuota(self, mock_watchlist, mock_salva):
        """
        Con watchlist vuota aggiorna_prezzi non deve
        chiamare salva_prezzo né sollevare errori.
        """
        mock_watchlist.return_value = []

        from modules.market_data import aggiorna_prezzi
        aggiorna_prezzi()

        mock_salva.assert_not_called()


    @patch("modules.market_data.salva_prezzo")
    @patch("modules.market_data.get_watchlist")
    @patch("modules.market_data.yf.Ticker")
    def test_aggiorna_prezzi_nessun_prezzo(self, mock_yf, mock_watchlist, mock_salva):
        """
        Se Yahoo Finance non restituisce un prezzo (ticker delisted
        o dati non disponibili) aggiorna_prezzi deve saltare il ticker
        senza salvare nulla e senza sollevare errori.
        """
        mock_watchlist.return_value = [
            {"ticker": "INVALID", "nome": ""}
        ]

        # Info vuota — nessun prezzo disponibile
        mock_yf.return_value.info = {}

        from modules.market_data import aggiorna_prezzi
        aggiorna_prezzi()

        mock_salva.assert_not_called()


    @patch("modules.market_data.salva_prezzo")
    @patch("modules.market_data.get_watchlist")
    @patch("modules.market_data.yf.Ticker")
    def test_aggiorna_prezzi_errore_api(self, mock_yf, mock_watchlist, mock_salva):
        """
        Se Yahoo Finance solleva un'eccezione (rete assente,
        rate limit ecc.) aggiorna_prezzi deve continuare
        con i ticker successivi senza crashare.
        """
        mock_watchlist.return_value = [
            {"ticker": "AAPL", "nome": "Apple Inc."},
            {"ticker": "TSLA", "nome": "Tesla Inc."}
        ]

        # Il primo ticker solleva un errore, il secondo funziona
        mock_yf.side_effect = [
            Exception("Connection error"),
            MagicMock(info={
                "currentPrice": 250.0,
                "regularMarketChangePercent": -0.5,
                "regularMarketVolume": 30000000,
                "fiftyTwoWeekHigh": 300.0,
                "fiftyTwoWeekLow": 150.0
            })
        ]

        from modules.market_data import aggiorna_prezzi
        aggiorna_prezzi()

        # Solo TSLA deve essere stato salvato
        mock_salva.assert_called_once()
        assert mock_salva.call_args[0][0] == "TSLA"


# ─────────────────────────────────────────────
# TEST NEWS — FILTRO PERTINENZA
# ─────────────────────────────────────────────

class TestNewsRelevance:
    """
    Testa la funzione _e_rilevante che filtra le notizie
    non pertinenti prima di salvarle nel database.
    Questi test non richiedono mock — lavorano solo su stringhe.
    """

    def test_articolo_rilevante_per_nome(self):
        """
        Un articolo che menziona il nome dell'azienda
        nel titolo deve essere considerato rilevante.
        """
        from modules.news import _e_rilevante
        assert _e_rilevante(
            "Apple reports record quarterly earnings",
            "The tech giant Apple surpassed analyst expectations",
            "AAPL",
            "Apple Inc."
        ) == True


    def test_articolo_rilevante_per_ticker(self):
        """
        Un articolo che menziona il ticker nel titolo
        deve essere considerato rilevante.
        """
        from modules.news import _e_rilevante
        assert _e_rilevante(
            "TSLA stock surges after earnings beat",
            "Tesla shares rose sharply following better than expected results",
            "TSLA",
            "Tesla Inc."
        ) == True


    def test_articolo_non_rilevante(self):
        """
        Un articolo che non menziona né il ticker né il nome
        dell'azienda deve essere scartato.
        """
        from modules.news import _e_rilevante
        assert _e_rilevante(
            "Fed raises interest rates by 25 basis points",
            "The Federal Reserve announced a rate hike today",
            "AAPL",
            "Apple Inc."
        ) == False


    def test_articolo_rilevante_crypto(self):
        """
        Per i ticker crypto come BTC-USD la funzione deve
        riconoscere termini come 'bitcoin' e 'btc'.
        """
        from modules.news import _e_rilevante
        assert _e_rilevante(
            "Bitcoin hits new all-time high above $70,000",
            "The cryptocurrency market surged as BTC broke records",
            "BTC-USD",
            "Bitcoin USD"
        ) == True


    def test_articolo_rilevante_gold_futures(self):
        """
        Per i futures come GC=F la funzione deve
        riconoscere termini come 'gold'.
        """
        from modules.news import _e_rilevante
        assert _e_rilevante(
            "Gold prices rise amid inflation fears",
            "Investors flock to safe haven assets as gold climbs",
            "GC=F",
            ""
        ) == True


# ─────────────────────────────────────────────
# TEST NEWS — COSTRUZIONE QUERY
# ─────────────────────────────────────────────

class TestNewsQuery:

    def test_query_ticker_speciale(self):
        """
        Per ticker con caratteri speciali come GC=F
        la funzione deve usare parole chiave predefinite
        invece del ticker grezzo.
        """
        from modules.news import _costruisci_query
        query = _costruisci_query("GC=F", "Gold Futures")
        assert query == "gold price futures"


    def test_query_ticker_normale_con_nome(self):
        """
        Per un ticker normale con nome azienda disponibile
        la query deve usare le prime due parole del nome.
        """
        from modules.news import _costruisci_query
        query = _costruisci_query("AAPL", "Apple Inc.")
        assert query == "Apple Inc."


    def test_query_ticker_senza_nome(self):
        """
        Senza nome azienda la query deve usare
        il ticker tra virgolette per una ricerca esatta.
        """
        from modules.news import _costruisci_query
        query = _costruisci_query("XYZ", "")
        assert '"XYZ"' in query


# ─────────────────────────────────────────────
# TEST NEWS — AGGIORNAMENTO COMPLETO
# ─────────────────────────────────────────────

class TestAggiornaNews:

    @patch("modules.news.salva_notizia")
    @patch("modules.news.get_watchlist")
    @patch("modules.news.requests.get")
    def test_aggiorna_notizie_successo(self, mock_req, mock_watchlist, mock_salva):
        """
        Con una notizia rilevante restituita da NewsAPI
        aggiorna_notizie deve salvarla nel database.
        """
        mock_watchlist.return_value = [
            {"ticker": "AAPL", "nome": "Apple Inc."}
        ]

        # Simula risposta NewsAPI con un articolo rilevante
        mock_req.return_value.json.return_value = {
            "status": "ok",
            "articles": [{
                "title":       "Apple launches new MacBook Pro",
                "description": "Apple Inc announced a new MacBook",
                "source":      {"name": "TechCrunch"},
                "url":         "https://techcrunch.com/123",
                "publishedAt": "2024-01-15T10:00:00Z"
            }]
        }
        mock_salva.return_value = True

        from modules.news import aggiorna_notizie
        aggiorna_notizie()

        mock_salva.assert_called_once()


    @patch("modules.news.salva_notizia")
    @patch("modules.news.get_watchlist")
    @patch("modules.news.requests.get")
    def test_aggiorna_notizie_filtra_non_rilevanti(self, mock_req, mock_watchlist, mock_salva):
        """
        Gli articoli non rilevanti per il ticker
        non devono essere salvati nel database.
        """
        mock_watchlist.return_value = [
            {"ticker": "AAPL", "nome": "Apple Inc."}
        ]

        # Articolo che non menziona Apple
        mock_req.return_value.json.return_value = {
            "status": "ok",
            "articles": [{
                "title":       "Fed raises interest rates",
                "description": "The Federal Reserve announced a rate hike",
                "source":      {"name": "Reuters"},
                "url":         "https://reuters.com/456",
                "publishedAt": "2024-01-15T10:00:00Z"
            }]
        }

        from modules.news import aggiorna_notizie
        aggiorna_notizie()

        # L'articolo non rilevante non deve essere salvato
        mock_salva.assert_not_called()


    @patch("modules.news.salva_notizia")
    @patch("modules.news.get_watchlist")
    def test_aggiorna_notizie_api_key_mancante(self, mock_watchlist, mock_salva):
        """
        Senza API key aggiorna_notizie deve terminare
        immediatamente senza chiamare NewsAPI né salvare nulla.
        """
        mock_watchlist.return_value = [
            {"ticker": "AAPL", "nome": "Apple Inc."}
        ]

        # Sovrascrive temporaneamente la NEWS_API_KEY con stringa vuota
        with patch("modules.news.NEWS_API_KEY", ""):
            from modules.news import aggiorna_notizie
            aggiorna_notizie()

        mock_salva.assert_not_called()