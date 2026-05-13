// frontend/js/dashboard.js
// Gestisce tutta la logica della dashboard:
// navigazione, rendering dati, grafici e interazioni utente.

import { api } from "./api.js";

// ─────────────────────────────────────────────
// STATO GLOBALE
// ─────────────────────────────────────────────

// Stato dell'applicazione — unica fonte di verità
const stato = {
    paginaCorrente: "dashboard",
    watchlist: [],
    prezzi: [],
    graficoCorrente: null,    // Istanza del grafico Lightweight Charts
    tickerSelezionato: null,
    cercaTimeout: null,        // Timeout per il debounce della ricerca

    indicatori: {
        sma20:     true,
        sma50:     true,
        bollinger: true,
        volume:    true,
        rsi:       true
    },

    serie: {
        sma20:        null,
        sma50:        null,
        bbUpper:      null,
        bbLower:      null
    }

};


// ─────────────────────────────────────────────
// UTILITY UI
// ─────────────────────────────────────────────

/**
 * Mostra un toast di notifica in basso a destra.
 * type: "success" | "error" | "info"
 */
function toast(messaggio, type = "success") {
    const container = document.getElementById("toast-container");
    const el = document.createElement("div");
    el.className = `toast toast-${type}`;
    el.innerHTML = `
        <span class="toast-icon">${type === "success" ? "✓" : type === "error" ? "✕" : "i"}</span>
        <span>${messaggio}</span>
    `;
    container.appendChild(el);
    // Animazione entrata
    requestAnimationFrame(() => el.classList.add("toast-show"));
    // Rimozione automatica dopo 3 secondi
    setTimeout(() => {
        el.classList.remove("toast-show");
        setTimeout(() => el.remove(), 300);
    }, 3000);
}

/**
 * Mostra uno stato di caricamento in un contenitore.
 */
function setLoading(id, loading) {
    const el = document.getElementById(id);
    if (!el) return;
    if (loading) {
        el.innerHTML = `
            <div class="loading">
                <div class="loading-bar"></div>
                <div class="loading-bar"></div>
                <div class="loading-bar"></div>
            </div>
        `;
    }
}

/**
 * Formatta un numero grande in formato leggibile.
 * Es: 1500000 → 1.5M
 */
function formatVolume(n) {
    if (!n) return "—";
    if (n >= 1e9) return (n / 1e9).toFixed(1) + "B";
    if (n >= 1e6) return (n / 1e6).toFixed(1) + "M";
    if (n >= 1e3) return (n / 1e3).toFixed(1) + "K";
    return n.toString();
}

/**
 * Restituisce la classe CSS in base alla variazione percentuale.
 */
function classVariazione(v) {
    if (!v) return "neutral";
    return v > 0 ? "positive" : "negative";
}


// ─────────────────────────────────────────────
// NAVIGAZIONE
// ─────────────────────────────────────────────
// Mappa dei titoli per ogni pagina
const titoli = {
    dashboard: "Dashboard",
    watchlist: "Watchlist",
    grafici:   "Grafici",
    notizie:   "Notizie",
    segnali:   "Segnali Tecnici"
};


function navigaA(pagina) {
    stato.paginaCorrente = pagina;

    // Salva la pagina corrente nel localStorage
    localStorage.setItem("fintracker-pagina", pagina);

    const topbarTitle = document.getElementById("topbar-title");
    if (topbarTitle) topbarTitle.textContent = titoli[pagina] || pagina;

    document.querySelectorAll(".nav-link").forEach(link => {
        link.classList.toggle("active", link.dataset.pagina === pagina);
    });

    document.querySelectorAll(".pagina").forEach(section => {
        section.classList.toggle("hidden", section.id !== `pagina-${pagina}`);
    });

    switch (pagina) {
        case "dashboard":  caricaDashboard();  break;
        case "watchlist":  caricaWatchlist();  break;
        case "grafici":    caricaGrafici();    break;
        case "notizie":    caricaNotizie();    break;
        case "segnali":    caricaSegnali();    break;
    }
}


// ─────────────────────────────────────────────
// DASHBOARD
// ─────────────────────────────────────────────

