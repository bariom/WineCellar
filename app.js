const state = {
  wines: [],
  filter: "All",
  selectedWineId: null,
  formReturn: "cellar",
  lang: localStorage.getItem("wine-cellar-language") || "it",
  catalog: [],
  search: "",
};

const translations = {
  en: {
    addOwner: "Add Owner",
    addScore: "Add Score",
    addWine: "+ Add Wine",
    all: "All",
    appellation: "Appellation",
    assigned: "Assigned",
    back: "Back",
    bottle: "bottle",
    bottles: "bottles",
    bottlesInCellar: "Bottles In Cellar",
    bottlesOnOrder: "Bottles On Order",
    cancel: "Cancel",
    cachedRates: "cached rates",
    addSale: "Add Sale",
    buyer: "Buyer",
    cellar: "Cellar",
    cellarValue: "Cellar Value",
    color: "Color",
    currentPositionValue: "Current Position Value",
    currentUnitValue: "Current Unit Value",
    currentValue: "Current Value",
    currentValuePerUnit: "Current Value per Unit",
    convertedRates: "Converted to CHF using {source} from {date}.",
    currency: "Currency",
    delete: "Delete",
    delivered: "Delivered",
    dessert: "Dessert",
    drankOne: "Drank 1",
    edit: "Edit",
    emptyFilter: "No wines found for this filter.",
    emptyOwnership: "No ownership data.",
    exchangeUnavailable: "Exchange rates unavailable: {error}",
    expected: "Expected",
    expectedDelivery: "Expected Delivery",
    export: "Export",
    format: "Format",
    formatBottle: "Bottle (750ml)",
    formatHalf: "Half (375ml)",
    formatMagnum: "Magnum (1.5L)",
    import: "Import",
    importInvalid: "The selected file does not contain a valid cellar.",
    insights: "Insights",
    latestRates: "latest rates",
    merchant: "Merchant",
    merchantRequired: "Merchant / Store *",
    myBottles: "My Bottles",
    myCost: "My Cost",
    myOwnershipPct: "My Ownership %",
    myShare: "My Share",
    newOrder: "New Order",
    noFutureDeliveries: "There are no future deliveries to show.",
    noScores: "No scores recorded.",
    notSpecified: "Unspecified",
    onlyDelivered: "Only delivered bottles can be marked as drunk",
    orderDate: "Order Date",
    ordered: "Ordered",
    otherOwners: "Other Owners",
    ownerName: "Owner name",
    ownership: "Ownership",
    priceRequired: "Price per Unit *",
    producerRequired: "Producer *",
    quantity: "Quantity",
    quantityRequired: "Quantity *",
    region: "Region",
    remove: "Remove",
    rose: "Rose",
    saveOrder: "Save Order",
    saveSale: "Save Sale",
    saveUnable: "Unable to save order: {error}",
    salePrice: "Sale Price",
    sales: "Sales",
    soldTo: "Sold to {buyer}",
    saleProfit: "Profit",
    saleLoss: "Loss",
    noSales: "No sales recorded.",
    saleUnable: "Unable to save sale: {error}",
    searchPlaceholder: "Search wine, producer, region",
    score: "Score",
    scoreNote: "Note",
    scores: "Scores",
    critic: "Critic",
    shipped: "Shipped",
    sparkling: "Sparkling",
    status: "Status",
    statusLabel: "Status:",
    timeline: "Timeline",
    topRegions: "Top Regions",
    sharedPositions: "Shared Positions",
    totalPositionValue: "Total Position Value",
    totalCurrentPositionValue: "Total Current Position Value",
    totalPositionCost: "Total Position Cost",
    totalBottlesInCellar: "Total Bottles In Cellar",
    totalBottlesOnOrder: "Total Bottles On Order",
    totalInvested: "Total Invested",
    grossCurrentValue: "Current Total Value",
    topRegionsAll: "Top Regions - All Owners",
    type: "Type",
    unableBottleCount: "Unable to update bottle count: {error}",
    unitPrice: "Unit Price",
    unrealizedGainLoss: "Unrealized P/L",
    values: "Values",
    vintageRequired: "Vintage *",
    white: "White",
    wineNameRequired: "Wine Name *",
    autofilled: "Wine details autofilled from your cellar history.",
    red: "Red",
  },
  it: {
    addOwner: "Aggiungi proprietario",
    addScore: "Aggiungi punteggio",
    addWine: "+ Aggiungi vino",
    all: "Tutti",
    appellation: "Denominazione",
    assigned: "Assegnato",
    back: "Indietro",
    bottle: "bottiglia",
    bottles: "bottiglie",
    bottlesInCellar: "Bottiglie in cantina",
    bottlesOnOrder: "Bottiglie ordinate",
    cancel: "Annulla",
    cachedRates: "cambi in cache",
    addSale: "Aggiungi vendita",
    buyer: "Acquirente",
    cellar: "Cantina",
    cellarValue: "Valore cantina",
    color: "Colore",
    currentPositionValue: "Valore attuale posizione",
    currentUnitValue: "Valore unitario attuale",
    currentValue: "Valore attuale",
    currentValuePerUnit: "Valore attuale unitario",
    convertedRates: "Convertito in CHF con {source} del {date}.",
    currency: "Valuta",
    delete: "Elimina",
    delivered: "In cantina",
    dessert: "Dolce",
    drankOne: "Bevuta 1",
    edit: "Modifica",
    emptyFilter: "Nessun vino trovato per questo filtro.",
    emptyOwnership: "Nessun dato di proprietà.",
    exchangeUnavailable: "Cambi non disponibili: {error}",
    expected: "Previsto",
    expectedDelivery: "Consegna prevista",
    export: "Esporta",
    format: "Formato",
    formatBottle: "Bottiglia (750ml)",
    formatHalf: "Mezza (375ml)",
    formatMagnum: "Magnum (1.5L)",
    import: "Importa",
    importInvalid: "Il file selezionato non contiene una cantina valida.",
    insights: "Statistiche",
    latestRates: "ultimi cambi",
    merchant: "Venditore",
    merchantRequired: "Venditore / Negozio *",
    myBottles: "Mie bottiglie",
    myCost: "Mio costo",
    myOwnershipPct: "Mia quota %",
    myShare: "Mia quota",
    newOrder: "Nuovo ordine",
    noFutureDeliveries: "Non ci sono consegne future da mostrare.",
    noScores: "Nessun punteggio registrato.",
    notSpecified: "Non specificato",
    onlyDelivered: "Puoi segnare come bevute solo bottiglie gia in cantina",
    orderDate: "Data ordine",
    ordered: "Ordinato",
    otherOwners: "Altri proprietari",
    ownerName: "Nome proprietario",
    ownership: "Proprietà",
    priceRequired: "Prezzo unitario *",
    producerRequired: "Produttore *",
    quantity: "Quantità",
    quantityRequired: "Quantità *",
    region: "Regione",
    remove: "Rimuovi",
    rose: "Rosé",
    saveOrder: "Salva ordine",
    saveSale: "Salva vendita",
    saveUnable: "Impossibile salvare l'ordine: {error}",
    salePrice: "Prezzo vendita",
    sales: "Vendite",
    soldTo: "Venduto a {buyer}",
    saleProfit: "Utile",
    saleLoss: "Perdita",
    noSales: "Nessuna vendita registrata.",
    saleUnable: "Impossibile salvare la vendita: {error}",
    searchPlaceholder: "Cerca vino, produttore, regione",
    score: "Punteggio",
    scoreNote: "Nota",
    scores: "Punteggi",
    critic: "Critico",
    shipped: "Spedito",
    sparkling: "Spumante",
    status: "Stato",
    statusLabel: "Stato:",
    timeline: "Timeline",
    topRegions: "Regioni principali",
    sharedPositions: "Posizioni condivise",
    totalPositionValue: "Valore totale posizioni",
    totalCurrentPositionValue: "Valore attuale posizione totale",
    totalPositionCost: "Costo posizione totale",
    totalBottlesInCellar: "Bottiglie totali in cantina",
    totalBottlesOnOrder: "Bottiglie totali ordinate",
    totalInvested: "Totale investito",
    grossCurrentValue: "Valore attuale totale",
    topRegionsAll: "Regioni principali - tutti",
    type: "Tipo",
    unableBottleCount: "Impossibile aggiornare il numero di bottiglie: {error}",
    unitPrice: "Prezzo unitario",
    unrealizedGainLoss: "Utile/perdita potenziale",
    values: "Valori",
    vintageRequired: "Annata *",
    white: "Bianco",
    wineNameRequired: "Nome vino *",
    autofilled: "Dati vino completati dalla tua cronologia.",
    red: "Rosso",
  },
};

