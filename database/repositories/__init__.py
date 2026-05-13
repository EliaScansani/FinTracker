# database/repositories/__init__.py
# Esporta tutte le funzioni dei repository in un unico punto.
# Gli altri moduli importeranno da qui invece che dai singoli file.
# Es: from database.repositories import get_watchlist, salva_prezzo

from database.repositories.watchlist import (
    get_watchlist, aggiungi_ticker, rimuovi_ticker, cerca_ticker
)
from database.repositories.prezzi import (
    salva_prezzo, get_ultimi_prezzi, get_storico_ticker
)
from database.repositories.notizie import (
    salva_notizia, get_notizie, get_notizie_recenti_per_telegram
)
from database.repositories.segnali import (
    salva_segnale, get_segnali, get_segnali_importanti_oggi
)