async function caricaDashboard() {
    setLoading("prezzi-grid", true);

    try {
        const [prezzi, segnali, notizie] = await Promise.all([
            api.prezzi.get(),
            api.segnali.get(true, true),
            api.notizie.get(null, true)
        ]);

        stato.prezzi = prezzi;
        renderPrezziGrid(prezzi);
        renderSegnaliDashboard(segnali);
        renderNotizieDashboard(notizie);

    } catch (e) {
        document.getElementById("prezzi-grid").innerHTML =
            `<p class="error-msg">Errore nel caricamento: ${e.message}</p>`;
    }
}

function renderPrezziGrid(prezzi) {
    const grid = document.getElementById("prezzi-grid");
    if (!prezzi.length) {
        grid.innerHTML = `<p class="empty-msg">Nessun prezzo disponibile.<br>Clicca <strong>Aggiorna prezzi</strong> per iniziare.</p>`;
        return;
    }

    grid.innerHTML = prezzi.map(p => {
        const varClass = classVariazione(p.variazione_pct);
        const varStr = p.variazione_pct != null
            ? `${p.variazione_pct > 0 ? "+" : ""}${p.variazione_pct}%`
            : "—";

        return `
        <div class="price-card" onclick="navigaGrafico('${p.ticker}')">
            <div class="price-card-header">
                <span class="ticker-badge">${p.ticker}</span>
                <span class="price-time">${p.timestamp ? p.timestamp.slice(11, 16) : ""}</span>
            </div>
            <div class="price-value">$${p.prezzo ?? "—"}</div>
            <div class="price-change ${varClass}">${varStr}</div>
            <div class="price-meta">
                <span>Vol: ${formatVolume(p.volume)}</span>
                <span>52w ▲${p.max_52w ?? "—"}</span>
            </div>
        </div>
        `;
    }).join("");
}

function renderSegnaliDashboard(segnali) {
    const el = document.getElementById("segnali-preview");
    if (!segnali.length) {
        el.innerHTML = `<p class="empty-msg">Nessun segnale importante oggi.</p>`;
        return;
    }
    el.innerHTML = segnali.slice(0, 4).map(s => `
        <div class="segnale-row">
            <span class="ticker-badge small">${s.ticker}</span>
            <span class="segnale-label">${s.indicatore}</span>
            <span class="segnale-text">${s.segnale}</span>
            <span class="badge-alta">ALTA</span>
        </div>
    `).join("");
}

function renderNotizieDashboard(notizie) {
    const el = document.getElementById("notizie-preview");
    if (!notizie.length) {
        el.innerHTML = `<p class="empty-msg">Nessuna notizia oggi. Clicca <strong>Aggiorna notizie</strong>.</p>`;
        return;
    }
    el.innerHTML = notizie.slice(0, 4).map(n => `
        <a href="${n.url}" target="_blank" class="news-item">
            <span class="ticker-badge small">${n.ticker}</span>
            <span class="news-title">${n.titolo}</span>
            <span class="news-fonte">${n.fonte} · ${n.pubblicata_il?.slice(0, 10) ?? ""}</span>
        </a>
    `).join("");
}


// ─────────────────────────────────────────────
// WATCHLIST
// ─────────────────────────────────────────────

async function caricaWatchlist() {
    setLoading("watchlist-table", true);
    try {
        const [watchlist, prezzi] = await Promise.all([
            api.watchlist.get(),
            api.prezzi.get()
        ]);
        stato.watchlist = watchlist;
        const prezziMap = Object.fromEntries(prezzi.map(p => [p.ticker, p]));
        renderWatchlist(watchlist, prezziMap);
    } catch (e) {
        toast(e.message, "error");
    }
}

function renderWatchlist(watchlist, prezziMap) {
    const el = document.getElementById("watchlist-table");
    if (!watchlist.length) {
        el.innerHTML = `<p class="empty-msg">La watchlist è vuota. Cerca un ticker qui sopra per iniziare.</p>`;
        return;
    }

    el.innerHTML = `
    <table class="data-table">
        <thead>
            <tr>
                <th>Ticker</th>
                <th>Nome</th>
                <th>Prezzo</th>
                <th>Variazione</th>
                <th>Aggiunto il</th>
                <th>Note</th>
                <th></th>
            </tr>
        </thead>
        <tbody>
            ${watchlist.map(w => {
                const p = prezziMap[w.ticker];
                const varClass = p ? classVariazione(p.variazione_pct) : "neutral";
                const varStr = p?.variazione_pct != null
                    ? `${p.variazione_pct > 0 ? "+" : ""}${p.variazione_pct}%`
                    : "—";
                return `
                <tr>
                    <td><span class="ticker-badge">${w.ticker}</span></td>
                    <td>${w.nome || "—"}</td>
                    <td class="mono">${p ? "$" + p.prezzo : "—"}</td>
                    <td class="mono ${varClass}">${varStr}</td>
                    <td>${w.data_aggiunta?.slice(0, 10) || "—"}</td>
                    <td>${w.note || "—"}</td>
                    <td>
                        <button class="btn-icon danger" onclick="rimuoviTicker('${w.ticker}')">✕</button>
                    </td>
                </tr>`;
            }).join("")}
        </tbody>
    </table>`;
}