const screens = {
  cellar: document.querySelector("#screen-cellar"),
  timeline: document.querySelector("#screen-timeline"),
  insights: document.querySelector("#screen-insights"),
  detail: document.querySelector("#screen-detail"),
  form: document.querySelector("#screen-form"),
};

const wineList = document.querySelector("#wine-list");
const cellarSearch = document.querySelector("#cellar-search");
const timelineList = document.querySelector("#timeline-list");
const regionList = document.querySelector("#region-list");
const grossRegionList = document.querySelector("#gross-region-list");
const form = document.querySelector("#wine-form");
const deleteButton = document.querySelector("#delete-button");
const drinkButton = document.querySelector("#drink-bottle-button");
const ownersFormList = document.querySelector("#owners-form-list");
const scoresFormList = document.querySelector("#scores-form-list");
const bottomNav = document.querySelector(".bottom-nav");
const languageButton = document.querySelector("#language-button");
const saleForm = document.querySelector("#sale-form");
const showSaleFormButton = document.querySelector("#show-sale-form-button");
const saleList = document.querySelector("#sale-list");
const wineNameInput = document.querySelector("#name");
const wineNameSuggestions = document.querySelector("#wine-name-suggestions");

function t(key, replacements = {}) {
  const dictionary = translations[state.lang] || translations.it;
  const text = dictionary[key] || translations.en[key] || key;
  return Object.entries(replacements).reduce((value, [name, replacement]) => {
    return value.replaceAll(`{${name}}`, replacement);
  }, text);
}

