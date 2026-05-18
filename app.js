const THEME_OPTIONS = [
  { id: "classic", color: "#74171b" },
  { id: "graphite", color: "#8f2431" },
  { id: "alpine", color: "#2f6652" },
  { id: "midnight", color: "#a63d4a" },
  { id: "dusk", color: "#8f4a58" },
  { id: "champagne", color: "#9f5d16" },
];
const THEME_IDS = new Set(THEME_OPTIONS.map((theme) => theme.id));
const requestedTheme = normalizeTheme(new URLSearchParams(window.location.search).get("theme"));
const APP_LOCK_BACKGROUND_GRACE_MS = 20000;

const state = {
  wines: [],
  filter: "All",
  ownerFilter: "All",
  quantityFilter: "Available",
  sort: "delivery-desc",
  insightFilter: null,
  selectedWineId: null,
  selectedWishlistId: null,
  formReturn: "cellar",
  lang: localStorage.getItem("wine-cellar-language") || "it",
  catalog: [],
  wishlist: [],
  movements: [],
  search: "",
  role: "anonymous",
  authEnabled: false,
  appLockSuppressed: false,
  passkeysEnabled: false,
  passkeyAvailable: false,
  passkeyRegistered: false,
  settings: null,
  theme: requestedTheme || normalizeTheme(localStorage.getItem("wine-cellar-theme")) || "classic",
  wishlistStrategies: {},
  drinkNowCollapsed: {
    dontWait: true,
    ideal: true,
    pastIdeal: true,
    ready: true,
    unknown: true,
    wait: true,
  },
};

let installPromptEvent = null;
let appLockTimer = null;