// Funzione globale per la ricerca ticker con debounce
window.cercaTicker = async function(query) {
    clearTimeout(stato.cercaTimeout);
    const risultatiEl = document.getElementById("cerca-risultati");

    if (query.length < 2) {
        risultatiEl.classList.add("hidden");
        return;
    }

    // Debounce — aspetta 400ms prima di cercare per non sovraccaricare l'API
    stato.cercaTimeout = setTimeout(async () => {
        try {
            const data = await api.watchlist.cerca(query);
            if (!data.risultati.length) {
                risultatiEl.innerHTML = `<div class="cerca-item empty">Nessun risultato</div>`;
            } else {
                risultatiEl.innerHTML = data.risultati.map(r => `
                    <div class="cerca-item" onclick="selezionaTicker('${r.ticker}', '${r.nome.replace(/'/g, "\\'")}')">
                        <span class="ticker-badge small">${r.ticker}</span>
                        <span class="cerca-nome">${r.nome}</span>
                        <span class="cerca-meta">${r.tipo} · ${r.borsa}</span>
                    </div>
                `).join("");
            }
            risultatiEl.classList.remove("hidden");
        } catch (e) {
            risultatiEl.classList.add("hidden");
        }
    }, 400);
};

// Seleziona un ticker dalla lista di ricerca
window.selezionaTicker = function(ticker, nome) {
    document.getElementById("cerca-input").value = `${ticker} — ${nome}`;
    document.getElementById("cerca-risultati").classList.add("hidden");
    stato.tickerSelezionato = ticker;
};

// Aggiunge il ticker selezionato alla watchlist
window.aggiungiTicker = async function() {
    if (!stato.tickerSelezionato) {
        toast("Seleziona un ticker dalla lista", "error");
        return;
    }
    try {
        const note = document.getElementById("note-input").value;
        await api.watchlist.aggiungi(stato.tickerSelezionato, note);
        toast(`${stato.tickerSelezionato} aggiunto alla watchlist`);
        stato.tickerSelezionato = null;
        document.getElementById("cerca-input").value = "";
        document.getElementById("note-input").value = "";
        caricaWatchlist();
    } catch (e) {
        toast(e.message, "error");
    }
};

window.rimuoviTicker = async function(ticker) {
    if (!confirm(`Rimuovere ${ticker} dalla watchlist?`)) return;
    try {
        await api.watchlist.rimuovi(ticker);
        toast(`${ticker} rimosso`);
        caricaWatchlist();
    } catch (e) {
        toast(e.message, "error");
    }
};


// ─────────────────────────────────────────────
// GRAFICI
// ─────────────────────────────────────────────

async function caricaGrafici(tickerForzato = null) {
    try{
        const watchlist = await api.watchlist.get();
        stato.watchlist = watchlist;
        if (!watchlist.length) {
            document.getElementById("grafico-container").innerHTML =
                `<p class="empty-msg">La watchlist è vuota. Aggiungi un ticker per visualizzare i grafici.</p>`;
            return;
        }

        const select = document.getElementById("ticker-select");
        select.innerHTML = watchlist.map(w =>
            `<option value="${w.ticker}">${w.ticker} — ${w.nome}</option>`
        ).join("");

        // Usa il ticker forzato se presente, altrimenti il primo della lista
        const ticker = tickerForzato ?? watchlist[0].ticker;
        select.value = ticker;

        // Carica il grafico per il ticker selezionato
        await caricaGrafico(ticker, "6mo");
    }

    catch (e) {
        document.getElementById("grafico-container").innerHTML =
            `<p class="error-msg">Errore nel caricamento: ${e.message}</p>`;
    }
}