function applyTranslations() {
  document.documentElement.lang = state.lang;
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    element.placeholder = t(element.dataset.i18nPlaceholder);
  });
  languageButton.textContent = state.lang.toUpperCase();
  document.querySelectorAll(".owner-name").forEach((input) => {
    input.placeholder = t("ownerName");
  });
  document.querySelectorAll(".score-critic").forEach((input) => {
    input.placeholder = t("critic");
  });
  document.querySelectorAll(".score-value").forEach((input) => {
    input.placeholder = t("score");
  });
  document.querySelectorAll(".score-note").forEach((input) => {
    input.placeholder = t("scoreNote");
  });
  document.querySelectorAll(".owner-remove").forEach((button) => {
    button.textContent = t("remove");
  });
  document.querySelectorAll(".score-remove").forEach((button) => {
    button.textContent = t("remove");
  });
  renderCellar();
  const currentScreen = Object.entries(screens).find(([, screen]) => screen.classList.contains("active"))?.[0];
  if (currentScreen === "timeline") renderTimeline();
  if (currentScreen === "insights") renderInsights();
  if (currentScreen === "detail") openDetail(state.wines.find((wine) => wine.id === state.selectedWineId));
  if (currentScreen === "form") {
    document.querySelector("#form-title").textContent = form.elements.id.value ? t("edit") : t("newOrder");
  }
  if (currentScreen === "detail") renderSales(state.selectedWineId);
}

function statusLabel(status) {
  return t({ Ordered: "ordered", Shipped: "shipped", Delivered: "delivered" }[status] || "notSpecified");
}

function typeLabel(type) {
  return t({ Red: "red", White: "white", Rose: "rose", Sparkling: "sparkling", Dessert: "dessert" }[type] || "notSpecified");
}

function formatLabel(format) {
  return (
    {
      "Half (375ml)": t("formatHalf"),
      "Bottle (750ml)": t("formatBottle"),
      "Magnum (1.5L)": t("formatMagnum"),
    }[format] || format
  );
}

function bottleLabel(quantity) {
  return Number(quantity) === 1 ? t("bottle") : t("bottles");
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }

  if (response.status === 204) return null;
  return response.json();
}

async function loadWines() {
  const [wines, catalog] = await Promise.all([api("/api/wines"), api("/api/wine-catalog")]);
  state.wines = wines;
  state.catalog = catalog;
  renderWineSuggestions();
  renderCellar();
}

