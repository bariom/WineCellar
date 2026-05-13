from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
import uuid
from argparse import ArgumentParser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from secrets import token_urlsafe
from http.cookies import SimpleCookie
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "cellar.db"
RATES_URL = "https://api.frankfurter.dev/v1/latest?base=EUR&symbols=CHF,USD"
RATES_CACHE_SECONDS = 60 * 60 * 12
REFERENCE_CURRENCY = "CHF"
SUPPORTED_CURRENCIES = {"CHF", "EUR", "USD"}
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
VIEWER_PASSWORD = os.environ.get("VIEWER_PASSWORD", "")
SHARED_VIEWER_PASSWORD = os.environ.get("SHARED_VIEWER_PASSWORD", "")
AUTH_ENABLED = bool(ADMIN_PASSWORD and (VIEWER_PASSWORD or SHARED_VIEWER_PASSWORD))
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.4-nano")
OPENAI_VALUE_MODEL = os.environ.get("OPENAI_VALUE_MODEL", "gpt-5.4-mini")
OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
SESSION_COOKIE = "wine_cellar_session"
SESSIONS: dict[str, str] = {}
OPENAI_MODEL_OPTIONS = [
    {
        "id": "gpt-5.4-nano",
        "label": "GPT-5.4 nano",
        "description": "Economico e veloce. Buono per abbinamenti quotidiani.",
        "input_per_million": 0.20,
        "output_per_million": 1.25,
        "relative_cost": 1.0,
    },
    {
        "id": "gpt-5.4-mini",
        "label": "GPT-5.4 mini",
        "description": "Più preciso. Scelta utile per piatti complessi o richieste importanti.",
        "input_per_million": 0.75,
        "output_per_million": 4.50,
        "relative_cost": 3.6,
    },
    {
        "id": "gpt-5.4",
        "label": "GPT-5.4",
        "description": "Modello più forte, ma sensibilmente più costoso.",
        "input_per_million": 2.50,
        "output_per_million": 15.00,
        "relative_cost": 12.3,
    },
    {
        "id": "gpt-5.5",
        "label": "GPT-5.5",
        "description": "Massima qualità disponibile in lista, da usare solo quando serve.",
        "input_per_million": 5.00,
        "output_per_million": 30.00,
        "relative_cost": 24.6,
    },
]
OPENAI_MODEL_OPTION_IDS = {option["id"] for option in OPENAI_MODEL_OPTIONS}
APP_THEME_OPTIONS = [
    {
        "id": "classic",
        "label": "Classic cellar",
        "description": "Carta calda, accenti bordeaux e look attuale.",
        "color": "#74171b",
    },
    {
        "id": "graphite",
        "label": "Graphite",
        "description": "Neutro, piu tecnico e compatto, con accenti rubino.",
        "color": "#8f2431",
    },
    {
        "id": "alpine",
        "label": "Alpine",
        "description": "Chiaro e pulito, con accenti verdi e minerali.",
        "color": "#2f6652",
    },
    {
        "id": "midnight",
        "label": "Midnight",
        "description": "Scuro, alto contrasto, pensato per uso serale.",
        "color": "#a63d4a",
    },
    {
        "id": "dusk",
        "label": "Dusk",
        "description": "Scuro piu morbido, con fondo grafite caldo e contrasto meno marcato.",
        "color": "#8f4a58",
    },
    {
        "id": "champagne",
        "label": "Champagne",
        "description": "Luminoso e morbido, con accenti dorati e rosa.",
        "color": "#9f5d16",
    },
]
APP_THEME_OPTION_IDS = {option["id"] for option in APP_THEME_OPTIONS}
PUBLIC_STATIC_PATHS = {
    "/",
    "/index.html",
    "/styles.css",
    "/app.js",
    "/favicon.svg",
    "/manifest.webmanifest",
    "/sw.js",
    "/pwa-icon.svg",
    "/pwa-icon-192.png",
    "/pwa-icon-512.png",
}

FIELDS = [
    "id",
    "name",
    "producer",
    "vintage",
    "quantity",
    "format",
    "type",
    "region",
    "appellation",
    "price",
    "current_value",
    "currency",
    "merchant",
    "order_date",
    "expected_delivery",
    "status",
    "owner_share_pct",
    "owners",
    "scores",
    "notes",
    "ai_notes",
    "drink_from",
    "drink_peak_from",
    "drink_peak_to",
    "drink_to",
    "drink_window_notes",
    "ai_value_notes",
]

SEED_WINES = [
    {
        "id": "seed-domaine-chevalier-2020",
        "name": "Domaine de Chevalier",
        "producer": "Domaine de Chevalier",
        "vintage": "2020",
        "quantity": 3,
        "format": "Magnum (1.5L)",
        "type": "Red",
        "region": "Bordeaux",
        "appellation": "Pessac-Leognan",
        "price": 160,
        "currency": "CHF",
        "merchant": "Millesima",
        "order_date": "2021-05-12",
        "expected_delivery": "2023-10-01",
        "status": "Delivered",
    },
    {
        "id": "seed-yquem-2021",
        "name": "Chateau d'Yquem",
        "producer": "Chateau d'Yquem",
        "vintage": "2021",
        "quantity": 12,
        "format": "Half (375ml)",
        "type": "Dessert",
        "region": "Bordeaux",
        "appellation": "Sauternes",
        "price": 180,
        "currency": "CHF",
        "merchant": "Berry Bros & Rudd",
        "order_date": "2022-06-10",
        "expected_delivery": "2024-05-01",
        "status": "Delivered",
    },
    {
        "id": "seed-tignanello-2021",
        "name": "Tignanello",
        "producer": "Marchesi Antinori",
        "vintage": "2021",
        "quantity": 12,
        "format": "Bottle (750ml)",
        "type": "Red",
        "region": "Tuscany",
        "appellation": "Toscana IGT",
        "price": 140,
        "currency": "CHF",
        "merchant": "Berry Bros & Rudd",
        "order_date": "2022-11-18",
        "expected_delivery": "2024-10-01",
        "status": "Shipped",
    },
    {
        "id": "seed-opus-one-2021",
        "name": "Opus One",
        "producer": "Opus One Winery",
        "vintage": "2021",
        "quantity": 6,
        "format": "Bottle (750ml)",
        "type": "Red",
        "region": "Napa Valley",
        "appellation": "Oakville",
        "price": 350,
        "currency": "CHF",
        "merchant": "K&L",
        "order_date": "2022-09-03",
        "expected_delivery": "2024-12-01",
        "status": "Ordered",
    },
    {
        "id": "seed-margaux-2022",
        "name": "Chateau Margaux",
        "producer": "Chateau Margaux",
        "vintage": "2022",
        "quantity": 6,
        "format": "Bottle (750ml)",
        "type": "Red",
        "region": "Bordeaux",
        "appellation": "Margaux",
        "price": 520,
        "currency": "CHF",
        "merchant": "Millesima",
        "order_date": "2023-06-22",
        "expected_delivery": "2025-05-01",
        "status": "Ordered",
    },
    {
        "id": "seed-montrachet-2023",
        "name": "Montrachet Grand Cru",
        "producer": "Domaine Leflaive",
        "vintage": "2023",
        "quantity": 1,
        "format": "Bottle (750ml)",
        "type": "White",
        "region": "Burgundy",
        "appellation": "Montrachet",
        "price": 1650,
        "currency": "CHF",
        "merchant": "Justerini & Brooks",
        "order_date": "2024-07-15",
        "expected_delivery": "2026-09-01",
        "status": "Ordered",
    },
]

CATALOG_PATH = ROOT / "data" / "wine_catalog.json"