const translations = {
  en: {
    addOwner: "Add Owner",
    addScore: "Add Score",
    addWine: "+ Add Wine",
    aiNotes: "AI Notes",
    aiModelsHelp: "Choose the OpenAI model for each AI feature. Recommendations help balance quality, speed, and cost.",
    aiModelsTitle: "AI models",
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
    addWishlistItem: "+ Add",
    adminSettings: "Admin",
    buyer: "Buyer",
    cellar: "Cellar",
    cellarValue: "Cellar Value",
    color: "Color",
    clearFilter: "Clear filter",
    currentPositionValue: "Current Position Value",
    currentValueShort: "Current",
    currentUnitValue: "Current Unit Value",
    currentValue: "Current Value",
    currentValuePerUnit: "Current Value per Unit",
    convertedRates: "Converted to CHF using {source} from {date}.",
    consumedBottles: "Bottles Drunk",
    consumedValue: "Consumed Value",
    currency: "Currency",
    delete: "Delete",
    delivered: "Delivered",
    dessert: "Dessert",
    drinkCategoryDinner: "Dinner",
    drinkCategoryEveryday: "Everyday",
    drinkCategoryGreatBottle: "Great bottle",
    drinkCategoryReady: "Ready",
    drinkDecline: "Past peak",
    drinkNow: "Drink Now",
    drinkNowEmpty: "No delivered bottles with quantity available.",
    drinkNowListTab: "List",
    drinkNowNav: "What to drink?",
    drinkNowReasonDecline: "Past the estimated window",
    drinkNowReasonIdeal: "Inside the ideal window",
    drinkNowReasonMissing: "No drinking window yet",
    drinkNowReasonPastIdeal: "Past the ideal window",
    drinkNowReasonReady: "Inside the drinking window",
    drinkNowReasonWait: "Better to wait",
    drinkNowSectionDontWait: "Do not wait",
    drinkNowSectionIdeal: "Ideal now",
    drinkNowSectionPastIdeal: "Past ideal",
    drinkNowSectionReady: "Ready",
    drinkNowSectionWait: "Too young",
    drinkNowSectionUnknown: "No window",
    drinkNowStatus: "Status",
    drinkNowWindow: "Window",
    drinkPeak: "Ideal",
    drinkConfirm: "Mark one bottle of {wine} as drunk?",
    drinkNotePrompt: "Optional note for this bottle",
    drinkWindow: "Drinking Window",
    drinkWindowEstimate: "AI estimate",
    drinkWindowMissing: "No drinking window generated.",
    drinkWindowYear: "Current year",
    drinkYoung: "Young",
    drankOne: "Drank 1",
    edit: "Edit",
    emptyFilter: "No wines found for this filter.",
    emptyInsightFilter: "No wines found for {filter}.",
    emptyOwnership: "No ownership data.",
    emptyWishlist: "Your wishlist is empty.",
    exchangeUnavailable: "Exchange rates unavailable: {error}",
    expected: "Expected",
    expectedDelivery: "Expected Delivery",
    export: "Export",
    filters: "Filters",
    filterActive: "Filter: {filter}",
    format: "Format",
    formatBottle: "Bottle (750ml)",
    formatHalf: "Half (375ml)",
    formatMagnum: "Magnum (1.5L)",
    generateAiNotes: "Generate",
    generateAiNotesConfirm: "Replace the current AI notes?",
    generateAiNotesUnable: "Unable to generate AI notes: {error}",
    generateAiValue: "Estimate Value",
    generateAiValueConfirm: "Replace the current unit value with an AI estimate?",
    generateAiValueUnable: "Unable to estimate current value: {error}",
    generateDrinkWindow: "Generate",
    generateDrinkWindowConfirm: "Replace the current drinking window?",
    generateDrinkWindowUnable: "Unable to generate drinking window: {error}",
    import: "Import",
    historyNav: "History",
    installApp: "Install",
    importInvalid: "The selected file does not contain a valid cellar.",
    insights: "Insights",
    invalidLogin: "Invalid password.",
    latestRates: "latest rates",
    login: "Login",
    loginPrompt: "Enter your password to continue.",
    logout: "Logout",
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
    onlyMine: "Only Mine",
    orderDate: "Order Date",
    ordered: "Ordered",
    otherOwners: "Other Owners",
    ownerName: "Owner name",
    ownership: "Ownership",
    password: "Password",
    passkeyLogin: "Use passkey",
    passkeyRegister: "Enable passkey",
    passkeyRegistered: "Passkey enabled.",
    passkeyHelp: "Use Face ID, Touch ID, fingerprint, or device unlock for login.",
    passkeyTitle: "Passkey",
    passkeyUnavailable: "Passkeys are not available in this browser or connection.",
    pairing: "Pairing",
    pairingCellarMatches: "From your cellar",
    pairingDish: "Dish or food",
    pairingEmptyDish: "Enter a dish first.",
    pairingIncludeMarket: "Also show 2 bottles outside my cellar",
    pairingMarketFallback: "Suggested bottles to buy",
    pairingMarketOnly: "Restaurant mode: ignore my cellar",
    pairingModelUsed: "Model used: {model}",
    pairingNoCellarMatch: "No ideal bottle found in your cellar.",
    pairingPlaceholder: "E.g. mushroom risotto, braised beef, sushi",
    pairingSubmit: "Find pairing",
    pairingUnable: "Unable to suggest a pairing: {error}",
    pairingWhy: "Why",
    pairingModelHelp: "Choose the OpenAI model used for pairing requests. More expensive models can give more accurate answers.",
    pairingModelLegend: "Model",
    pairingModelSaved: "Settings saved.",
    pairingModelTitle: "Pairing model",
    settingsFunctionAiNotes: "AI notes",
    settingsFunctionAiNotesHelp: "Generates the short descriptive note on the wine detail page.",
    settingsFunctionAiValue: "Value estimate",
    settingsFunctionAiValueHelp: "Estimates the current bottle value and the short pricing note.",
    settingsFunctionDrinkWindow: "Drinking window",
    settingsFunctionDrinkWindowHelp: "Estimates the drinking window, peak years, and supporting note.",
    settingsFunctionPairing: "Pairing",
    settingsFunctionPairingHelp: "Suggests cellar and market bottles for a dish.",
    settingsFunctionWishlistStrategy: "Wishlist strategy",
    settingsFunctionWishlistStrategyHelp: "Generates the short buy, monitor, or avoid suggestion for wishlist items.",
    settingsRecommended: "Recommended: {model}",
    themeClassic: "Classic cellar",
    themeGraphite: "Graphite",
    themeAlpine: "Alpine",
    themeMidnight: "Midnight",
    themeDusk: "Dusk",
    themeChampagne: "Champagne",
    themeClassicDescription: "Warm paper, burgundy accents and the current look.",
    themeGraphiteDescription: "Neutral, sharper and compact, with ruby accents.",
    themeAlpineDescription: "Clean and bright, with green and mineral accents.",
    themeMidnightDescription: "Dark, high contrast, designed for evening use.",
    themeDuskDescription: "Softer dark theme, with warm graphite surfaces and lower contrast.",
    themeChampagneDescription: "Light and soft, with gold and rose accents.",
    themeHelp: "You can also apply a theme by opening the app with ?theme=classic, graphite, alpine, midnight, dusk or champagne.",
    themeLegend: "Theme",
    priceRequired: "Price per Unit *",
    priority: "Priority",
    priorityHigh: "High",
    priorityLow: "Low",
    priorityMedium: "Medium",
    producerRequired: "Producer *",
    quantity: "Quantity",
    quantityAvailable: "Available",
    quantityEmpty: "Empty",
    quantityFilter: "Quantity:",
    quantityRequired: "Quantity *",
    region: "Region",
    remove: "Remove",
    rose: "Rose",
    saveOrder: "Save Order",
    saveSale: "Save Sale",
    saveSettings: "Save settings",
    saveWishlistItem: "Save",
    saveUnable: "Unable to save order: {error}",
    salePrice: "Sale Price",
    realizedGainLoss: "Realized P/L",
    sales: "Sales",
    soldTo: "Sold to {buyer}",
    soldBottles: "Bottles Sold",
    soldRevenue: "Sale Revenue",
    saleProfit: "Profit",
    saleLoss: "Loss",
    noSales: "No sales recorded.",
    movementDrink: "Drunk",
    movementEmpty: "No bottle movements recorded.",
    movementCancel: "Cancel",
    movementCancelConfirm: "Cancel this movement and restore the bottle quantity?",
    movementEdit: "Edit",
    movementEditNotePrompt: "Note",
    movementEditQuantityPrompt: "Quantity",
    movementHistory: "Bottle Movements",
    movementStats: "Movements",
    movementSale: "Sold",
    movementAdjustment: "Adjustment",
    movementArrival: "Arrival",
    movementUnable: "Unable to update movement: {error}",
    notes: "Notes",
    resultsCount: "{count} {bottles}",
    saleUnable: "Unable to save sale: {error}",
    searchPlaceholder: "Search wine, producer, region",
    score: "Score",
    scoreNote: "Note",
    scores: "Scores",
    suggestScores: "Suggest",
    suggestScoresEmpty: "No reliable score suggestions found.",
    suggestScoresUnable: "Unable to suggest scores: {error}",
    suggestedScoresAdded: "{count} score suggestions added to the edit form. Review and save to confirm.",
    critic: "Critic",
    shipped: "Shipped",
    sparkling: "Sparkling",
    status: "Status",
    statusLabel: "Status:",
    timeline: "Timeline",
    timelineNav: "Timeline e En Primeur",
    targetPrice: "Target Price",
    estimatedMarketRange: "AI Estimated Range",
    priceAssessmentAi: "AI Price Assessment",
    topRegions: "Top Regions",
    topConsumedRegions: "Top Drunk Regions",
    topColors: "Top Colors",
    sharedPositions: "Shared Positions",
    shared: "Shared",
    sortBy: "Sort by",
    sortDeliveryDesc: "Newest arrival",
    sortNameAsc: "Wine name A-Z",
    sortProducerAsc: "Producer A-Z",
    sortTypeAsc: "Type / color",
    sortValueDesc: "Highest value",
    sortVintageDesc: "Newest vintage",
    totalPositions: "Total Positions",
    totalPositionValue: "Total Position Value",
    totalCurrentPositionValue: "Total Current Position Value",
    totalPositionCost: "Total Position Cost",
    totalBottlesInCellar: "Total Bottles In Cellar",
    totalBottlesOnOrder: "Total Bottles On Order",
    totalInvested: "Total Invested",
    grossCurrentValue: "Current Total Value",
    topRegionsShared: "Top Regions - Shared",
    topRegionsAll: "Top Regions - All Owners",
    type: "Type",
    unableBottleCount: "Unable to update bottle count: {error}",
    unitPrice: "Unit Price",
    unrealizedGainLoss: "Unrealized P/L",
    values: "Values",
    vintageRequired: "Vintage *",
    white: "White",
    wishlist: "Wishlist",
    wishlistBuy: "Buy",
    wishlistEvaluate: "Evaluate",
    wishlistMonitor: "Monitor",
    wishlistPurpose: "Purpose",
    wishlistPurposeCellar: "Cellar",
    wishlistPurposeCompare: "Compare",
    wishlistPurposeDrink: "Drink",
    wishlistPurposeGift: "Gift",
    wishlistPurposeInvest: "Investment",
    wishlistStrategy: "AI Strategy",
    wishlistStrategyAlternative: "Alternative",
    wishlistStrategyAvoid: "Avoid",
    wishlistStrategyBuy: "Buy",
    wishlistStrategyLoading: "Building strategy...",
    wishlistStrategyMonitor: "Monitor",
    wishlistStrategySources: "Sources",
    wishlistStrategyUnable: "Unable to generate strategy: {error}",
    wishlistStatusAi: "AI",
    wishlistStatusAiLong: "Set by AI",
    wishlistSkipped: "Skipped",
    wineNameRequired: "Wine Name *",
    autofilled: "Wine details autofilled from your cellar history.",
    red: "Red",
  },
  it: {
    addOwner: "Aggiungi proprietario",
    addScore: "Aggiungi punteggio",
    addWine: "+ Aggiungi vino",
    aiNotes: "Note AI",
    aiModelsHelp: "Scegli il modello OpenAI per ciascuna funzione AI. Le raccomandazioni aiutano a bilanciare qualita, velocita e costo.",
    aiModelsTitle: "Modelli AI",
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
    addWishlistItem: "+ Aggiungi",
    adminSettings: "Admin",
    buyer: "Acquirente",
    cellar: "Cantina",
    cellarValue: "Valore cantina",
    color: "Colore",
    clearFilter: "Rimuovi filtro",
    currentPositionValue: "Valore attuale posizione",
    currentValueShort: "Attuale",
    currentUnitValue: "Valore unitario attuale",
    currentValue: "Valore attuale",
    currentValuePerUnit: "Valore attuale unitario",
    convertedRates: "Convertito in CHF con {source} del {date}.",
    consumedBottles: "Bottiglie bevute",
    consumedValue: "Valore consumato",
    currency: "Valuta",
    delete: "Elimina",
    delivered: "In cantina",
    dessert: "Dolce",
    drinkCategoryDinner: "Cena",
    drinkCategoryEveryday: "Quotidiano",
    drinkCategoryGreatBottle: "Grande bottiglia",
    drinkCategoryReady: "Pronto",
    drinkDecline: "Oltre apice",
    drinkNow: "Da bere ora",
    drinkNowEmpty: "Nessuna bottiglia in cantina con quantita disponibile.",
    drinkNowListTab: "Lista",
    drinkNowNav: "Cosa bere?",
    drinkNowReasonDecline: "Oltre la finestra stimata",
    drinkNowReasonIdeal: "Dentro la finestra ideale",
    drinkNowReasonMissing: "Finestra degustazione assente",
    drinkNowReasonPastIdeal: "Oltre la finestra ideale",
    drinkNowReasonReady: "Dentro la finestra di degustazione",
    drinkNowReasonWait: "Meglio aspettare",
    drinkNowSectionDontWait: "Da non aspettare",
    drinkNowSectionIdeal: "Ideale ora",
    drinkNowSectionPastIdeal: "Oltre ideale",
    drinkNowSectionReady: "Pronto",
    drinkNowSectionWait: "Troppo giovane",
    drinkNowSectionUnknown: "Senza finestra",
    drinkNowStatus: "Stato",
    drinkNowWindow: "Finestra",
    drinkPeak: "Ideale",
    drinkConfirm: "Segnare una bottiglia di {wine} come bevuta?",
    drinkNotePrompt: "Nota opzionale per questa bottiglia",
    drinkWindow: "Finestra degustazione",
    drinkWindowEstimate: "Stima AI",
    drinkWindowMissing: "Nessuna finestra di degustazione generata.",
    drinkWindowYear: "Anno corrente",
    drinkYoung: "Giovane",
    drankOne: "Bevuta 1",
    edit: "Modifica",
    emptyFilter: "Nessun vino trovato per questo filtro.",
    emptyInsightFilter: "Nessun vino trovato per {filter}.",
    emptyOwnership: "Nessun dato di proprietà.",
    emptyWishlist: "La wishlist e vuota.",
    exchangeUnavailable: "Cambi non disponibili: {error}",
    expected: "Previsto",
    expectedDelivery: "Consegna prevista",
    export: "Esporta",
    filters: "Filtri",
    filterActive: "Filtro: {filter}",
    format: "Formato",
    formatBottle: "Bottiglia (750ml)",
    formatHalf: "Mezza (375ml)",
    formatMagnum: "Magnum (1.5L)",
    generateAiNotes: "Genera",
    generateAiNotesConfirm: "Sostituire le Note AI attuali?",
    generateAiNotesUnable: "Impossibile generare le Note AI: {error}",
    generateAiValue: "Stima valore",
    generateAiValueConfirm: "Sostituire il valore unitario attuale con una stima AI?",
    generateAiValueUnable: "Impossibile stimare il valore attuale: {error}",
    generateDrinkWindow: "Genera",
    generateDrinkWindowConfirm: "Sostituire la finestra di degustazione attuale?",
    generateDrinkWindowUnable: "Impossibile generare la finestra di degustazione: {error}",
    import: "Importa",
    historyNav: "Storico",
    installApp: "Installa",
    importInvalid: "Il file selezionato non contiene una cantina valida.",
    insights: "Statistiche",
    invalidLogin: "Password non valida.",
    latestRates: "ultimi cambi",
    login: "Accedi",
    loginPrompt: "Inserisci la password per continuare.",
    logout: "Esci",
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
    onlyMine: "Solo miei",
    orderDate: "Data ordine",
    ordered: "Ordinato",
    otherOwners: "Altri proprietari",
    ownerName: "Nome proprietario",
    ownership: "Proprietà",
    password: "Password",
    passkeyLogin: "Usa passkey",
    passkeyRegister: "Attiva passkey",
    passkeyRegistered: "Passkey attivata.",
    passkeyHelp: "Usa Face ID, Touch ID, impronta o sblocco dispositivo per accedere.",
    passkeyTitle: "Passkey",
    passkeyUnavailable: "Le passkey non sono disponibili in questo browser o connessione.",
    pairing: "Abbinamento",
    pairingCellarMatches: "Dalla tua cantina",
    pairingDish: "Piatto o pietanza",
    pairingEmptyDish: "Inserisci prima un piatto.",
    pairingIncludeMarket: "Mostra anche 2 proposte fuori cantina",
    pairingMarketFallback: "Bottiglie suggerite da acquistare",
    pairingMarketOnly: "Sono al ristorante: ignora la mia cantina",
    pairingModelUsed: "Modello usato: {model}",
    pairingNoCellarMatch: "Nessuna bottiglia ideale trovata in cantina.",
    pairingPlaceholder: "Es. risotto ai funghi, brasato, sushi",
    pairingSubmit: "Trova abbinamento",
    pairingUnable: "Impossibile suggerire un abbinamento: {error}",
    pairingWhy: "Perché",
    pairingModelHelp: "Scegli il modello OpenAI usato per la richiesta di abbinamento. Modelli piu costosi possono dare risposte piu accurate.",
    pairingModelLegend: "Modello",
    pairingModelSaved: "Impostazioni salvate.",
    pairingModelTitle: "Modello abbinamenti",
    settingsFunctionAiNotes: "Note AI",
    settingsFunctionAiNotesHelp: "Genera la nota descrittiva breve nella pagina dettaglio del vino.",
    settingsFunctionAiValue: "Stima valore",
    settingsFunctionAiValueHelp: "Stima il valore attuale della bottiglia e la nota sintetica di valutazione.",
    settingsFunctionDrinkWindow: "Finestra degustazione",
    settingsFunctionDrinkWindowHelp: "Stima finestra di bevuta, anni ideali e nota di supporto.",
    settingsFunctionPairing: "Abbinamento",
    settingsFunctionPairingHelp: "Suggerisce bottiglie dalla cantina e dal mercato per un piatto.",
    settingsFunctionWishlistStrategy: "Strategia wishlist",
    settingsFunctionWishlistStrategyHelp: "Genera il suggerimento breve compra, monitora o evita per i vini in wishlist.",
    settingsRecommended: "Consigliato: {model}",
    themeClassic: "Classic cellar",
    themeGraphite: "Graphite",
    themeAlpine: "Alpine",
    themeMidnight: "Midnight",
    themeDusk: "Dusk",
    themeChampagne: "Champagne",
    themeClassicDescription: "Carta calda, accenti bordeaux e look attuale.",
    themeGraphiteDescription: "Neutro, piu tecnico e compatto, con accenti rubino.",
    themeAlpineDescription: "Chiaro e pulito, con accenti verdi e minerali.",
    themeMidnightDescription: "Scuro, alto contrasto, pensato per uso serale.",
    themeDuskDescription: "Scuro piu morbido, con fondo grafite caldo e contrasto meno marcato.",
    themeChampagneDescription: "Luminoso e morbido, con accenti dorati e rosa.",
    themeHelp: "Puoi anche applicare un tema aprendo l'app con ?theme=classic, graphite, alpine, midnight, dusk o champagne.",
    themeLegend: "Tema",
    priceRequired: "Prezzo unitario *",
    priority: "Priorita",
    priorityHigh: "Alta",
    priorityLow: "Bassa",
    priorityMedium: "Media",
    producerRequired: "Produttore *",
    quantity: "Quantità",
    quantityAvailable: "Disponibili",
    quantityEmpty: "Finite",
    quantityFilter: "Quantità:",
    quantityRequired: "Quantità *",
    region: "Regione",
    remove: "Rimuovi",
    rose: "Rosé",
    saveOrder: "Salva ordine",
    saveSale: "Salva vendita",
    saveSettings: "Salva impostazioni",
    saveWishlistItem: "Salva",
    saveUnable: "Impossibile salvare l'ordine: {error}",
    salePrice: "Prezzo vendita",
    realizedGainLoss: "Utile/perdita realizzata",
    sales: "Vendite",
    soldTo: "Venduto a {buyer}",
    soldBottles: "Bottiglie vendute",
    soldRevenue: "Ricavi vendita",
    saleProfit: "Utile",
    saleLoss: "Perdita",
    noSales: "Nessuna vendita registrata.",
    movementDrink: "Bevuta",
    movementEmpty: "Nessun movimento bottiglie registrato.",
    movementCancel: "Annulla",
    movementCancelConfirm: "Annullare questo movimento e ripristinare la quantità?",
    movementEdit: "Modifica",
    movementEditNotePrompt: "Nota",
    movementEditQuantityPrompt: "Quantità",
    movementHistory: "Movimenti bottiglie",
    movementStats: "Movimenti",
    movementSale: "Vendita",
    movementAdjustment: "Rettifica",
    movementArrival: "Arrivo",
    movementUnable: "Impossibile aggiornare il movimento: {error}",
    notes: "Note",
    resultsCount: "{count} {bottles}",
    saleUnable: "Impossibile salvare la vendita: {error}",
    searchPlaceholder: "Cerca vino, produttore, regione",
    score: "Punteggio",
    scoreNote: "Nota",
    scores: "Punteggi",
    suggestScores: "Suggerisci",
    suggestScoresEmpty: "Nessun suggerimento affidabile trovato.",
    suggestScoresUnable: "Impossibile suggerire punteggi: {error}",
    suggestedScoresAdded: "{count} suggerimenti aggiunti al form. Verifica e salva per confermare.",
    critic: "Critico",
    shipped: "Spedito",
    sparkling: "Spumante",
    status: "Stato",
    statusLabel: "Stato:",
    timeline: "Timeline",
    timelineNav: "Timeline e En Primeur",
    targetPrice: "Prezzo obiettivo",
    estimatedMarketRange: "Fascia stimata AI",
    priceAssessmentAi: "Valutazione prezzo AI",
    topRegions: "Regioni principali",
    topConsumedRegions: "Regioni piu bevute",
    topColors: "Colori principali",
    sharedPositions: "Posizioni condivise",
    shared: "Condivisi",
    sortBy: "Ordina per",
    sortDeliveryDesc: "Arrivo piu recente",
    sortNameAsc: "Nome vino A-Z",
    sortProducerAsc: "Produttore A-Z",
    sortTypeAsc: "Tipo / colore",
    sortValueDesc: "Valore piu alto",
    sortVintageDesc: "Annata piu recente",
    totalPositions: "Posizioni totali",
    totalPositionValue: "Valore totale posizioni",
    totalCurrentPositionValue: "Valore attuale posizione totale",
    totalPositionCost: "Costo posizione totale",
    totalBottlesInCellar: "Bottiglie totali in cantina",
    totalBottlesOnOrder: "Bottiglie totali ordinate",
    totalInvested: "Totale investito",
    grossCurrentValue: "Valore attuale totale",
    topRegionsShared: "Regioni principali - condivise",
    topRegionsAll: "Regioni principali - tutti",
    type: "Tipo",
    unableBottleCount: "Impossibile aggiornare il numero di bottiglie: {error}",
    unitPrice: "Prezzo unitario",
    unrealizedGainLoss: "Utile/perdita potenziale",
    values: "Valori",
    vintageRequired: "Annata *",
    white: "Bianco",
    wishlist: "Wishlist",
    wishlistBuy: "Comprare",
    wishlistEvaluate: "Valutare",
    wishlistMonitor: "Monitorare",
    wishlistPurpose: "Scopo",
    wishlistPurposeCellar: "Cantina",
    wishlistPurposeCompare: "Confronto",
    wishlistPurposeDrink: "Da bere",
    wishlistPurposeGift: "Regalo",
    wishlistPurposeInvest: "Investimento",
    wishlistStrategy: "Strategia AI",
    wishlistStrategyAlternative: "Alternativa",
    wishlistStrategyAvoid: "Evita",
    wishlistStrategyBuy: "Compra",
    wishlistStrategyLoading: "Sto preparando la strategia...",
    wishlistStrategyMonitor: "Monitora",
    wishlistStrategySources: "Fonti",
    wishlistStrategyUnable: "Impossibile generare la strategia: {error}",
    wishlistStatusAi: "AI",
    wishlistStatusAiLong: "Impostato da AI",
    wishlistSkipped: "Scartato",
    wineNameRequired: "Nome vino *",
    autofilled: "Dati vino completati dalla tua cronologia.",
    red: "Rosso",
  },
};