function renderWineSuggestions() {
  const seen = new Set();
  const suggestions = [
    ...state.wines.map((wine) => ({ ...wine, source: "cellar" })),
    ...state.catalog.map((wine) => ({ ...wine, source: "catalog", currency: "CHF", owner_share_pct: 100 })),
  ];

  wineNameSuggestions.innerHTML = suggestions
    .filter((wine) => {
      const key = wine.name.trim().toLowerCase();
      if (!key || seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .sort((a, b) => a.name.localeCompare(b.name))
    .map((wine) => {
      const source = wine.source === "catalog" ? "catalog" : "cellar";
      return `<option value="${escapeAttribute(wine.name)}" label="${escapeAttribute([wine.producer, wine.region, source].filter(Boolean).join(" - "))}"></option>`;
    })
    .join("");
}

function matchingWineTemplate(name) {
  const normalized = name.trim().toLowerCase();
  if (!normalized) return null;
  return (
    state.wines.find((wine) => wine.name.trim().toLowerCase() === normalized) ||
    state.catalog.find((wine) => wine.name.trim().toLowerCase() === normalized) ||
    null
  );
}

function applyWineTemplate(wine) {
  if (!wine || form.elements.id.value) return;

  const fieldValues = {
    producer: wine.producer,
    region: wine.region,
    appellation: wine.appellation,
    format: wine.format,
    type: wine.type,
    currency: wine.currency || "CHF",
    current_value: wine.current_value,
    owner_share_pct: wine.owner_share_pct ?? 100,
  };

  Object.entries(fieldValues).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    const field = form.elements[key];
    if (!field) return;
    if (field instanceof RadioNodeList) {
      const option = [...field].find((input) => input.value === value);
      if (option) option.checked = true;
      return;
    }
    field.value = value;
  });
}

function formatMoney(value, currency = "CHF") {
  return new Intl.NumberFormat(state.lang === "it" ? "it-CH" : "en-CH", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(Number(value) || 0);
}

function formatMonthYear(dateValue) {
  if (!dateValue) return "TBD";
  return new Intl.DateTimeFormat(state.lang === "it" ? "it-IT" : "en-GB", { month: "short", year: "numeric" }).format(new Date(dateValue));
}

function formatDate(dateValue) {
  if (!dateValue) return "TBD";
  return new Intl.DateTimeFormat(state.lang === "it" ? "it-IT" : "en-GB", { day: "2-digit", month: "2-digit", year: "numeric" }).format(
    new Date(dateValue),
  );
}

function deliveryYear(wine) {
  if (!wine.expected_delivery) return "TBD";
  return new Date(wine.expected_delivery).getFullYear().toString();
}

function formatNumber(value) {
  return new Intl.NumberFormat(state.lang === "it" ? "it-CH" : "en-CH", { maximumFractionDigits: 2 }).format(Number(value) || 0);
}

function personalQuantity(wine) {
  return Number(wine.quantity || 0) * Number(wine.owner_share_pct ?? 100) / 100;
}

function unitCurrentValue(wine) {
  return Number(wine.current_value ?? wine.price ?? 0);
}

function showScreen(name) {
  Object.entries(screens).forEach(([key, screen]) => {
    screen.classList.toggle("active", key === name);
  });

  bottomNav.hidden = name === "form" || name === "detail";
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.classList.toggle("active", item.dataset.screen === name);
  });

  if (name === "timeline") renderTimeline();
  if (name === "insights") renderInsights();
}

function openDetail(wine) {
  if (!wine) return;
  state.selectedWineId = wine.id;

  document.querySelector("#detail-title").textContent = wine.name;
  document.querySelector("#detail-producer").textContent = wine.producer;
  document.querySelector("#detail-vintage").textContent = wine.vintage;

  const status = document.querySelector("#detail-status");
  status.textContent = statusLabel(wine.status);
  status.className = `status-pill ${wine.status}`;

  document.querySelector("#detail-position-value").textContent = formatMoney(
    Number(wine.price || 0) * personalQuantity(wine),
    wine.currency,
  );
  document.querySelector("#detail-total-position-cost").textContent = formatMoney(
    Number(wine.price || 0) * Number(wine.quantity || 0),
    wine.currency,
  );
  document.querySelector("#detail-unit-price").textContent = formatMoney(wine.price, wine.currency);
  document.querySelector("#detail-current-unit-value").textContent = formatMoney(unitCurrentValue(wine), wine.currency);
  document.querySelector("#detail-current-position-value").textContent = formatMoney(
    unitCurrentValue(wine) * personalQuantity(wine),
    wine.currency,
  );
  document.querySelector("#detail-total-current-position-value").textContent = formatMoney(
    unitCurrentValue(wine) * Number(wine.quantity || 0),
    wine.currency,
  );
  document.querySelector("#detail-quantity").textContent = `${wine.quantity} ${bottleLabel(wine.quantity)}`;
  document.querySelector("#detail-owner-share").textContent = `${formatNumber(wine.owner_share_pct ?? 100)}%`;
  document.querySelector("#detail-owned-quantity").textContent = `${formatNumber(personalQuantity(wine))} ${bottleLabel(personalQuantity(wine))}`;
  document.querySelector("#detail-format").textContent = formatLabel(wine.format);
  document.querySelector("#detail-type").textContent = typeLabel(wine.type);
  document.querySelector("#detail-merchant").textContent = wine.merchant;
  document.querySelector("#detail-region").textContent = wine.region || t("notSpecified");
  document.querySelector("#detail-appellation").textContent = wine.appellation || t("notSpecified");
  document.querySelector("#detail-order-date").textContent = formatDate(wine.order_date);
  document.querySelector("#detail-expected-delivery").textContent = formatDate(wine.expected_delivery);
  drinkButton.disabled = Number(wine.quantity) <= 0 || wine.status !== "Delivered";
  drinkButton.title = wine.status === "Delivered" ? "" : t("onlyDelivered");
  renderOwnerList(wine);
  renderScoreList(wine);
  renderSales(wine.id);

  showScreen("detail");
}

