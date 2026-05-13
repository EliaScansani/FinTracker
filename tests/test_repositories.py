# tests/test_repositories.py
# Testa le operazioni sui repository del database.
# Usa unittest.mock per simulare la connessione PostgreSQL —
# i test non toccano il database reale e girano senza connessione attiva.

import pytest
from unittest.mock import patch, MagicMock


# ─────────────────────────────────────────────
# TEST WATCHLIST
# ─────────────────────────────────────────────

class TestWatchlistRepository:

    @patch("database.repositories.watchlist.get_connection")
    def test_get_watchlist_vuota(self, mock_conn):
        """
        Se il database è vuoto get_watchlist deve restituire
        una lista vuota senza sollevare errori.
        """
        # Configura il mock per simulare un database vuoto
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.return_value.cursor.return_value = mock_cursor

        from database.repositories.watchlist import get_watchlist
        risultato = get_watchlist()

        assert risultato == []
        mock_cursor.execute.assert_called_once()  # Verifica che la query sia stata eseguita


    @patch("database.repositories.watchlist.get_connection")
    def test_get_watchlist_con_dati(self, mock_conn):
        """
        Con dati presenti get_watchlist deve restituire
        una lista di dizionari con i campi corretti.
        """
        # Simula una riga del database
        mock_riga = MagicMock()
        mock_riga.keys.return_value = ["ticker", "nome", "data_aggiunta", "note"]
        mock_riga.__iter__ = lambda self: iter(["AAPL", "Apple Inc.", "2024-01-01", ""])

        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"ticker": "AAPL", "nome": "Apple Inc.", "data_aggiunta": "2024-01-01", "note": ""}
        ]
        mock_conn.return_value.cursor.return_value = mock_cursor

        from database.repositories.watchlist import get_watchlist
        risultato = get_watchlist()

        assert len(risultato) == 1
        assert risultato[0]["ticker"] == "AAPL"
        assert risultato[0]["nome"] == "Apple Inc."


    @patch("database.repositories.watchlist.get_connection")
    @patch("database.repositories.watchlist.yf.Ticker")
    def test_aggiungi_ticker_valido(self, mock_yf, mock_conn):
        """
        Con un ticker valido (Yahoo Finance risponde correttamente)
        aggiungi_ticker deve salvarlo nel database e restituire True.
        """
        # Simula Yahoo Finance che trova il ticker
        mock_yf.return_value.info = {
            "currentPrice": 182.5,
            "symbol":       "AAPL",
            "longName":     "Apple Inc."
        }

        # Simula il database che accetta l'inserimento
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1   # 1 riga inserita = successo
        mock_conn.return_value.cursor.return_value = mock_cursor

        from database.repositories.watchlist import aggiungi_ticker
        risultato = aggiungi_ticker("AAPL")

        assert risultato == True
        mock_cursor.execute.assert_called_once()


    @patch("database.repositories.watchlist.get_connection")
    @patch("database.repositories.watchlist.yf.Ticker")
    def test_aggiungi_ticker_non_esistente(self, mock_yf, mock_conn):
        """
        Con un ticker inesistente Yahoo Finance restituisce
        un dizionario vuoto — aggiungi_ticker deve restituire False
        senza salvare nulla nel database.
        """
        # Simula Yahoo Finance che non trova il ticker
        mock_yf.return_value.info = {}

        from database.repositories.watchlist import aggiungi_ticker
        risultato = aggiungi_ticker("XXXXINVALID")

        assert risultato == False
        # Il database non deve essere stato toccato
        mock_conn.assert_not_called()


    @patch("database.repositories.watchlist.get_connection")
    @patch("database.repositories.watchlist.yf.Ticker")
    def test_aggiungi_ticker_duplicato(self, mock_yf, mock_conn):
        """
        Se il ticker è già presente nel database (rowcount = 0
        per via di ON CONFLICT DO NOTHING) aggiungi_ticker
        deve restituire False.
        """
        mock_yf.return_value.info = {
            "currentPrice": 182.5,
            "symbol":       "AAPL",
            "longName":     "Apple Inc."
        }

        # rowcount = 0 significa che ON CONFLICT ha bloccato l'inserimento
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_conn.return_value.cursor.return_value = mock_cursor

        from database.repositories.watchlist import aggiungi_ticker
        risultato = aggiungi_ticker("AAPL")

        assert risultato == False


    @patch("database.repositories.watchlist.get_connection")
    def test_rimuovi_ticker(self, mock_conn):
        """
        rimuovi_ticker deve eseguire DELETE su tutte e quattro
        le tabelle collegate — prezzi, notizie, segnali e watchlist.
        """
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor

        from database.repositories.watchlist import rimuovi_ticker
        rimuovi_ticker("AAPL")

        # Deve essere stato chiamato 4 volte — una DELETE per tabella
        assert mock_cursor.execute.call_count == 4
        mock_conn.return_value.commit.assert_called_once()


# ─────────────────────────────────────────────
# TEST PREZZI
# ─────────────────────────────────────────────