async function caricaGrafico(ticker, periodo) {
    const container = document.getElementById("grafico-container");
    container.innerHTML = `<div class="loading-chart">Caricamento ${ticker}...</div>`;

    try {
        const dati = await api.storico.get(ticker, periodo);
        const tipo = document.getElementById("tipo-grafico")?.value || "candlestick";

        const { createChart } = LightweightCharts;
        container.innerHTML = "";

        // Legenda personalizzata sopra il grafico
        const legenda = document.createElement("div");
        legenda.style.cssText = `
            display: flex;
            gap: 16px;
            padding: 8px 12px;
            font-size: 12px;
            font-family: var(--font-display);
        `;
        legenda.innerHTML = `
            <span style="color:#94a3b8">
                <span style="display:inline-block;width:12px;height:2px;background:#00ff87;vertical-align:middle;margin-right:4px"></span>
                ${ticker}
            </span>
            <span style="color:#818cf8">
                <span style="display:inline-block;width:12px;height:2px;background:#818cf8;vertical-align:middle;margin-right:4px"></span>
                SMA 20
            </span>
            <span style="color:#fb923c">
                <span style="display:inline-block;width:12px;height:2px;background:#fb923c;vertical-align:middle;margin-right:4px"></span>
                SMA 50
            </span>
        `;

        legenda.innerHTML += `
            <span style="color:#ff02c8ce">
                <span style="display:inline-block;width:12px;height:2px;
                    background:#ff02c8ce;vertical-align:middle;margin-right:4px;
                    border-top:2px dashed #ff02c8ce;background:none"></span>
                BB (20)
            </span>
        `;
        container.appendChild(legenda);

        const chart = createChart(container, {
            width: container.clientWidth,
            height: 420,
            layout: {
                background: { color: "transparent" },
                textColor: "#94a3b8"
            },
            grid: {
                vertLines: { color: "#1e293b" },
                horzLines: { color: "#1e293b" }
            },
            crosshair: { mode: 1 },
            rightPriceScale: { borderColor: "#1e293b" },
            timeScale: { borderColor: "#1e293b", timeVisible: true }
        });

        // ── Crea la serie in base al tipo selezionato ──
        let serie;

        if (tipo === "candlestick") {
            serie = chart.addCandlestickSeries({
                upColor:         "#00ff87",
                downColor:       "#ff4757",
                borderUpColor:   "#00ff87",
                borderDownColor: "#ff4757",
                wickUpColor:     "#00ff87",
                wickDownColor:   "#ff4757"
            });
            serie.setData(dati.map(d => ({
                time: d.data, open: d.open,
                high: d.high, low:  d.low, close: d.close
            })));

        } else if (tipo === "barre") {
            // Le barre mostrano OHLC come segmenti verticali
            // simili alle candele ma senza il corpo colorato
            serie = chart.addBarSeries({
                upColor:   "#00ff87",
                downColor: "#ff4757"
            });
            serie.setData(dati.map(d => ({
                time: d.data, open: d.open,
                high: d.high, low:  d.low, close: d.close
            })));

        } else if (tipo === "area") {
            // Area mostra solo il prezzo di chiusura con area colorata sotto
            // ottima per vedere il trend generale su periodi lunghi
            serie = chart.addAreaSeries({
                lineColor:   "#00ff87",
                topColor:    "#00ff8730",
                bottomColor: "#00ff8705",
                lineWidth: 2
            });
            serie.setData(dati.map(d => ({
                time: d.data, value: d.close
            })));

        } else if (tipo === "linea") {
            // Linea semplice sul prezzo di chiusura
            // la più leggibile per confrontare trend
            serie = chart.addLineSeries({
                color:     "#00ff87",
                lineWidth: 2
            });
            serie.setData(dati.map(d => ({
                time: d.data, value: d.close
            })));
        }

        // SMA 20
        const sma20 = calcolaSMA(dati, 20);
        if (sma20.length) {
            stato.serie.sma20 = chart.addLineSeries({
                color: "#818cf8",
                lineWidth: 1.5,
                priceLineVisible: false,
                lastValueVisible: false,
                visible: stato.indicatori.sma20
            });
            stato.serie.sma20.setData(sma20);
        }

        // SMA 50 — solo se ci sono abbastanza dati
        if (dati.length >= 50) {
            const sma50 = calcolaSMA(dati, 50);
            if (sma50.length) {
                stato.serie.sma50 = chart.addLineSeries({
                    color: "#fb923c",
                    lineWidth: 1.5,
                    lineStyle: 2,
                    priceLineVisible: false,
                    lastValueVisible: false,
                    visible: stato.indicatori.sma50
                });
                stato.serie.sma50.setData(sma50);
            }
        }

        // Bollinger Bands — visibili solo se i dati sono presenti
        const bbDati = dati.filter(d => d.bb_upper && d.bb_lower);

        if (bbDati.length) {
            // Banda superiore
            stato.serie.bbUpper = chart.addLineSeries({
                color:            "#ff02c8ce",
                lineWidth:        1,
                lineStyle:        1,       // Linea tratteggiata
                priceLineVisible: false,
                lastValueVisible: false,
                visible: stato.indicatori.bollinger
            });
            stato.serie.bbUpper.setData(bbDati.map(d => ({
                time: d.data, value: d.bb_upper
            })));

            // Banda inferiore
            stato.serie.bbLower = chart.addLineSeries({
                color:            "#ff02c8ce",
                lineWidth:        1,
                lineStyle:        1,
                priceLineVisible: false,
                lastValueVisible: false,
                visible: stato.indicatori.bollinger
            });
            stato.serie.bbLower.setData(bbDati.map(d => ({
                time: d.data, value: d.bb_lower
            })));
        }

        // Rispetta lo stato corrente di volume e RSI
        if (!stato.indicatori.volume) {
            document.getElementById("volume-container").style.display = "none";
        }
        if (!stato.indicatori.rsi) {
            const rsiSection = document.getElementById("rsi-container").closest(".grafico-section");
            if (rsiSection) rsiSection.style.display = "none";
        }

        chart.timeScale().fitContent();
        renderVolumeChart(dati);
        renderRSIChart(dati);

        stato.graficoCorrente = chart;
        window.addEventListener("resize", () => {
            chart.applyOptions({ width: container.clientWidth });
        });

    } catch (e) {
        container.innerHTML = `<p class="error-msg">${e.message}</p>`;
    }
}

