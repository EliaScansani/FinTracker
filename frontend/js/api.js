// frontend/js/api.js
// Modulo centralizzato per tutte le chiamate API al backend FastAPI.
// Ogni funzione corrisponde a un endpoint e restituisce sempre
// una Promise — il chiamante decide come gestire i dati.

const BASE_URL = "http://localhost:8000/api";

// ─────────────────────────────────────────────
// UTILITY
// ─────────────────────────────────────────────

/**
 * Wrapper attorno a fetch() che gestisce gli errori in modo uniforme.
 * Lancia un errore con il messaggio del backend se la risposta non è ok.
 */
async function request(path, options = {}) {
    const risposta = await fetch(`${BASE_URL}${path}`, {
        headers: { "Content-Type": "application/json" },
        ...options
    });

    if (!risposta.ok) {
        const errore = await risposta.json().catch(() => ({}));
        throw new Error(errore.detail || `Errore ${risposta.status}`);
    }

    return risposta.json();
}


// ─────────────────────────────────────────────
// WATCHLIST
// ─────────────────────────────────────────────

export const api = {

    watchlist: {
        /** Restituisce tutti i ticker in watchlist */
        get: () => request("/watchlist/"),

        /** Cerca ticker per nome o simbolo */
        cerca: (query) => request(`/watchlist/cerca/${encodeURIComponent(query)}`),

        /** Aggiunge un ticker alla watchlist */
        aggiungi: (ticker, note = "") => request(`/watchlist/${ticker}`, {
            method: "POST",
            body: JSON.stringify({ note })
        }),

        /** Rimuove un ticker dalla watchlist */
        rimuovi: (ticker) => request(`/watchlist/${ticker}`, {
            method: "DELETE"
        })
    },


    // ─────────────────────────────────────────
    // PREZZI
    // ─────────────────────────────────────────

    prezzi: {
        /** Ultimi prezzi salvati per ogni ticker */
        get: () => request("/prezzi/"),

        /** Forza aggiornamento prezzi da Yahoo Finance */
        aggiorna: () => request("/prezzi/aggiorna", { method: "POST" })
    },


    // ─────────────────────────────────────────
    // NOTIZIE
    // ─────────────────────────────────────────

    notizie: {
        /**
         * Legge le notizie dal database.
         * @param {string|null} ticker - filtra per ticker specifico
         * @param {boolean} soloOggi - true = solo oggi, false = 7 giorni
         */
        get: (ticker = null, soloOggi = true) => {
            const params = new URLSearchParams({ solo_oggi: soloOggi });
            if (ticker) params.append("ticker", ticker);
            return request(`/notizie/?${params}`);
        },

        /** Aggiorna le notizie da NewsAPI */
        aggiorna: () => request("/notizie/aggiorna", { method: "POST" })
    },


    // ─────────────────────────────────────────
    // SEGNALI
    // ─────────────────────────────────────────

    segnali: {
        /**
         * Legge i segnali tecnici.
         * @param {boolean} soloOggi - true = solo oggi, false = 30 giorni
         * @param {boolean} soloImportanti - true = solo importanza ALTA
         */
        get: (soloOggi = true, soloImportanti = false) => {
            const params = new URLSearchParams({
                solo_oggi: soloOggi,
                solo_importanti: soloImportanti
            });
            return request(`/segnali/?${params}`);
        },

        /** Avvia analisi tecnica completa */
        analisi: () => request("/segnali/analisi", { method: "POST" })
    },

    // ─────────────────────────────────────────
    // STORICO
    // ─────────────────────────────────────────

    storico: {
        /**
         * Dati storici OHLCV per i grafici.
         * @param {string} ticker - simbolo del titolo
         * @param {string} periodo - 1mo, 3mo, 6mo, 1y, 2y
         */
        get: (ticker, periodo = "6mo") => request(`/storico/${ticker}?periodo=${periodo}`)
    },

    // ─────────────────────────────────────────
    // TELEGRAM
    // ─────────────────────────────────────────
    telegram: {
        /** Invia il riepilogo giornaliero su Telegram */
        invia: () => request("/telegram/riepilogo", { method: "POST" })
    }


};