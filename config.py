# config.py
# Configurazione centrale di FinTracker
# Modifica qui le impostazioni senza toccare il resto del codice

import os
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# --- Percorsi ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "fintracker.db")

# --- Telegram (da compilare in .env) ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# --- News API (da compilare in .env) ---
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

# --- Impostazioni di monitoraggio ---
VARIAZIONE_SOGLIA = 3.0  # Notifica se un titolo varia più del 3%