function calcolaSMA(dati, periodo) {
    return dati
        .map((d, i) => {
            if (i < periodo - 1) return null;
            const media = dati.slice(i - periodo + 1, i + 1)
                .reduce((sum, x) => sum + x.close, 0) / periodo;
            return { time: d.data, value: parseFloat(media.toFixed(2)) };
        })
        .filter(Boolean);
}

function renderVolumeChart(dati) {
    const container = document.getElementById("volume-container");
    container.innerHTML = "";

    const { createChart } = LightweightCharts;
    const chart = createChart(container, {
        width: container.clientWidth,
        height: 120,
        layout: { background: { color: "transparent" }, textColor: "#94a3b8" },
        grid: { vertLines: { color: "#1e293b" }, horzLines: { color: "#1e293b" } },
        rightPriceScale: { borderColor: "#1e293b" },
        timeScale: { borderColor: "#1e293b", timeVisible: true }
    });

    const volSeries = chart.addHistogramSeries({
        priceFormat: { type: "volume" },
        priceScaleId: ""
    });

    volSeries.setData(dati.map(d => ({
        time:  d.data,
        value: d.volume,
        color: d.close >= d.open ? "#00ff8740" : "#ff475740"
    })));

    chart.timeScale().fitContent();
    window.addEventListener("resize", () => {
        chart.applyOptions({ width: container.clientWidth });
    });
}