class TestPrezziRepository:

    @patch("database.repositories.prezzi.get_connection")
    def test_salva_prezzo(self, mock_conn):
        """
        salva_prezzo deve eseguire una INSERT con i valori corretti
        e fare commit sul database.
        """
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor

        from database.repositories.prezzi import salva_prezzo
        salva_prezzo("AAPL", 182.5, 1.25, 50000000, 198.0, 155.0)

        mock_cursor.execute.assert_called_once()
        mock_conn.return_value.commit.assert_called_once()

        # Verifica che i valori corretti siano stati passati alla query
        args = mock_cursor.execute.call_args[0][1]
        assert args[0] == "AAPL"
        assert args[1] == 182.5
        assert args[2] == 1.25


    @patch("database.repositories.prezzi.get_connection")
    def test_get_ultimi_prezzi_vuoto(self, mock_conn):
        """
        Con database vuoto get_ultimi_prezzi deve restituire
        una lista vuota.
        """
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.return_value.cursor.return_value = mock_cursor

        from database.repositories.prezzi import get_ultimi_prezzi
        risultato = get_ultimi_prezzi()

        assert risultato == []


# ─────────────────────────────────────────────
# TEST NOTIZIE
# ─────────────────────────────────────────────

class TestNotizieRepository:

    @patch("database.repositories.notizie.get_connection")
    def test_salva_notizia_nuova(self, mock_conn):
        """
        Una notizia con URL nuovo deve essere salvata
        e la funzione deve restituire True.
        """
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1   # 1 riga inserita
        mock_conn.return_value.cursor.return_value = mock_cursor

        from database.repositories.notizie import salva_notizia
        risultato = salva_notizia(
            "AAPL",
            "Apple announces new iPhone",
            "Reuters",
            "https://reuters.com/article/123",
            "2024-01-15T10:00:00Z"
        )

        assert risultato == True
        mock_cursor.execute.assert_called_once()


    @patch("database.repositories.notizie.get_connection")
    def test_salva_notizia_duplicata(self, mock_conn):
        """
        Una notizia con URL già presente (ON CONFLICT DO NOTHING)
        deve restituire False senza errori.
        """
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0   # 0 righe inserite = duplicato
        mock_conn.return_value.cursor.return_value = mock_cursor

        from database.repositories.notizie import salva_notizia
        risultato = salva_notizia(
            "AAPL",
            "Apple announces new iPhone",
            "Reuters",
            "https://reuters.com/article/123",
            "2024-01-15T10:00:00Z"
        )

        assert risultato == False


    @patch("database.repositories.notizie.get_connection")
    def test_get_notizie_filtro_oggi(self, mock_conn):
        """
        Con solo_oggi=True la query deve includere
        il filtro CURRENT_DATE.
        """
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.return_value.cursor.return_value = mock_cursor

        from database.repositories.notizie import get_notizie
        get_notizie(solo_oggi=True)

        query_eseguita = mock_cursor.execute.call_args[0][0]
        assert "CURRENT_DATE" in query_eseguita


    @patch("database.repositories.notizie.get_connection")
    def test_get_notizie_filtro_storico(self, mock_conn):
        """
        Con solo_oggi=False la query deve includere
        il filtro INTERVAL per gli ultimi 7 giorni.
        """
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.return_value.cursor.return_value = mock_cursor

        from database.repositories.notizie import get_notizie
        get_notizie(solo_oggi=False)

        query_eseguita = mock_cursor.execute.call_args[0][0]
        assert "INTERVAL" in query_eseguita


# ─────────────────────────────────────────────
# TEST SEGNALI
# ─────────────────────────────────────────────

class TestSegnaliRepository:

    @patch("database.repositories.segnali.get_connection")
    def test_salva_segnale(self, mock_conn):
        """
        salva_segnale deve eseguire una INSERT con
        ticker, indicatore, valore, segnale e importanza corretti.
        """
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor

        from database.repositories.segnali import salva_segnale
        salva_segnale("AAPL", "RSI", 75.5, "IPERCOMPRATO", "ALTA")

        mock_cursor.execute.assert_called_once()
        args = mock_cursor.execute.call_args[0][1]
        assert args[0] == "AAPL"
        assert args[1] == "RSI"
        assert args[4] == "ALTA"


    @patch("database.repositories.segnali.get_connection")
    def test_get_segnali_solo_oggi(self, mock_conn):
        """
        Con solo_oggi=True la query deve filtrare
        per CURRENT_DATE.
        """
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.return_value.cursor.return_value = mock_cursor

        from database.repositories.segnali import get_segnali
        get_segnali(solo_oggi=True)

        query_eseguita = mock_cursor.execute.call_args[0][0]
        assert "CURRENT_DATE" in query_eseguita


    @patch("database.repositories.segnali.get_connection")
    def test_get_segnali_solo_importanti(self, mock_conn):
        """
        Con solo_importanti=True la query deve includere
        il filtro per importanza ALTA.
        """
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.return_value.cursor.return_value = mock_cursor

        from database.repositories.segnali import get_segnali
        get_segnali(solo_importanti=True)

        query_eseguita = mock_cursor.execute.call_args[0][0]
        assert "ALTA" in query_eseguita