const screens = {
  login: document.querySelector("#screen-login"),
  cellar: document.querySelector("#screen-cellar"),
  timeline: document.querySelector("#screen-timeline"),
  drinkNow: document.querySelector("#screen-drink-now"),
  insights: document.querySelector("#screen-insights"),
  wishlist: document.querySelector("#screen-wishlist"),
  history: document.querySelector("#screen-history"),
  settings: document.querySelector("#screen-settings"),
  detail: document.querySelector("#screen-detail"),
  form: document.querySelector("#screen-form"),
};

const wineList = document.querySelector("#wine-list");
const wishlistList = document.querySelector("#wishlist-list");
const wishlistForm = document.querySelector("#wishlist-form");
const wishlistNameInput = document.querySelector("#wishlist-name");
const deleteWishlistButton = document.querySelector("#delete-wishlist-button");
const loginForm = document.querySelector("#login-form");
const loginError = document.querySelector("#login-error");
const cellarSearch = document.querySelector("#cellar-search");
const cellarSort = document.querySelector("#cellar-sort");
const filterToggle = document.querySelector("#filter-toggle");
const filterPanel = document.querySelector("#filter-panel");
const filterCount = document.querySelector("#filter-count");
const activeInsightFilter = document.querySelector("#active-insight-filter");
const timelineList = document.querySelector("#timeline-list");
const drinkNowList = document.querySelector("#drink-now-list");
const drinkNowListPanel = document.querySelector("#drink-now-list-panel");
const drinkNowPairingPanel = document.querySelector("#drink-now-pairing-panel");
const pairingForm = document.querySelector("#pairing-form");
const pairingResult = document.querySelector("#pairing-result");
const settingsForm = document.querySelector("#settings-form");
const aiModelSettings = document.querySelector("#ai-model-settings");
const settingsPricingNote = document.querySelector("#settings-pricing-note");
const regionList = document.querySelector("#region-list");
const colorList = document.querySelector("#color-list");
const sharedRegionList = document.querySelector("#shared-region-list");
const sharedColorList = document.querySelector("#shared-color-list");
const grossRegionList = document.querySelector("#gross-region-list");
const grossColorList = document.querySelector("#gross-color-list");
const movementConsumedRegionList = document.querySelector("#movement-consumed-region-list");
const form = document.querySelector("#wine-form");
const deleteButton = document.querySelector("#delete-button");
const drinkButton = document.querySelector("#drink-bottle-button");
const generateAiNotesButton = document.querySelector("#generate-ai-notes-button");
const generateDrinkWindowButton = document.querySelector("#generate-drink-window-button");
const generateAiValueButton = document.querySelector("#generate-ai-value-button");
const suggestAiScoresButton = document.querySelector("#suggest-ai-scores-button");
const ownersFormList = document.querySelector("#owners-form-list");
const scoresFormList = document.querySelector("#scores-form-list");
const bottomNav = document.querySelector(".bottom-nav");
const installAppButton = document.querySelector("#install-app-button");
const languageButton = document.querySelector("#language-button");
const passkeyLoginButton = document.querySelector("#passkey-login-button");
const passkeyRegisterButton = document.querySelector("#passkey-register-button");
const saleForm = document.querySelector("#sale-form");
const showSaleFormButton = document.querySelector("#show-sale-form-button");
const saleList = document.querySelector("#sale-list");
const movementList = document.querySelector("#movement-list");
const historyList = document.querySelector("#history-list");
const wineNameInput = document.querySelector("#name");
const wineNameSuggestions = document.querySelector("#wine-name-suggestions");
const themeOptions = document.querySelector("#theme-options");
const themeColorMeta = document.querySelector("meta[name='theme-color']");

function normalizeTheme(theme) {
  return THEME_IDS.has(theme) ? theme : "";
}

function themeLabelKey(themeId) {
  return `theme${themeId.charAt(0).toUpperCase()}${themeId.slice(1)}`;
}

function themeDescriptionKey(themeId) {
  return `${themeLabelKey(themeId)}Description`;
}

function applyTheme(themeId) {
  const theme = normalizeTheme(themeId) || "classic";
  state.theme = theme;
  document.body.dataset.theme = theme;
  localStorage.setItem("wine-cellar-theme", theme);
  const option = THEME_OPTIONS.find((item) => item.id === theme);
  if (themeColorMeta && option?.color) themeColorMeta.setAttribute("content", option.color);
}

applyTheme(state.theme);

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
  if (currentScreen === "drinkNow") renderDrinkNow();
  if (currentScreen === "insights") renderInsights();
  if (currentScreen === "wishlist") renderWishlist();
  if (currentScreen === "history") renderHistory();
  if (currentScreen === "detail") openDetail(state.wines.find((wine) => wine.id === state.selectedWineId));
  if (currentScreen === "form") {
    document.querySelector("#form-title").textContent = form.elements.id.value ? t("edit") : t("newOrder");
  }
  if (currentScreen === "detail") {
    renderSales(state.selectedWineId);
    renderMovements(state.selectedWineId);
  }
  applyPermissions();
}

function statusLabel(status) {
  return t({ Ordered: "ordered", Shipped: "shipped", Delivered: "delivered" }[status] || "notSpecified");
}

function typeLabel(type) {
  return t({ Red: "red", White: "white", Rose: "rose", Sparkling: "sparkling", Dessert: "dessert" }[type] || "notSpecified");
}

function hasRoseCue(wine) {
  return [wine.name, wine.producer, wine.region, wine.appellation]
    .filter(Boolean)
    .some((value) => {
      const normalized = String(value).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
      return /(^|[^a-z])rose([^a-z]|$)|(^|[^a-z])rosato([^a-z]|$)/.test(normalized);
    });
}