async function renderSales(wineId) {
  if (!wineId) return;
  try {
    const sales = await api(`/api/wines/${encodeURIComponent(wineId)}/sales`);
    saleList.innerHTML = sales.length
      ? sales
          .map((sale) => {
            const isProfit = Number(sale.profit_loss) >= 0;
            return `
              <div class="sale-row">
                <div>
                  <strong>${sale.quantity} ${bottleLabel(sale.quantity)}</strong>
                  <span>${t("soldTo", { buyer: escapeHtml(sale.buyer) })}</span>
                </div>
                <div class="sale-numbers">
                  <strong>${formatMoney(Number(sale.sale_price) * Number(sale.quantity), sale.currency)}</strong>
                  <span class="${isProfit ? "profit" : "loss"}">
                    ${isProfit ? t("saleProfit") : t("saleLoss")}: ${formatMoney(Math.abs(sale.profit_loss), sale.currency)}
                  </span>
                </div>
              </div>
            `;
          })
          .join("")
      : `<p class="empty-state compact">${t("noSales")}</p>`;
  } catch (error) {
    saleList.innerHTML = `<p class="empty-state compact">${escapeHtml(error.message)}</p>`;
  }
}

function renderOwnerList(wine) {
  const owners = [{ name: state.lang === "it" ? "Io" : "Me", share_pct: Number(wine.owner_share_pct ?? 100) }, ...(wine.owners || [])];
  const assigned = owners.reduce((sum, owner) => sum + Number(owner.share_pct || 0), 0);
  const rows = owners
    .filter((owner) => owner.name || Number(owner.share_pct) > 0)
    .map(
      (owner) => `
        <div class="owner-row">
          <span>${escapeHtml(owner.name)}</span>
          <strong>${formatNumber(owner.share_pct)}%</strong>
        </div>
      `,
    )
    .join("");

  document.querySelector("#detail-owner-list").innerHTML = `
    ${rows || `<p class="empty-state compact">${t("emptyOwnership")}</p>`}
    <div class="owner-row total">
      <span>${t("assigned")}</span>
      <strong>${formatNumber(assigned)}%</strong>
    </div>
  `;
}

function renderScoreList(wine) {
  const scores = wine.scores || [];
  document.querySelector("#detail-score-list").innerHTML = scores.length
    ? scores
        .map(
          (score) => `
            <div class="score-row">
              <div>
                <strong>${escapeHtml(score.critic)}</strong>
                ${score.note ? `<span>${escapeHtml(score.note)}</span>` : ""}
              </div>
              <strong class="score-value-pill">${escapeHtml(score.score)}</strong>
            </div>
          `,
        )
        .join("")
    : `<p class="empty-state compact">${t("noScores")}</p>`;
}

function renderCellar() {
  const query = state.search.trim().toLowerCase();
  const wines = state.wines
    .filter((wine) => state.filter === "All" || wine.status === state.filter)
    .filter((wine) => {
      if (!query) return true;
      return [wine.name, wine.producer, wine.region, wine.appellation, wine.vintage]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(query));
    })
    .sort((a, b) => (b.expected_delivery || "").localeCompare(a.expected_delivery || ""));

  wineList.innerHTML = wines.length
    ? wines
        .map(
          (wine) => `
            <button class="wine-card" data-id="${wine.id}" data-type="${escapeHtml(wine.type)}" type="button">
              <div>
                <p class="wine-title">${escapeHtml(wine.name)}</p>
                <p class="wine-meta">${escapeHtml(wine.producer)}</p>
                <p class="wine-meta">${wine.quantity}x ${escapeHtml(formatLabel(wine.format))}</p>
                ${scoreSummary(wine) ? `<p class="score-summary">${escapeHtml(scoreSummary(wine))}</p>` : ""}
                <p class="wine-meta">${state.lang === "it" ? "Arrivo" : "Arrival"}: ${formatMonthYear(wine.expected_delivery)}</p>
              </div>
              <div class="card-side">
                <span class="vintage">${escapeHtml(wine.vintage)}</span>
                <span class="status-pill ${escapeHtml(wine.status)}">${escapeHtml(statusLabel(wine.status))}</span>
                <span class="price">${formatMoney(wine.price, wine.currency)} &gt;</span>
              </div>
            </button>
          `,
        )
        .join("")
    : `<p class="empty-state">${t("emptyFilter")}</p>`;
}

function scoreSummary(wine) {
  return (wine.scores || [])
    .slice(0, 3)
    .map((score) => `${score.critic} ${score.score}`)
    .join(" | ");
}

