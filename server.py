from __future__ import annotations

import hashlib
import json
import os
import base64
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
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature, encode_dss_signature


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "cellar.db"
RATES_URL = "https://api.frankfurter.dev/v1/latest?base=EUR&symbols=CHF,USD"
RATES_CACHE_SECONDS = 60 * 60 * 12
REFERENCE_CURRENCY = "CHF"
SUPPORTED_CURRENCIES = {"CHF", "EUR", "USD"}
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
VIEWER_PASSWORD = os.environ.get("VIEWER_PASSWORD", "")
SHARED_VIEWER_PASSWORD = os.environ.get("SHARED_VIEWER_PASSWORD", "")
AUTH_ENABLED = bool(ADMIN_PASSWORD)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.4-nano")
OPENAI_VALUE_MODEL = os.environ.get("OPENAI_VALUE_MODEL", "gpt-5.4-mini")
OPENAI_WISHLIST_STRATEGY_MODEL = os.environ.get("OPENAI_WISHLIST_STRATEGY_MODEL", "gpt-5.4")
OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
SESSION_COOKIE = "wine_cellar_session"
SESSIONS: dict[str, str] = {}
WEBAUTHN_CHALLENGES: dict[str, dict] = {}
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
AI_MODEL_SETTINGS = [
    {
        "key": "pairing_model",
        "default": OPENAI_MODEL,
        "recommended": "gpt-5.4-mini",
    },
    {
        "key": "ai_notes_model",
        "default": OPENAI_MODEL,
        "recommended": "gpt-5.4-mini",
    },
    {
        "key": "drink_window_model",
        "default": OPENAI_MODEL,
        "recommended": "gpt-5.4",
    },
    {
        "key": "ai_value_model",
        "default": OPENAI_VALUE_MODEL,
        "recommended": "gpt-5.4-mini",
    },
    {
        "key": "grape_composition_model",
        "default": OPENAI_MODEL,
        "recommended": "gpt-5.4-nano",
    },
    {
        "key": "wishlist_strategy_model",
        "default": OPENAI_WISHLIST_STRATEGY_MODEL,
        "recommended": "gpt-5.4",
    },
]
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
    "grapes",
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
    conn.execute("PRAGMA foreign_keys = ON")
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
                grapes_json TEXT NOT NULL DEFAULT '[]',
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
        ensure_column(conn, "wines", "grapes_json", "TEXT NOT NULL DEFAULT '[]'")
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
            CREATE TABLE IF NOT EXISTS passkey_credentials (
                credential_id TEXT PRIMARY KEY,
                role TEXT NOT NULL,
                public_key_cose BLOB NOT NULL,
                sign_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_used_at TEXT
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
            CREATE TABLE IF NOT EXISTS wine_movements (
                id TEXT PRIMARY KEY,
                wine_id TEXT NOT NULL,
                movement_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                related_id TEXT,
                value REAL,
                currency TEXT,
                occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (wine_id) REFERENCES wines(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_wine_movements_wine_id_occurred_at
            ON wine_movements (wine_id, occurred_at DESC)
            """
        )
        conn.execute(
            """
            INSERT INTO wine_movements (
                id, wine_id, movement_type, quantity, note, related_id, value, currency, occurred_at
            )
            SELECT lower(hex(randomblob(16))), s.wine_id, 'sale', -s.quantity,
                   'sale:' || s.buyer, s.id, s.sale_price * s.quantity, s.currency, s.sold_at
            FROM sales s
            JOIN wines w ON w.id = s.wine_id
            WHERE NOT EXISTS (
                SELECT 1
                FROM wine_movements m
                WHERE m.related_id = s.id AND m.movement_type = 'sale'
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
                status_source TEXT NOT NULL DEFAULT 'manual',
                ai_strategy TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        ensure_column(conn, "wishlist", "purpose", "TEXT NOT NULL DEFAULT 'Drink'")
        ensure_column(conn, "wishlist", "status_source", "TEXT NOT NULL DEFAULT 'manual'")
        ensure_column(conn, "wishlist", "ai_strategy", "TEXT NOT NULL DEFAULT ''")
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
    return get_ai_model_setting(conn, "pairing_model", OPENAI_MODEL)


def get_ai_model_setting(conn: sqlite3.Connection, key: str, default: str) -> str:
    model = get_setting(conn, key, default)
    return model if model in OPENAI_MODEL_OPTION_IDS else default


def get_app_theme(conn: sqlite3.Connection) -> str:
    theme = get_setting(conn, "app_theme", "classic")
    return theme if theme in APP_THEME_OPTION_IDS else "classic"


def get_app_settings() -> dict:
    with connect() as conn:
        app_theme = get_app_theme(conn)
        ai_models = {
            spec["key"]: get_ai_model_setting(conn, spec["key"], spec["default"])
            for spec in AI_MODEL_SETTINGS
        }
    return {
        "ai_models": ai_models,
        "ai_model_settings": AI_MODEL_SETTINGS,
        "model_options": OPENAI_MODEL_OPTIONS,
        "app_theme": app_theme,
        "theme_options": APP_THEME_OPTIONS,
        "pricing_note": "Prezzi indicativi OpenAI standard per 1M token. Il costo reale dipende da input e output della richiesta.",
    }


def update_app_settings(payload: dict) -> dict:
    app_theme = str(payload.get("app_theme", "classic")).strip()
    if app_theme not in APP_THEME_OPTION_IDS:
        raise ValueError("Invalid app theme")

    with connect() as conn:
        ai_models: dict[str, str] = {}
        for spec in AI_MODEL_SETTINGS:
            model = str(payload.get(spec["key"], get_ai_model_setting(conn, spec["key"], spec["default"]))).strip()
            if model not in OPENAI_MODEL_OPTION_IDS:
                raise ValueError(f"Invalid model for {spec['key']}")
            ai_models[spec["key"]] = model
        for key, model in ai_models.items():
            conn.execute(
                """
                INSERT INTO app_settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
                """,
                (key, model),
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
                   ai_value_notes, grapes_json
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


def list_movements(wine_id: str, role: str = "admin") -> list[dict]:
    with connect() as conn:
        wine = get_wine(conn, wine_id)
        if not wine:
            raise LookupError("Wine not found")
        if role == "shared_viewer" and not is_shared_position(wine):
            raise LookupError("Wine not found")
        rows = conn.execute(
            """
            SELECT id, wine_id, movement_type, quantity, note, related_id, value, currency, occurred_at
            FROM wine_movements
            WHERE wine_id = ?
            ORDER BY occurred_at DESC, created_at DESC, rowid DESC
            """,
            (wine_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def list_all_movements() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT m.id, m.wine_id, m.movement_type, m.quantity, m.note, m.related_id,
                   m.value, m.currency, m.occurred_at,
                   w.name AS wine_name, w.producer AS wine_producer, w.vintage AS wine_vintage
            FROM wine_movements m
            JOIN wines w ON w.id = m.wine_id
            ORDER BY m.occurred_at DESC, m.created_at DESC, m.rowid DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def visible_movements(role: str) -> list[dict]:
    movements = list_all_movements()
    if role == "shared_viewer":
        visible_ids = {wine["id"] for wine in visible_wines(role)}
        return [movement for movement in movements if movement["wine_id"] in visible_ids]
    return movements


def list_wishlist() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, name, producer, vintage, format, type, region, appellation,
                   target_price, currency, merchant, purpose, priority, status, status_source, ai_strategy, notes
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
               target_price, currency, merchant, purpose, priority, status, status_source, ai_strategy, notes
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
    status_source = str(payload.get("status_source", "manual")).strip().lower()
    if status_source not in {"manual", "ai"}:
        status_source = "manual"
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
        "status_source": status_source,
        "ai_strategy": str(payload.get("ai_strategy", "")).strip() if status_source == "ai" else "",
        "notes": str(payload.get("notes", "")).strip(),
    }


def upsert_wishlist_item(payload: dict, item_id: str | None = None) -> dict:
    data = clean_wishlist_item(payload, item_id)
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO wishlist (
                id, name, producer, vintage, format, type, region, appellation,
                target_price, currency, merchant, purpose, priority, status, status_source, ai_strategy, notes
            )
            VALUES (
                :id, :name, :producer, :vintage, :format, :type, :region, :appellation,
                :target_price, :currency, :merchant, :purpose, :priority, :status, :status_source, :ai_strategy, :notes
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
                status_source = excluded.status_source,
                ai_strategy = excluded.ai_strategy,
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
    signal = str(payload.get("signal", "") or payload.get("summary", "")).strip()
    reason = str(payload.get("reason", "")).strip()
    price_assessment = str(payload.get("price_assessment", "") or payload.get("priceAssessment", "")).strip()
    market_price_low = clean_optional_float(payload.get("market_price_low"))
    market_price_high = clean_optional_float(payload.get("market_price_high"))
    market_price_currency = str(payload.get("market_price_currency", "")).strip().upper()
    if market_price_currency not in SUPPORTED_CURRENCIES:
        market_price_currency = ""
    sources = clean_wishlist_price_sources(payload.get("sources", []))

    alternative_payload = payload.get("alternative", {})
    alternative = None
    if isinstance(alternative_payload, dict):
        name = str(alternative_payload.get("name", "")).strip()
        if name:
            alternative = {
                "name": name,
                "producer": str(alternative_payload.get("producer", "")).strip(),
            }

    return {
        "recommendation": recommendation,
        "signal": signal[:80],
        "reason": reason[:120],
        "price_assessment": price_assessment[:140],
        "market_price_low": market_price_low,
        "market_price_high": market_price_high,
        "market_price_currency": market_price_currency,
        "sources": sources,
        "alternative": alternative,
    }


def clean_wishlist_price_sources(payload: object) -> list[dict]:
    if not isinstance(payload, list):
        return []
    cleaned = []
    seen = set()
    for source in payload:
        if not isinstance(source, dict):
            continue
        url = str(source.get("url", "")).strip()
        title = str(source.get("title", "") or source.get("name", "")).strip()
        observed_price = clean_optional_float(source.get("observed_price"))
        observed_currency = str(source.get("observed_currency", "")).strip().upper()
        observed_vintage = str(source.get("observed_vintage", "")).strip()
        observed_format = str(source.get("observed_format", "")).strip()
        match_quality = str(source.get("match_quality", "")).strip().lower()
        source_kind = str(source.get("source_kind", "")).strip().lower()
        if not url.startswith(("http://", "https://")) or url in seen:
            continue
        if observed_currency and observed_currency not in SUPPORTED_CURRENCIES:
            observed_currency = ""
        if match_quality not in {"exact", "related", "unknown"}:
            match_quality = "unknown"
        if source_kind not in {"merchant", "search", "auction", "flash", "marketplace", "unknown"}:
            source_kind = "unknown"
        seen.add(url)
        cleaned.append(
            {
                "title": title[:80] or url[:80],
                "url": url[:500],
                "observed_price": observed_price,
                "observed_currency": observed_currency,
                "observed_vintage": observed_vintage[:20],
                "observed_format": observed_format[:40],
                "match_quality": match_quality,
                "source_kind": source_kind,
            }
        )
        if len(cleaned) >= 4:
            break
    return cleaned


def extract_web_search_sources(payload: dict) -> list[dict]:
    sources = []
    for item in payload.get("output", []):
        if not isinstance(item, dict) or item.get("type") != "web_search_call":
            continue
        action = item.get("action", {})
        if not isinstance(action, dict):
            continue
        sources.extend(action.get("sources", []) or [])
    return clean_wishlist_price_sources(sources)


def merge_wishlist_price_sources(*source_groups: list[dict]) -> list[dict]:
    merged = []
    seen = set()
    for group in source_groups:
        for source in group:
            url = source.get("url", "")
            if not url or url in seen:
                continue
            seen.add(url)
            merged.append(source)
            if len(merged) >= 4:
                return merged
    return merged


def format_price_short(value: float | None, currency: str) -> str:
    if value is None:
        return ""
    rounded = round(float(value), 2)
    if rounded.is_integer():
        rendered = str(int(rounded))
    else:
        rendered = f"{rounded:.2f}".rstrip("0").rstrip(".")
    return f"{currency} {rendered}"


def wishlist_market_range_label(low: float, high: float, currency: str) -> str:
    return f"{format_price_short(low, currency)}-{format_price_short(high, currency).removeprefix(currency + ' ')}"


def wishlist_search_reference(item: dict) -> str:
    parts = [
        str(item.get("producer") or "").strip(),
        str(item.get("name") or "").strip(),
        str(item.get("vintage") or "").strip(),
        str(item.get("format") or "").strip(),
    ]
    return " ".join(part for part in parts if part)


def normalize_wishlist_format_label(value: str) -> str:
    normalized = str(value or "").strip().lower()
    compact = (
        normalized.replace(" ", "")
        .replace(".", "")
        .replace(",", ".")
        .replace("cl", "00ml")
        .replace("litre", "l")
        .replace("litro", "l")
    )
    if "1500ml" in compact or "15l" in compact or "1.5l" in compact or "magnum" in normalized:
        return "1500ml"
    if "375ml" in compact or "0375l" in compact or "0.375l" in compact or "half" in normalized or "mezza" in normalized:
        return "375ml"
    if "750ml" in compact or "075l" in compact or "0.75l" in compact or "bottle" in normalized or "bottiglia" in normalized:
        return "750ml"
    return compact


FLASH_DEAL_SOURCE_DOMAINS = {
    "deindeal.ch",
}


PREFERRED_WINE_MERCHANT_DOMAINS = {
    "arvi.ch",
    "millesima.ch",
    "millesima.com",
    "hawesko.de",
    "idealwine.com",
    "vino.com",
    "berrybros.com",
    "farrvintners.com",
}


def wishlist_source_domain(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def wishlist_source_is_excluded(source: dict) -> bool:
    domain = wishlist_source_domain(str(source.get("url") or ""))
    source_kind = str(source.get("source_kind") or "").strip().lower()
    return domain in FLASH_DEAL_SOURCE_DOMAINS or source_kind == "flash"


def wishlist_source_is_preferred(source: dict) -> bool:
    domain = wishlist_source_domain(str(source.get("url") or ""))
    source_kind = str(source.get("source_kind") or "").strip().lower()
    return domain in PREFERRED_WINE_MERCHANT_DOMAINS or source_kind == "merchant"


def derive_market_range_from_sources(strategy: dict, item: dict, rates: dict | None = None) -> dict:
    sources = strategy.get("sources", [])
    if not isinstance(sources, list) or not sources:
        return strategy

    item_vintage = str(item.get("vintage") or "").strip().lower()
    item_format = normalize_wishlist_format_label(str(item.get("format") or ""))
    target_currency = str(item.get("currency") or "").strip().upper() or "CHF"
    exact_prices = []
    preferred_exact_prices = []

    for source in sources:
        if not isinstance(source, dict):
            continue
        if wishlist_source_is_excluded(source):
            continue
        price = clean_optional_float(source.get("observed_price"))
        currency = str(source.get("observed_currency") or "").strip().upper()
        source_vintage = str(source.get("observed_vintage") or "").strip().lower()
        source_format = normalize_wishlist_format_label(str(source.get("observed_format") or ""))
        match_quality = str(source.get("match_quality") or "").strip().lower()
        if not price or not currency or currency not in SUPPORTED_CURRENCIES:
            continue
        vintage_matches = not item_vintage or source_vintage == item_vintage
        format_matches = not item_format or not source_format or source_format == item_format
        if match_quality != "exact" or not vintage_matches or not format_matches:
            continue
        if currency == target_currency:
            normalized_price = price
        else:
            if rates is None:
                rates = get_rates()
            normalized_price = convert_to_chf(price, currency, rates)
            if target_currency != "CHF":
                target_rate = rates["rates_to_chf"].get(target_currency)
                if target_rate is None:
                    raise ValueError(f"Unsupported currency: {target_currency}")
                normalized_price = normalized_price / target_rate
        rounded_price = round(normalized_price, 2)
        exact_prices.append(rounded_price)
        if wishlist_source_is_preferred(source):
            preferred_exact_prices.append(rounded_price)

    selected_prices = preferred_exact_prices or exact_prices

    if selected_prices:
        strategy["market_price_low"] = min(selected_prices)
        strategy["market_price_high"] = max(selected_prices)
        strategy["market_price_currency"] = target_currency
    else:
        strategy["market_price_low"] = None
        strategy["market_price_high"] = None
        strategy["market_price_currency"] = ""
    return strategy


def wishlist_price_position(strategy: dict, item: dict, rates: dict | None = None) -> dict | None:
    target_price = clean_optional_float(item.get("target_price"))
    target_currency = str(item.get("currency") or "").upper()
    market_low = clean_optional_float(strategy.get("market_price_low"))
    market_high = clean_optional_float(strategy.get("market_price_high"))
    market_currency = str(strategy.get("market_price_currency") or "").upper()

    if market_currency not in SUPPORTED_CURRENCIES:
        market_currency = ""

    if not target_price or not target_currency or not market_low or not market_high or not market_currency:
        return None

    if market_low > market_high:
        market_low, market_high = market_high, market_low
        strategy["market_price_low"] = market_low
        strategy["market_price_high"] = market_high

    if target_currency == market_currency:
        target_in_market_currency = target_price
    else:
        if rates is None:
            rates = get_rates()
        target_chf = convert_to_chf(target_price, target_currency, rates)
        market_rate = rates["rates_to_chf"].get(market_currency)
        if market_rate is None:
            raise ValueError(f"Unsupported currency: {market_currency}")
        target_in_market_currency = target_chf / market_rate

    if target_in_market_currency <= market_low * 0.8:
        position = "very_below"
    elif target_in_market_currency < market_low:
        position = "below"
    elif target_in_market_currency <= market_high:
        position = "within"
    else:
        position = "above"

    return {
        "position": position,
        "target_price": target_price,
        "target_currency": target_currency,
        "market_low": market_low,
        "market_high": market_high,
        "market_currency": market_currency,
    }


def apply_wishlist_price_assessment(strategy: dict, item: dict, rates: dict | None = None) -> dict:
    price_position = wishlist_price_position(strategy, item, rates)
    if not price_position:
        target_price = clean_optional_float(item.get("target_price"))
        strategy["price_assessment"] = (
            strategy.get("price_assessment")
            or (
                "Prezzo obiettivo non indicato: nessun confronto prezzo disponibile."
                if not target_price
                else "Fascia mercato non stimata: valutazione prezzo incerta."
            )
        )
        return strategy

    target_price = price_position["target_price"]
    target_currency = price_position["target_currency"]
    market_low = price_position["market_low"]
    market_high = price_position["market_high"]
    market_currency = price_position["market_currency"]
    position = price_position["position"]

    target_label = format_price_short(target_price, target_currency)
    range_label = wishlist_market_range_label(market_low, market_high, market_currency)
    if position == "very_below":
        assessment = f"{target_label} e molto sotto la fascia stimata {range_label}: prezzo molto interessante."
    elif position == "below":
        assessment = f"{target_label} e sotto la fascia stimata {range_label}: prezzo interessante."
    elif position == "within":
        assessment = f"{target_label} e dentro la fascia stimata {range_label}: prezzo neutro."
    else:
        assessment = f"{target_label} e sopra la fascia stimata {range_label}: prezzo caro."
    strategy["price_assessment"] = assessment
    return strategy


def normalize_wishlist_recommendation(strategy: dict, item: dict, rates: dict | None = None) -> dict:
    price_position = wishlist_price_position(strategy, item, rates)
    if not price_position:
        return strategy

    recommendation = str(strategy.get("recommendation", "monitor") or "monitor").lower()
    purpose = str(item.get("purpose", "") or "")
    position = price_position["position"]

    if position in {"very_below", "below"}:
        if purpose in {"Cellar", "Invest"}:
            strategy["recommendation"] = "buy"
            strategy["signal"] = "Compra" if position == "very_below" else "Interessante"
        elif recommendation == "avoid":
            strategy["recommendation"] = "monitor"
            strategy["signal"] = "Monitora"
    elif position == "above" and recommendation == "buy":
        strategy["recommendation"] = "monitor"
        strategy["signal"] = "Monitora"

    return strategy


def wishlist_status_from_strategy(recommendation: str) -> str:
    return {
        "buy": "Buy",
        "monitor": "Monitor",
        "avoid": "Skipped",
    }.get(recommendation, "Monitor")


def get_wishlist_strategy_model(conn: sqlite3.Connection) -> str:
    return get_ai_model_setting(conn, "wishlist_strategy_model", OPENAI_WISHLIST_STRATEGY_MODEL)


def suggest_wishlist_strategy(item_id: str) -> dict:
    with connect() as conn:
        item = get_wishlist_item(conn, item_id)
        if not item:
            raise LookupError("Wishlist item not found")
        strategy_model = get_wishlist_strategy_model(conn)

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not configured")

    context = {
        "wishlist_item": item,
        "search_reference": wishlist_search_reference(item),
        "source_preferences": {
            "prefer_merchants": ["Arvi", "Millesima", "Hawesko", "iDealwine", "Vino.com", "Berry Bros. & Rudd", "Farr Vintners"],
            "avoid_sources": ["DeinDeal", "flash deals", "one-day deals", "expired auction lots", "generic marketplaces"],
        },
        "decision_constraints": {
            "target_price": item.get("target_price"),
            "currency": item.get("currency"),
            "merchant": item.get("merchant"),
            "target_price_meaning": (
                "Il prezzo target e il prezzo realisticamente ottenibile o negoziabile per questa bottiglia, "
                "non un prezzo teorico ideale. Se e vuoto, significa che non c'e alcun prezzo da sottoporre."
            ),
            "price_rule": (
                "La recommendation finale deve considerare il prezzo target come prezzo davvero ottenibile. "
                "Confronta il prezzo target con la fascia stimata e usa questo confronto per decidere cosa "
                "fare: buy se il target e favorevole rispetto al valore stimato e non emergono rischi forti; "
                "monitor se il target e vicino al valore stimato o il caso e incerto; avoid se il target e "
                "sfavorevole o il vino ha criticita rilevanti. Se il prezzo target manca, non assumere un prezzo "
                "favorevole o sfavorevole: valuta il vino senza confronto prezzo e segnala maggiore incertezza."
            ),
        },
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
    strategy_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "recommendation": {"type": "string", "enum": ["buy", "monitor", "avoid"]},
            "signal": {"type": "string"},
            "reason": {"type": "string"},
            "price_assessment": {"type": "string"},
            "market_price_low": {"type": ["number", "null"]},
            "market_price_high": {"type": ["number", "null"]},
            "market_price_currency": {"type": "string", "enum": ["CHF", "EUR", "USD", ""]},
            "sources": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "title": {"type": "string"},
                        "url": {"type": "string"},
                        "observed_price": {"type": ["number", "null"]},
                        "observed_currency": {"type": "string", "enum": ["CHF", "EUR", "USD", ""]},
                        "observed_vintage": {"type": "string"},
                        "observed_format": {"type": "string"},
                        "match_quality": {"type": "string", "enum": ["exact", "related", "unknown"]},
                        "source_kind": {"type": "string", "enum": ["merchant", "search", "auction", "flash", "marketplace", "unknown"]},
                    },
                    "required": [
                        "title",
                        "url",
                        "observed_price",
                        "observed_currency",
                        "observed_vintage",
                        "observed_format",
                        "match_quality",
                        "source_kind",
                    ],
                },
            },
            "alternative": {
                "type": ["object", "null"],
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "producer": {"type": "string"},
                },
                "required": ["name", "producer"],
            },
        },
        "required": [
            "recommendation",
            "signal",
            "reason",
            "price_assessment",
            "market_price_low",
            "market_price_high",
            "market_price_currency",
            "sources",
            "alternative",
        ],
    }
    request_payload = {
        "model": strategy_model,
        "instructions": (
            "Sei un consulente privato per collezionismo vino. Devi dare un resoconto operativo "
            "estremamente breve per un vino in wishlist in base allo scopo dell'osservazione. Rispondi "
            "solo con JSON valido, senza Markdown e senza testo prima o dopo. Non presentare "
            "la risposta come consulenza finanziaria certa. Devi usare la ricerca web live per stimare "
            "il prezzo corrente o recente da fonti verificabili. Preferisci commercianti di vino stabili "
            "e specializzati come Arvi o simili; evita offerte flash, one-day deal, outlet temporanei, "
            "aste concluse e marketplace generici come fonte principale della fascia. Preferisci risultati per la stessa "
            "etichetta, produttore, annata e formato; usa come riferimento esatto i campi presenti in wishlist. "
            "Se non trovi almeno una fonte con annata uguale, non restituire una fascia numerica inventata: "
            "usa market_price_low null, market_price_high null e spiega brevemente in reason che mancano "
            "fonti precise. Se trovi solo formati diversi, ad esempio magnum o cassa, non usarli come base "
            "principale per la fascia 750ml. Il prezzo target in wishlist e il prezzo realisticamente ottenibile: la tua "
            "recommendation finale deve dire cosa fare con il vino proprio tenendo conto di quel prezzo. "
            "Se il prezzo target e vuoto, significa che non c'e nessun prezzo disponibile da valutare. "
            "Devi essere sintetico: "
            "signal deve essere una sola parola o pochissime parole, ad esempio 'Compra', 'Evita', "
            "'Monitora', 'Troppo caro', 'Buono da bere'. reason deve essere opzionale e lunga al "
            "massimo 20 parole. Devi stimare una fascia di mercato corrente o recente per la stessa "
            "etichetta e annata: market_price_low, market_price_high e market_price_currency. Stima questa "
            "fascia prima e in modo indipendente dal prezzo target: non usare il prezzo target per dedurre "
            "o comprimere la fascia di mercato. Se non sei certo, usa una fascia prudente ma realistica "
            "basata solo su produttore, annata, formato, fonti web trovate e mercato europeo. Non usare "
            "prezzi di annate diverse come riferimento principale. Devi poi "
            "confrontare sempre il prezzo target con quella fascia e fare dipendere la recommendation finale "
            "da questo confronto. Se il prezzo target manca, non fare il confronto prezzo e non usare "
            "price_assessment per suggerire convenienza. Se il prezzo target e almeno 20% "
            "sotto il limite basso stimato, price_assessment deve indicare che il prezzo e molto "
            "interessante, salvo rischi specifici spiegati nella reason. Per purpose Cellar o Invest, "
            "se il prezzo target e sotto la fascia stimata non usare recommendation avoid solo perche "
            "il vino non e perfetto: un target favorevole deve pesare molto nella decisione finale e "
            "normalmente deve portare a buy o almeno monitor, non avoid. "
            "Se e dentro la fascia stimata, usa una valutazione neutra. Se e sopra la fascia stimata, indica che e caro. Non usare "
            "prezzi di vini diversi o annate diverse come riferimento principale. Per purpose Invest valuta liquidita, reputazione "
            "del produttore, annata, prezzo target, track record e rischio di immobilizzo; se "
            "il profilo non e convincente, recommendation deve essere avoid o monitor e, se "
            "possibile, proponi una alternativa paritetica per fascia prezzo/stile. Per purpose "
            "Drink privilegia piacere di bevuta, finestra e prezzo target. Usa italiano corretto."
        ),
        "input": (
            "Contesto wishlist e cantina:\n"
            f"{json.dumps(context, ensure_ascii=False)}\n\n"
            "Restituisci solo questo oggetto JSON: "
            "{\"recommendation\":\"buy|monitor|avoid\",\"signal\":\"1-4 parole\","
            "\"reason\":\"massimo 12 parole\","
            "\"price_assessment\":\"valutazione sintetica del prezzo target\","
            "\"market_price_low\":numero_o_null,\"market_price_high\":numero_o_null,"
            "\"market_price_currency\":\"CHF|EUR|USD|\","
            "\"sources\":[{\"title\":\"fonte prezzo\",\"url\":\"https://...\",\"observed_price\":numero_o_null,"
            "\"observed_currency\":\"CHF|EUR|USD|\",\"observed_vintage\":\"annata trovata\","
            "\"observed_format\":\"formato trovato\",\"match_quality\":\"exact|related|unknown\","
            "\"source_kind\":\"merchant|search|auction|flash|marketplace|unknown\"}],"
            "\"alternative\":{\"name\":\"vino alternativo\",\"producer\":\"produttore\"}}. "
            "Per ogni source, compila observed_price e observed_currency se il prezzo e visibile. "
            "Usa match_quality exact solo se etichetta, produttore, annata e formato coincidono davvero. "
            "Usa source_kind merchant per commercianti stabili di vino, flash per offerte temporanee come DeinDeal. "
            "Se non hai una alternativa credibile, usa alternative null."
        ),
        "text": {
            "format": {
                "type": "json_schema",
                "name": "wishlist_strategy",
                "strict": True,
                "schema": strategy_schema,
            }
        },
        "tools": [
            {
                "type": "web_search",
                "external_web_access": True,
                "user_location": {
                    "type": "approximate",
                    "country": "CH",
                    "timezone": "Europe/Zurich",
                },
            }
        ],
        "tool_choice": "required",
        "include": ["web_search_call.action.sources"],
        "max_output_tokens": 480,
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
    strategy = clean_wishlist_strategy_payload(parse_json_object(raw_text))
    strategy["sources"] = merge_wishlist_price_sources(
        strategy.get("sources", []),
        extract_web_search_sources(response_payload),
    )
    try:
        rates = get_rates()
        strategy = derive_market_range_from_sources(strategy, item, rates)
        strategy = apply_wishlist_price_assessment(strategy, item, rates)
        strategy = normalize_wishlist_recommendation(strategy, item, rates)
    except ValueError:
        strategy["price_assessment"] = (
            strategy.get("price_assessment")
            or "Cambio valuta non disponibile: valutazione prezzo incerta."
        )
    status = wishlist_status_from_strategy(strategy["recommendation"])
    strategy_json = json.dumps(strategy, ensure_ascii=False, separators=(",", ":"))
    with connect() as conn:
        conn.execute(
            """
            UPDATE wishlist
            SET status = ?, status_source = 'ai', ai_strategy = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, strategy_json, item_id),
        )
        updated_item = get_wishlist_item(conn, item_id)
    return {"strategy": strategy, "item": updated_item}


def wine_from_row(row: sqlite3.Row) -> dict:
    wine = dict(row)
    owners_json = wine.pop("owners_json", "[]")
    grapes_json = wine.pop("grapes_json", "[]")
    try:
        owners = json.loads(owners_json or "[]")
    except json.JSONDecodeError:
        owners = []
    try:
        grapes = json.loads(grapes_json or "[]")
    except json.JSONDecodeError:
        grapes = []
    wine["owners"] = owners if isinstance(owners, list) else []
    wine["grapes"] = grapes if isinstance(grapes, list) else []
    wine.setdefault("scores", [])
    return wine


def wine_from_data(data: dict) -> dict:
    wine = dict(data)
    owners_json = wine.pop("owners_json", "[]")
    grapes_json = wine.pop("grapes_json", "[]")
    wine["owners"] = json.loads(owners_json or "[]")
    wine["grapes"] = json.loads(grapes_json or "[]")
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

    wine_by_id = {wine["id"]: wine for wine in wines}
    visible_ids = set(wine_by_id)
    consumed_bottles = 0
    sold_bottles = 0
    consumed_value_chf = 0.0
    sold_revenue_chf = 0.0
    realized_gain_loss_chf = 0.0
    consumed_regions: dict[str, int] = {}
    if visible_ids:
        placeholders = ",".join("?" for _ in visible_ids)
        with connect() as conn:
            movement_rows = conn.execute(
                f"""
                SELECT wine_id, movement_type, quantity
                FROM wine_movements
                WHERE wine_id IN ({placeholders})
                  AND movement_type IN ('drink', 'sale')
                """,
                tuple(visible_ids),
            ).fetchall()
            sale_rows = conn.execute(
                f"""
                SELECT wine_id, quantity, sale_price, currency, profit_loss
                FROM sales
                WHERE wine_id IN ({placeholders})
                """,
                tuple(visible_ids),
            ).fetchall()

        for row in movement_rows:
            quantity = abs(int(row["quantity"] or 0))
            wine = wine_by_id.get(row["wine_id"])
            if not wine or quantity <= 0:
                continue
            if row["movement_type"] == "drink":
                consumed_bottles += quantity
                consumed_value_chf += convert_to_chf(float(wine["price"] or 0) * quantity, wine["currency"], rates)
                region = wine["region"] or "Unspecified"
                consumed_regions[region] = consumed_regions.get(region, 0) + quantity
            elif row["movement_type"] == "sale":
                sold_bottles += quantity

        for row in sale_rows:
            sold_revenue_chf += convert_to_chf(float(row["sale_price"] or 0) * int(row["quantity"] or 0), row["currency"], rates)
            realized_gain_loss_chf += convert_to_chf(float(row["profit_loss"] or 0), row["currency"], rates)

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
        "movements": {
            "consumed_bottles": consumed_bottles,
            "sold_bottles": sold_bottles,
            "consumed_value": round(consumed_value_chf, 2),
            "sold_revenue": round(sold_revenue_chf, 2),
            "realized_gain_loss": round(realized_gain_loss_chf, 2),
            "consumed_regions": [
                {"region": region, "bottles": bottles}
                for region, bottles in sorted(consumed_regions.items(), key=lambda item: item[1], reverse=True)[:5]
            ],
        },
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
    grapes = clean_grapes(payload.get("grapes", []))
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
        "grapes_json": json.dumps(grapes),
        "grapes": grapes,
        "notes": str(payload.get("notes", "")).strip(),
        "ai_notes": str(payload.get("ai_notes", "")).strip(),
        "drink_from": clean_optional_int(payload.get("drink_from")),
        "drink_peak_from": clean_optional_int(payload.get("drink_peak_from")),
        "drink_peak_to": clean_optional_int(payload.get("drink_peak_to")),
        "drink_to": clean_optional_int(payload.get("drink_to")),
        "drink_window_notes": str(payload.get("drink_window_notes", "")).strip(),
        "ai_value_notes": str(payload.get("ai_value_notes", "")).strip(),
    }


def clean_movement(payload: dict) -> dict:
    movement_type = str(payload.get("movement_type", "")).strip()
    if movement_type not in {"drink", "sale", "adjustment", "arrival"}:
        raise ValueError(f"Unsupported movement type: {movement_type}")
    wine_id = str(payload.get("wine_id", "")).strip()
    if not wine_id:
        raise ValueError("Movement wine_id is required")
    currency = str(payload.get("currency") or "").strip().upper() or None
    if currency and currency not in SUPPORTED_CURRENCIES:
        raise ValueError(f"Unsupported currency: {currency}")
    occurred_at = str(payload.get("occurred_at", "")).strip()
    return {
        "id": str(payload.get("id") or uuid.uuid4()),
        "wine_id": wine_id,
        "movement_type": movement_type,
        "quantity": int(payload.get("quantity") or 0),
        "note": str(payload.get("note", "")).strip(),
        "related_id": str(payload.get("related_id") or "").strip() or None,
        "value": clean_optional_float(payload.get("value")),
        "currency": currency,
        "occurred_at": occurred_at,
    }


def clean_movement_update(payload: dict, existing: dict) -> dict:
    raw_quantity = payload.get("quantity", existing["quantity"])
    quantity = int(raw_quantity or 0)
    if existing["movement_type"] in {"drink", "sale"}:
        quantity = -abs(quantity)
    elif existing["movement_type"] == "arrival":
        quantity = abs(quantity)
    if quantity == 0:
        raise ValueError("Movement quantity cannot be zero")

    note = str(payload.get("note", existing.get("note", ""))).strip()
    return {"quantity": quantity, "note": note}


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


def clean_grapes(raw_grapes: object) -> list[dict]:
    if raw_grapes in (None, ""):
        return []
    if not isinstance(raw_grapes, list):
        raise ValueError("Grapes must be a list")

    grapes = []
    seen = set()
    for raw_grape in raw_grapes:
        if not isinstance(raw_grape, dict):
            raise ValueError("Each grape must be an object")
        name = str(raw_grape.get("name", "")).strip()
        if not name:
            continue
        percentage = clean_optional_float(raw_grape.get("percentage"))
        if percentage is not None and (percentage < 0 or percentage > 100):
            raise ValueError("Grape percentage must be between 0 and 100")
        normalized_name = name.lower()
        if normalized_name in seen:
            continue
        seen.add(normalized_name)
        grapes.append({"name": name, "percentage": percentage})

    total_percentage = sum(grape["percentage"] for grape in grapes if grape["percentage"] is not None)
    if total_percentage > 100.0001:
        raise ValueError("Grape percentages cannot exceed 100")
    return grapes


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
               ai_value_notes, grapes_json
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
    grapes = data.pop("grapes", [])
    conn.execute(
        """
        INSERT INTO wines (
            id, name, producer, vintage, quantity, format, type, region, appellation,
            price, current_value, currency, merchant, order_date, expected_delivery, status,
            owner_share_pct, owners_json, notes, ai_notes,
            drink_from, drink_peak_from, drink_peak_to, drink_to, drink_window_notes,
            ai_value_notes, grapes_json
        )
        VALUES (
            :id, :name, :producer, :vintage, :quantity, :format, :type, :region, :appellation,
            :price, :current_value, :currency, :merchant, :order_date, :expected_delivery, :status,
            :owner_share_pct, :owners_json, :notes, :ai_notes,
            :drink_from, :drink_peak_from, :drink_peak_to, :drink_to, :drink_window_notes,
            :ai_value_notes, :grapes_json
        )
        """,
        data,
    )
    replace_wine_scores(conn, data["id"], scores)
    data["scores"] = scores
    data["grapes"] = grapes
    return data


def upsert_wine(payload: dict, wine_id: str | None = None) -> dict:
    preserve_ai_notes = wine_id is not None and "ai_notes" not in payload
    preserve_ai_value_notes = wine_id is not None and "ai_value_notes" not in payload
    drink_window_fields = ["drink_from", "drink_peak_from", "drink_peak_to", "drink_to", "drink_window_notes"]
    preserve_drink_window = wine_id is not None and not any(field in payload for field in drink_window_fields)
    data = clean_wine(payload, wine_id)
    scores = data.pop("scores", [])
    grapes = data.pop("grapes", [])
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
                ai_value_notes, grapes_json
            )
            VALUES (
                :id, :name, :producer, :vintage, :quantity, :format, :type, :region, :appellation,
                :price, :current_value, :currency, :merchant, :order_date, :expected_delivery, :status,
                :owner_share_pct, :owners_json, :notes, :ai_notes,
                :drink_from, :drink_peak_from, :drink_peak_to, :drink_to, :drink_window_notes,
                :ai_value_notes, :grapes_json
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
                grapes_json = excluded.grapes_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            data,
        )
        replace_wine_scores(conn, data["id"], scores)
        data["grapes"] = grapes
        saved = get_wine(conn, data["id"])
    return saved


def delete_wine(wine_id: str) -> bool:
    with connect() as conn:
        cursor = conn.execute("DELETE FROM wines WHERE id = ?", (wine_id,))
        return cursor.rowcount > 0


def add_movement(
    conn: sqlite3.Connection,
    wine_id: str,
    movement_type: str,
    quantity: int,
    note: str = "",
    related_id: str | None = None,
    value: float | None = None,
    currency: str | None = None,
) -> str:
    movement_id = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO wine_movements (id, wine_id, movement_type, quantity, note, related_id, value, currency)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (movement_id, wine_id, movement_type, quantity, note, related_id, value, currency),
    )
    return movement_id


def get_movement(conn: sqlite3.Connection, movement_id: str) -> dict | None:
    row = conn.execute(
        """
        SELECT id, wine_id, movement_type, quantity, note, related_id, value, currency, occurred_at
        FROM wine_movements
        WHERE id = ?
        """,
        (movement_id,),
    ).fetchone()
    return dict(row) if row else None


def ensure_movement_visible(conn: sqlite3.Connection, movement: dict | None, role: str) -> dict:
    if not movement:
        raise LookupError("Movement not found")
    wine = get_wine(conn, movement["wine_id"])
    if not wine or (role == "shared_viewer" and not is_shared_position(wine)):
        raise LookupError("Movement not found")
    return wine


def apply_quantity_delta(conn: sqlite3.Connection, wine_id: str, delta: int) -> dict:
    wine = get_wine(conn, wine_id)
    if not wine:
        raise LookupError("Wine not found")
    new_quantity = int(wine["quantity"] or 0) + int(delta)
    if new_quantity < 0:
        raise ValueError("Movement would make bottle quantity negative")
    conn.execute(
        "UPDATE wines SET quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (new_quantity, wine_id),
    )
    updated = get_wine(conn, wine_id)
    if not updated:
        raise LookupError("Wine not found")
    return updated


def update_movement(movement_id: str, payload: dict) -> dict:
    with connect() as conn:
        existing = get_movement(conn, movement_id)
        ensure_movement_visible(conn, existing, "admin")
        data = clean_movement_update(payload, existing)
        delta = data["quantity"] - int(existing["quantity"] or 0)
        updated_wine = apply_quantity_delta(conn, existing["wine_id"], delta)

        value = existing.get("value")
        if existing["movement_type"] == "sale" and existing.get("related_id"):
            sale = conn.execute(
                "SELECT sale_price, unit_cost FROM sales WHERE id = ?",
                (existing["related_id"],),
            ).fetchone()
            if sale:
                sold_quantity = abs(data["quantity"])
                value = float(sale["sale_price"] or 0) * sold_quantity
                profit_loss = (float(sale["sale_price"] or 0) - float(sale["unit_cost"] or 0)) * sold_quantity
                conn.execute(
                    "UPDATE sales SET quantity = ?, profit_loss = ? WHERE id = ?",
                    (sold_quantity, profit_loss, existing["related_id"]),
                )

        conn.execute(
            """
            UPDATE wine_movements
            SET quantity = ?, note = ?, value = ?
            WHERE id = ?
            """,
            (data["quantity"], data["note"], value, movement_id),
        )
        movement = get_movement(conn, movement_id)
    return {"movement": movement, "wine": updated_wine}


def delete_movement(movement_id: str) -> dict:
    with connect() as conn:
        movement = get_movement(conn, movement_id)
        ensure_movement_visible(conn, movement, "admin")
        updated_wine = apply_quantity_delta(conn, movement["wine_id"], -int(movement["quantity"] or 0))
        if movement["movement_type"] == "sale" and movement.get("related_id"):
            conn.execute("DELETE FROM sales WHERE id = ?", (movement["related_id"],))
        conn.execute("DELETE FROM wine_movements WHERE id = ?", (movement_id,))
    return {"wine": updated_wine}


def drink_bottle(wine_id: str, payload: dict | None = None) -> dict:
    note = str((payload or {}).get("note", "")).strip() or "Bevuta 1"
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
        add_movement(conn, wine_id, "drink", -1, note)
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
        add_movement(
            conn,
            wine_id,
            "sale",
            -quantity,
            f"sale:{buyer}",
            sale_id,
            sale_price * quantity,
            currency,
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
        notes_model = get_ai_model_setting(conn, "ai_notes_model", OPENAI_MODEL)

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
        "model": notes_model,
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


def clean_grape_composition_payload(payload: dict) -> list[dict]:
    grapes = payload.get("grapes", payload if isinstance(payload, list) else [])
    return clean_grapes(grapes)


def generate_grape_composition(wine_id: str) -> dict:
    with connect() as conn:
        wine = get_wine(conn, wine_id)
        if not wine:
            raise LookupError("Wine not found")
        grape_model = get_ai_model_setting(conn, "grape_composition_model", OPENAI_MODEL)

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
        "ai_notes": wine.get("ai_notes", ""),
    }
    request_payload = {
        "model": grape_model,
        "instructions": (
            "Sei un assistente esperto di vitigni e composizione dei vini. Devi completare la lista "
            "delle uve che compongono un vino specifico. Rispondi solo con JSON valido, senza Markdown "
            "e senza testo prima o dopo. Non inventare percentuali precise se non sei ragionevolmente "
            "sicuro: in quel caso usa percentage null. Se il blend non e chiaro, restituisci solo i "
            "vitigni di cui sei abbastanza sicuro. Usa nomi vitigno standard in italiano o internazionale."
        ),
        "input": (
            "Restituisci solo questo oggetto JSON: "
            "{\"grapes\":[{\"name\":\"nome vitigno\",\"percentage\":numero_o_null}]}. "
            "Ogni percentage deve essere tra 0 e 100. Se conosci un solo vitigno dominante ma non la quota "
            "esatta, usa percentage null. Se il vino e monovitigno e sei sicuro, puoi usare 100. "
            "Contesto:\n"
            f"{json.dumps(wine_context, ensure_ascii=False)}"
        ),
        "text": {
            "format": {
                "type": "json_schema",
                "name": "grape_composition",
                "strict": True,
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "grapes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "name": {"type": "string"},
                                    "percentage": {"type": ["number", "null"]},
                                },
                                "required": ["name", "percentage"],
                            },
                        }
                    },
                    "required": ["grapes"],
                },
            }
        },
        "max_output_tokens": 220,
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
        with urlopen(request, timeout=25) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"OpenAI request failed: {error_body or exc.reason}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise ValueError(f"OpenAI request failed: {exc}") from exc

    raw_text = extract_response_text(response_payload)
    if not raw_text:
        raise ValueError("OpenAI response did not include text")
    grapes = clean_grape_composition_payload(parse_json_object(raw_text))

    with connect() as conn:
        conn.execute(
            "UPDATE wines SET grapes_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (json.dumps(grapes, ensure_ascii=False), wine_id),
        )
        updated = get_wine(conn, wine_id)
    return updated


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
        drink_window_model = get_ai_model_setting(conn, "drink_window_model", OPENAI_MODEL)

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
        "model": drink_window_model,
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
        ai_value_model = get_ai_model_setting(conn, "ai_value_model", OPENAI_VALUE_MODEL)

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
        "model": ai_value_model,
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


def replace_all_movements(movements: list[dict]) -> list[dict]:
    cleaned = [clean_movement(movement) for movement in movements]
    with connect() as conn:
        conn.execute("DELETE FROM wine_movements")
        for movement in cleaned:
            if not get_wine(conn, movement["wine_id"]):
                continue
            if movement["occurred_at"]:
                conn.execute(
                    """
                    INSERT INTO wine_movements (
                        id, wine_id, movement_type, quantity, note, related_id, value, currency, occurred_at
                    )
                    VALUES (
                        :id, :wine_id, :movement_type, :quantity, :note, :related_id, :value, :currency, :occurred_at
                    )
                    """,
                    movement,
                )
            else:
                conn.execute(
                    """
                    INSERT INTO wine_movements (id, wine_id, movement_type, quantity, note, related_id, value, currency)
                    VALUES (:id, :wine_id, :movement_type, :quantity, :note, :related_id, :value, :currency)
                    """,
                    movement,
                )
    return list_all_movements()


def replace_all_wishlist(items: list[dict]) -> list[dict]:
    cleaned = [clean_wishlist_item(item) for item in items]
    with connect() as conn:
        conn.execute("DELETE FROM wishlist")
        for item in cleaned:
            conn.execute(
                """
                INSERT INTO wishlist (
                    id, name, producer, vintage, format, type, region, appellation,
                    target_price, currency, merchant, purpose, priority, status, status_source, ai_strategy, notes
                )
                VALUES (
                    :id, :name, :producer, :vintage, :format, :type, :region, :appellation,
                    :target_price, :currency, :merchant, :purpose, :priority, :status, :status_source, :ai_strategy, :notes
                )
                """,
                item,
            )
    return list_wishlist()


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def b64url_decode(value: str) -> bytes:
    padding_len = (-len(value)) % 4
    return base64.urlsafe_b64decode((value + ("=" * padding_len)).encode("ascii"))


class CborReader:
    def __init__(self, data: bytes):
        self.data = data
        self.index = 0

    def read(self, length: int) -> bytes:
        if self.index + length > len(self.data):
            raise ValueError("CBOR payload is truncated")
        value = self.data[self.index:self.index + length]
        self.index += length
        return value

    def read_uint(self, info: int) -> int:
        if info < 24:
            return info
        if info == 24:
            return self.read(1)[0]
        if info == 25:
            return int.from_bytes(self.read(2), "big")
        if info == 26:
            return int.from_bytes(self.read(4), "big")
        if info == 27:
            return int.from_bytes(self.read(8), "big")
        raise ValueError("Unsupported CBOR integer length")

    def decode(self):
        initial = self.read(1)[0]
        major = initial >> 5
        info = initial & 0x1F
        if major == 0:
            return self.read_uint(info)
        if major == 1:
            return -1 - self.read_uint(info)
        if major == 2:
            return self.read(self.read_uint(info))
        if major == 3:
            return self.read(self.read_uint(info)).decode("utf-8")
        if major == 4:
            return [self.decode() for _ in range(self.read_uint(info))]
        if major == 5:
            return {self.decode(): self.decode() for _ in range(self.read_uint(info))}
        if major == 7:
            if info == 20:
                return False
            if info == 21:
                return True
            if info == 22:
                return None
        raise ValueError("Unsupported CBOR value")


def cbor_decode(data: bytes):
    reader = CborReader(data)
    value = reader.decode()
    if reader.index != len(data):
        raise ValueError("CBOR payload has trailing data")
    return value


def webauthn_rp_id(headers) -> str:
    host = headers.get("X-Forwarded-Host") or headers.get("Host") or "localhost"
    return host.split(":", 1)[0]


def webauthn_origin(headers) -> str:
    proto = headers.get("X-Forwarded-Proto") or ("http" if webauthn_rp_id(headers) in {"localhost", "127.0.0.1"} else "https")
    host = headers.get("X-Forwarded-Host") or headers.get("Host") or "localhost"
    return f"{proto}://{host}"


def make_challenge(kind: str, role: str = "") -> str:
    challenge = b64url_encode(os.urandom(32))
    WEBAUTHN_CHALLENGES[challenge] = {"kind": kind, "role": role, "expires_at": time.time() + 300}
    return challenge


def consume_challenge(challenge: str, kind: str) -> dict:
    record = WEBAUTHN_CHALLENGES.pop(challenge, None)
    if not record or record.get("kind") != kind or record.get("expires_at", 0) < time.time():
        raise ValueError("Invalid or expired passkey challenge")
    return record


def parse_client_data(encoded: str, expected_type: str, expected_origin: str) -> dict:
    raw = b64url_decode(encoded)
    data = json.loads(raw.decode("utf-8"))
    if data.get("type") != expected_type:
        raise ValueError("Invalid passkey response type")
    if data.get("origin") != expected_origin:
        raise ValueError("Invalid passkey origin")
    consume_challenge(data.get("challenge", ""), expected_type)
    return data


def parse_authenticator_data(auth_data: bytes, rp_id: str, require_attested: bool = False) -> dict:
    if len(auth_data) < 37:
        raise ValueError("Invalid authenticator data")
    expected_hash = hashlib.sha256(rp_id.encode("utf-8")).digest()
    if auth_data[:32] != expected_hash:
        raise ValueError("Invalid passkey relying party")
    flags = auth_data[32]
    if not flags & 0x01:
        raise ValueError("Passkey user presence is required")
    sign_count = int.from_bytes(auth_data[33:37], "big")
    result = {"flags": flags, "sign_count": sign_count}
    if require_attested:
        if not flags & 0x40:
            raise ValueError("Passkey attestation data is missing")
        offset = 37 + 16
        credential_len = int.from_bytes(auth_data[offset:offset + 2], "big")
        offset += 2
        credential_id = auth_data[offset:offset + credential_len]
        offset += credential_len
        public_key_cose = auth_data[offset:]
        cbor_decode(public_key_cose)
        result.update({"credential_id": credential_id, "public_key_cose": public_key_cose})
    return result


def cose_public_key(cose: bytes):
    key = cbor_decode(cose)
    if key.get(1) == 2 and key.get(3) == -7 and key.get(-1) == 1:
        x = int.from_bytes(key[-2], "big")
        y = int.from_bytes(key[-3], "big")
        return ec.EllipticCurvePublicNumbers(x, y, ec.SECP256R1()).public_key()
    if key.get(1) == 3 and key.get(3) == -257:
        n = int.from_bytes(key[-1], "big")
        e = int.from_bytes(key[-2], "big")
        return rsa.RSAPublicNumbers(e, n).public_key()
    raise ValueError("Unsupported passkey public key")


def verify_webauthn_signature(cose: bytes, signature: bytes, signed_data: bytes) -> None:
    public_key = cose_public_key(cose)
    if isinstance(public_key, ec.EllipticCurvePublicKey):
        try:
            r, s = decode_dss_signature(signature)
            public_key.verify(encode_dss_signature(r, s), signed_data, ec.ECDSA(hashes.SHA256()))
        except (ValueError, InvalidSignature) as exc:
            raise ValueError("Invalid passkey signature") from exc
        return
    public_key.verify(signature, signed_data, padding.PKCS1v15(), hashes.SHA256())


def list_passkey_credentials(role: str | None = None) -> list[dict]:
    with connect() as conn:
        if role:
            rows = conn.execute("SELECT credential_id, role FROM passkey_credentials WHERE role = ?", (role,)).fetchall()
        else:
            rows = conn.execute("SELECT credential_id, role FROM passkey_credentials").fetchall()
    return [dict(row) for row in rows]


def passkey_register_options(role: str, headers) -> dict:
    rp_id = webauthn_rp_id(headers)
    challenge = make_challenge("webauthn.create", role)
    existing = list_passkey_credentials(role)
    return {
        "challenge": challenge,
        "rp": {"name": "Wine Cellar", "id": rp_id},
        "user": {"id": b64url_encode(role.encode("utf-8")), "name": role, "displayName": role},
        "pubKeyCredParams": [{"type": "public-key", "alg": -7}, {"type": "public-key", "alg": -257}],
        "timeout": 60000,
        "attestation": "none",
        "authenticatorSelection": {"residentKey": "preferred", "userVerification": "required"},
        "excludeCredentials": [{"type": "public-key", "id": item["credential_id"]} for item in existing],
    }


def verify_passkey_registration(payload: dict, role: str, headers) -> dict:
    client_data_json = payload.get("response", {}).get("clientDataJSON", "")
    attestation_object = payload.get("response", {}).get("attestationObject", "")
    parse_client_data(client_data_json, "webauthn.create", webauthn_origin(headers))
    attestation = cbor_decode(b64url_decode(attestation_object))
    auth = parse_authenticator_data(attestation.get("authData", b""), webauthn_rp_id(headers), require_attested=True)
    credential_id = b64url_encode(auth["credential_id"])
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO passkey_credentials (credential_id, role, public_key_cose, sign_count)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(credential_id) DO UPDATE SET role = excluded.role, public_key_cose = excluded.public_key_cose,
                sign_count = excluded.sign_count
            """,
            (credential_id, role, auth["public_key_cose"], auth["sign_count"]),
        )
    return {"registered": True}


def passkey_login_options(headers) -> dict:
    challenge = make_challenge("webauthn.get")
    credentials = list_passkey_credentials()
    return {
        "challenge": challenge,
        "rpId": webauthn_rp_id(headers),
        "timeout": 60000,
        "userVerification": "required",
        "allowCredentials": [{"type": "public-key", "id": item["credential_id"]} for item in credentials],
    }


def verify_passkey_login(payload: dict, headers) -> str:
    credential_id = payload.get("rawId") or payload.get("id")
    if not credential_id:
        raise ValueError("Missing passkey credential")
    response = payload.get("response", {})
    client_data_json = response.get("clientDataJSON", "")
    authenticator_data = b64url_decode(response.get("authenticatorData", ""))
    signature = b64url_decode(response.get("signature", ""))
    parse_client_data(client_data_json, "webauthn.get", webauthn_origin(headers))
    auth = parse_authenticator_data(authenticator_data, webauthn_rp_id(headers))
    with connect() as conn:
        row = conn.execute(
            "SELECT credential_id, role, public_key_cose, sign_count FROM passkey_credentials WHERE credential_id = ?",
            (credential_id,),
        ).fetchone()
        if not row:
            raise LookupError("Passkey not found")
        signed_data = authenticator_data + hashlib.sha256(b64url_decode(client_data_json)).digest()
        verify_webauthn_signature(row["public_key_cose"], signature, signed_data)
        if auth["sign_count"] and row["sign_count"] and auth["sign_count"] <= row["sign_count"]:
            raise ValueError("Passkey sign counter is invalid")
        conn.execute(
            "UPDATE passkey_credentials SET sign_count = ?, last_used_at = CURRENT_TIMESTAMP WHERE credential_id = ?",
            (auth["sign_count"], credential_id),
        )
        return row["role"]


def auth_payload(role: str) -> dict:
    with connect() as conn:
        app_theme = get_app_theme(conn)
    passkey_supported = AUTH_ENABLED
    return {
        "authenticated": role != "anonymous",
        "role": role,
        "auth_enabled": AUTH_ENABLED,
        "app_theme": app_theme,
        "passkeys_enabled": passkey_supported,
        "passkey_available": bool(list_passkey_credentials()),
        "passkey_registered": bool(role != "anonymous" and list_passkey_credentials(role)),
    }


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
        if path == "/api/movements":
            self.send_json(visible_movements(self.current_role()))
            return
        if path == "/api/export":
            if not self.require_admin():
                return
            self.send_json({"wines": list_wines(), "wishlist": list_wishlist(), "movements": list_all_movements()})
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
        if path.startswith("/api/wines/") and path.endswith("/movements"):
            wine_id = unquote(path.removeprefix("/api/wines/").removesuffix("/movements"))
            try:
                self.send_json(list_movements(wine_id, self.current_role()))
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
            if path == "/api/passkeys/login/options":
                self.send_json(passkey_login_options(self.headers))
                return
            if path == "/api/passkeys/login/verify":
                try:
                    role = verify_passkey_login(self.read_json(), self.headers)
                    self.start_session(role)
                except LookupError as exc:
                    self.send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
                return
            if path == "/api/logout":
                self.logout()
                return
            if path == "/api/passkeys/register/options":
                if not self.require_authenticated():
                    return
                self.send_json(passkey_register_options(self.current_role(), self.headers))
                return
            if path == "/api/passkeys/register/verify":
                if not self.require_authenticated():
                    return
                self.send_json(verify_passkey_registration(self.read_json(), self.current_role(), self.headers))
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
            if path.startswith("/api/wines/") and path.endswith("/grapes"):
                wine_id = unquote(path.removeprefix("/api/wines/").removesuffix("/grapes"))
                try:
                    self.send_json(generate_grape_composition(wine_id))
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
                    self.send_json(drink_bottle(wine_id, self.read_json()))
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
                movements = []
                if "movements" in payload:
                    if not isinstance(payload["movements"], list):
                        raise ValueError("Import movements payload must be a list")
                    movements = replace_all_movements(payload["movements"])
                if "wishlist" in payload:
                    if not isinstance(payload["wishlist"], list):
                        raise ValueError("Import wishlist payload must be a list")
                    wishlist = replace_all_wishlist(payload["wishlist"])
                else:
                    wishlist = list_wishlist()
                self.send_json({"wines": wines, "wishlist": wishlist, "movements": movements})
                return
            self.send_error(HTTPStatus.NOT_FOUND)
        except ValueError as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def do_PUT(self) -> None:
        path = urlparse(self.path).path
        if path.startswith("/api/movements/"):
            if not self.require_admin():
                return
            movement_id = unquote(path.removeprefix("/api/movements/"))
            try:
                self.send_json(update_movement(movement_id, self.read_json()))
            except LookupError as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
            except ValueError as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
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
        if path.startswith("/api/movements/"):
            if not self.require_admin():
                return
            movement_id = unquote(path.removeprefix("/api/movements/"))
            try:
                self.send_json(delete_movement(movement_id))
            except LookupError as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
            except ValueError as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
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

        self.start_session(role)

    def start_session(self, role: str) -> None:
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
