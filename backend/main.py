# backend/main.py
# Entry point dell'applicazione FastAPI.
# Registra tutte le route e configura CORS per permettere
# al frontend HTML/JS di comunicare con il backend.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from database.migrations import esegui_migrazioni

from backend.routes.watchlist import router as watchlist_router
from backend.routes.prezzi import router as prezzi_router
from backend.routes.notizie import router as notizie_router
from backend.routes.segnali import router as segnali_router
from backend.routes.storico import router as storico_router
from backend.routes.telegram import router as telegram_router

# ─────────────────────────────────────────────
# LIFESPAN
# ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inizializza il database all'avvio del server."""
    print("🚀 FinTracker Backend in avvio...")
    esegui_migrazioni()
    print("✅ Database pronto.")
    yield
    print("👋 Server spento.")


# ─────────────────────────────────────────────
# CREAZIONE APP
# ─────────────────────────────────────────────

app = FastAPI(
    title="FinTracker API",
    version="2.1.0",
    lifespan=lifespan
)

# CORS — permette al frontend (aperto nel browser) di chiamare le API
# In sviluppo locale permettiamo tutto, in produzione va ristretto al dominio
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"]
)


# ─────────────────────────────────────────────
# REGISTRAZIONE ROUTE
# ─────────────────────────────────────────────

app.include_router(watchlist_router, prefix="/api/watchlist", tags=["Watchlist"])
app.include_router(prezzi_router,    prefix="/api/prezzi",    tags=["Prezzi"])
app.include_router(notizie_router,   prefix="/api/notizie",   tags=["Notizie"])
app.include_router(segnali_router,   prefix="/api/segnali",   tags=["Segnali"])
app.include_router(storico_router,   prefix="/api/storico",   tags=["Storico"])
app.include_router(telegram_router,  prefix="/api/telegram",  tags=["Telegram"])

# ─────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────

@app.get("/api/health")
async def health():
    """Verifica che il server sia attivo."""
    return {"status": "ok", "version": "2.1.0"}


# ─────────────────────────────────────────────
# SERVE FRONTEND STATICO
# ─────────────────────────────────────────────

# Serve i file HTML/CSS/JS dalla cartella frontend/
# Così un solo server gestisce sia le API che il frontend
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