function cardVisualType(wine) {
  if (hasRoseCue(wine)) return "Rose";
  return wine.type;
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

function isAdmin() {
  return state.role === "admin";
}

function isSharedViewer() {
  return state.role === "shared_viewer";
}

function isAuthenticated() {
  return !state.authEnabled || state.role !== "anonymous";
}

function clearAuthenticatedState() {
  state.role = state.authEnabled ? "anonymous" : "admin";
  state.wines = [];
  state.wishlist = [];
  state.movements = [];
  state.settings = null;
  state.selectedWineId = null;
  state.selectedWishlistId = null;
  state.wishlistStrategies = {};
  state.passkeyRegistered = false;
}

function sendLogoutBeacon() {
  const body = new Blob(["{}"], { type: "application/json" });
  if (navigator.sendBeacon && navigator.sendBeacon("/api/logout", body)) return;
  fetch("/api/logout", {
    method: "POST",
    body: "{}",
    headers: { "Content-Type": "application/json" },
    keepalive: true,
  }).catch(() => {});
}

function lockApplication() {
  if (!state.authEnabled || !isAuthenticated() || state.appLockSuppressed) return;
  cancelScheduledApplicationLock();
  sendLogoutBeacon();
  clearAuthenticatedState();
  applyPermissions();
  showScreen("login");
}

function cancelScheduledApplicationLock() {
  if (!appLockTimer) return;
  window.clearTimeout(appLockTimer);
  appLockTimer = null;
}

function scheduleApplicationLock() {
  if (!state.authEnabled || !isAuthenticated() || state.appLockSuppressed || appLockTimer) return;
  appLockTimer = window.setTimeout(() => {
    appLockTimer = null;
    if (document.visibilityState === "hidden") lockApplication();
  }, APP_LOCK_BACKGROUND_GRACE_MS);
}

function browserSupportsPasskeys() {
  return window.isSecureContext && "PublicKeyCredential" in window && navigator.credentials;
}

function applyPermissions() {
  document.body.dataset.role = state.role;
  document.querySelectorAll(".admin-only").forEach((element) => {
    element.hidden = !isAdmin();
  });
  const ownershipFilterRow = document.querySelector("#ownership-filter-row");
  if (ownershipFilterRow) ownershipFilterRow.hidden = isSharedViewer();
  document.querySelectorAll("[data-insight-tab]").forEach((button) => {
    button.hidden = isSharedViewer() && button.dataset.insightTab !== "shared";
    button.classList.toggle("active", isSharedViewer() ? button.dataset.insightTab === "shared" : button.dataset.insightTab === "mine");
  });
  document.querySelectorAll(".insight-panel").forEach((panel) => {
    panel.classList.toggle("active", isSharedViewer() ? panel.id === "insight-shared" : panel.id === "insight-mine");
  });
  if (isSharedViewer()) {
    state.ownerFilter = "All";
    document.querySelectorAll("[data-owner-filter]").forEach((item) => {
      item.classList.toggle("active", item.dataset.ownerFilter === "All");
    });
  }
  if (!isAdmin()) showDrinkNowTab("list");
  const showPasskeys = state.passkeysEnabled && browserSupportsPasskeys();
  passkeyLoginButton.hidden = !showPasskeys || !state.passkeyAvailable || isAuthenticated();
  passkeyRegisterButton.hidden = !showPasskeys || !isAuthenticated();
  passkeyRegisterButton.textContent = state.passkeyRegistered ? t("passkeyRegistered") : t("passkeyRegister");
  updateFilterCount();
}

async function loadSession() {
  const session = await api("/api/session");
  state.role = session.role;
  state.authEnabled = session.auth_enabled;
  state.passkeysEnabled = Boolean(session.passkeys_enabled);
  state.passkeyAvailable = Boolean(session.passkey_available);
  state.passkeyRegistered = Boolean(session.passkey_registered);
  if (!requestedTheme && session.app_theme) applyTheme(session.app_theme);
  applyPermissions();
  if (session.auth_enabled && !session.authenticated) {
    showScreen("login");
    return;
  }
  await loadWines();
  showScreen("cellar");
}

async function loadWines() {
  const [wines, catalog, wishlist, movements] = await Promise.all([api("/api/wines"), api("/api/wine-catalog"), api("/api/wishlist"), api("/api/movements")]);
  state.wines = wines;
  state.catalog = catalog;
  state.wishlist = wishlist;
  state.movements = movements;
  renderWineSuggestions();
  renderCellar();
  renderWishlist();
}

async function loadSettings() {
  if (!isAdmin()) return null;
  state.settings = await api("/api/settings");
  renderSettings();
  return state.settings;
}

function formatModelPrice(value) {
  return `$${Number(value).toFixed(2)}/1M`;
}

function aiSettingTitle(key) {
  return t(
    {
      pairing_model: "settingsFunctionPairing",
      ai_notes_model: "settingsFunctionAiNotes",
      drink_window_model: "settingsFunctionDrinkWindow",
      ai_value_model: "settingsFunctionAiValue",
      wishlist_strategy_model: "settingsFunctionWishlistStrategy",
    }[key] || "pairingModelTitle",
  );
}

function aiSettingHelp(key) {
  return t(
    {
      pairing_model: "settingsFunctionPairingHelp",
      ai_notes_model: "settingsFunctionAiNotesHelp",
      drink_window_model: "settingsFunctionDrinkWindowHelp",
      ai_value_model: "settingsFunctionAiValueHelp",
      wishlist_strategy_model: "settingsFunctionWishlistStrategyHelp",
    }[key] || "pairingModelHelp",
  );
}

function renderSettings() {
  if (!state.settings) return;
  const selectedTheme = normalizeTheme(state.settings.app_theme) || state.theme;
  themeOptions.innerHTML = state.settings.theme_options
    .map((option) => {
      const checked = option.id === selectedTheme ? "checked" : "";
      return `
        <label class="theme-option" data-theme-preview="${escapeAttribute(option.id)}">
          <input type="radio" name="app_theme" value="${escapeAttribute(option.id)}" ${checked} />
          <span class="theme-swatch" aria-hidden="true"></span>
          <span>
            <strong>${escapeHtml(t(themeLabelKey(option.id)))}</strong>
            <small>${escapeHtml(t(themeDescriptionKey(option.id)))}</small>
          </span>
        </label>
      `;
    })
    .join("");
  themeOptions.querySelectorAll("input[name='app_theme']").forEach((input) => {
    input.addEventListener("change", () => applyTheme(input.value));
  });
  aiModelSettings.innerHTML = state.settings.ai_model_settings
    .map((setting) => {
      const selectedModel = state.settings.ai_models?.[setting.key] || setting.default;
      const recommended = state.settings.model_options.find((option) => option.id === setting.recommended);
      return `
        <fieldset class="model-options model-setting-group">
          <legend>${escapeHtml(aiSettingTitle(setting.key))}</legend>
          <p class="settings-note">${escapeHtml(aiSettingHelp(setting.key))}</p>
          ${recommended ? `<p class="settings-recommendation">${escapeHtml(t("settingsRecommended", { model: recommended.label }))}</p>` : ""}
          ${state.settings.model_options
            .map((option) => {
              const checked = option.id === selectedModel ? "checked" : "";
              return `
                <label class="model-option">
                  <input type="radio" name="${escapeAttribute(setting.key)}" value="${escapeAttribute(option.id)}" ${checked} />
                  <span>
                    <strong>${escapeHtml(option.label)}</strong>
                    <small>${escapeHtml(option.description)}</small>
                    <em>${escapeHtml(formatModelPrice(option.input_per_million))} input · ${escapeHtml(formatModelPrice(option.output_per_million))} output · ~${escapeHtml(String(option.relative_cost))}x nano</em>
                  </span>
                </label>
              `;
            })
            .join("")}
        </fieldset>
      `;
    })
    .join("");
  settingsPricingNote.textContent = state.settings.pricing_note || "";
}

async function openSettings() {
  if (!isAdmin()) return;
  showScreen("settings");
  await loadSettings();
}

async function saveSettings(event) {
  event.preventDefault();
  const submitButton = settingsForm.querySelector("button[type='submit']");
  const previousText = submitButton.textContent;
  submitButton.disabled = true;
  submitButton.textContent = "...";
  try {
    const aiModelPayload = Object.fromEntries(
      (state.settings?.ai_model_settings || []).map((setting) => [setting.key, settingsForm.elements[setting.key].value]),
    );
    state.settings = await api("/api/settings", {
      method: "POST",
      body: JSON.stringify({
        ...aiModelPayload,
        app_theme: settingsForm.elements.app_theme.value,
      }),
    });
    applyTheme(state.settings.app_theme);
    renderSettings();
    alert(t("pairingModelSaved"));
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = previousText;
  }
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
      return `<option value="${escapeAttribute(wine.name)}" label="${escapeAttribute([wine.name, wine.producer, wine.region, source].filter(Boolean).join(" - "))}"></option>`;
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

function formatDateTime(dateValue) {
  if (!dateValue) return "TBD";
  return new Intl.DateTimeFormat(state.lang === "it" ? "it-IT" : "en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(dateValue));
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

function updateWineInState(wine) {
  const index = state.wines.findIndex((item) => item.id === wine.id);
  if (index >= 0) state.wines[index] = wine;
  else state.wines.unshift(wine);
}

async function refreshAfterInventoryChange(wine) {
  updateWineInState(wine);
  state.movements = await api("/api/movements");
  renderWineSuggestions();
  renderCellar();
  renderDrinkNow();
  renderHistory();
  await renderInsights();
  if (state.selectedWineId === wine.id) {
    renderSales(wine.id);
    renderMovements(wine.id);
  }
}

function isSharedWine(wine) {
  const otherShare = (wine.owners || []).reduce((sum, owner) => sum + Number(owner.share_pct || 0), 0);
  return Number(wine.owner_share_pct ?? 100) < 100 || otherShare > 0;
}

function unitCurrentValue(wine) {
  return Number(wine.current_value ?? wine.price ?? 0);
}

function hasCurrentUnitValue(wine) {
  return wine.current_value !== null && wine.current_value !== undefined && wine.current_value !== "";
}

function renderCardCurrentValue(wine) {
  if (!hasCurrentUnitValue(wine)) return "";
  return `<span class="current-card-value"><small>${escapeHtml(t("currentValueShort"))}</small>${formatMoney(wine.current_value, wine.currency)}</span>`;
}

function insightFilterLabel(filter = state.insightFilter) {
  if (!filter) return "";
  const value = filter.field === "type" ? typeLabel(filter.value) : filter.value === "Unspecified" ? t("notSpecified") : filter.value;
  return `${value} - ${t(filter.field === "type" ? "color" : "region")}`;
}

function matchesInsightFilter(wine) {
  const filter = state.insightFilter;
  if (!filter) return true;
  if (filter.scope === "shared" && !isSharedWine(wine)) return false;
  if (filter.scope === "mine" && personalQuantity(wine) <= 0) return false;
  if (filter.field === "region") return (wine.region || "Unspecified") === filter.value;
  if (filter.field === "type") return (wine.type || "Unspecified") === filter.value;
  return true;
}

function matchesQuantityFilter(wine) {
  const quantity = Number(wine.quantity || 0);
  if (state.quantityFilter === "All") return true;
  if (state.quantityFilter === "Empty") return quantity <= 0;
  return quantity > 0;
}

function compareText(a, b) {
  return String(a || "").localeCompare(String(b || ""), state.lang === "it" ? "it" : "en", { sensitivity: "base", numeric: true });
}

function sortWines(wines) {
  const sorted = [...wines];
  sorted.sort((a, b) => {
    if (state.sort === "name-asc") return compareText(a.name, b.name) || compareText(a.producer, b.producer) || compareText(b.vintage, a.vintage);
    if (state.sort === "type-asc") return compareText(typeLabel(a.type), typeLabel(b.type)) || compareText(a.name, b.name);
    if (state.sort === "producer-asc") return compareText(a.producer, b.producer) || compareText(a.name, b.name);
    if (state.sort === "vintage-desc") return compareText(b.vintage, a.vintage) || compareText(a.name, b.name);
    if (state.sort === "value-desc") return unitCurrentValue(b) * Number(b.quantity || 0) - unitCurrentValue(a) * Number(a.quantity || 0) || compareText(a.name, b.name);
    return compareText(b.expected_delivery, a.expected_delivery) || compareText(a.name, b.name);
  });
  return sorted;
}

function updateFilterCount() {
  const activeFilters = [state.filter !== "All", state.ownerFilter !== "All", state.quantityFilter !== "Available", Boolean(state.insightFilter)].filter(Boolean).length;
  filterCount.textContent = activeFilters ? String(activeFilters) : "";
  filterCount.hidden = activeFilters === 0;
  activeInsightFilter.hidden = !state.insightFilter;
  if (state.insightFilter) activeInsightFilter.textContent = `${t("filterActive", { filter: insightFilterLabel() })} x`;
}

function updateActiveInsightFilterCount(count) {
  if (!state.insightFilter) return;
  activeInsightFilter.textContent = `${t("filterActive", { filter: insightFilterLabel() })} - ${t("resultsCount", {
    count: formatNumber(count),
    bottles: bottleLabel(count),
  })} x`;
}

function showScreen(name) {
  if (name !== "login" && !isAuthenticated()) name = "login";
  if (name === "form" && !isAdmin()) name = "cellar";
  if (name === "settings" && !isAdmin()) name = "cellar";
  Object.entries(screens).forEach(([key, screen]) => {
    screen.classList.toggle("active", key === name);
  });

  bottomNav.hidden = name === "form" || name === "detail" || name === "login";
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.classList.toggle("active", item.dataset.screen === name);
  });

  if (name === "timeline") renderTimeline();
  if (name === "drinkNow") renderDrinkNow();
  if (name === "insights") renderInsights();
  if (name === "wishlist") renderWishlist();
  if (name === "history") renderHistory();
  if (name === "settings" && state.settings) renderSettings();
}

function renderDrinkWindow(wine) {
  const chart = document.querySelector("#drink-window-chart");
  const empty = document.querySelector("#drink-window-empty");
  const notes = document.querySelector("#drink-window-notes");
  const values = ["drink_peak_from", "drink_peak_to", "drink_to"].map((field) => Number(wine[field]));
  const vintage = Number.parseInt(wine.vintage, 10);
  const hasWindow = Number.isFinite(vintage) && values.every((value) => Number.isFinite(value) && value > 0);

  chart.hidden = !hasWindow;
  empty.hidden = hasWindow;
  notes.hidden = !hasWindow;
  if (!hasWindow) {
    empty.textContent = t("drinkWindowMissing");
    notes.textContent = "";
    return;
  }

  const currentYear = new Date().getFullYear();
  const startYear = Math.min(vintage, Number(wine.drink_from) || vintage);
  const peakFrom = Number(wine.drink_peak_from);
  const peakTo = Number(wine.drink_peak_to);
  const endYear = Math.max(Number(wine.drink_to), peakTo + 1);
  const totalSpan = Math.max(endYear - startYear, 1);
  const youngPct = Math.max(((peakFrom - startYear) / totalSpan) * 100, 8);
  const peakPct = Math.max(((peakTo - peakFrom) / totalSpan) * 100, 8);
  const declinePct = Math.max(100 - youngPct - peakPct, 8);
  const markerPct = Math.min(Math.max(((currentYear - startYear) / totalSpan) * 100, 0), 100);
  const arrivalYear = Number.parseInt(String(wine.expected_delivery || "").slice(0, 4), 10);
  const arrivalPct = Number.isFinite(arrivalYear) ? Math.min(Math.max(((arrivalYear - startYear) / totalSpan) * 100, 0), 100) : null;

  document.querySelector("#drink-window-start-year").textContent = `${startYear}`;
  document.querySelector("#drink-window-peak-years").textContent = `${peakFrom}-${peakTo}`;
  document.querySelector("#drink-window-end-year").textContent = `${endYear}`;
  document.querySelector("#drink-segment-young").style.flexBasis = `${youngPct}%`;
  document.querySelector("#drink-segment-peak").style.flexBasis = `${peakPct}%`;
  document.querySelector("#drink-segment-decline").style.flexBasis = `${declinePct}%`;
  const marker = document.querySelector("#drink-current-marker");
  marker.style.left = `${markerPct}%`;
  marker.title = `${t("drinkWindowYear")}: ${currentYear}`;
  const arrivalMarker = document.querySelector("#drink-arrival-marker");
  if (arrivalMarker) {
    arrivalMarker.hidden = arrivalPct === null;
    if (arrivalPct !== null) {
      arrivalMarker.style.left = `${arrivalPct}%`;
      arrivalMarker.title = `${state.lang === "it" ? "Arrivo" : "Arrival"}: ${arrivalYear}`;
    }
  }
  notes.textContent = wine.drink_window_notes ? `${t("drinkWindowEstimate")}: ${wine.drink_window_notes}` : t("drinkWindowEstimate");
}

function drinkWindowChartData(wine) {
  const vintage = Number.parseInt(wine.vintage, 10);
  const peakFrom = Number(wine.drink_peak_from);
  const peakTo = Number(wine.drink_peak_to);
  const drinkTo = Number(wine.drink_to);
  if (![vintage, peakFrom, peakTo, drinkTo].every((value) => Number.isFinite(value) && value > 0)) return null;

  const startYear = Math.min(vintage, Number(wine.drink_from) || vintage);
  const endYear = Math.max(drinkTo, peakTo + 1);
  const totalSpan = Math.max(endYear - startYear, 1);
  const youngPct = Math.max(((peakFrom - startYear) / totalSpan) * 100, 8);
  const peakPct = Math.max(((peakTo - peakFrom) / totalSpan) * 100, 8);
  const declinePct = Math.max(100 - youngPct - peakPct, 8);
  const currentYear = new Date().getFullYear();
  const markerPct = Math.min(Math.max(((currentYear - startYear) / totalSpan) * 100, 0), 100);
  const arrivalYear = Number.parseInt(String(wine.expected_delivery || "").slice(0, 4), 10);
  const arrivalPct = Number.isFinite(arrivalYear) ? Math.min(Math.max(((arrivalYear - startYear) / totalSpan) * 100, 0), 100) : null;

  return { startYear, peakFrom, peakTo, endYear, youngPct, peakPct, declinePct, markerPct, currentYear, arrivalPct, arrivalYear };
}

function renderMiniDrinkWindow(wine) {
  const data = drinkWindowChartData(wine);
  if (!data) return "";

  return `
    <div class="mini-drink-window" aria-label="${escapeAttribute(t("drinkWindow"))}">
      <div class="mini-drink-window-years">
        <span>${data.startYear}</span>
        <span>${data.peakFrom}-${data.peakTo}</span>
        <span>${data.endYear}</span>
      </div>
      <div class="mini-drink-window-bar" title="${escapeAttribute(`${t("drinkWindowYear")}: ${data.currentYear}`)}">
        <span class="drink-segment drink-young" style="flex-basis: ${data.youngPct}%"></span>
        <span class="drink-segment drink-peak" style="flex-basis: ${data.peakPct}%"></span>
        <span class="drink-segment drink-decline" style="flex-basis: ${data.declinePct}%"></span>
        ${data.arrivalPct === null ? "" : `<span class="drink-arrival-marker" style="left: ${data.arrivalPct}%" title="${escapeAttribute(`${state.lang === "it" ? "Arrivo" : "Arrival"}: ${data.arrivalYear}`)}"></span>`}
        <span class="drink-current-marker" style="left: ${data.markerPct}%"></span>
      </div>
    </div>
  `;
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
  const aiValueNotes = document.querySelector("#detail-ai-value-notes");
  aiValueNotes.textContent = wine.ai_value_notes || "";
  aiValueNotes.hidden = !wine.ai_value_notes;
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
  document.querySelector("#detail-notes").textContent = wine.notes || t("notSpecified");
  document.querySelector("#detail-ai-notes").textContent = wine.ai_notes || t("notSpecified");
  renderDrinkWindow(wine);
  drinkButton.disabled = Number(wine.quantity) <= 0 || wine.status !== "Delivered";
  drinkButton.title = wine.status === "Delivered" ? "" : t("onlyDelivered");
  renderOwnerList(wine);
  renderScoreList(wine);
  renderSales(wine.id);
  renderMovements(wine.id);

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

function movementLabel(type) {
  return (
    {
      drink: "movementDrink",
      sale: "movementSale",
      adjustment: "movementAdjustment",
      arrival: "movementArrival",
    }[type] || "movementAdjustment"
  );
}

function movementWineTitle(movement) {
  return [movement.wine_name, movement.wine_producer, movement.wine_vintage].filter(Boolean).join(" - ");
}

function movementNoteText(movement) {
  if (movement.movement_type === "drink" && ["Bottle marked as drunk", "Bevuta 1"].includes(movement.note)) {
    return t("drankOne");
  }
  if (movement.movement_type === "sale") {
    if (String(movement.note || "").startsWith("sale:")) {
      return t("soldTo", { buyer: movement.note.slice(5) });
    }
    if (String(movement.note || "").startsWith("Sold to ")) {
      return t("soldTo", { buyer: movement.note.slice(8) });
    }
  }
  return movement.note || "";
}

function renderMovementRows(movements, { includeWine = false } = {}) {
  if (!movements.length) return `<p class="empty-state compact">${t("movementEmpty")}</p>`;
  return movements
    .map((movement) => {
      const quantity = Number(movement.quantity || 0);
      const value = movement.value ? `<span>${escapeHtml(formatMoney(movement.value, movement.currency || "CHF"))}</span>` : "";
      const actions = isAdmin()
        ? `
          <div class="movement-actions">
            <button class="btn btn-soft" data-movement-edit="${escapeAttribute(movement.id)}" type="button">${escapeHtml(t("movementEdit"))}</button>
            <button class="btn btn-soft" data-movement-delete="${escapeAttribute(movement.id)}" type="button">${escapeHtml(t("movementCancel"))}</button>
          </div>
        `
        : "";
      const title = includeWine ? movementWineTitle(movement) : t(movementLabel(movement.movement_type));
      const subtitle = includeWine ? t(movementLabel(movement.movement_type)) : "";
      const note = movementNoteText(movement);
      return `
        <div class="movement-row" data-id="${escapeAttribute(movement.id)}" data-wine-id="${escapeAttribute(movement.wine_id)}" data-movement="${escapeAttribute(movement.movement_type)}">
          <div>
            <strong>${escapeHtml(title)}</strong>
            ${subtitle ? `<span>${escapeHtml(subtitle)}</span>` : ""}
            <span>${escapeHtml(formatDateTime(movement.occurred_at))}</span>
            ${note ? `<span>${escapeHtml(note)}</span>` : ""}
            ${actions}
          </div>
          <div class="movement-numbers">
            <strong>${quantity > 0 ? "+" : ""}${escapeHtml(formatNumber(quantity))}</strong>
            ${value}
          </div>
        </div>
      `;
    })
    .join("");
}

async function renderMovements(wineId) {
  if (!wineId || !movementList) return;
  try {
    const movements = await api(`/api/wines/${encodeURIComponent(wineId)}/movements`);
    movementList.innerHTML = renderMovementRows(movements);
  } catch (error) {
    movementList.innerHTML = `<p class="empty-state compact">${escapeHtml(error.message)}</p>`;
  }
}

async function renderHistory() {
  if (!historyList) return;
  try {
    state.movements = await api("/api/movements");
    historyList.innerHTML = renderMovementRows(state.movements, { includeWine: true });
  } catch (error) {
    historyList.innerHTML = `<p class="empty-state compact">${escapeHtml(error.message)}</p>`;
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
      if (state.ownerFilter === "All") return true;
      const shared = isSharedWine(wine);
      return state.ownerFilter === "Shared" ? shared : !shared;
    })
    .filter(matchesQuantityFilter)
    .filter((wine) => {
      if (!query) return true;
      return [wine.name, wine.producer, wine.region, wine.appellation, wine.vintage]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(query));
    })
    .filter(matchesInsightFilter)
  const sortedWines = sortWines(wines);

  updateActiveInsightFilterCount(sortedWines.reduce((sum, wine) => sum + Number(wine.quantity || 0), 0));
  wineList.innerHTML = sortedWines.length
    ? sortedWines
        .map(
          (wine) => `
            <button class="wine-card" data-id="${wine.id}" data-type="${escapeHtml(cardVisualType(wine))}" type="button">
              <div class="wine-card-main">
                <p class="wine-title">${escapeHtml(wine.name)}</p>
                <p class="wine-meta wine-producer">${escapeHtml(wine.producer)}</p>
                <div class="wine-card-details">
                  <span>${wine.quantity}x ${escapeHtml(formatLabel(wine.format))}</span>
                  <span>${state.lang === "it" ? "Arrivo" : "Arrival"}: ${formatMonthYear(wine.expected_delivery)}</span>
                </div>
                ${scoreSummary(wine) ? `<p class="score-summary">${escapeHtml(scoreSummary(wine))}</p>` : ""}
                ${renderMiniDrinkWindow(wine)}
              </div>
              <div class="card-side">
                <span class="vintage">${escapeHtml(wine.vintage)}</span>
                <span class="status-pill ${escapeHtml(wine.status)}">${escapeHtml(statusLabel(wine.status))}</span>
                <span class="price-stack">
                  <span class="price">${formatMoney(wine.price, wine.currency)} &gt;</span>
                  ${renderCardCurrentValue(wine)}
                </span>
              </div>
            </button>
          `,
        )
        .join("")
    : `<p class="empty-state">${state.insightFilter ? t("emptyInsightFilter", { filter: insightFilterLabel() }) : t("emptyFilter")}</p>`;
}

function drinkNowStatus(wine) {
  const currentYear = new Date().getFullYear();
  const drinkFrom = Number(wine.drink_from);
  const peakFrom = Number(wine.drink_peak_from);
  const peakTo = Number(wine.drink_peak_to);
  const drinkTo = Number(wine.drink_to);

  if (Number.isFinite(drinkTo) && drinkTo > 0 && currentYear > drinkTo) {
    return { section: "dontWait", priority: 100 + currentYear - drinkTo, reason: t("drinkNowReasonDecline") };
  }

  if (Number.isFinite(peakFrom) && Number.isFinite(peakTo) && peakFrom > 0 && peakTo > 0 && currentYear >= peakFrom && currentYear <= peakTo) {
    return { section: "ideal", priority: 90, reason: t("drinkNowReasonIdeal") };
  }

  if (Number.isFinite(peakTo) && peakTo > 0 && currentYear > peakTo) {
    const nearEnd = Number.isFinite(drinkTo) && drinkTo > 0 && drinkTo - currentYear <= 1;
    return { section: nearEnd ? "dontWait" : "pastIdeal", priority: nearEnd ? 89 : 84, reason: t("drinkNowReasonPastIdeal") };
  }

  if (Number.isFinite(drinkFrom) && Number.isFinite(drinkTo) && drinkFrom > 0 && drinkTo > 0 && currentYear >= drinkFrom && currentYear <= drinkTo) {
    const nearEnd = drinkTo - currentYear <= 1;
    return { section: nearEnd ? "dontWait" : "ready", priority: nearEnd ? 88 : 70, reason: t("drinkNowReasonReady") };
  }

  if (Number.isFinite(drinkFrom) && drinkFrom > 0 && currentYear < drinkFrom) {
    return { section: "wait", priority: Math.max(1, 40 - (drinkFrom - currentYear)), reason: t("drinkNowReasonWait") };
  }

  return { section: "unknown", priority: 50, reason: t("drinkNowReasonMissing") };
}

function drinkNowCategory(wine) {
  const value = unitCurrentValue(wine);
  if (value >= 180) return t("drinkCategoryGreatBottle");
  if (value >= 70) return t("drinkCategoryDinner");
  if (value > 0) return t("drinkCategoryEveryday");
  return t("drinkCategoryReady");
}

function idealWindowLabel(wine) {
  const peakFrom = Number(wine.drink_peak_from) || null;
  const peakTo = Number(wine.drink_peak_to) || null;
  if (peakFrom && peakTo) return `${peakFrom}-${peakTo}`;
  if (peakFrom) return `${peakFrom}`;
  return t("notSpecified");
}

function drinkRangeLabel(wine) {
  const drinkFrom = Number(wine.drink_from) || null;
  const drinkTo = Number(wine.drink_to) || null;
  if (drinkFrom && drinkTo) return `${drinkFrom}-${drinkTo}`;
  if (drinkTo) return `${drinkTo}`;
  return t("notSpecified");
}

function renderDrinkNow() {
  const sectionLabels = {
    dontWait: t("drinkNowSectionDontWait"),
    ideal: t("drinkNowSectionIdeal"),
    pastIdeal: t("drinkNowSectionPastIdeal"),
    ready: t("drinkNowSectionReady"),
    unknown: t("drinkNowSectionUnknown"),
    wait: t("drinkNowSectionWait"),
  };
  const recommendations = state.wines
    .filter((wine) => wine.status === "Delivered" && Number(wine.quantity || 0) > 0)
    .map((wine) => ({ wine, status: drinkNowStatus(wine) }))
    .sort((a, b) => b.status.priority - a.status.priority || a.wine.name.localeCompare(b.wine.name));

  if (!recommendations.length) {
    drinkNowList.innerHTML = `<p class="empty-state">${escapeHtml(t("drinkNowEmpty"))}</p>`;
    return;
  }

  drinkNowList.innerHTML = ["dontWait", "ideal", "pastIdeal", "ready", "unknown", "wait"]
    .map((section) => {
      const items = recommendations.filter((item) => item.status.section === section);
      if (!items.length) return "";
      const collapsed = Boolean(state.drinkNowCollapsed[section]);
      const sectionContentId = `drink-now-section-${section}`;
      return `
        <section class="drink-now-section" data-drink-now-section="${escapeAttribute(section)}">
          <h2>
            <button class="drink-now-section-toggle" data-drink-now-toggle="${escapeAttribute(section)}" type="button" aria-expanded="${collapsed ? "false" : "true"}" aria-controls="${escapeAttribute(sectionContentId)}">
              <span>${escapeHtml(sectionLabels[section])}</span>
              <span class="drink-now-section-count">${escapeHtml(formatNumber(items.length))}</span>
            </button>
          </h2>
          <div class="content-list" id="${escapeAttribute(sectionContentId)}" ${collapsed ? "hidden" : ""}>
            ${items
              .map(({ wine, status }) => {
                const drinkAction = isAdmin()
                  ? `<button class="btn btn-soft drink-now-action" data-drink-now-drink="${escapeAttribute(wine.id)}" type="button">${escapeHtml(t("drankOne"))}</button>`
                  : "";
                return `
                  <article class="drink-now-card" data-id="${escapeAttribute(wine.id)}" data-status="${escapeAttribute(status.section)}" data-type="${escapeHtml(cardVisualType(wine))}" tabindex="0">
                    <div>
                      <span class="drink-now-status">${escapeHtml(sectionLabels[status.section])}</span>
                      <p class="wine-title">${escapeHtml(wine.name)} <span class="small-vintage">${escapeHtml(wine.vintage)}</span></p>
                      <p class="wine-meta">${escapeHtml(wine.producer)} - ${escapeHtml(wine.region || t("notSpecified"))}</p>
                      <div class="drink-now-window-grid">
                        <div class="drink-now-window-cell highlight">
                          <span>${escapeHtml(t("drinkPeak"))}</span>
                          <strong>${escapeHtml(idealWindowLabel(wine))}</strong>
                        </div>
                        <div class="drink-now-window-cell">
                          <span>${escapeHtml(t("drinkNowWindow"))}</span>
                          <strong>${escapeHtml(drinkRangeLabel(wine))}</strong>
                        </div>
                      </div>
                      ${renderMiniDrinkWindow(wine)}
                      <p class="drink-now-reason"><strong>${escapeHtml(t("drinkNowStatus"))}:</strong> ${escapeHtml(status.reason)}</p>
                    </div>
                    <div class="drink-now-side">
                      <span class="drink-now-chip">${escapeHtml(drinkNowCategory(wine))}</span>
                      <span class="wine-meta">${escapeHtml(formatNumber(wine.quantity))} ${escapeHtml(bottleLabel(wine.quantity))}</span>
                      ${drinkAction}
                    </div>
                  </article>
                `;
              })
              .join("")}
          </div>
        </section>
      `;
    })
    .join("");
}

function showDrinkNowTab(tab) {
  const selectedTab = tab === "pairing" && isAdmin() ? "pairing" : "list";
  document.querySelectorAll("[data-drink-now-tab]").forEach((button) => {
    button.classList.toggle("active", button.dataset.drinkNowTab === selectedTab);
  });
  drinkNowListPanel.classList.toggle("active", selectedTab === "list");
  drinkNowPairingPanel.classList.toggle("active", selectedTab === "pairing");
}

function renderPairingResult(result) {
  const matches = Array.isArray(result.cellar_matches) ? result.cellar_matches : [];
  const market = result.market_recommendations || {};
  const marketGroups = [
    ["low", t("priorityLow")],
    ["medium", t("priorityMedium")],
    ["high", t("priorityHigh")],
  ];

  pairingResult.hidden = false;
  pairingResult.innerHTML = `
    ${result.summary ? `<p class="pairing-summary">${escapeHtml(result.summary)}</p>` : ""}
    ${result.model ? `<p class="pairing-model-used">${escapeHtml(t("pairingModelUsed", { model: result.model }))}</p>` : ""}
    ${
      matches.length
        ? `
          <h2>${escapeHtml(t("pairingCellarMatches"))}</h2>
          <div class="pairing-match-list">
            ${matches
              .map((match) => {
                const wine = state.wines.find((item) => item.id === match.wine_id);
                return `
                  <button class="pairing-match" data-pairing-wine="${escapeAttribute(match.wine_id)}" type="button">
                    <strong>${escapeHtml(match.wine_name || wine?.name || "")} ${wine?.vintage ? `<span class="small-vintage">${escapeHtml(wine.vintage)}</span>` : ""}</strong>
                    <span>${escapeHtml(match.producer || wine?.producer || "")}</span>
                    <span><b>${escapeHtml(t("pairingWhy"))}:</b> ${escapeHtml(match.reason || "")}</span>
                    ${match.serving_note ? `<span>${escapeHtml(match.serving_note)}</span>` : ""}
                  </button>
                `;
              })
              .join("")}
          </div>
        `
        : `<p class="pairing-summary">${escapeHtml(t("pairingNoCellarMatch"))}</p>`
    }
    ${
      marketGroups.some(([key]) => Array.isArray(market[key]) && market[key].length)
        ? `
          <h2>${escapeHtml(t("pairingMarketFallback"))}</h2>
          <div class="pairing-market-grid">
            ${marketGroups
              .map(([key, label]) => {
                const items = Array.isArray(market[key]) ? market[key] : [];
                if (!items.length) return "";
                return `
                  <section class="pairing-market-tier">
                    <h3>${escapeHtml(label)}</h3>
                    ${items
                      .map(
                        (item) => `
                          <article>
                            <strong>${escapeHtml(item.name || "")}</strong>
                            ${item.producer ? `<span>${escapeHtml(item.producer)}</span>` : ""}
                            ${item.price_hint ? `<span>${escapeHtml(item.price_hint)}</span>` : ""}
                            <p>${escapeHtml(item.reason || "")}</p>
                          </article>
                        `,
                      )
                      .join("")}
                  </section>
                `;
              })
              .join("")}
          </div>
        `
        : ""
    }
  `;
}

async function suggestPairing(event) {
  event.preventDefault();
  const dish = pairingForm.elements.dish.value.trim();
  if (!dish) {
    alert(t("pairingEmptyDish"));
    return;
  }
  const includeMarket = Boolean(pairingForm.elements.include_market?.checked);
  const marketOnly = Boolean(pairingForm.elements.market_only?.checked);
  const submitButton = pairingForm.querySelector("button[type='submit']");
  const previousText = submitButton.textContent;
  submitButton.disabled = true;
  submitButton.textContent = "...";
  pairingResult.hidden = false;
  pairingResult.innerHTML = `<p class="pairing-summary">...</p>`;
  try {
    const result = await api("/api/pairing", { method: "POST", body: JSON.stringify({ dish, include_market: includeMarket, market_only: marketOnly }) });
    renderPairingResult(result);
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = previousText;
  }
}

function wishlistStatusLabel(status) {
  return t(
    {
      Evaluate: "wishlistEvaluate",
      Monitor: "wishlistMonitor",
      Buy: "wishlistBuy",
      Skipped: "wishlistSkipped",
    }[status] || "wishlistMonitor",
  );
}

function priorityLabel(priority) {
  return t(
    {
      High: "priorityHigh",
      Medium: "priorityMedium",
      Low: "priorityLow",
    }[priority] || "priorityMedium",
  );
}

function priorityClass(priority) {
  return `priority-${String(priority || "Medium").toLowerCase()}`;
}

function wishlistPurposeLabel(purpose) {
  return t(
    {
      Drink: "wishlistPurposeDrink",
      Invest: "wishlistPurposeInvest",
      Gift: "wishlistPurposeGift",
      Cellar: "wishlistPurposeCellar",
      Compare: "wishlistPurposeCompare",
    }[purpose] || "wishlistPurposeDrink",
  );
}

function wishlistStrategyLabel(recommendation) {
  return t(
    {
      buy: "wishlistStrategyBuy",
      monitor: "wishlistStrategyMonitor",
      avoid: "wishlistStrategyAvoid",
    }[recommendation] || "wishlistStrategyMonitor",
  );
}

function isAiWishlistStatus(item) {
  return String(item?.status_source || "").toLowerCase() === "ai";
}

function renderWishlistStatus(item) {
  const strategy = persistedWishlistStrategy(item);
  const recommendation = strategy?.recommendation || "";
  const badge = isAiWishlistStatus(item)
    ? `<span class="wishlist-ai-badge" data-recommendation="${escapeAttribute(recommendation || "monitor")}" title="${escapeAttribute(t("wishlistStatusAiLong"))}" aria-label="${escapeAttribute(t("wishlistStatusAiLong"))}">${escapeHtml(t("wishlistStatusAi"))}</span>`
    : "";
  return `<span class="wishlist-status-inline" data-recommendation="${escapeAttribute(recommendation || "manual")}">${escapeHtml(wishlistStatusLabel(item.status))}${badge}</span>`;
}

function persistedWishlistStrategy(item) {
  if (!item?.ai_strategy) return null;
  if (typeof item.ai_strategy === "object") return item.ai_strategy;
  try {
    return JSON.parse(item.ai_strategy);
  } catch {
    return null;
  }
}

function renderWishlistStrategy(item) {
  const strategy = state.wishlistStrategies[item.id] || persistedWishlistStrategy(item);
  if (!strategy) return "";
  if (strategy.loading) return `<div class="wishlist-strategy"><p>${escapeHtml(t("wishlistStrategyLoading"))}</p></div>`;
  const signal = strategy.signal || wishlistStrategyLabel(strategy.recommendation);
  const sources = renderWishlistStrategySources(strategy.sources);
  return `
    <div class="wishlist-strategy" data-recommendation="${escapeAttribute(strategy.recommendation || "monitor")}">
      <span>${escapeHtml(signal)}</span>
      ${strategy.reason ? `<p>${escapeHtml(strategy.reason)}</p>` : ""}
      ${
        strategy.alternative
          ? `<p><b>${escapeHtml(t("wishlistStrategyAlternative"))}:</b> ${escapeHtml([strategy.alternative.name, strategy.alternative.producer].filter(Boolean).join(" - "))}</p>`
          : ""
      }
      ${sources}
    </div>
  `;
}

function renderWishlistStrategySources(sources = []) {
  if (!Array.isArray(sources) || !sources.length) return "";
  return `
    <div class="wishlist-strategy-sources">
      <b>${escapeHtml(t("wishlistStrategySources"))}:</b>
      ${sources
        .slice(0, 4)
        .map((source) => `<a href="${escapeAttribute(source.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(source.title || source.url)}</a>`)
        .join("")}
    </div>
  `;
}

function wishlistPriceAssessment(item) {
  const strategy = state.wishlistStrategies[item.id] || persistedWishlistStrategy(item);
  return strategy?.price_assessment || "";
}

function wishlistEstimatedRange(item) {
  const strategy = state.wishlistStrategies[item.id] || persistedWishlistStrategy(item);
  const low = Number(strategy?.market_price_low);
  const high = Number(strategy?.market_price_high);
  const currency = strategy?.market_price_currency || item.currency || "CHF";
  if (!Number.isFinite(low) || !Number.isFinite(high) || low <= 0 || high <= 0) return "";
  return `${formatMoney(Math.min(low, high), currency)} - ${formatMoney(Math.max(low, high), currency)}`;
}

function renderWishlist() {
  if (!wishlistList) return;
  wishlistList.innerHTML = state.wishlist.length
    ? state.wishlist
        .map((item) => {
          const strategy = persistedWishlistStrategy(item);
          const recommendation = strategy?.recommendation || "";
          const highlight = isAiWishlistStatus(item) && ["buy", "avoid"].includes(recommendation) ? recommendation : "";
          return `
            <article class="wishlist-card" data-id="${item.id}" data-recommendation="${escapeAttribute(recommendation || "manual")}" data-highlight="${escapeAttribute(highlight)}">
              <button class="wishlist-card-header" data-wishlist-toggle="${item.id}" type="button" aria-expanded="false">
                <div>
                  <h2>${escapeHtml(item.name)} ${item.vintage ? `<span class="small-vintage">${escapeHtml(item.vintage)}</span>` : ""}</h2>
                  <p>${escapeHtml([item.producer, item.region, item.appellation].filter(Boolean).join(" - ") || t("notSpecified"))}</p>
                  <p class="wishlist-closed-meta">${escapeHtml(wishlistPurposeLabel(item.purpose))} - ${renderWishlistStatus(item)} - ${item.target_price ? formatMoney(item.target_price, item.currency) : t("notSpecified")}</p>
                </div>
                <span class="wishlist-card-side">
                  <span class="wishlist-chip ${priorityClass(item.priority)}">${escapeHtml(priorityLabel(item.priority))}</span>
                  <span class="wishlist-chevron" aria-hidden="true">v</span>
                </span>
              </button>
              <div class="wishlist-card-detail" hidden>
                <dl>
                  <div><dt>${escapeHtml(t("status"))}</dt><dd>${renderWishlistStatus(item)}</dd></div>
                  <div><dt>${escapeHtml(t("wishlistPurpose"))}</dt><dd>${escapeHtml(wishlistPurposeLabel(item.purpose))}</dd></div>
                  <div><dt>${escapeHtml(t("targetPrice"))}</dt><dd>${item.target_price ? formatMoney(item.target_price, item.currency) : t("notSpecified")}</dd></div>
                  <div><dt>${escapeHtml(t("estimatedMarketRange"))}</dt><dd>${escapeHtml(wishlistEstimatedRange(item) || t("notSpecified"))}</dd></div>
                  <div><dt>${escapeHtml(t("priceAssessmentAi"))}</dt><dd>${escapeHtml(wishlistPriceAssessment(item) || t("notSpecified"))}</dd></div>
                  <div><dt>${escapeHtml(t("merchant"))}</dt><dd>${escapeHtml(item.merchant || t("notSpecified"))}</dd></div>
                  <div><dt>${escapeHtml(t("format"))}</dt><dd>${escapeHtml(formatLabel(item.format))}</dd></div>
                  <div><dt>${escapeHtml(t("type"))}</dt><dd>${escapeHtml(typeLabel(item.type))}</dd></div>
                  <div><dt>${escapeHtml(t("notes"))}</dt><dd>${escapeHtml(item.notes || t("notSpecified"))}</dd></div>
                </dl>
                <div class="wishlist-card-actions">
                  <button class="btn btn-soft" data-wishlist-edit="${item.id}" type="button">${escapeHtml(t("edit"))}</button>
                  <button class="btn btn-soft admin-only" data-wishlist-strategy="${item.id}" type="button">${escapeHtml(t("wishlistStrategy"))}</button>
                  <button class="btn btn-wine admin-only" data-wishlist-convert="${item.id}" type="button">${escapeHtml(t("newOrder"))}</button>
                </div>
                ${renderWishlistStrategy(item)}
              </div>
            </article>
          `;
        })
        .join("")
    : `<p class="empty-state">${t("emptyWishlist")}</p>`;
  applyPermissions();
}

function expandWishlistCard(id) {
  const card = [...wishlistList.querySelectorAll(".wishlist-card")].find((item) => item.dataset.id === id);
  if (!card) return;
  const detail = card.querySelector(".wishlist-card-detail");
  const toggle = card.querySelector("[data-wishlist-toggle]");
  if (detail) detail.hidden = false;
  if (toggle) toggle.setAttribute("aria-expanded", "true");
}

function openWishlistForm(item = null) {
  wishlistForm.reset();
  state.selectedWishlistId = item?.id || null;
  deleteWishlistButton.hidden = !item || !isAdmin();
  const defaults = {
    currency: "CHF",
    purpose: "Drink",
    priority: "Medium",
    status: "Monitor",
    format: "Bottle (750ml)",
    type: "Red",
  };
  const values = { ...defaults, ...item };
  Object.entries(values).forEach(([key, value]) => {
    const field = wishlistForm.elements[key];
    if (field) field.value = value ?? "";
  });
  wishlistForm.hidden = false;
  requestAnimationFrame(() => {
    wishlistForm.scrollIntoView({ behavior: "smooth", block: "start" });
    wishlistNameInput?.focus({ preventScroll: true });
  });
}

function wishlistFormToItem() {
  const data = new FormData(wishlistForm);
  return {
    id: data.get("id") || undefined,
    name: data.get("name").trim(),
    producer: data.get("producer").trim(),
    vintage: data.get("vintage").trim(),
    region: data.get("region").trim(),
    appellation: data.get("appellation").trim(),
    format: data.get("format"),
    type: data.get("type"),
    target_price: data.get("target_price") === "" ? null : Number(data.get("target_price")),
    currency: data.get("currency"),
    merchant: data.get("merchant").trim(),
    purpose: data.get("purpose"),
    priority: data.get("priority"),
    status: data.get("status"),
    notes: data.get("notes").trim(),
  };
}

async function saveWishlistItem(event) {
  event.preventDefault();
  const item = wishlistFormToItem();
  const saved = item.id
    ? await api(`/api/wishlist/${encodeURIComponent(item.id)}`, { method: "PUT", body: JSON.stringify(item) })
    : await api("/api/wishlist", { method: "POST", body: JSON.stringify(item) });
  const index = state.wishlist.findIndex((candidate) => candidate.id === saved.id);
  if (index >= 0) state.wishlist[index] = saved;
  else state.wishlist.unshift(saved);
  wishlistForm.hidden = true;
  renderWishlist();
}

async function deleteCurrentWishlistItem() {
  const id = wishlistForm.elements.id.value;
  if (!id) return;
  await api(`/api/wishlist/${encodeURIComponent(id)}`, { method: "DELETE" });
  state.wishlist = state.wishlist.filter((item) => item.id !== id);
  wishlistForm.hidden = true;
  renderWishlist();
}

async function convertWishlistItem(id) {
  const saved = await api(`/api/wishlist/${encodeURIComponent(id)}/convert`, { method: "POST", body: JSON.stringify({}) });
  state.wishlist = state.wishlist.filter((item) => item.id !== id);
  state.wines.unshift(saved);
  renderWineSuggestions();
  renderWishlist();
  renderCellar();
  openDetail(saved);
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
    document.querySelector("#shared-total-value").textContent = formatMoney(
      summary.shared_total_value,
      summary.reference_currency,
    );
    document.querySelector("#shared-current-value").textContent = formatMoney(
      summary.shared_current_value,
      summary.reference_currency,
    );
    document.querySelector("#shared-unrealized-gain-loss").textContent = formatMoney(
      summary.shared_unrealized_gain_loss,
      summary.reference_currency,
    );
    document.querySelector("#shared-cellar-bottles").textContent = formatNumber(summary.shared_cellar_bottles);
    document.querySelector("#shared-ordered-bottles").textContent = formatNumber(summary.shared_ordered_bottles);
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

    regionList.innerHTML = renderInsightRows(summary.regions, "region", "mine");
    colorList.innerHTML = renderInsightRows(summary.colors, "type", "mine");
    sharedRegionList.innerHTML = renderInsightRows(summary.shared_regions, "region", "shared");
    sharedColorList.innerHTML = renderInsightRows(summary.shared_colors, "type", "shared");
    grossRegionList.innerHTML = renderInsightRows(summary.gross_regions, "region", "total");
    grossColorList.innerHTML = renderInsightRows(summary.gross_colors, "type", "total");
    const movements = summary.movements || {};
    document.querySelector("#movement-consumed-bottles").textContent = formatNumber(movements.consumed_bottles);
    document.querySelector("#movement-sold-bottles").textContent = formatNumber(movements.sold_bottles);
    document.querySelector("#movement-consumed-value").textContent = formatMoney(movements.consumed_value, summary.reference_currency);
    document.querySelector("#movement-sold-revenue").textContent = formatMoney(movements.sold_revenue, summary.reference_currency);
    document.querySelector("#movement-realized-gain-loss").textContent = formatMoney(movements.realized_gain_loss, summary.reference_currency);
    movementConsumedRegionList.innerHTML = renderInsightRows(movements.consumed_regions || [], "region", "movements");

    const sourceLabel = summary.rates.cached ? t("cachedRates") : t("latestRates");
    document.querySelector("#rates-note").textContent = t("convertedRates", {
      source: sourceLabel,
      date: summary.rates.date,
    });
  } catch (error) {
    document.querySelector("#rates-note").textContent = t("exchangeUnavailable", { error: error.message });
  }
}

function renderInsightRows(items, field, scope) {
  const maxBottles = Math.max(...items.map((item) => Number(item.bottles) || 0), 0);
  return items
    .map((item) => {
      const value = field === "region" ? item.region : item.type;
      const label = field === "type" ? typeLabel(value) : value === "Unspecified" ? t("notSpecified") : value;
      const barWidth = maxBottles ? Math.max(8, Math.round((Number(item.bottles) / maxBottles) * 100)) : 0;
      return `
        <button class="region-row" data-insight-field="${field}" data-insight-scope="${scope}" data-insight-value="${escapeAttribute(value)}" style="--bar-width: ${barWidth}%;" type="button">
          <span>${escapeHtml(label)}</span>
          <strong>${formatNumber(item.bottles)} btl</strong>
        </button>
      `;
    })
    .join("") || `<p class="empty-state compact">${t("emptyFilter")}</p>`;
}

function applyInsightListFilter(field, value, scope) {
  state.insightFilter = { field, value, scope };
  state.filter = "All";
  state.ownerFilter = "All";
  state.quantityFilter = "Available";
  state.sort = "delivery-desc";
  cellarSearch.value = "";
  cellarSort.value = state.sort;
  state.search = "";
  document.querySelectorAll("[data-filter]").forEach((item) => item.classList.toggle("active", item.dataset.filter === "All"));
  document.querySelectorAll("[data-owner-filter]").forEach((item) => item.classList.toggle("active", item.dataset.ownerFilter === "All"));
  document.querySelectorAll("[data-quantity-filter]").forEach((item) => item.classList.toggle("active", item.dataset.quantityFilter === "Available"));
  updateFilterCount();
  renderCellar();
  showScreen("cellar");
}

function clearInsightListFilter() {
  state.insightFilter = null;
  updateFilterCount();
  renderCellar();
}

function openForm(wine) {
  if (!isAdmin()) return;
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
    notes: "",
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

async function suggestWishlistStrategy(id) {
  state.wishlistStrategies[id] = { loading: true };
  renderWishlist();
  expandWishlistCard(id);
  try {
    const result = await api(`/api/wishlist/${encodeURIComponent(id)}/strategy`, { method: "POST", body: JSON.stringify({}) });
    state.wishlistStrategies[id] = result.strategy || result;
    if (result.item) {
      const index = state.wishlist.findIndex((item) => item.id === result.item.id);
      if (index >= 0) state.wishlist[index] = result.item;
    }
  } catch (error) {
    delete state.wishlistStrategies[id];
    renderWishlist();
    throw error;
  }
  renderWishlist();
  expandWishlistCard(id);
}

function isUsableScoreSuggestion(score) {
  const value = String(score?.score || "").trim();
  const normalized = value.toLowerCase().replace(/[ .:-]+$/g, "");
  if (!score?.critic || !value || !/\d/.test(value)) return false;
  return !["da verific", "non ho", "n/d", "nd", "n.a.", "na", "unknown", "sconosciuto", "non disponibile", "nessun"].some((marker) =>
    normalized.includes(marker)
  );
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
  const existingWine = state.wines.find((wine) => wine.id === data.get("id"));
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
    notes: data.get("notes").trim(),
    ai_notes: existingWine?.ai_notes || "",
    drink_from: existingWine?.drink_from ?? null,
    drink_peak_from: existingWine?.drink_peak_from ?? null,
    drink_peak_to: existingWine?.drink_peak_to ?? null,
    drink_to: existingWine?.drink_to ?? null,
    drink_window_notes: existingWine?.drink_window_notes || "",
    ai_value_notes: existingWine?.ai_value_notes || "",
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
  if (!confirm(t("drinkConfirm", { wine: wine.name }))) return;
  const note = prompt(t("drinkNotePrompt"), "");
  if (note === null) return;

  drinkButton.disabled = true;
  try {
    const saved = await markBottleDrunk(wine.id, note);
    openDetail(saved);
  } finally {
    drinkButton.disabled = false;
  }
}

async function markBottleDrunk(wineId, note = "") {
  const saved = await api(`/api/wines/${encodeURIComponent(wineId)}/drink`, {
    method: "POST",
    body: JSON.stringify({ note: note.trim() }),
  });
  await refreshAfterInventoryChange(saved);
  return saved;
}

function movementById(id) {
  return state.movements.find((movement) => movement.id === id);
}

async function editMovement(id) {
  const existing = movementById(id) || (await api("/api/movements")).find((movement) => movement.id === id);
  if (!existing) return;
  const currentQuantity = Math.abs(Number(existing.quantity || 0));
  const quantityInput = prompt(t("movementEditQuantityPrompt"), String(currentQuantity));
  if (quantityInput === null) return;
  const quantity = Number.parseInt(quantityInput, 10);
  if (!Number.isFinite(quantity) || quantity <= 0) {
    alert(t("movementUnable", { error: "Invalid quantity" }));
    return;
  }
  const note = prompt(t("movementEditNotePrompt"), existing.note || "");
  if (note === null) return;

  try {
    const result = await api(`/api/movements/${encodeURIComponent(id)}`, {
      method: "PUT",
      body: JSON.stringify({ quantity, note }),
    });
    await refreshAfterInventoryChange(result.wine);
    if (state.selectedWineId === result.wine.id) openDetail(result.wine);
  } catch (error) {
    alert(t("movementUnable", { error: error.message }));
  }
}

async function cancelMovement(id) {
  if (!confirm(t("movementCancelConfirm"))) return;
  try {
    const result = await api(`/api/movements/${encodeURIComponent(id)}`, { method: "DELETE" });
    await refreshAfterInventoryChange(result.wine);
    if (state.selectedWineId === result.wine.id) openDetail(result.wine);
  } catch (error) {
    alert(t("movementUnable", { error: error.message }));
  }
}

async function generateAiNotes() {
  const wine = state.wines.find((item) => item.id === state.selectedWineId);
  if (!wine) return;
  if (wine.ai_notes && !confirm(t("generateAiNotesConfirm"))) return;

  generateAiNotesButton.disabled = true;
  const previousText = generateAiNotesButton.textContent;
  generateAiNotesButton.textContent = "...";
  try {
    const saved = await api(`/api/wines/${encodeURIComponent(wine.id)}/ai-notes`, { method: "POST" });
    const index = state.wines.findIndex((item) => item.id === saved.id);
    if (index >= 0) state.wines[index] = saved;
    openDetail(saved);
  } finally {
    generateAiNotesButton.disabled = false;
    generateAiNotesButton.textContent = previousText;
  }
}

async function suggestAiScores() {
  const wine = state.wines.find((item) => item.id === state.selectedWineId);
  if (!wine) return;

  suggestAiScoresButton.disabled = true;
  const previousText = suggestAiScoresButton.textContent;
  suggestAiScoresButton.textContent = "...";
  try {
    const result = await api(`/api/wines/${encodeURIComponent(wine.id)}/ai-scores`, { method: "POST" });
    const suggestions = (Array.isArray(result.scores) ? result.scores : []).filter(isUsableScoreSuggestion);
    if (!suggestions.length) {
      alert(t("suggestScoresEmpty"));
      return;
    }
    openForm(wine);
    const existing = new Set(collectScores().map((score) => `${score.critic.toLowerCase()}|${score.score.toLowerCase()}`));
    let added = 0;
    suggestions.forEach((score) => {
      const key = `${String(score.critic || "").toLowerCase()}|${String(score.score || "").toLowerCase()}`;
      if (!score.critic || !score.score || existing.has(key)) return;
      existing.add(key);
      added += 1;
      addScoreRow(score);
    });
    alert(added ? t("suggestedScoresAdded", { count: formatNumber(added) }) : t("suggestScoresEmpty"));
  } finally {
    suggestAiScoresButton.disabled = false;
    suggestAiScoresButton.textContent = previousText;
  }
}

async function generateAiValue() {
  const wine = state.wines.find((item) => item.id === state.selectedWineId);
  if (!wine) return;
  if (wine.current_value && !confirm(t("generateAiValueConfirm"))) return;

  generateAiValueButton.disabled = true;
  const previousText = generateAiValueButton.textContent;
  generateAiValueButton.textContent = "...";
  try {
    const saved = await api(`/api/wines/${encodeURIComponent(wine.id)}/ai-value`, { method: "POST" });
    const index = state.wines.findIndex((item) => item.id === saved.id);
    if (index >= 0) state.wines[index] = saved;
    renderCellar();
    await renderInsights();
    openDetail(saved);
  } finally {
    generateAiValueButton.disabled = false;
    generateAiValueButton.textContent = previousText;
  }
}

async function generateDrinkWindow() {
  const wine = state.wines.find((item) => item.id === state.selectedWineId);
  if (!wine) return;
  if (wine.drink_to && !confirm(t("generateDrinkWindowConfirm"))) return;

  generateDrinkWindowButton.disabled = true;
  const previousText = generateDrinkWindowButton.textContent;
  generateDrinkWindowButton.textContent = "...";
  try {
    const saved = await api(`/api/wines/${encodeURIComponent(wine.id)}/drink-window`, { method: "POST" });
    const index = state.wines.findIndex((item) => item.id === saved.id);
    if (index >= 0) state.wines[index] = saved;
    openDetail(saved);
  } finally {
    generateDrinkWindowButton.disabled = false;
    generateDrinkWindowButton.textContent = previousText;
  }
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
    saleForm.hidden = true;
    saleForm.reset();
    await refreshAfterInventoryChange(result.wine);
    openDetail(result.wine);
  } catch (error) {
    alert(t("saleUnable", { error: error.message }));
  }
}

async function exportData() {
  const data = await api("/api/export");
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const timestamp = new Date().toISOString().slice(0, 19).replace("T", "_").replaceAll(":", "-");
  const link = document.createElement("a");
  link.href = url;
  link.download = `wine-cellar-${timestamp}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

function importData(file) {
  const reader = new FileReader();
  reader.addEventListener("load", async () => {
    try {
      const parsed = JSON.parse(reader.result);
      const result = await api("/api/import", { method: "POST", body: JSON.stringify(parsed) });
      state.wines = Array.isArray(result) ? result : result.wines;
      state.wishlist = Array.isArray(result) ? state.wishlist : result.wishlist || [];
      state.movements = Array.isArray(result) ? [] : result.movements || [];
      renderWineSuggestions();
      renderCellar();
      renderWishlist();
      renderHistory();
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

function base64urlToBuffer(value) {
  const padded = `${value}${"=".repeat((4 - (value.length % 4)) % 4)}`.replaceAll("-", "+").replaceAll("_", "/");
  const binary = atob(padded);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
  return bytes.buffer;
}

function bufferToBase64url(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
}

function publicKeyCredentialToJson(credential) {
  const response = credential.response;
  const payload = {
    id: credential.id,
    rawId: bufferToBase64url(credential.rawId),
    type: credential.type,
    response: {
      clientDataJSON: bufferToBase64url(response.clientDataJSON),
    },
  };
  if (response.attestationObject) payload.response.attestationObject = bufferToBase64url(response.attestationObject);
  if (response.authenticatorData) payload.response.authenticatorData = bufferToBase64url(response.authenticatorData);
  if (response.signature) payload.response.signature = bufferToBase64url(response.signature);
  if (response.userHandle) payload.response.userHandle = bufferToBase64url(response.userHandle);
  return payload;
}

function preparePasskeyCreationOptions(options) {
  return {
    ...options,
    challenge: base64urlToBuffer(options.challenge),
    user: { ...options.user, id: base64urlToBuffer(options.user.id) },
    excludeCredentials: (options.excludeCredentials || []).map((credential) => ({ ...credential, id: base64urlToBuffer(credential.id) })),
  };
}

function preparePasskeyRequestOptions(options) {
  return {
    ...options,
    challenge: base64urlToBuffer(options.challenge),
    allowCredentials: (options.allowCredentials || []).map((credential) => ({ ...credential, id: base64urlToBuffer(credential.id) })),
  };
}

async function registerPasskey() {
  if (!browserSupportsPasskeys()) {
    alert(t("passkeyUnavailable"));
    return;
  }
  state.appLockSuppressed = true;
  try {
    const options = await api("/api/passkeys/register/options", { method: "POST", body: JSON.stringify({}) });
    const credential = await navigator.credentials.create({ publicKey: preparePasskeyCreationOptions(options) });
    await api("/api/passkeys/register/verify", { method: "POST", body: JSON.stringify(publicKeyCredentialToJson(credential)) });
    state.passkeyRegistered = true;
    state.passkeyAvailable = true;
    applyPermissions();
    alert(t("passkeyRegistered"));
  } finally {
    state.appLockSuppressed = false;
  }
}

async function loginWithPasskey() {
  if (!browserSupportsPasskeys()) {
    alert(t("passkeyUnavailable"));
    return;
  }
  loginError.hidden = true;
  state.appLockSuppressed = true;
  try {
    const options = await api("/api/passkeys/login/options", { method: "POST", body: JSON.stringify({}) });
    const credential = await navigator.credentials.get({ publicKey: preparePasskeyRequestOptions(options) });
    const session = await api("/api/passkeys/login/verify", { method: "POST", body: JSON.stringify(publicKeyCredentialToJson(credential)) });
    state.role = session.role;
    state.authEnabled = session.auth_enabled;
    state.passkeysEnabled = Boolean(session.passkeys_enabled);
    state.passkeyAvailable = Boolean(session.passkey_available);
    state.passkeyRegistered = Boolean(session.passkey_registered);
    loginForm.reset();
    applyPermissions();
    await loadWines();
    showScreen("cellar");
  } finally {
    state.appLockSuppressed = false;
  }
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  loginError.hidden = true;
  try {
    const session = await api("/api/login", {
      method: "POST",
      body: JSON.stringify({ password: loginForm.elements.password.value }),
    });
    state.role = session.role;
    state.authEnabled = session.auth_enabled;
    state.passkeysEnabled = Boolean(session.passkeys_enabled);
    state.passkeyAvailable = Boolean(session.passkey_available);
    state.passkeyRegistered = Boolean(session.passkey_registered);
    loginForm.reset();
    applyPermissions();
    await loadWines();
    showScreen("cellar");
  } catch {
    loginError.textContent = t("invalidLogin");
    loginError.hidden = false;
  }
});

passkeyLoginButton.addEventListener("click", () => {
  loginWithPasskey().catch((error) => {
    loginError.textContent = error.message || t("invalidLogin");
    loginError.hidden = false;
  });
});

passkeyRegisterButton.addEventListener("click", () => {
  registerPasskey().catch((error) => alert(error.message || t("passkeyUnavailable")));
});

document.querySelector("#new-wine-button").addEventListener("click", () => openForm());
document.querySelector("#new-wishlist-button").addEventListener("click", () => openWishlistForm());
wineNameInput.addEventListener("change", () => applyWineTemplate(matchingWineTemplate(wineNameInput.value)));
wineNameInput.addEventListener("blur", () => applyWineTemplate(matchingWineTemplate(wineNameInput.value)));
wishlistNameInput.addEventListener("change", () => {
  const template = matchingWineTemplate(wishlistNameInput.value);
  if (!template || wishlistForm.elements.id.value) return;
  ["producer", "region", "appellation", "format", "type", "currency"].forEach((key) => {
    if (template[key] && wishlistForm.elements[key]) wishlistForm.elements[key].value = template[key];
  });
});
document.querySelector("#add-owner-button").addEventListener("click", () => addOwnerRow());
document.querySelector("#add-score-button").addEventListener("click", () => addScoreRow());
filterToggle.addEventListener("click", () => {
  const expanded = filterToggle.getAttribute("aria-expanded") === "true";
  filterToggle.setAttribute("aria-expanded", String(!expanded));
  filterPanel.hidden = expanded;
});
activeInsightFilter.addEventListener("click", clearInsightListFilter);
languageButton.addEventListener("click", () => {
  state.lang = state.lang === "it" ? "en" : "it";
  localStorage.setItem("wine-cellar-language", state.lang);
  applyTranslations();
  renderSettings();
});
document.querySelector("#settings-button").addEventListener("click", () => {
  openSettings().catch((error) => alert(error.message));
});
document.querySelector("#logout-button").addEventListener("click", async () => {
  await api("/api/logout", { method: "POST" });
  clearAuthenticatedState();
  applyPermissions();
  if (state.authEnabled) showScreen("login");
  else {
    await loadWines();
    showScreen("cellar");
  }
});

document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "hidden") {
    scheduleApplicationLock();
    return;
  }
  cancelScheduledApplicationLock();
});

window.addEventListener("pagehide", (event) => {
  cancelScheduledApplicationLock();
  if (event.persisted) return;
  lockApplication();
});

settingsForm.addEventListener("submit", (event) => {
  saveSettings(event).catch((error) => alert(error.message));
});

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  installPromptEvent = event;
  installAppButton.hidden = false;
});