function renderTimeline() {
  const groups = state.wines
    .filter((wine) => wine.status !== "Delivered")
    .sort((a, b) => (a.expected_delivery || "").localeCompare(b.expected_delivery || ""))
    .reduce((acc, wine) => {
      const year = deliveryYear(wine);
      acc[year] ||= [];
      acc[year].push(wine);
      return acc;
    }, {});

  const years = Object.keys(groups).sort();
  timelineList.innerHTML = years.length
    ? years
        .map(
          (year) => `
            <section class="year-group">
              <h2 class="year-heading">${year}</h2>
              ${groups[year]
                .map(
                  (wine) => `
                    <article class="timeline-card">
                      <strong>${escapeHtml(wine.name)} <span class="small-vintage">${escapeHtml(wine.vintage)}</span></strong>
                      <p>${wine.quantity}x ${escapeHtml(formatLabel(wine.format))} - ${escapeHtml(wine.merchant)}</p>
                      <p>${t("expected")}: ${formatMonthYear(wine.expected_delivery)}</p>
                    </article>
                  `,
                )
                .join("")}
            </section>
          `,
        )
        .join("")
    : `<p class="empty-state">${t("noFutureDeliveries")}</p>`;
}

async function renderInsights() {
  try {
    const summary = await api("/api/summary");
    document.querySelector("#total-invested").textContent = formatMoney(
      summary.total_invested,
      summary.reference_currency,
    );
    document.querySelector("#cellar-bottles").textContent = formatNumber(summary.cellar_bottles);
    document.querySelector("#ordered-bottles").textContent = formatNumber(summary.ordered_bottles);
    document.querySelector("#current-value").textContent = formatMoney(summary.current_value, summary.reference_currency);
    document.querySelector("#unrealized-gain-loss").textContent = formatMoney(
      summary.unrealized_gain_loss,
      summary.reference_currency,
    );
    document.querySelector("#gross-total-value").textContent = formatMoney(
      summary.gross_total_value,
      summary.reference_currency,
    );
    document.querySelector("#gross-current-value").textContent = formatMoney(
      summary.gross_current_value,
      summary.reference_currency,
    );
    document.querySelector("#gross-unrealized-gain-loss").textContent = formatMoney(
      summary.gross_unrealized_gain_loss,
      summary.reference_currency,
    );
    document.querySelector("#gross-cellar-bottles").textContent = formatNumber(summary.gross_cellar_bottles);
    document.querySelector("#gross-ordered-bottles").textContent = formatNumber(summary.gross_ordered_bottles);

    regionList.innerHTML = summary.regions
      .map(
        (item) => `
          <div class="region-row">
            <span>${escapeHtml(item.region)}</span>
            <strong>${formatNumber(item.bottles)} btl</strong>
          </div>
        `,
      )
      .join("");

    grossRegionList.innerHTML = summary.gross_regions
      .map(
        (item) => `
          <div class="region-row">
            <span>${escapeHtml(item.region)}</span>
            <strong>${formatNumber(item.bottles)} btl</strong>
          </div>
        `,
      )
      .join("");

    const sourceLabel = summary.rates.cached ? t("cachedRates") : t("latestRates");
    document.querySelector("#rates-note").textContent = t("convertedRates", {
      source: sourceLabel,
      date: summary.rates.date,
    });
  } catch (error) {
    document.querySelector("#rates-note").textContent = t("exchangeUnavailable", { error: error.message });
  }
}

function openForm(wine) {
  form.reset();
  ownersFormList.innerHTML = "";
  scoresFormList.innerHTML = "";
  document.querySelector("#form-title").textContent = wine ? t("edit") : t("newOrder");
  document.querySelector("#wine-id").value = wine?.id || "";
  deleteButton.hidden = !wine;
  state.formReturn = wine ? "detail" : "cellar";

  const defaults = {
    order_date: new Date().toISOString().slice(0, 10),
    expected_delivery: new Date().toISOString().slice(0, 10),
    quantity: 1,
    currency: "CHF",
    status: "Ordered",
    format: "Bottle (750ml)",
    type: "Red",
    owner_share_pct: 100,
    owners: [],
    scores: [],
  };

  const values = { ...defaults, ...wine };
  Object.entries(values).forEach(([key, value]) => {
    const field = form.elements[key];
    if (!field) return;

    if (field instanceof RadioNodeList) {
      const option = [...field].find((input) => input.value === value);
      if (option) option.checked = true;
      return;
    }

    field.value = value ?? "";
  });

  (values.owners || []).forEach((owner) => addOwnerRow(owner));
  (values.scores || []).forEach((score) => addScoreRow(score));

  showScreen("form");
}