function renderRSIChart(dati) {
    const container = document.getElementById("rsi-container");
    container.innerHTML = "";

    // Calcolo RSI manuale
    const periodo = 14;
    const rsiData = [];
    for (let i = periodo; i < dati.length; i++) {
        const slice = dati.slice(i - periodo, i);
        let guadagni = 0, perdite = 0;
        for (let j = 1; j < slice.length; j++) {
            const delta = slice[j].close - slice[j-1].close;
            if (delta > 0) guadagni += delta;
            else perdite += Math.abs(delta);
        }
        const rs = guadagni / (perdite || 1);
        rsiData.push({
            time: dati[i].data,
            value: parseFloat((100 - 100 / (1 + rs)).toFixed(2))
        });
    }

    const { createChart } = LightweightCharts;
    const chart = createChart(container, {
        width: container.clientWidth,
        height: 140,
        layout: { background: { color: "transparent" }, textColor: "#94a3b8" },
        grid: { vertLines: { color: "#1e293b" }, horzLines: { color: "#1e293b" } },
        rightPriceScale: { borderColor: "#1e293b", autoScale: false,
                          scaleMargins: { top: 0.1, bottom: 0.1 } },
        timeScale: { borderColor: "#1e293b" }
    });

    const rsiSeries = chart.addLineSeries({
        color: "#c980f9", lineWidth: 1.5,
        priceFormat: { type: "price", precision: 1 }
    });
    rsiSeries.setData(rsiData);

    // Linee ipercomprato/ipervenduto
    const linea70 = chart.addLineSeries({ color: "#ff475750", lineWidth: 1, lineStyle: 2 });
    const linea30 = chart.addLineSeries({ color: "#00ff8750", lineWidth: 1, lineStyle: 2 });
    linea70.setData(rsiData.map(d => ({ time: d.time, value: 70 })));
    linea30.setData(rsiData.map(d => ({ time: d.time, value: 30 })));

    chart.timeScale().fitContent();
    window.addEventListener("resize", () => {
        chart.applyOptions({ width: container.clientWidth });
    });
}

window.toggleIndicatore = function(indicatore) {
    const btn = document.querySelector(`[data-ind="${indicatore}"]`);
    const attivo = !stato.indicatori[indicatore];
    stato.indicatori[indicatore] = attivo;

    // Aggiorna lo stile del pulsante
    btn.classList.toggle("active", attivo);

    // Mostra/nasconde l'elemento corrispondente
    switch (indicatore) {
        case "sma20":
            if (stato.serie.sma20) {
                stato.serie.sma20.applyOptions({
                    visible: attivo
                });
            }
            break;

        case "sma50":
            if (stato.serie.sma50) {
                stato.serie.sma50.applyOptions({
                    visible: attivo
                });
            }
            break;

        case "bollinger":
            if (stato.serie.bbUpper) stato.serie.bbUpper.applyOptions({ visible: attivo });
            if (stato.serie.bbLower) stato.serie.bbLower.applyOptions({ visible: attivo });
            break;

        case "volume":
            // Mostra/nasconde il container del volume
            document.getElementById("volume-container").style.display =
                attivo ? "block" : "none";
            break;

        case "rsi":
            // Mostra/nasconde il container dell'RSI e la sua card
            const rsiSection = document.getElementById("rsi-container").closest(".grafico-section");
            if (rsiSection) rsiSection.style.display = attivo ? "block" : "none";
            break;
    }
};

// Funzioni globali chiamate dall'HTML
window.cambiaGrafico = () => {
    const ticker = document.getElementById("ticker-select").value;
    const periodo = document.getElementById("periodo-select").value;
    caricaGrafico(ticker, periodo);
};

window.navigaGrafico = (ticker) => {
    stato.paginaCorrente = "grafici";
    localStorage.setItem("fintracker-pagina", "grafici");

    // Aggiorna topbar
    const topbar = document.getElementById("topbar-title");
    if (topbar) topbar.textContent = "Grafici";
    
    document.querySelectorAll(".nav-link").forEach(link => {
        link.classList.toggle("active", link.dataset.pagina === "grafici");
    });

    document.querySelectorAll(".pagina").forEach(section => {
        section.classList.toggle("hidden", section.id !== "pagina-grafici");
    });

    // Carica i grafici con il ticker specifico richiesto
    caricaGrafici(ticker);
};


// ─────────────────────────────────────────────
// NOTIZIE
// ─────────────────────────────────────────────

async function caricaNotizie(soloOggi = true, ticker = null) {
    setLoading("notizie-list", true);
    try {
        const notizie = await api.notizie.get(ticker, soloOggi);
        renderNotizie(notizie, soloOggi);
    } catch (e) {
        toast(e.message, "error");
    }
}

function renderNotizie(notizie, soloOggi) {
    const el = document.getElementById("notizie-list");
    const label = soloOggi ? "oggi" : "ultimi 7 giorni";

    if (!notizie.length) {
        el.innerHTML = `<p class="empty-msg">Nessuna notizia per ${label}.</p>`;
        return;
    }

    el.innerHTML = notizie.map(n => `
        <a href="${n.url}" target="_blank" class="news-card-full">
            <div class="news-card-header">
                <span class="ticker-badge">${n.ticker}</span>
                <span class="news-date">${n.pubblicata_il?.slice(0, 10) ?? ""}</span>
            </div>
            <div class="news-card-title">${n.titolo}</div>
            <div class="news-card-fonte">${n.fonte}</div>
        </a>
    `).join("");
}