window.addEventListener("appinstalled", () => {
  installPromptEvent = null;
  installAppButton.hidden = true;
});

installAppButton.addEventListener("click", async () => {
  if (!installPromptEvent) return;
  installPromptEvent.prompt();
  await installPromptEvent.userChoice;
  installPromptEvent = null;
  installAppButton.hidden = true;
});

cellarSearch.addEventListener("input", () => {
  state.search = cellarSearch.value;
  renderCellar();
});
cellarSort.addEventListener("change", () => {
  state.sort = cellarSort.value;
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
document.querySelector(".insights").addEventListener("click", (event) => {
  const row = event.target.closest("[data-insight-field]");
  if (!row) return;
  applyInsightListFilter(row.dataset.insightField, row.dataset.insightValue, row.dataset.insightScope);
});
document.querySelectorAll("[data-drink-now-tab]").forEach((button) => {
  button.addEventListener("click", () => showDrinkNowTab(button.dataset.drinkNowTab));
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
generateAiNotesButton.addEventListener("click", () => {
  generateAiNotes().catch((error) => {
    generateAiNotesButton.disabled = false;
    alert(t("generateAiNotesUnable", { error: error.message }));
  });
});
suggestAiScoresButton.addEventListener("click", () => {
  suggestAiScores().catch((error) => {
    suggestAiScoresButton.disabled = false;
    alert(t("suggestScoresUnable", { error: error.message }));
  });
});
generateAiValueButton.addEventListener("click", () => {
  generateAiValue().catch((error) => {
    generateAiValueButton.disabled = false;
    alert(t("generateAiValueUnable", { error: error.message }));
  });
});
generateDrinkWindowButton.addEventListener("click", () => {
  generateDrinkWindow().catch((error) => {
    generateDrinkWindowButton.disabled = false;
    alert(t("generateDrinkWindowUnable", { error: error.message }));
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
pairingForm.addEventListener("submit", (event) => {
  suggestPairing(event).catch((error) => alert(t("pairingUnable", { error: error.message })));
});
document.querySelector("#export-button").addEventListener("click", exportData);
document.querySelector("#import-input").addEventListener("change", (event) => {
  const [file] = event.target.files;
  if (file) importData(file);
  event.target.value = "";
});

deleteButton.addEventListener("click", deleteCurrentWine);
form.addEventListener("submit", handleSubmit);
wishlistForm.addEventListener("submit", (event) => {
  saveWishlistItem(event).catch((error) => alert(t("saveUnable", { error: error.message })));
});
deleteWishlistButton.addEventListener("click", () => {
  deleteCurrentWishlistItem().catch((error) => alert(error.message));
});
document.querySelector("#cancel-wishlist-button").addEventListener("click", () => {
  wishlistForm.hidden = true;
});
wishlistList.addEventListener("click", (event) => {
  const toggleButton = event.target.closest("[data-wishlist-toggle]");
  if (toggleButton) {
    const card = toggleButton.closest(".wishlist-card");
    const detail = card.querySelector(".wishlist-card-detail");
    const expanded = toggleButton.getAttribute("aria-expanded") === "true";
    toggleButton.setAttribute("aria-expanded", String(!expanded));
    detail.hidden = expanded;
    return;
  }
  const editButton = event.target.closest("[data-wishlist-edit]");
  if (editButton) {
    openWishlistForm(state.wishlist.find((item) => item.id === editButton.dataset.wishlistEdit));
    return;
  }
  const convertButton = event.target.closest("[data-wishlist-convert]");
  if (convertButton) {
    convertWishlistItem(convertButton.dataset.wishlistConvert).catch((error) => alert(error.message));
  }
  const strategyButton = event.target.closest("[data-wishlist-strategy]");
  if (strategyButton) {
    strategyButton.disabled = true;
    suggestWishlistStrategy(strategyButton.dataset.wishlistStrategy).catch((error) => alert(t("wishlistStrategyUnable", { error: error.message })));
  }
});

drinkNowList.addEventListener("click", (event) => {
  const sectionToggle = event.target.closest("[data-drink-now-toggle]");
  if (sectionToggle) {
    const section = sectionToggle.dataset.drinkNowToggle;
    state.drinkNowCollapsed[section] = !state.drinkNowCollapsed[section];
    renderDrinkNow();
    return;
  }

  const drinkButton = event.target.closest("[data-drink-now-drink]");
  if (drinkButton) {
    const wine = state.wines.find((item) => item.id === drinkButton.dataset.drinkNowDrink);
    if (!wine || !confirm(t("drinkConfirm", { wine: wine.name }))) return;
    const note = prompt(t("drinkNotePrompt"), "");
    if (note === null) return;
    drinkButton.disabled = true;
    markBottleDrunk(drinkButton.dataset.drinkNowDrink, note).catch((error) => {
      drinkButton.disabled = false;
      alert(t("unableBottleCount", { error: error.message }));
    });
    return;
  }

  const card = event.target.closest(".drink-now-card");
  if (!card) return;
  openDetail(state.wines.find((wine) => wine.id === card.dataset.id));
});

drinkNowList.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" && event.key !== " ") return;
  const card = event.target.closest(".drink-now-card");
  if (!card) return;
  event.preventDefault();
  openDetail(state.wines.find((wine) => wine.id === card.dataset.id));
});

pairingResult.addEventListener("click", (event) => {
  const match = event.target.closest("[data-pairing-wine]");
  if (!match) return;
  openDetail(state.wines.find((wine) => wine.id === match.dataset.pairingWine));
});

function handleMovementListClick(event) {
  const editButton = event.target.closest("[data-movement-edit]");
  if (editButton) {
    editMovement(editButton.dataset.movementEdit);
    return;
  }
  const deleteButton = event.target.closest("[data-movement-delete]");
  if (deleteButton) {
    cancelMovement(deleteButton.dataset.movementDelete);
    return;
  }
  const row = event.target.closest("[data-wine-id]");
  if (row && row.dataset.wineId) {
    const wine = state.wines.find((item) => item.id === row.dataset.wineId);
    if (wine) openDetail(wine);
  }
}

movementList?.addEventListener("click", handleMovementListClick);
historyList?.addEventListener("click", handleMovementListClick);

document.querySelectorAll(".nav-item").forEach((button) => {
  button.addEventListener("click", () => showScreen(button.dataset.screen));
});

document.querySelectorAll("[data-filter]").forEach((button) => {
  button.addEventListener("click", () => {
    state.filter = button.dataset.filter;
    document.querySelectorAll("[data-filter]").forEach((item) => item.classList.toggle("active", item === button));
    updateFilterCount();
    renderCellar();
  });
});

document.querySelectorAll("[data-owner-filter]").forEach((button) => {
  button.addEventListener("click", () => {
    state.ownerFilter = button.dataset.ownerFilter;
    document.querySelectorAll("[data-owner-filter]").forEach((item) => item.classList.toggle("active", item === button));
    updateFilterCount();
    renderCellar();
  });
});

document.querySelectorAll("[data-quantity-filter]").forEach((button) => {
  button.addEventListener("click", () => {
    state.quantityFilter = button.dataset.quantityFilter;
    document.querySelectorAll("[data-quantity-filter]").forEach((item) => item.classList.toggle("active", item === button));
    updateFilterCount();
    renderCellar();
  });
});

wineList.addEventListener("click", (event) => {
  const card = event.target.closest(".wine-card");
  if (!card) return;
  openDetail(state.wines.find((wine) => wine.id === card.dataset.id));
});

applyTranslations();
updateFilterCount();
loadSession().catch((error) => {
  wineList.innerHTML = `<p class="empty-state">${escapeHtml(error.message)}</p>`;
});

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch((error) => {
      console.warn("Service worker registration failed", error);
    });
  });
}