function addOwnerRow(owner = { name: "", share_pct: "" }) {
  const row = document.createElement("div");
  row.className = "owner-form-row";
  row.innerHTML = `
    <input class="form-control owner-name" placeholder="${escapeAttribute(t("ownerName"))}" value="${escapeAttribute(owner.name || "")}" />
    <input class="form-control owner-share" type="number" min="0" max="100" step="0.01" inputmode="decimal" placeholder="%" value="${escapeAttribute(owner.share_pct ?? "")}" />
    <button class="btn btn-soft owner-remove" type="button">${escapeHtml(t("remove"))}</button>
  `;
  row.querySelector(".owner-remove").addEventListener("click", () => row.remove());
  ownersFormList.appendChild(row);
}

function collectOwners() {
  return [...ownersFormList.querySelectorAll(".owner-form-row")]
    .map((row) => ({
      name: row.querySelector(".owner-name").value.trim(),
      share_pct: Number(row.querySelector(".owner-share").value || 0),
    }))
    .filter((owner) => owner.name);
}

function addScoreRow(score = { critic: "", score: "", note: "" }) {
  const row = document.createElement("div");
  row.className = "score-form-row";
  row.innerHTML = `
    <input class="form-control score-critic" placeholder="${escapeAttribute(t("critic"))}" value="${escapeAttribute(score.critic || "")}" />
    <input class="form-control score-value" placeholder="${escapeAttribute(t("score"))}" value="${escapeAttribute(score.score || "")}" />
    <input class="form-control score-note" placeholder="${escapeAttribute(t("scoreNote"))}" value="${escapeAttribute(score.note || "")}" />
    <button class="btn btn-soft score-remove" type="button">${escapeHtml(t("remove"))}</button>
  `;
  row.querySelector(".score-remove").addEventListener("click", () => row.remove());
  scoresFormList.appendChild(row);
}

function collectScores() {
  return [...scoresFormList.querySelectorAll(".score-form-row")]
    .map((row) => ({
      critic: row.querySelector(".score-critic").value.trim(),
      score: row.querySelector(".score-value").value.trim(),
      note: row.querySelector(".score-note").value.trim(),
    }))
    .filter((score) => score.critic || score.score || score.note);
}

function formToWine() {
  const data = new FormData(form);
  return {
    id: data.get("id") || undefined,
    name: data.get("name").trim(),
    producer: data.get("producer").trim(),
    vintage: data.get("vintage").trim(),
    region: data.get("region").trim(),
    appellation: data.get("appellation").trim(),
    format: data.get("format"),
    type: data.get("type"),
    quantity: Number(data.get("quantity")),
    price: Number(data.get("price")),
    current_value: data.get("current_value") === "" ? null : Number(data.get("current_value")),
    currency: data.get("currency"),
    status: data.get("status"),
    merchant: data.get("merchant").trim(),
    order_date: data.get("order_date"),
    expected_delivery: data.get("expected_delivery"),
    owner_share_pct: Number(data.get("owner_share_pct") || 100),
    owners: collectOwners(),
    scores: collectScores(),
  };
}

async function handleSubmit(event) {
  event.preventDefault();
  let saved;
  try {
    const wine = formToWine();
    saved = wine.id
      ? await api(`/api/wines/${encodeURIComponent(wine.id)}`, { method: "PUT", body: JSON.stringify(wine) })
      : await api("/api/wines", { method: "POST", body: JSON.stringify(wine) });
  } catch (error) {
    alert(t("saveUnable", { error: error.message }));
    return;
  }

  const index = state.wines.findIndex((item) => item.id === saved.id);
  if (index >= 0) state.wines[index] = saved;
  else state.wines.unshift(saved);

  renderWineSuggestions();
  renderCellar();
  if (state.formReturn === "detail") openDetail(saved);
  else showScreen("cellar");
}

async function deleteCurrentWine() {
  const id = document.querySelector("#wine-id").value;
  if (!id) return;

  await api(`/api/wines/${encodeURIComponent(id)}`, { method: "DELETE" });
  state.wines = state.wines.filter((wine) => wine.id !== id);
  renderWineSuggestions();
  renderCellar();
  showScreen("cellar");
}

async function drinkBottle() {
  const wine = state.wines.find((item) => item.id === state.selectedWineId);
  if (!wine || Number(wine.quantity) <= 0) return;

  drinkButton.disabled = true;
  const saved = await api(`/api/wines/${encodeURIComponent(wine.id)}/drink`, { method: "POST" });
  const index = state.wines.findIndex((item) => item.id === saved.id);
  if (index >= 0) state.wines[index] = saved;
  renderWineSuggestions();
  renderCellar();
  await renderInsights();
  openDetail(saved);
}