window.filtraNotizie = function() {
    const soloOggi = document.getElementById("toggle-storico-notizie").checked === false;
    const ticker = document.getElementById("filtro-ticker-notizie").value || null;
    caricaNotizie(soloOggi, ticker);
};


// ─────────────────────────────────────────────
// SEGNALI
// ─────────────────────────────────────────────

async function caricaSegnali(soloOggi = true, soloImportanti = false) {
    setLoading("segnali-list", true);
    try {
        const segnali = await api.segnali.get(soloOggi, soloImportanti);
        renderSegnali(segnali, soloOggi);
    } catch (e) {
        toast(e.message, "error");
    }
}

function renderSegnali(segnali, soloOggi) {
    const el = document.getElementById("segnali-list");
    const label = soloOggi ? "oggi" : "ultimi 30 giorni";

    if (!segnali.length) {
        el.innerHTML = `<p class="empty-msg">Nessun segnale per ${label}.</p>`;
        return;
    }

    // Raggruppa per ticker
    const perTicker = segnali.reduce((acc, s) => {
        if (!acc[s.ticker]) acc[s.ticker] = [];
        acc[s.ticker].push(s);
        return acc;
    }, {});

    el.innerHTML = Object.entries(perTicker).map(([ticker, lista]) => `
        <div class="segnali-gruppo">
            <div class="segnali-gruppo-header">
                <span class="ticker-badge">${ticker}</span>
                <span class="segnali-count">${lista.length} segnali</span>
            </div>
            <div class="segnali-cards">
                ${lista.map(s => `
                    <div class="segnale-card importanza-${s.importanza.toLowerCase()}">
                        <div class="segnale-card-top">
                            <span class="segnale-indicatore">${s.indicatore}</span>
                            <span class="badge-${s.importanza.toLowerCase()}">${s.importanza}</span>
                        </div>
                        <div class="segnale-card-testo">${s.segnale}</div>
                        <div class="segnale-card-time">${s.timestamp?.slice(0, 16) ?? ""}</div>
                    </div>
                `).join("")}
            </div>
        </div>
    `).join("");
}

window.filtraSegnali = function() {
    const soloOggi = !document.getElementById("toggle-storico-segnali").checked;
    const soloImportanti = document.getElementById("toggle-importanti").checked;
    caricaSegnali(soloOggi, soloImportanti);
};


// ─────────────────────────────────────────────
// AZIONI RAPIDE SIDEBAR
// ─────────────────────────────────────────────

window.azioneSidebar = async function(azione) {
    const btn = document.querySelector(`[data-azione="${azione}"]`);
    if (btn) {
        btn.disabled = true;
        btn.classList.add("loading-btn");
    }

    try {
        switch (azione) {
            case "aggiorna-prezzi":
                await api.prezzi.aggiorna();
                toast("Prezzi aggiornati");
                if (stato.paginaCorrente === "dashboard") caricaDashboard();
                if (stato.paginaCorrente === "watchlist") caricaWatchlist();
                break;
            case "aggiorna-notizie":
                await api.notizie.aggiorna();
                toast("Notizie aggiornate");
                if (stato.paginaCorrente === "notizie") caricaNotizie();
                break;
            case "analisi-tecnica":
                await api.segnali.analisi();
                toast("Analisi tecnica completata");
                if (stato.paginaCorrente === "segnali") caricaSegnali();
                break;
            case "invia-telegram":
                await api.telegram.invia();
                toast("Riepilogo inviato su Telegram");
                break;
        }
    } catch (e) {
        toast(e.message, "error");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.classList.remove("loading-btn");
        }
    }
};


// ─────────────────────────────────────────────
// INIT
// ─────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".nav-link").forEach(link => {
        link.addEventListener("click", () => navigaA(link.dataset.pagina));
    });

    const primaVisita = !localStorage.getItem("fintracker-visitato");
    if (primaVisita) {
        localStorage.setItem("fintracker-visitato", "true");
        navigaA("dashboard");
    }
    else {
        // Ripristina l'ultima pagina visitata, altrimenti apre la dashboard
        const paginaSalvata = localStorage.getItem("fintracker-pagina") || "dashboard";
        navigaA(paginaSalvata);
    }
});