def load_catalog_wines() -> tuple[int, list[dict]]:
    raw_catalog = CATALOG_PATH.read_text(encoding="utf-8")
    catalog_version = int(hashlib.sha256(raw_catalog.encode("utf-8")).hexdigest()[:12], 16)
    catalog_wines = json.loads(raw_catalog)
    if not isinstance(catalog_wines, list):
        raise ValueError("Wine catalog must be a JSON list")
    required_fields = {"name", "producer", "region", "appellation", "type", "format"}
    for index, wine in enumerate(catalog_wines, start=1):
        if not isinstance(wine, dict):
            raise ValueError(f"Wine catalog item {index} must be an object")
        missing_fields = required_fields - set(wine)
        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(f"Wine catalog item {index} is missing: {missing}")
    return catalog_version, catalog_wines


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS wines (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                producer TEXT NOT NULL,
                vintage TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                format TEXT NOT NULL,
                type TEXT NOT NULL,
                region TEXT,
                appellation TEXT,
                price REAL NOT NULL,
                current_value REAL,
                currency TEXT NOT NULL,
                merchant TEXT NOT NULL,
                order_date TEXT,
                expected_delivery TEXT,
                status TEXT NOT NULL,
                owner_share_pct REAL NOT NULL DEFAULT 100,
                owners_json TEXT NOT NULL DEFAULT '[]',
                notes TEXT NOT NULL DEFAULT '',
                ai_notes TEXT NOT NULL DEFAULT '',
                drink_from INTEGER,
                drink_peak_from INTEGER,
                drink_peak_to INTEGER,
                drink_to INTEGER,
                drink_window_notes TEXT NOT NULL DEFAULT '',
                ai_value_notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        ensure_column(conn, "wines", "owner_share_pct", "REAL NOT NULL DEFAULT 100")
        ensure_column(conn, "wines", "owners_json", "TEXT NOT NULL DEFAULT '[]'")
        ensure_column(conn, "wines", "current_value", "REAL")
        ensure_column(conn, "wines", "notes", "TEXT NOT NULL DEFAULT ''")
        ensure_column(conn, "wines", "ai_notes", "TEXT NOT NULL DEFAULT ''")
        ensure_column(conn, "wines", "drink_from", "INTEGER")
        ensure_column(conn, "wines", "drink_peak_from", "INTEGER")
        ensure_column(conn, "wines", "drink_peak_to", "INTEGER")
        ensure_column(conn, "wines", "drink_to", "INTEGER")
        ensure_column(conn, "wines", "drink_window_notes", "TEXT NOT NULL DEFAULT ''")
        ensure_column(conn, "wines", "ai_value_notes", "TEXT NOT NULL DEFAULT ''")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS exchange_rates (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                rate_date TEXT NOT NULL,
                rates_json TEXT NOT NULL,
                fetched_at INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sales (
                id TEXT PRIMARY KEY,
                wine_id TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                sale_price REAL NOT NULL,
                currency TEXT NOT NULL,
                buyer TEXT NOT NULL,
                sold_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                unit_cost REAL NOT NULL,
                profit_loss REAL NOT NULL,
                FOREIGN KEY (wine_id) REFERENCES wines(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS wine_scores (
                id TEXT PRIMARY KEY,
                wine_id TEXT NOT NULL,
                critic TEXT NOT NULL,
                score TEXT NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (wine_id) REFERENCES wines(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS wine_catalog (
                name TEXT PRIMARY KEY,
                producer TEXT NOT NULL,
                region TEXT,
                appellation TEXT,
                type TEXT NOT NULL,
                format TEXT NOT NULL,
                catalog_version INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS wishlist (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                producer TEXT,
                vintage TEXT,
                format TEXT NOT NULL DEFAULT 'Bottle (750ml)',
                type TEXT NOT NULL DEFAULT 'Red',
                region TEXT,
                appellation TEXT,
                target_price REAL,
                currency TEXT NOT NULL DEFAULT 'CHF',
                merchant TEXT,
                purpose TEXT NOT NULL DEFAULT 'Drink',
                priority TEXT NOT NULL DEFAULT 'Medium',
                status TEXT NOT NULL DEFAULT 'Monitor',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        ensure_column(conn, "wishlist", "purpose", "TEXT NOT NULL DEFAULT 'Drink'")
        seed_catalog(conn)
        count = conn.execute("SELECT COUNT(*) FROM wines").fetchone()[0]
        if count == 0:
            for wine in SEED_WINES:
                insert_wine(conn, wine)


def ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def seed_catalog(conn: sqlite3.Connection) -> None:
    catalog_version, catalog_wines = load_catalog_wines()
    current_version = conn.execute("SELECT COALESCE(MAX(catalog_version), 0) FROM wine_catalog").fetchone()[0]
    if current_version == catalog_version:
        return
    conn.execute("DELETE FROM wine_catalog")
    conn.executemany(
        """
        INSERT INTO wine_catalog (name, producer, region, appellation, type, format, catalog_version)
        VALUES (:name, :producer, :region, :appellation, :type, :format, :catalog_version)
        """,
        [{**wine, "catalog_version": catalog_version} for wine in catalog_wines],
    )


def list_catalog_wines() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT name, producer, region, appellation, type, format
            FROM wine_catalog
            ORDER BY name ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_setting(conn: sqlite3.Connection, key: str, default: str) -> str:
    row = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
    return str(row["value"]) if row else default


def get_pairing_model(conn: sqlite3.Connection) -> str:
    model = get_setting(conn, "pairing_model", OPENAI_MODEL)
    return model if model in OPENAI_MODEL_OPTION_IDS else OPENAI_MODEL


def get_app_theme(conn: sqlite3.Connection) -> str:
    theme = get_setting(conn, "app_theme", "classic")
    return theme if theme in APP_THEME_OPTION_IDS else "classic"


def get_app_settings() -> dict:
    with connect() as conn:
        pairing_model = get_pairing_model(conn)
        app_theme = get_app_theme(conn)
    return {
        "pairing_model": pairing_model,
        "model_options": OPENAI_MODEL_OPTIONS,
        "app_theme": app_theme,
        "theme_options": APP_THEME_OPTIONS,
        "pricing_note": "Prezzi indicativi OpenAI standard per 1M token. Il costo reale dipende da input e output della richiesta.",
    }


def update_app_settings(payload: dict) -> dict:
    pairing_model = str(payload.get("pairing_model", "")).strip()
    if pairing_model not in OPENAI_MODEL_OPTION_IDS:
        raise ValueError("Invalid pairing model")
    app_theme = str(payload.get("app_theme", "classic")).strip()
    if app_theme not in APP_THEME_OPTION_IDS:
        raise ValueError("Invalid app theme")

    with connect() as conn:
        conn.execute(
            """
            INSERT INTO app_settings (key, value, updated_at)
            VALUES ('pairing_model', ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
            """,
            (pairing_model,),
        )
        conn.execute(
            """
            INSERT INTO app_settings (key, value, updated_at)
            VALUES ('app_theme', ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
            """,
            (app_theme,),
        )
    return get_app_settings()


def list_wines() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, name, producer, vintage, quantity, format, type, region, appellation,
                   price, current_value, currency, merchant, order_date, expected_delivery, status,
                   owner_share_pct, owners_json, notes, ai_notes,
                   drink_from, drink_peak_from, drink_peak_to, drink_to, drink_window_notes,
                   ai_value_notes
            FROM wines
            ORDER BY expected_delivery DESC, name ASC
            """
        ).fetchall()
        wines = [wine_from_row(row) for row in rows]
        attach_scores(conn, wines)
    return wines


def visible_wines(role: str) -> list[dict]:
    wines = list_wines()
    if role == "shared_viewer":
        return [wine for wine in wines if is_shared_position(wine)]
    return wines


def list_sales(wine_id: str, role: str = "admin") -> list[dict]:
    with connect() as conn:
        wine = get_wine(conn, wine_id)
        if not wine:
            raise LookupError("Wine not found")
        if role == "shared_viewer" and not is_shared_position(wine):
            raise LookupError("Wine not found")
        rows = conn.execute(
            """
            SELECT id, wine_id, quantity, sale_price, currency, buyer, sold_at, unit_cost, profit_loss
            FROM sales
            WHERE wine_id = ?
            ORDER BY sold_at DESC
            """,
            (wine_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def list_wishlist() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, name, producer, vintage, format, type, region, appellation,
                   target_price, currency, merchant, purpose, priority, status, notes
            FROM wishlist
            ORDER BY
                CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END,
                updated_at DESC,
                name ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_wishlist_item(conn: sqlite3.Connection, item_id: str) -> dict | None:
    row = conn.execute(
        """
        SELECT id, name, producer, vintage, format, type, region, appellation,
               target_price, currency, merchant, purpose, priority, status, notes
        FROM wishlist
        WHERE id = ?
        """,
        (item_id,),
    ).fetchone()
    return dict(row) if row else None


def clean_wishlist_item(payload: dict, item_id: str | None = None) -> dict:
    if not str(payload.get("name", "")).strip():
        raise ValueError("Name is required")
    currency = str(payload.get("currency", "CHF")).strip().upper()
    if currency not in SUPPORTED_CURRENCIES:
        raise ValueError(f"Unsupported currency: {currency}")
    priority = str(payload.get("priority", "Medium")).strip()
    if priority not in {"High", "Medium", "Low"}:
        raise ValueError("Unsupported priority")
    purpose = str(payload.get("purpose", "Drink")).strip()
    if purpose not in {"Drink", "Invest", "Gift", "Cellar", "Compare"}:
        raise ValueError("Unsupported wishlist purpose")
    status = str(payload.get("status", "Monitor")).strip()
    if status not in {"Evaluate", "Monitor", "Buy", "Skipped"}:
        raise ValueError("Unsupported wishlist status")
    return {
        "id": item_id or payload.get("id") or str(uuid.uuid4()),
        "name": str(payload.get("name", "")).strip(),
        "producer": str(payload.get("producer", "")).strip(),
        "vintage": str(payload.get("vintage", "")).strip(),
        "format": str(payload.get("format", "Bottle (750ml)")).strip(),
        "type": str(payload.get("type", "Red")).strip(),
        "region": str(payload.get("region", "")).strip(),
        "appellation": str(payload.get("appellation", "")).strip(),
        "target_price": clean_optional_float(payload.get("target_price")),
        "currency": currency,
        "merchant": str(payload.get("merchant", "")).strip(),
        "purpose": purpose,
        "priority": priority,
        "status": status,
        "notes": str(payload.get("notes", "")).strip(),
    }


def upsert_wishlist_item(payload: dict, item_id: str | None = None) -> dict:
    data = clean_wishlist_item(payload, item_id)
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO wishlist (
                id, name, producer, vintage, format, type, region, appellation,
                target_price, currency, merchant, purpose, priority, status, notes
            )
            VALUES (
                :id, :name, :producer, :vintage, :format, :type, :region, :appellation,
                :target_price, :currency, :merchant, :purpose, :priority, :status, :notes
            )
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                producer = excluded.producer,
                vintage = excluded.vintage,
                format = excluded.format,
                type = excluded.type,
                region = excluded.region,
                appellation = excluded.appellation,
                target_price = excluded.target_price,
                currency = excluded.currency,
                merchant = excluded.merchant,
                purpose = excluded.purpose,
                priority = excluded.priority,
                status = excluded.status,
                notes = excluded.notes,
                updated_at = CURRENT_TIMESTAMP
            """,
            data,
        )
    return data


def delete_wishlist_item(item_id: str) -> bool:
    with connect() as conn:
        cursor = conn.execute("DELETE FROM wishlist WHERE id = ?", (item_id,))
        return cursor.rowcount > 0


def convert_wishlist_item(item_id: str, payload: dict) -> dict:
    with connect() as conn:
        item = get_wishlist_item(conn, item_id)
        if not item:
            raise LookupError("Wishlist item not found")
        wine_payload = {
            "name": item["name"],
            "producer": item["producer"] or "TBD",
            "vintage": item["vintage"] or "TBD",
            "region": item["region"],
            "appellation": item["appellation"],
            "format": item["format"],
            "type": item["type"],
            "quantity": int(payload.get("quantity") or 1),
            "price": payload.get("price") if payload.get("price") not in (None, "") else item["target_price"] or 0,
            "current_value": None,
            "currency": item["currency"],
            "merchant": payload.get("merchant") or item["merchant"] or "TBD",
            "order_date": payload.get("order_date") or "",
            "expected_delivery": payload.get("expected_delivery") or "",
            "status": "Ordered",
            "owner_share_pct": 100,
            "owners": [],
            "scores": [],
            "notes": item["notes"],
        }
        wine = insert_wine(conn, wine_payload)
        conn.execute("DELETE FROM wishlist WHERE id = ?", (item_id,))
        saved = get_wine(conn, wine["id"])
    return saved


def clean_wishlist_strategy_payload(payload: dict) -> dict:
    recommendation = str(payload.get("recommendation", "")).strip().lower()
    if recommendation not in {"buy", "monitor", "avoid"}:
        recommendation = "monitor"
    summary = str(payload.get("summary", "")).strip()
    market_assumption = str(payload.get("market_assumption", "")).strip()

    def clean_text_list(value: object, limit: int) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value[:limit] if str(item).strip()]

    alternative_payload = payload.get("alternative", {})
    alternative = None
    if isinstance(alternative_payload, dict):
        name = str(alternative_payload.get("name", "")).strip()
        if name:
            alternative = {
                "name": name,
                "producer": str(alternative_payload.get("producer", "")).strip(),
                "reason": str(alternative_payload.get("reason", "")).strip(),
                "price_hint": str(alternative_payload.get("price_hint", "")).strip(),
            }

    return {
        "recommendation": recommendation,
        "summary": summary,
        "market_assumption": market_assumption,
        "rationale": clean_text_list(payload.get("rationale", []), 4),
        "risks": clean_text_list(payload.get("risks", []), 4),
        "actions": clean_text_list(payload.get("actions", []), 4),
        "alternative": alternative,
    }


def suggest_wishlist_strategy(item_id: str) -> dict:
    with connect() as conn:
        item = get_wishlist_item(conn, item_id)
        if not item:
            raise LookupError("Wishlist item not found")

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not configured")

    context = {
        "wishlist_item": item,
        "purpose_meaning": {
            "Drink": "vino da bere",
            "Invest": "vino da investimento",
            "Gift": "vino da regalare",
            "Cellar": "vino da mettere in cantina",
            "Compare": "vino da confrontare con alternative simili",
        },
        "existing_cellar_near_matches": [
            {
                "name": wine["name"],
                "producer": wine["producer"],
                "vintage": wine["vintage"],
                "region": wine.get("region", ""),
                "appellation": wine.get("appellation", ""),
                "current_value": wine.get("current_value"),
                "price": wine.get("price"),
                "currency": wine.get("currency"),
                "scores": wine.get("scores", []),
            }
            for wine in list_wines()[:80]
            if (
                item.get("producer")
                and str(item.get("producer", "")).lower() in str(wine.get("producer", "")).lower()
            )
            or (
                item.get("region")
                and str(item.get("region", "")).lower() == str(wine.get("region", "")).lower()
            )
        ][:12],
    }
    request_payload = {
        "model": OPENAI_VALUE_MODEL,
        "instructions": (
            "Sei un consulente privato per collezionismo vino. Devi suggerire una strategia "
            "pratica per un vino in wishlist in base allo scopo dell'osservazione. Rispondi "
            "solo con JSON valido, senza Markdown e senza testo prima o dopo. Non presentare "
            "la risposta come consulenza finanziaria certa o quotazione live. Se non hai dati "
            "di mercato affidabili o aggiornati, dichiaralo chiaramente in market_assumption e "
            "usa una raccomandazione prudente. Per purpose Invest valuta liquidita, reputazione "
            "del produttore, annata, prezzo target, track record e rischio di immobilizzo; se "
            "il profilo non e convincente, recommendation deve essere avoid o monitor e, se "
            "possibile, proponi una alternativa paritetica per fascia prezzo/stile. Per purpose "
            "Drink privilegia piacere di bevuta, finestra e prezzo. Usa italiano corretto."
        ),
        "input": (
            "Contesto wishlist e cantina:\n"
            f"{json.dumps(context, ensure_ascii=False)}\n\n"
            "Restituisci solo questo oggetto JSON: "
            "{\"recommendation\":\"buy|monitor|avoid\",\"summary\":\"decisione breve\","
            "\"market_assumption\":\"limiti dei dati usati\","
            "\"rationale\":[\"motivo\"],\"risks\":[\"rischio\"],\"actions\":[\"prossimo passo\"],"
            "\"alternative\":{\"name\":\"vino alternativo\",\"producer\":\"produttore\","
            "\"price_hint\":\"fascia prezzo simile\",\"reason\":\"perche e paritetico o migliore\"}}. "
            "Se non hai una alternativa credibile, usa alternative null."
        ),
        "max_output_tokens": 900,
    }
    request = Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(request_payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "WineCellar/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=40) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"OpenAI request failed: {error_body or exc.reason}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise ValueError(f"OpenAI request failed: {exc}") from exc

    raw_text = extract_response_text(response_payload)
    if not raw_text:
        raise ValueError("OpenAI response did not include text")
    return clean_wishlist_strategy_payload(parse_json_object(raw_text))


def wine_from_row(row: sqlite3.Row) -> dict:
    wine = dict(row)
    owners_json = wine.pop("owners_json", "[]")
    try:
        owners = json.loads(owners_json or "[]")
    except json.JSONDecodeError:
        owners = []
    wine["owners"] = owners if isinstance(owners, list) else []
    wine.setdefault("scores", [])
    return wine


def wine_from_data(data: dict) -> dict:
    wine = dict(data)
    owners_json = wine.pop("owners_json", "[]")
    wine["owners"] = json.loads(owners_json or "[]")
    wine["scores"] = wine.get("scores", [])
    return wine


def attach_scores(conn: sqlite3.Connection, wines: list[dict]) -> None:
    if not wines:
        return
    wine_ids = [wine["id"] for wine in wines]
    placeholders = ",".join("?" for _ in wine_ids)
    rows = conn.execute(
        f"""
        SELECT id, wine_id, critic, score, note
        FROM wine_scores
        WHERE wine_id IN ({placeholders})
        ORDER BY critic ASC, score DESC
        """,
        wine_ids,
    ).fetchall()
    scores_by_wine: dict[str, list[dict]] = {wine_id: [] for wine_id in wine_ids}
    for row in rows:
        score = dict(row)
        scores_by_wine.setdefault(score.pop("wine_id"), []).append(score)
    for wine in wines:
        wine["scores"] = scores_by_wine.get(wine["id"], [])


def get_rates(force_refresh: bool = False) -> dict:
    cached = read_cached_rates()
    now = int(time.time())
    if cached and not force_refresh and now - cached["fetched_at"] < RATES_CACHE_SECONDS:
        return cached

    try:
        request = Request(RATES_URL, headers={"User-Agent": "WineCellar/1.0"})
        with urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
        rates = payload["rates"]
        chf_per_eur = float(rates["CHF"])
        usd_per_eur = float(rates["USD"])
        converted = {
            "reference": REFERENCE_CURRENCY,
            "date": payload["date"],
            "rates_to_chf": {
                "CHF": 1.0,
                "EUR": chf_per_eur,
                "USD": chf_per_eur / usd_per_eur,
            },
            "source": "Frankfurter API / European Central Bank reference rates",
            "source_url": RATES_URL,
            "fetched_at": now,
            "cached": False,
        }
        write_cached_rates(converted)
        return converted
    except (KeyError, ValueError, HTTPError, URLError, TimeoutError, OSError):
        if cached:
            cached["cached"] = True
            return cached
        raise ValueError("Exchange rates are unavailable and no cached rates exist yet")


def read_cached_rates() -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT rate_date, rates_json, fetched_at FROM exchange_rates WHERE id = 1").fetchone()
    if not row:
        return None
    return {
        "reference": REFERENCE_CURRENCY,
        "date": row["rate_date"],
        "rates_to_chf": json.loads(row["rates_json"]),
        "source": "Cached Frankfurter API / European Central Bank reference rates",
        "source_url": RATES_URL,
        "fetched_at": row["fetched_at"],
        "cached": True,
    }


def write_cached_rates(rate_payload: dict) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO exchange_rates (id, rate_date, rates_json, fetched_at)
            VALUES (1, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                rate_date = excluded.rate_date,
                rates_json = excluded.rates_json,
                fetched_at = excluded.fetched_at
            """,
            (
                rate_payload["date"],
                json.dumps(rate_payload["rates_to_chf"]),
                rate_payload["fetched_at"],
            ),
        )


def convert_to_chf(amount: float, currency: str, rates: dict) -> float:
    normalized_currency = currency.upper()
    rate = rates["rates_to_chf"].get(normalized_currency)
    if rate is None:
        raise ValueError(f"Unsupported currency: {currency}")
    return amount * rate


def get_summary(role: str = "admin") -> dict:
    wines = visible_wines(role)
    rates = get_rates()
    shared_wines = [wine for wine in wines if is_shared_position(wine)]
    total_chf = sum(
        convert_to_chf(personal_position_value(wine), wine["currency"], rates)
        for wine in wines
    )
    current_chf = sum(
        convert_to_chf(personal_current_value(wine), wine["currency"], rates)
        for wine in wines
    )
    gross_total_chf = sum(
        convert_to_chf(float(wine["price"] or 0) * int(wine["quantity"] or 0), wine["currency"], rates)
        for wine in wines
    )
    gross_current_chf = sum(
        convert_to_chf(unit_current_value(wine) * int(wine["quantity"] or 0), wine["currency"], rates)
        for wine in wines
    )
    shared_total_chf = sum(
        convert_to_chf(float(wine["price"] or 0) * int(wine["quantity"] or 0), wine["currency"], rates)
        for wine in shared_wines
    )
    shared_current_chf = sum(
        convert_to_chf(unit_current_value(wine) * int(wine["quantity"] or 0), wine["currency"], rates)
        for wine in shared_wines
    )
    cellar = sum(personal_quantity(wine) for wine in wines if wine["status"] == "Delivered")
    ordered = sum(personal_quantity(wine) for wine in wines if wine["status"] != "Delivered")
    gross_cellar = sum(int(wine["quantity"] or 0) for wine in wines if wine["status"] == "Delivered")
    gross_ordered = sum(int(wine["quantity"] or 0) for wine in wines if wine["status"] != "Delivered")
    shared_cellar = sum(int(wine["quantity"] or 0) for wine in shared_wines if wine["status"] == "Delivered")
    shared_ordered = sum(int(wine["quantity"] or 0) for wine in shared_wines if wine["status"] != "Delivered")
    regions: dict[str, float] = {}
    colors: dict[str, float] = {}
    shared_regions: dict[str, int] = {}
    shared_colors: dict[str, int] = {}
    gross_regions: dict[str, int] = {}
    gross_colors: dict[str, int] = {}
    for wine in wines:
        region = wine["region"] or "Unspecified"
        color = wine["type"] or "Unspecified"
        regions[region] = regions.get(region, 0) + personal_quantity(wine)
        colors[color] = colors.get(color, 0) + personal_quantity(wine)
        gross_regions[region] = gross_regions.get(region, 0) + int(wine["quantity"] or 0)
        gross_colors[color] = gross_colors.get(color, 0) + int(wine["quantity"] or 0)
    for wine in shared_wines:
        region = wine["region"] or "Unspecified"
        color = wine["type"] or "Unspecified"
        shared_regions[region] = shared_regions.get(region, 0) + int(wine["quantity"] or 0)
        shared_colors[color] = shared_colors.get(color, 0) + int(wine["quantity"] or 0)

    return {
        "reference_currency": REFERENCE_CURRENCY,
        "total_invested": round(total_chf, 2),
        "current_value": round(current_chf, 2),
        "unrealized_gain_loss": round(current_chf - total_chf, 2),
        "cellar_bottles": round(cellar, 2),
        "ordered_bottles": round(ordered, 2),
        "gross_total_value": round(gross_total_chf, 2),
        "gross_current_value": round(gross_current_chf, 2),
        "gross_unrealized_gain_loss": round(gross_current_chf - gross_total_chf, 2),
        "gross_cellar_bottles": gross_cellar,
        "gross_ordered_bottles": gross_ordered,
        "shared_total_value": round(shared_total_chf, 2),
        "shared_current_value": round(shared_current_chf, 2),
        "shared_unrealized_gain_loss": round(shared_current_chf - shared_total_chf, 2),
        "shared_cellar_bottles": shared_cellar,
        "shared_ordered_bottles": shared_ordered,
        "regions": [
            {"region": region, "bottles": bottles}
            for region, bottles in sorted(regions.items(), key=lambda item: item[1], reverse=True)[:5]
        ],
        "colors": [
            {"type": color, "bottles": bottles}
            for color, bottles in sorted(colors.items(), key=lambda item: item[1], reverse=True)
        ],
        "shared_regions": [
            {"region": region, "bottles": bottles}
            for region, bottles in sorted(shared_regions.items(), key=lambda item: item[1], reverse=True)[:5]
        ],
        "shared_colors": [
            {"type": color, "bottles": bottles}
            for color, bottles in sorted(shared_colors.items(), key=lambda item: item[1], reverse=True)
        ],
        "gross_regions": [
            {"region": region, "bottles": bottles}
            for region, bottles in sorted(gross_regions.items(), key=lambda item: item[1], reverse=True)[:5]
        ],
        "gross_colors": [
            {"type": color, "bottles": bottles}
            for color, bottles in sorted(gross_colors.items(), key=lambda item: item[1], reverse=True)
        ],
        "rates": rates,
    }


def clean_wine(payload: dict, wine_id: str | None = None) -> dict:
    required = ["name", "producer", "vintage", "quantity", "format", "type", "price", "currency", "merchant", "status"]
    missing = [field for field in required if payload.get(field) in (None, "")]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    currency = str(payload.get("currency", "CHF")).strip().upper()
    if currency not in SUPPORTED_CURRENCIES:
        raise ValueError(f"Unsupported currency: {currency}")

    owner_share_pct = float(payload.get("owner_share_pct", 100) or 0)
    owners = clean_owners(payload.get("owners", []))
    scores = clean_scores(payload.get("scores", []))
    total_share = owner_share_pct + sum(float(owner["share_pct"]) for owner in owners)
    if owner_share_pct < 0 or owner_share_pct > 100:
        raise ValueError("Your ownership share must be between 0 and 100")
    if total_share > 100.0001:
        raise ValueError("Ownership shares cannot exceed 100%")

    return {
        "id": wine_id or payload.get("id") or str(uuid.uuid4()),
        "name": str(payload.get("name", "")).strip(),
        "producer": str(payload.get("producer", "")).strip(),
        "vintage": str(payload.get("vintage", "")).strip(),
        "quantity": int(payload.get("quantity") or 0),
        "format": str(payload.get("format", "")).strip(),
        "type": str(payload.get("type", "")).strip(),
        "region": str(payload.get("region", "")).strip(),
        "appellation": str(payload.get("appellation", "")).strip(),
        "price": float(payload.get("price") or 0),
        "current_value": clean_optional_float(payload.get("current_value")),
        "currency": currency,
        "merchant": str(payload.get("merchant", "")).strip(),
        "order_date": str(payload.get("order_date", "")).strip(),
        "expected_delivery": str(payload.get("expected_delivery", "")).strip(),
        "status": str(payload.get("status", "Ordered")).strip(),
        "owner_share_pct": owner_share_pct,
        "owners_json": json.dumps(owners),
        "scores": scores,
        "notes": str(payload.get("notes", "")).strip(),
        "ai_notes": str(payload.get("ai_notes", "")).strip(),
        "drink_from": clean_optional_int(payload.get("drink_from")),
        "drink_peak_from": clean_optional_int(payload.get("drink_peak_from")),
        "drink_peak_to": clean_optional_int(payload.get("drink_peak_to")),
        "drink_to": clean_optional_int(payload.get("drink_to")),
        "drink_window_notes": str(payload.get("drink_window_notes", "")).strip(),
        "ai_value_notes": str(payload.get("ai_value_notes", "")).strip(),
    }


def clean_owners(raw_owners: object) -> list[dict]:
    if raw_owners in (None, ""):
        return []
    if not isinstance(raw_owners, list):
        raise ValueError("Owners must be a list")

    owners = []
    for raw_owner in raw_owners:
        if not isinstance(raw_owner, dict):
            raise ValueError("Each owner must be an object")
        name = str(raw_owner.get("name", "")).strip()
        if not name:
            continue
        share_pct = float(raw_owner.get("share_pct", 0) or 0)
        if share_pct < 0 or share_pct > 100:
            raise ValueError("Owner shares must be between 0 and 100")
        owners.append({"name": name, "share_pct": share_pct})
    return owners


def clean_scores(raw_scores: object) -> list[dict]:
    if raw_scores in (None, ""):
        return []
    if not isinstance(raw_scores, list):
        raise ValueError("Scores must be a list")

    scores = []
    for raw_score in raw_scores:
        if not isinstance(raw_score, dict):
            raise ValueError("Each score must be an object")
        critic = str(raw_score.get("critic", "")).strip()
        score = str(raw_score.get("score", "")).strip()
        note = str(raw_score.get("note", "")).strip()
        if not critic and not score and not note:
            continue
        if not critic or not score:
            raise ValueError("Each score requires critic and score")
        scores.append({"critic": critic, "score": score, "note": note})
    return scores


def clean_optional_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def clean_optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def personal_quantity(wine: dict) -> float:
    return int(wine["quantity"] or 0) * float(wine.get("owner_share_pct", 100) or 0) / 100


def personal_position_value(wine: dict) -> float:
    return float(wine["price"] or 0) * personal_quantity(wine)


def unit_current_value(wine: dict) -> float:
    return float(wine["current_value"] if wine.get("current_value") not in (None, "") else wine["price"] or 0)


def personal_current_value(wine: dict) -> float:
    return unit_current_value(wine) * personal_quantity(wine)


def is_shared_position(wine: dict) -> bool:
    other_share = sum(float(owner.get("share_pct", 0) or 0) for owner in wine.get("owners", []))
    return float(wine.get("owner_share_pct", 100) or 0) < 100 or other_share > 0


def get_wine(conn: sqlite3.Connection, wine_id: str) -> dict | None:
    row = conn.execute(
        """
        SELECT id, name, producer, vintage, quantity, format, type, region, appellation,
               price, current_value, currency, merchant, order_date, expected_delivery, status,
               owner_share_pct, owners_json, notes, ai_notes,
               drink_from, drink_peak_from, drink_peak_to, drink_to, drink_window_notes,
               ai_value_notes
        FROM wines
        WHERE id = ?
        """,
        (wine_id,),
    ).fetchone()
    if not row:
        return None
    wine = wine_from_row(row)
    attach_scores(conn, [wine])
    return wine


def replace_wine_scores(conn: sqlite3.Connection, wine_id: str, scores: list[dict]) -> None:
    conn.execute("DELETE FROM wine_scores WHERE wine_id = ?", (wine_id,))
    conn.executemany(
        """
        INSERT INTO wine_scores (id, wine_id, critic, score, note)
        VALUES (:id, :wine_id, :critic, :score, :note)
        """,
        [{**score, "id": str(uuid.uuid4()), "wine_id": wine_id} for score in scores],
    )


def insert_wine(conn: sqlite3.Connection, wine: dict) -> dict:
    data = clean_wine(wine)
    scores = data.pop("scores", [])
    conn.execute(
        """
        INSERT INTO wines (
            id, name, producer, vintage, quantity, format, type, region, appellation,
            price, current_value, currency, merchant, order_date, expected_delivery, status,
            owner_share_pct, owners_json, notes, ai_notes,
            drink_from, drink_peak_from, drink_peak_to, drink_to, drink_window_notes,
            ai_value_notes
        )
        VALUES (
            :id, :name, :producer, :vintage, :quantity, :format, :type, :region, :appellation,
            :price, :current_value, :currency, :merchant, :order_date, :expected_delivery, :status,
            :owner_share_pct, :owners_json, :notes, :ai_notes,
            :drink_from, :drink_peak_from, :drink_peak_to, :drink_to, :drink_window_notes,
            :ai_value_notes
        )
        """,
        data,
    )
    replace_wine_scores(conn, data["id"], scores)
    data["scores"] = scores
    return data


def upsert_wine(payload: dict, wine_id: str | None = None) -> dict:
    preserve_ai_notes = wine_id is not None and "ai_notes" not in payload
    preserve_ai_value_notes = wine_id is not None and "ai_value_notes" not in payload
    drink_window_fields = ["drink_from", "drink_peak_from", "drink_peak_to", "drink_to", "drink_window_notes"]
    preserve_drink_window = wine_id is not None and not any(field in payload for field in drink_window_fields)
    data = clean_wine(payload, wine_id)
    scores = data.pop("scores", [])
    with connect() as conn:
        if preserve_ai_notes or preserve_ai_value_notes or preserve_drink_window:
            existing = get_wine(conn, data["id"])
            if existing:
                if preserve_ai_notes:
                    data["ai_notes"] = existing.get("ai_notes", "")
                if preserve_ai_value_notes:
                    data["ai_value_notes"] = existing.get("ai_value_notes", "")
                if preserve_drink_window:
                    for field in drink_window_fields:
                        data[field] = existing.get(field)
        conn.execute(
            """
            INSERT INTO wines (
                id, name, producer, vintage, quantity, format, type, region, appellation,
                price, current_value, currency, merchant, order_date, expected_delivery, status,
                owner_share_pct, owners_json, notes, ai_notes,
                drink_from, drink_peak_from, drink_peak_to, drink_to, drink_window_notes,
                ai_value_notes
            )
            VALUES (
                :id, :name, :producer, :vintage, :quantity, :format, :type, :region, :appellation,
                :price, :current_value, :currency, :merchant, :order_date, :expected_delivery, :status,
                :owner_share_pct, :owners_json, :notes, :ai_notes,
                :drink_from, :drink_peak_from, :drink_peak_to, :drink_to, :drink_window_notes,
                :ai_value_notes
            )
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                producer = excluded.producer,
                vintage = excluded.vintage,
                quantity = excluded.quantity,
                format = excluded.format,
                type = excluded.type,
                region = excluded.region,
                appellation = excluded.appellation,
                price = excluded.price,
                current_value = excluded.current_value,
                currency = excluded.currency,
                merchant = excluded.merchant,
                order_date = excluded.order_date,
                expected_delivery = excluded.expected_delivery,
                status = excluded.status,
                owner_share_pct = excluded.owner_share_pct,
                owners_json = excluded.owners_json,
                notes = excluded.notes,
                ai_notes = excluded.ai_notes,
                drink_from = excluded.drink_from,
                drink_peak_from = excluded.drink_peak_from,
                drink_peak_to = excluded.drink_peak_to,
                drink_to = excluded.drink_to,
                drink_window_notes = excluded.drink_window_notes,
                ai_value_notes = excluded.ai_value_notes,
                updated_at = CURRENT_TIMESTAMP
            """,
            data,
        )
        replace_wine_scores(conn, data["id"], scores)
        saved = get_wine(conn, data["id"])
    return saved


def delete_wine(wine_id: str) -> bool:
    with connect() as conn:
        cursor = conn.execute("DELETE FROM wines WHERE id = ?", (wine_id,))
        return cursor.rowcount > 0


def drink_bottle(wine_id: str) -> dict:
    with connect() as conn:
        wine = get_wine(conn, wine_id)
        if not wine:
            raise LookupError("Wine not found")
        if wine["status"] != "Delivered":
            raise ValueError("Only delivered bottles can be marked as drunk")
        if int(wine["quantity"]) <= 0:
            raise ValueError("No bottles left in this position")

        conn.execute(
            "UPDATE wines SET quantity = quantity - 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (wine_id,),
        )
        updated = get_wine(conn, wine_id)
    return updated


def sell_bottles(wine_id: str, payload: dict) -> dict:
    quantity = int(payload.get("quantity") or 0)
    sale_price = float(payload.get("sale_price") or 0)
    buyer = str(payload.get("buyer", "")).strip()
    currency = str(payload.get("currency", "CHF")).strip().upper()

    if quantity <= 0:
        raise ValueError("Sale quantity must be greater than 0")
    if sale_price < 0:
        raise ValueError("Sale price cannot be negative")
    if not buyer:
        raise ValueError("Buyer is required")
    if currency not in SUPPORTED_CURRENCIES:
        raise ValueError(f"Unsupported currency: {currency}")

    with connect() as conn:
        wine = get_wine(conn, wine_id)
        if not wine:
            raise LookupError("Wine not found")
        if wine["status"] != "Delivered":
            raise ValueError("Only delivered bottles can be sold")
        if quantity > personal_quantity(wine):
            raise ValueError("You cannot sell more bottles than you own")

        unit_cost = float(wine["price"] or 0)
        if currency != wine["currency"]:
            rates = get_rates()
            unit_cost_chf = convert_to_chf(unit_cost, wine["currency"], rates)
            sale_total_chf = convert_to_chf(sale_price * quantity, currency, rates)
            cost_total_chf = unit_cost_chf * quantity
            profit_loss = sale_total_chf - cost_total_chf
            stored_unit_cost = unit_cost_chf
            stored_currency = REFERENCE_CURRENCY
        else:
            profit_loss = (sale_price - unit_cost) * quantity
            stored_unit_cost = unit_cost
            stored_currency = currency

        sale_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO sales (id, wine_id, quantity, sale_price, currency, buyer, unit_cost, profit_loss)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (sale_id, wine_id, quantity, sale_price, stored_currency, buyer, stored_unit_cost, profit_loss),
        )
        conn.execute(
            "UPDATE wines SET quantity = quantity - ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (quantity, wine_id),
        )
        updated = get_wine(conn, wine_id)

    return {"wine": updated, "sale": list_sales(wine_id)[0]}


def extract_response_text(payload: dict) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"].strip()
    texts: list[str] = []
    for item in payload.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if isinstance(content, dict) and content.get("type") == "output_text":
                texts.append(str(content.get("text", "")).strip())
    return "\n".join(text for text in texts if text).strip()


def clean_ai_notes_text(text: str) -> str:
    cleaned_lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.lower().startswith("etichetta:"):
            line = line.split(":", 1)[1].strip()
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def clean_ai_score_suggestions(payload: dict) -> list[dict]:
    scores = payload.get("scores", payload if isinstance(payload, list) else [])
    if not isinstance(scores, list):
        raise ValueError("OpenAI response must include a scores list")

    placeholder_markers = (
        "da verific",
        "non ho",
        "n/d",
        "nd",
        "n.a.",
        "na",
        "unknown",
        "sconosciuto",
        "non disponibile",
        "nessun",
    )

    cleaned = []
    seen = set()
    for item in scores[:8]:
        if not isinstance(item, dict):
            continue
        critic = str(item.get("critic", "")).strip()
        score = str(item.get("score", "")).strip()
        note = str(item.get("note", "")).strip()
        confidence = str(item.get("confidence", "")).strip()
        if not critic or not score:
            continue
        normalized_score = score.lower().strip(" .:-")
        if any(marker in normalized_score for marker in placeholder_markers):
            continue
        if not any(char.isdigit() for char in score):
            continue
        if confidence and confidence.lower() == "bassa":
            continue
        key = (critic.lower(), score.lower())
        if key in seen:
            continue
        seen.add(key)
        if confidence and confidence.lower() != "alta" and "verific" not in note.lower():
            note = f"Da verificare: {note}" if note else "Da verificare prima del salvataggio."
        cleaned.append({"critic": critic, "score": score, "note": note})
    return cleaned


def parse_json_object(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("OpenAI response did not include a JSON object")
    payload = json.loads(cleaned[start : end + 1])
    if not isinstance(payload, dict):
        raise ValueError("OpenAI response JSON must be an object")
    return payload


def clean_market_recommendations(payload: dict) -> dict:
    def clean_optional_producer(value: object) -> str:
        producer = str(value or "").strip()
        lowered = producer.lower()
        placeholders = ("esempio", "example", "produttore", "cantina esempio", "domaine dell'esempio")
        if any(placeholder in lowered for placeholder in placeholders):
            return ""
        return producer

    recommendations: dict[str, list[dict]] = {}
    for tier in ("low", "medium", "high"):
        items = payload.get(tier, [])
        if not isinstance(items, list):
            items = []
        recommendations[tier] = [
            {
                "name": str(item.get("name", "")).strip(),
                "producer": clean_optional_producer(item.get("producer", "")),
                "price_hint": str(item.get("price_hint", "")).strip(),
                "reason": str(item.get("reason", "")).strip(),
            }
            for item in items[:2]
            if isinstance(item, dict) and str(item.get("name", "")).strip()
        ]
    return recommendations


def clean_pairing_payload(payload: dict, available_wine_ids: set[str], include_market: bool) -> dict:
    matches = payload.get("cellar_matches", [])
    if not isinstance(matches, list):
        matches = []
    cleaned_matches = []
    seen_ids = set()
    for match in matches[:3]:
        if not isinstance(match, dict):
            continue
        wine_id = str(match.get("wine_id", "")).strip()
        if wine_id not in available_wine_ids or wine_id in seen_ids:
            continue
        seen_ids.add(wine_id)
        cleaned_matches.append(
            {
                "wine_id": wine_id,
                "wine_name": str(match.get("wine_name", "")).strip(),
                "producer": str(match.get("producer", "")).strip(),
                "reason": str(match.get("reason", "")).strip(),
                "serving_note": str(match.get("serving_note", "")).strip(),
            }
        )

    market = (
        {"low": [], "medium": [], "high": []}
        if cleaned_matches and not include_market
        else clean_market_recommendations(payload.get("market_recommendations", {}) if isinstance(payload.get("market_recommendations"), dict) else {})
    )
    summary = str(payload.get("summary", "")).strip()
    return {"summary": summary, "cellar_matches": cleaned_matches, "market_recommendations": market}


def suggest_pairing(payload: dict, role: str) -> dict:
    dish = str(payload.get("dish", "")).strip()
    if len(dish) < 2:
        raise ValueError("Dish is required")
    if len(dish) > 240:
        raise ValueError("Dish is too long")
    include_market = bool(payload.get("include_market"))
    market_only = bool(payload.get("market_only"))
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not configured")
    with connect() as conn:
        pairing_model = get_pairing_model(conn)

    cellar_wines = [] if market_only else [
        wine
        for wine in visible_wines(role)
        if wine.get("status") == "Delivered" and int(wine.get("quantity") or 0) > 0
    ]
    wine_context = [
        {
            "id": wine["id"],
            "name": wine["name"],
            "producer": wine["producer"],
            "vintage": wine["vintage"],
            "type": wine.get("type", ""),
            "region": wine.get("region", ""),
            "appellation": wine.get("appellation", ""),
            "quantity": wine.get("quantity", 0),
            "format": wine.get("format", ""),
            "current_value": wine.get("current_value") if wine.get("current_value") not in (None, "") else wine.get("price"),
            "currency": wine.get("currency", "CHF"),
            "drink_peak_from": wine.get("drink_peak_from"),
            "drink_peak_to": wine.get("drink_peak_to"),
            "drink_to": wine.get("drink_to"),
            "scores": wine.get("scores", []),
        }
        for wine in cellar_wines[:120]
    ]
    request_payload = {
        "model": pairing_model,
        "instructions": (
            "Sei un sommelier privato. Devi consigliare vini per un piatto usando prima solo "
            "le bottiglie disponibili in cantina. Rispondi solo con JSON valido, senza Markdown "
            "e senza testo prima o dopo. Se market_only è true, ignora la cantina: cellar_matches "
            "deve essere vuoto e devi proporre solo due bottiglie fuori cantina per ciascuna delle tre fasce prezzo. "
            "Se market_only è false e trovi uno o piu vini adeguati in cantina, mettili in "
            "cellar_matches. Se include_market è false e trovi vini adeguati in cantina, lascia "
            "market_recommendations vuoto. Se include_market è true, proponi sempre anche due "
            "bottiglie fuori cantina per fascia prezzo in CHF. Se nessun vino in cantina è davvero "
            "adeguato, cellar_matches deve essere vuoto e devi proporre due bottiglie per fascia "
            "prezzo in CHF: low entro 30 CHF, medium entro 60 CHF, high oltre "
            "60 CHF. Non inventare che un vino è in cantina se non è nel contesto. Usa italiano "
            "corretto con accenti in summary, reason e serving_note, ad esempio 'è', 'perché', "
            "'può', 'già', 'qualità'. Per le proposte fuori cantina, se conosci un prezzo di "
            "mercato indicativo e plausibile in Svizzera o Europa, inseriscilo in price_hint "
            "come intervallo o circa, ad esempio 'circa 45 CHF' o '40-55 CHF'. Se non hai un "
            "riferimento attendibile, indica solo la fascia, ad esempio 'entro 60 CHF'. Usa solo "
            "produttori reali: non scrivere mai valori segnaposto come 'Produttore esempio', "
            "'Cantina esempio' o 'Domaine dell'esempio'. Se non sei sicuro del produttore, lascia "
            "producer come stringa vuota."
        ),
        "input": (
            "Piatto o pietanza: "
            f"{dish}\n"
            f"include_market: {str(include_market).lower()}\n\n"
            f"market_only: {str(market_only).lower()}\n\n"
            "Vini disponibili in cantina, solo questi possono essere scelti come cellar_matches:\n"
            f"{json.dumps(wine_context, ensure_ascii=False)}\n\n"
            "Restituisci solo questo oggetto JSON: "
            "{\"summary\":\"testo breve\","
            "\"cellar_matches\":[{\"wine_id\":\"id dal contesto\",\"wine_name\":\"nome\","
            "\"producer\":\"produttore reale\",\"reason\":\"perché funziona\",\"serving_note\":\"servizio\"}],"
            "\"market_recommendations\":{\"low\":[{\"name\":\"vino reale\",\"producer\":\"produttore reale o stringa vuota\","
            "\"price_hint\":\"prezzo di mercato indicativo o fascia CHF\",\"reason\":\"perché\"}],"
            "\"medium\":[],\"high\":[]}}."
        ),
        "max_output_tokens": 1200,
    }
    request = Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(request_payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "WineCellar/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=40) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"OpenAI request failed: {error_body or exc.reason}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise ValueError(f"OpenAI request failed: {exc}") from exc

    raw_text = extract_response_text(response_payload)
    if not raw_text:
        raise ValueError("OpenAI response did not include text")
    cleaned_payload = clean_pairing_payload(parse_json_object(raw_text), {wine["id"] for wine in cellar_wines}, include_market)
    cleaned_payload["model"] = pairing_model
    return cleaned_payload


def generate_ai_notes(wine_id: str) -> dict:
    with connect() as conn:
        wine = get_wine(conn, wine_id)
        if not wine:
            raise LookupError("Wine not found")

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not configured")

    wine_context = {
        "name": wine["name"],
        "producer": wine["producer"],
        "vintage": wine["vintage"],
        "region": wine.get("region", ""),
        "appellation": wine.get("appellation", ""),
        "type": wine.get("type", ""),
        "format": wine.get("format", ""),
        "scores": wine.get("scores", []),
    }
    request_payload = {
        "model": OPENAI_MODEL,
        "instructions": (
            "Sei un assistente esperto di vino. Scrivi note brevi, utili e interessanti "
            "per un collezionista privato. Rispondi in italiano. Non inventare dati specifici "
            "come punteggi, prezzi, date o classificazioni se non sono nel contesto. Se un fatto "
            "è incerto, dillo in modo prudente. Usa ortografia italiana corretta con accenti "
            "e apostrofi, ad esempio 'è', 'perché', 'può', 'già', 'qualità'. Usa solo testo "
            "semplice: niente Markdown, niente asterischi, niente grassetti, niente titoli con "
            "simboli e niente markup HTML."
        ),
        "input": (
            "Genera una scheda 'Note AI' per questo vino in testo semplice. Usa 5-7 righe brevi, "
            "ognuna nel formato 'Campo: testo', senza elenchi Markdown e senza asterischi. "
            "Non usare mai la parola generica 'Etichetta:' come campo. Usa campi specifici come "
            "Vino, Stile, Produttore/territorio, Annata, Abbinamenti, Finestra, Curiosita. "
            "Copri stile, produttore/territorio, annata se utile, abbinamenti, finestra indicativa "
            "di consumo e una curiosita. Contesto:\n"
            f"{json.dumps(wine_context, ensure_ascii=False)}"
        ),
        "max_output_tokens": 650,
    }
    request = Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(request_payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "WineCellar/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"OpenAI request failed: {error_body or exc.reason}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise ValueError(f"OpenAI request failed: {exc}") from exc

    ai_notes = clean_ai_notes_text(extract_response_text(response_payload))
    if not ai_notes:
        raise ValueError("OpenAI response did not include text")

    with connect() as conn:
        conn.execute(
            "UPDATE wines SET ai_notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (ai_notes, wine_id),
        )
        updated = get_wine(conn, wine_id)
    return updated


def suggest_ai_scores(wine_id: str) -> dict:
    with connect() as conn:
        wine = get_wine(conn, wine_id)
        if not wine:
            raise LookupError("Wine not found")

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not configured")

    wine_context = {
        "name": wine["name"],
        "producer": wine["producer"],
        "vintage": wine["vintage"],
        "region": wine.get("region", ""),
        "appellation": wine.get("appellation", ""),
        "type": wine.get("type", ""),
        "existing_scores": wine.get("scores", []),
    }
    request_payload = {
        "model": OPENAI_VALUE_MODEL,
        "instructions": (
            "Sei un assistente esperto di critica enologica. Suggerisci punteggi pubblicati "
            "per un vino specifico solo se sei ragionevolmente sicuro che riguardino esattamente "
            "quel vino e quella annata. Rispondi solo con JSON valido, senza Markdown. Non "
            "inventare punteggi. Non usare punteggi di annate diverse. Se non conosci un punteggio "
            "numerico reale, non inserire nessuna voce per quella testata. Non restituire mai "
            "placeholder come 'Da verificare', 'non ho dati', 'N/D' o simili nel campo score. Se "
            "non hai dati affidabili, restituisci {\"scores\":[]}. Se sei incerto ma hai un "
            "punteggio numerico plausibile, usa confidence 'media' e scrivi chiaramente "
            "'Da verificare' nella nota. "
            "Preferisci fonti/testate note come Wine Advocate, Vinous, James Suckling, Jeb Dunnuck, "
            "Decanter, Falstaff, Wine Spectator, Wine Enthusiast."
        ),
        "input": (
            "Trova al massimo 6 possibili punteggi numerici per questo vino. Restituisci solo questo JSON: "
            "{\"scores\":[{\"critic\":\"testata o critico\",\"score\":\"punteggio\","
            "\"note\":\"nota breve con eventuale Da verificare\",\"confidence\":\"alta|media|bassa\"}]}.\n"
            "Contesto:\n"
            f"{json.dumps(wine_context, ensure_ascii=False)}"
        ),
        "max_output_tokens": 700,
    }
    request = Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(request_payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "WineCellar/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=35) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"OpenAI request failed: {error_body or exc.reason}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise ValueError(f"OpenAI request failed: {exc}") from exc

    raw_text = extract_response_text(response_payload)
    if not raw_text:
        raise ValueError("OpenAI response did not include text")
    return {"scores": clean_ai_score_suggestions(parse_json_object(raw_text))}


def clean_drink_window_payload(payload: dict, vintage: str) -> dict:
    try:
        vintage_year = int(str(vintage).strip())
    except ValueError as exc:
        raise ValueError("Wine vintage must be a year to generate a drinking window") from exc

    required = ["drink_from", "drink_peak_from", "drink_peak_to", "drink_to"]
    missing = [field for field in required if payload.get(field) in (None, "")]
    if missing:
        raise ValueError(f"OpenAI response is missing: {', '.join(missing)}")

    window = {field: clean_optional_int(payload.get(field)) for field in required}
    notes = str(payload.get("notes", "")).strip()
    if not notes:
        raise ValueError("OpenAI response is missing notes")

    if any(value is None for value in window.values()):
        raise ValueError("OpenAI response contains invalid drinking window years")
    if not (vintage_year <= window["drink_from"] <= window["drink_peak_from"] <= window["drink_peak_to"] <= window["drink_to"]):
        raise ValueError("OpenAI response contains an inconsistent drinking window")
    if window["drink_to"] - vintage_year > 120:
        raise ValueError("OpenAI response drinking window is unrealistically long")

    return {**window, "drink_window_notes": notes}


def generate_drink_window(wine_id: str) -> dict:
    with connect() as conn:
        wine = get_wine(conn, wine_id)
        if not wine:
            raise LookupError("Wine not found")

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not configured")

    wine_context = {
        "name": wine["name"],
        "producer": wine["producer"],
        "vintage": wine["vintage"],
        "region": wine.get("region", ""),
        "appellation": wine.get("appellation", ""),
        "type": wine.get("type", ""),
        "format": wine.get("format", ""),
        "scores": wine.get("scores", []),
        "ai_notes": wine.get("ai_notes", ""),
    }
    request_payload = {
        "model": OPENAI_MODEL,
        "instructions": (
            "Sei un assistente esperto di vino. Stima una finestra di degustazione indicativa "
            "per un collezionista privato. Rispondi solo con JSON valido, senza Markdown, senza "
            "testo prima o dopo. Non inventare precisione eccessiva: se sei incerto, scegli una "
            "finestra prudente e spiega brevemente l'assunzione nelle note. Usa italiano corretto "
            "con accenti nelle note, ad esempio 'è', 'perché', 'può', 'già', 'qualità'."
        ),
        "input": (
            "Usa l'annata come riferimento temporale. Restituisci solo questo oggetto JSON: "
            "{\"drink_from\": anno, \"drink_peak_from\": anno, \"drink_peak_to\": anno, "
            "\"drink_to\": anno, \"notes\": \"testo semplice\"}. "
            "drink_from è l'inizio della fase in cui il vino è bevibile; drink_peak_from e "
            "drink_peak_to delimitano la maturazione ideale; drink_to è la fine indicativa della "
            "finestra utile prima del declino. Contesto:\n"
            f"{json.dumps(wine_context, ensure_ascii=False)}"
        ),
        "max_output_tokens": 350,
    }
    request = Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(request_payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "WineCellar/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"OpenAI request failed: {error_body or exc.reason}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise ValueError(f"OpenAI request failed: {exc}") from exc

    raw_text = extract_response_text(response_payload)
    if not raw_text:
        raise ValueError("OpenAI response did not include text")
    window = clean_drink_window_payload(parse_json_object(raw_text), wine["vintage"])

    with connect() as conn:
        conn.execute(
            """
            UPDATE wines
            SET drink_from = ?, drink_peak_from = ?, drink_peak_to = ?, drink_to = ?,
                drink_window_notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                window["drink_from"],
                window["drink_peak_from"],
                window["drink_peak_to"],
                window["drink_to"],
                window["drink_window_notes"],
                wine_id,
            ),
        )
        updated = get_wine(conn, wine_id)
    return updated


def clean_ai_value_payload(payload: dict) -> dict:
    value = clean_optional_float(payload.get("current_value"))
    if value is None or value <= 0:
        raise ValueError("OpenAI response contains an invalid current value")
    if value > 1000000:
        raise ValueError("OpenAI response current value is unrealistically high")
    currency = str(payload.get("currency", "")).strip().upper()
    if currency not in SUPPORTED_CURRENCIES:
        raise ValueError(f"OpenAI response contains unsupported currency: {currency}")
    notes = str(payload.get("notes", "")).strip()
    if not notes:
        raise ValueError("OpenAI response is missing notes")
    return {"current_value": round(value, 2), "currency": currency, "ai_value_notes": notes}


def generate_ai_value(wine_id: str) -> dict:
    with connect() as conn:
        wine = get_wine(conn, wine_id)
        if not wine:
            raise LookupError("Wine not found")

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not configured")

    wine_context = {
        "name": wine["name"],
        "producer": wine["producer"],
        "vintage": wine["vintage"],
        "region": wine.get("region", ""),
        "appellation": wine.get("appellation", ""),
        "type": wine.get("type", ""),
        "format": wine.get("format", ""),
        "purchase_price": wine.get("price"),
        "currency": wine.get("currency", "CHF"),
        "scores": wine.get("scores", []),
        "ai_notes": wine.get("ai_notes", ""),
        "drink_window_notes": wine.get("drink_window_notes", ""),
    }
    request_payload = {
        "model": OPENAI_VALUE_MODEL,
        "instructions": (
            "Sei un assistente esperto di valutazioni di vino. Stima un valore attuale unitario "
            "indicativo per un collezionista privato. Rispondi solo con JSON valido, senza Markdown "
            "e senza testo prima o dopo. Non presentare la stima come quotazione live o prezzo certo. "
            "Se non hai dati sufficienti, usa una stima prudente e spiega il limite nelle note. "
            "Usa italiano corretto con accenti nelle note, ad esempio 'è', 'perché', 'può', "
            "'già', 'qualità'."
        ),
        "input": (
            "Restituisci solo questo oggetto JSON: "
            "{\"current_value\": numero, \"currency\": \"CHF|EUR|USD\", \"notes\": \"testo semplice\"}. "
            "La valuta deve essere la stessa del vino se supportata. current_value è il valore stimato "
            "per una singola bottiglia nel formato indicato. Le note devono spiegare in 1-2 frasi "
            "che si tratta di una stima indicativa e quali fattori sono stati considerati. Contesto:\n"
            f"{json.dumps(wine_context, ensure_ascii=False)}"
        ),
        "max_output_tokens": 300,
    }
    request = Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(request_payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "WineCellar/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"OpenAI request failed: {error_body or exc.reason}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise ValueError(f"OpenAI request failed: {exc}") from exc

    raw_text = extract_response_text(response_payload)
    if not raw_text:
        raise ValueError("OpenAI response did not include text")
    estimate = clean_ai_value_payload(parse_json_object(raw_text))
    if estimate["currency"] != wine["currency"]:
        raise ValueError("OpenAI response currency does not match the wine currency")

    with connect() as conn:
        conn.execute(
            """
            UPDATE wines
            SET current_value = ?, ai_value_notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (estimate["current_value"], estimate["ai_value_notes"], wine_id),
        )
        updated = get_wine(conn, wine_id)
    return updated


def replace_all_wines(wines: list[dict]) -> list[dict]:
    cleaned = [clean_wine(wine) for wine in wines]
    with connect() as conn:
        conn.execute("DELETE FROM wines")
        for wine in cleaned:
            insert_wine(conn, wine)
    return list_wines()


def replace_all_wishlist(items: list[dict]) -> list[dict]:
    cleaned = [clean_wishlist_item(item) for item in items]
    with connect() as conn:
        conn.execute("DELETE FROM wishlist")
        for item in cleaned:
            conn.execute(
                """
                INSERT INTO wishlist (
                    id, name, producer, vintage, format, type, region, appellation,
                    target_price, currency, merchant, purpose, priority, status, notes
                )
                VALUES (
                    :id, :name, :producer, :vintage, :format, :type, :region, :appellation,
                    :target_price, :currency, :merchant, :purpose, :priority, :status, :notes
                )
                """,
                item,
            )
    return list_wishlist()


def auth_payload(role: str) -> dict:
    with connect() as conn:
        app_theme = get_app_theme(conn)
    return {"authenticated": role != "anonymous", "role": role, "auth_enabled": AUTH_ENABLED, "app_theme": app_theme}


class CellarHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def guess_type(self, path: str) -> str:
        if path.endswith(".webmanifest"):
            return "application/manifest+json"
        if path.endswith(".js"):
            return "text/javascript"
        return super().guess_type(path)

    def end_headers(self) -> None:
        path = urlparse(self.path).path
        if path in {"/manifest.webmanifest", "/sw.js"}:
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def is_public_static_path(self) -> bool:
        path = unquote(urlparse(self.path).path)
        return path in PUBLIC_STATIC_PATHS

    def do_HEAD(self) -> None:
        path = urlparse(self.path).path
        if path.startswith("/api/"):
            self.send_error(HTTPStatus.METHOD_NOT_ALLOWED)
            return
        if not self.is_public_static_path():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        super().do_HEAD()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/session":
            self.send_json(auth_payload(self.current_role()))
            return
        if path.startswith("/api/") and not self.require_authenticated():
            return
        if path == "/api/wines":
            self.send_json(visible_wines(self.current_role()))
            return
        if path == "/api/wine-catalog":
            self.send_json(list_catalog_wines())
            return
        if path == "/api/settings":
            if not self.require_admin():
                return
            self.send_json(get_app_settings())
            return
        if path == "/api/wishlist":
            self.send_json(list_wishlist())
            return
        if path == "/api/export":
            if not self.require_admin():
                return
            self.send_json({"wines": list_wines(), "wishlist": list_wishlist()})
            return
        if path == "/api/rates":
            try:
                self.send_json(get_rates(force_refresh=True))
            except ValueError as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_GATEWAY)
            return
        if path.startswith("/api/wines/") and path.endswith("/sales"):
            wine_id = unquote(path.removeprefix("/api/wines/").removesuffix("/sales"))
            try:
                self.send_json(list_sales(wine_id, self.current_role()))
            except LookupError as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
            return
        if path == "/api/summary":
            try:
                self.send_json(get_summary(self.current_role()))
            except ValueError as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_GATEWAY)
            return
        if not self.is_public_static_path():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/api/login":
                self.login()
                return
            if path == "/api/logout":
                self.logout()
                return
            if path == "/api/wishlist":
                if not self.require_authenticated():
                    return
                self.send_json(upsert_wishlist_item(self.read_json()), HTTPStatus.CREATED)
                return
            if path.startswith("/api/") and not self.require_admin():
                return
            if path == "/api/settings":
                self.send_json(update_app_settings(self.read_json()))
                return
            if path == "/api/pairing":
                self.send_json(suggest_pairing(self.read_json(), self.current_role()))
                return
            if path.startswith("/api/wishlist/") and path.endswith("/convert"):
                item_id = unquote(path.removeprefix("/api/wishlist/").removesuffix("/convert"))
                try:
                    self.send_json(convert_wishlist_item(item_id, self.read_json()), HTTPStatus.CREATED)
                except LookupError as exc:
                    self.send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
                return
            if path.startswith("/api/wishlist/") and path.endswith("/strategy"):
                item_id = unquote(path.removeprefix("/api/wishlist/").removesuffix("/strategy"))
                try:
                    self.send_json(suggest_wishlist_strategy(item_id))
                except LookupError as exc:
                    self.send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
                return
            if path.startswith("/api/wines/") and path.endswith("/ai-notes"):
                wine_id = unquote(path.removeprefix("/api/wines/").removesuffix("/ai-notes"))
                try:
                    self.send_json(generate_ai_notes(wine_id))
                except LookupError as exc:
                    self.send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
                return
            if path.startswith("/api/wines/") and path.endswith("/ai-scores"):
                wine_id = unquote(path.removeprefix("/api/wines/").removesuffix("/ai-scores"))
                try:
                    self.send_json(suggest_ai_scores(wine_id))
                except LookupError as exc:
                    self.send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
                return
            if path.startswith("/api/wines/") and path.endswith("/drink-window"):
                wine_id = unquote(path.removeprefix("/api/wines/").removesuffix("/drink-window"))
                try:
                    self.send_json(generate_drink_window(wine_id))
                except LookupError as exc:
                    self.send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
                return
            if path.startswith("/api/wines/") and path.endswith("/ai-value"):
                wine_id = unquote(path.removeprefix("/api/wines/").removesuffix("/ai-value"))
                try:
                    self.send_json(generate_ai_value(wine_id))
                except LookupError as exc:
                    self.send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
                return
            if path.startswith("/api/wines/") and path.endswith("/drink"):
                wine_id = unquote(path.removeprefix("/api/wines/").removesuffix("/drink"))
                try:
                    self.send_json(drink_bottle(wine_id))
                except LookupError as exc:
                    self.send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
                return
            if path.startswith("/api/wines/") and path.endswith("/sales"):
                wine_id = unquote(path.removeprefix("/api/wines/").removesuffix("/sales"))
                try:
                    self.send_json(sell_bottles(wine_id, self.read_json()), HTTPStatus.CREATED)
                except LookupError as exc:
                    self.send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
                return
            if path == "/api/wines":
                self.send_json(upsert_wine(self.read_json()), HTTPStatus.CREATED)
                return
            if path == "/api/import":
                payload = self.read_json()
                if isinstance(payload, list):
                    self.send_json({"wines": replace_all_wines(payload), "wishlist": list_wishlist()})
                    return
                if not isinstance(payload, dict) or not isinstance(payload.get("wines"), list):
                    raise ValueError("Import payload must include a wines list")
                wines = replace_all_wines(payload["wines"])
                if "wishlist" in payload:
                    if not isinstance(payload["wishlist"], list):
                        raise ValueError("Import wishlist payload must be a list")
                    wishlist = replace_all_wishlist(payload["wishlist"])
                else:
                    wishlist = list_wishlist()
                self.send_json({"wines": wines, "wishlist": wishlist})
                return
            self.send_error(HTTPStatus.NOT_FOUND)
        except ValueError as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def do_PUT(self) -> None:
        path = urlparse(self.path).path
        if path.startswith("/api/wishlist/"):
            if not self.require_authenticated():
                return
            item_id = unquote(path.removeprefix("/api/wishlist/"))
            try:
                self.send_json(upsert_wishlist_item(self.read_json(), item_id))
            except ValueError as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if not path.startswith("/api/wines/"):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not self.require_admin():
            return
        wine_id = unquote(path.removeprefix("/api/wines/"))
        try:
            self.send_json(upsert_wine(self.read_json(), wine_id))
        except ValueError as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path
        if path.startswith("/api/wishlist/"):
            if not self.require_admin():
                return
            item_id = unquote(path.removeprefix("/api/wishlist/"))
            if delete_wishlist_item(item_id):
                self.send_response(HTTPStatus.NO_CONTENT)
                self.end_headers()
                return
            self.send_json({"error": "Wishlist item not found"}, HTTPStatus.NOT_FOUND)
            return
        if not path.startswith("/api/wines/"):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not self.require_admin():
            return
        wine_id = unquote(path.removeprefix("/api/wines/"))
        if delete_wine(wine_id):
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
            return
        self.send_json({"error": "Wine not found"}, HTTPStatus.NOT_FOUND)

    def read_json(self) -> dict | list:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw or "{}")

    def send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def current_role(self) -> str:
        if not AUTH_ENABLED:
            return "admin"
        cookie_header = self.headers.get("Cookie", "")
        if not cookie_header:
            return "anonymous"
        cookie = SimpleCookie(cookie_header)
        morsel = cookie.get(SESSION_COOKIE)
        if not morsel:
            return "anonymous"
        return SESSIONS.get(morsel.value, "anonymous")

    def require_admin(self) -> bool:
        if self.current_role() == "admin":
            return True
        self.send_json({"error": "Admin access required"}, HTTPStatus.FORBIDDEN)
        return False

    def require_authenticated(self) -> bool:
        if self.current_role() != "anonymous":
            return True
        self.send_json({"error": "Authentication required"}, HTTPStatus.UNAUTHORIZED)
        return False

    def login(self) -> None:
        if not AUTH_ENABLED:
            self.send_json(auth_payload("admin"))
            return
        payload = self.read_json()
        password = str(payload.get("password", ""))
        role = ""
        if password == ADMIN_PASSWORD:
            role = "admin"
        elif VIEWER_PASSWORD and password == VIEWER_PASSWORD:
            role = "viewer"
        elif SHARED_VIEWER_PASSWORD and password == SHARED_VIEWER_PASSWORD:
            role = "shared_viewer"
        if not role:
            self.send_json({"error": "Invalid password"}, HTTPStatus.UNAUTHORIZED)
            return

        session_id = token_urlsafe(32)
        SESSIONS[session_id] = role
        body = json.dumps(auth_payload(role)).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Set-Cookie", f"{SESSION_COOKIE}={session_id}; Path=/; HttpOnly; SameSite=Lax")
        self.end_headers()
        self.wfile.write(body)

    def logout(self) -> None:
        cookie_header = self.headers.get("Cookie", "")
        if cookie_header:
            cookie = SimpleCookie(cookie_header)
            morsel = cookie.get(SESSION_COOKIE)
            if morsel:
                SESSIONS.pop(morsel.value, None)
        body = json.dumps(auth_payload("anonymous" if AUTH_ENABLED else "admin")).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Set-Cookie", f"{SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    parser = ArgumentParser(description="Run the Wine Cellar web app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=4173, type=int)
    args = parser.parse_args()

    init_db()
    server = ThreadingHTTPServer((args.host, args.port), CellarHandler)
    print(f"Wine Cellar running at http://{args.host}:{args.port}/")
    server.serve_forever()