async function saveSale(event) {
  event.preventDefault();
  const wine = state.wines.find((item) => item.id === state.selectedWineId);
  if (!wine) return;

  const data = new FormData(saleForm);
  const payload = {
    quantity: Number(data.get("quantity")),
    sale_price: Number(data.get("sale_price")),
    currency: data.get("currency"),
    buyer: data.get("buyer").trim(),
  };

  try {
    const result = await api(`/api/wines/${encodeURIComponent(wine.id)}/sales`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    const index = state.wines.findIndex((item) => item.id === result.wine.id);
    if (index >= 0) state.wines[index] = result.wine;
    saleForm.hidden = true;
    saleForm.reset();
    renderWineSuggestions();
    renderCellar();
    await renderInsights();
    openDetail(result.wine);
  } catch (error) {
    alert(t("saleUnable", { error: error.message }));
  }
}

async function exportData() {
  const data = await api("/api/export");
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "wine-cellar.json";
  link.click();
  URL.revokeObjectURL(url);
}

function importData(file) {
  const reader = new FileReader();
  reader.addEventListener("load", async () => {
    try {
      const parsed = JSON.parse(reader.result);
      state.wines = await api("/api/import", { method: "POST", body: JSON.stringify(parsed) });
      renderWineSuggestions();
      renderCellar();
      showScreen("cellar");
    } catch {
      alert(t("importInvalid"));
    }
  });
  reader.readAsText(file);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttribute(value) {
  return escapeHtml(value).replaceAll("`", "&#096;");
}

document.querySelector("#new-wine-button").addEventListener("click", () => openForm());
wineNameInput.addEventListener("change", () => applyWineTemplate(matchingWineTemplate(wineNameInput.value)));
wineNameInput.addEventListener("blur", () => applyWineTemplate(matchingWineTemplate(wineNameInput.value)));
document.querySelector("#add-owner-button").addEventListener("click", () => addOwnerRow());
document.querySelector("#add-score-button").addEventListener("click", () => addScoreRow());
languageButton.addEventListener("click", () => {
  state.lang = state.lang === "it" ? "en" : "it";
  localStorage.setItem("wine-cellar-language", state.lang);
  applyTranslations();
});
cellarSearch.addEventListener("input", () => {
  state.search = cellarSearch.value;
  renderCellar();
});
document.querySelectorAll("[data-insight-tab]").forEach((button) => {
  button.addEventListener("click", () => {
    const tab = button.dataset.insightTab;
    document.querySelectorAll("[data-insight-tab]").forEach((item) => item.classList.toggle("active", item === button));
    document.querySelectorAll(".insight-panel").forEach((panel) => {
      panel.classList.toggle("active", panel.id === `insight-${tab}`);
    });
  });
});
document.querySelector("#cancel-form-button").addEventListener("click", () => {
  if (state.formReturn === "detail") {
    openDetail(state.wines.find((wine) => wine.id === state.selectedWineId));
    return;
  }
  showScreen("cellar");
});
document.querySelector("#back-detail-button").addEventListener("click", () => showScreen("cellar"));
document.querySelector("#edit-detail-button").addEventListener("click", () => {
  openForm(state.wines.find((wine) => wine.id === state.selectedWineId));
});
drinkButton.addEventListener("click", () => {
  drinkBottle().catch((error) => {
    drinkButton.disabled = false;
    alert(t("unableBottleCount", { error: error.message }));
  });
});
showSaleFormButton.addEventListener("click", () => {
  saleForm.hidden = !saleForm.hidden;
  if (!saleForm.hidden) {
    const wine = state.wines.find((item) => item.id === state.selectedWineId);
    saleForm.elements.currency.value = wine?.currency || "CHF";
    saleForm.elements.quantity.value = 1;
  }
});
document.querySelector("#cancel-sale-button").addEventListener("click", () => {
  saleForm.hidden = true;
  saleForm.reset();
});
saleForm.addEventListener("submit", saveSale);
document.querySelector("#export-button").addEventListener("click", exportData);
document.querySelector("#import-input").addEventListener("change", (event) => {
  const [file] = event.target.files;
  if (file) importData(file);
  event.target.value = "";
});

deleteButton.addEventListener("click", deleteCurrentWine);
form.addEventListener("submit", handleSubmit);

document.querySelectorAll(".nav-item").forEach((button) => {
  button.addEventListener("click", () => showScreen(button.dataset.screen));
});

document.querySelectorAll("[data-filter]").forEach((button) => {
  button.addEventListener("click", () => {
    state.filter = button.dataset.filter;
    document.querySelectorAll("[data-filter]").forEach((item) => item.classList.toggle("active", item === button));
    renderCellar();
  });
});

wineList.addEventListener("click", (event) => {
  const card = event.target.closest(".wine-card");
  if (!card) return;
  openDetail(state.wines.find((wine) => wine.id === card.dataset.id));
});

applyTranslations();
loadWines().catch((error) => {
  wineList.innerHTML = `<p class="empty-state">${escapeHtml(error.message)}</p>`;
});
