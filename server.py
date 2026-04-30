from __future__ import annotations

import json
import sqlite3
import time
import uuid
from argparse import ArgumentParser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "cellar.db"
RATES_URL = "https://api.frankfurter.dev/v1/latest?base=EUR&symbols=CHF,USD"
RATES_CACHE_SECONDS = 60 * 60 * 12
REFERENCE_CURRENCY = "CHF"
SUPPORTED_CURRENCIES = {"CHF", "EUR", "USD"}

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

CATALOG_VERSION = 5
CATALOG_WINES = [
    {"name": "Chateau Lafite Rothschild", "producer": "Chateau Lafite Rothschild", "region": "Bordeaux", "appellation": "Pauillac", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Latour", "producer": "Chateau Latour", "region": "Bordeaux", "appellation": "Pauillac", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Margaux", "producer": "Chateau Margaux", "region": "Bordeaux", "appellation": "Margaux", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Mouton Rothschild", "producer": "Chateau Mouton Rothschild", "region": "Bordeaux", "appellation": "Pauillac", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Haut-Brion", "producer": "Chateau Haut-Brion", "region": "Bordeaux", "appellation": "Pessac-Leognan", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau d'Yquem", "producer": "Chateau d'Yquem", "region": "Bordeaux", "appellation": "Sauternes", "type": "Dessert", "format": "Half (375ml)"},
    {"name": "Petrus", "producer": "Petrus", "region": "Bordeaux", "appellation": "Pomerol", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Cheval Blanc", "producer": "Chateau Cheval Blanc", "region": "Bordeaux", "appellation": "Saint-Emilion", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Sassicaia", "producer": "Tenuta San Guido", "region": "Tuscany", "appellation": "Bolgheri Sassicaia", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Guidalberto", "producer": "Tenuta San Guido", "region": "Tuscany", "appellation": "Toscana IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Le Difese", "producer": "Tenuta San Guido", "region": "Tuscany", "appellation": "Toscana IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Tignanello", "producer": "Marchesi Antinori", "region": "Tuscany", "appellation": "Toscana IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Solaia", "producer": "Marchesi Antinori", "region": "Tuscany", "appellation": "Toscana IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Guado al Tasso", "producer": "Tenuta Guado al Tasso", "region": "Tuscany", "appellation": "Bolgheri Superiore", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Cont'Ugo", "producer": "Tenuta Guado al Tasso", "region": "Tuscany", "appellation": "Bolgheri", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Il Bruciato", "producer": "Tenuta Guado al Tasso", "region": "Tuscany", "appellation": "Bolgheri", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Scalabrone", "producer": "Tenuta Guado al Tasso", "region": "Tuscany", "appellation": "Bolgheri Rosato", "type": "Rose", "format": "Bottle (750ml)"},
    {"name": "Ornellaia", "producer": "Tenuta dell'Ornellaia", "region": "Tuscany", "appellation": "Bolgheri Superiore", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Le Serre Nuove dell'Ornellaia", "producer": "Tenuta dell'Ornellaia", "region": "Tuscany", "appellation": "Bolgheri Rosso", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Le Volte dell'Ornellaia", "producer": "Tenuta dell'Ornellaia", "region": "Tuscany", "appellation": "Toscana IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Poggio alle Gazze dell'Ornellaia", "producer": "Tenuta dell'Ornellaia", "region": "Tuscany", "appellation": "Toscana IGT", "type": "White", "format": "Bottle (750ml)"},
    {"name": "Masseto", "producer": "Masseto", "region": "Tuscany", "appellation": "Toscana IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Massetino", "producer": "Masseto", "region": "Tuscany", "appellation": "Toscana IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Biserno", "producer": "Tenuta di Biserno", "region": "Tuscany", "appellation": "Toscana IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Lodovico", "producer": "Tenuta di Biserno", "region": "Tuscany", "appellation": "Toscana IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Il Pino di Biserno", "producer": "Tenuta di Biserno", "region": "Tuscany", "appellation": "Toscana IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Insoglio del Cinghiale", "producer": "Tenuta di Biserno", "region": "Tuscany", "appellation": "Toscana IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Sof", "producer": "Tenuta di Biserno", "region": "Tuscany", "appellation": "Toscana IGT", "type": "Rose", "format": "Bottle (750ml)"},
    {"name": "Argentiera", "producer": "Tenuta Argentiera", "region": "Tuscany", "appellation": "Bolgheri Superiore", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Villa Donoratico", "producer": "Tenuta Argentiera", "region": "Tuscany", "appellation": "Bolgheri", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Poggio ai Ginepri", "producer": "Tenuta Argentiera", "region": "Tuscany", "appellation": "Bolgheri", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Grattamacco Bolgheri Superiore", "producer": "Grattamacco", "region": "Tuscany", "appellation": "Bolgheri Superiore", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "L'Alberello", "producer": "Grattamacco", "region": "Tuscany", "appellation": "Bolgheri", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Dedicato a Walter", "producer": "Poggio al Tesoro", "region": "Tuscany", "appellation": "Toscana IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Sondraia", "producer": "Poggio al Tesoro", "region": "Tuscany", "appellation": "Bolgheri Superiore", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Solengo", "producer": "Argiano", "region": "Tuscany", "appellation": "Toscana IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Barolo Monfortino", "producer": "Giacomo Conterno", "region": "Piedmont", "appellation": "Barolo", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Sori San Lorenzo", "producer": "Gaja", "region": "Piedmont", "appellation": "Langhe", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Montrachet Grand Cru", "producer": "Domaine Leflaive", "region": "Burgundy", "appellation": "Montrachet", "type": "White", "format": "Bottle (750ml)"},
    {"name": "Romanee-Conti Grand Cru", "producer": "Domaine de la Romanee-Conti", "region": "Burgundy", "appellation": "Romanee-Conti", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "La Tache Grand Cru", "producer": "Domaine de la Romanee-Conti", "region": "Burgundy", "appellation": "La Tache", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Krug Grande Cuvee", "producer": "Krug", "region": "Champagne", "appellation": "Champagne", "type": "Sparkling", "format": "Bottle (750ml)"},
    {"name": "Dom Perignon", "producer": "Dom Perignon", "region": "Champagne", "appellation": "Champagne", "type": "Sparkling", "format": "Bottle (750ml)"},
    {"name": "Cristal", "producer": "Louis Roederer", "region": "Champagne", "appellation": "Champagne", "type": "Sparkling", "format": "Bottle (750ml)"},
    {"name": "Opus One", "producer": "Opus One Winery", "region": "Napa Valley", "appellation": "Oakville", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Screaming Eagle Cabernet Sauvignon", "producer": "Screaming Eagle", "region": "Napa Valley", "appellation": "Oakville", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Penfolds Grange", "producer": "Penfolds", "region": "South Australia", "appellation": "South Australia", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Pontet-Canet", "producer": "Chateau Pontet-Canet", "region": "Bordeaux", "appellation": "Pauillac", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Palmer", "producer": "Chateau Palmer", "region": "Bordeaux", "appellation": "Margaux", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Lynch-Bages", "producer": "Chateau Lynch-Bages", "region": "Bordeaux", "appellation": "Pauillac", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Ducru-Beaucaillou", "producer": "Chateau Ducru-Beaucaillou", "region": "Bordeaux", "appellation": "Saint-Julien", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Leoville Las Cases", "producer": "Chateau Leoville Las Cases", "region": "Bordeaux", "appellation": "Saint-Julien", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Leoville Barton", "producer": "Chateau Leoville Barton", "region": "Bordeaux", "appellation": "Saint-Julien", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Leoville Poyferre", "producer": "Chateau Leoville Poyferre", "region": "Bordeaux", "appellation": "Saint-Julien", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Pichon Baron", "producer": "Chateau Pichon Baron", "region": "Bordeaux", "appellation": "Pauillac", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Pichon Longueville Comtesse de Lalande", "producer": "Chateau Pichon Longueville Comtesse de Lalande", "region": "Bordeaux", "appellation": "Pauillac", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Cos d'Estournel", "producer": "Chateau Cos d'Estournel", "region": "Bordeaux", "appellation": "Saint-Estephe", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Montrose", "producer": "Chateau Montrose", "region": "Bordeaux", "appellation": "Saint-Estephe", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Calon Segur", "producer": "Chateau Calon Segur", "region": "Bordeaux", "appellation": "Saint-Estephe", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Rauzan-Segla", "producer": "Chateau Rauzan-Segla", "region": "Bordeaux", "appellation": "Margaux", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Brane-Cantenac", "producer": "Chateau Brane-Cantenac", "region": "Bordeaux", "appellation": "Margaux", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Beychevelle", "producer": "Chateau Beychevelle", "region": "Bordeaux", "appellation": "Saint-Julien", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Canon", "producer": "Chateau Canon", "region": "Bordeaux", "appellation": "Saint-Emilion", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Figeac", "producer": "Chateau Figeac", "region": "Bordeaux", "appellation": "Saint-Emilion", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Angelus", "producer": "Chateau Angelus", "region": "Bordeaux", "appellation": "Saint-Emilion", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Ausone", "producer": "Chateau Ausone", "region": "Bordeaux", "appellation": "Saint-Emilion", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau La Conseillante", "producer": "Chateau La Conseillante", "region": "Bordeaux", "appellation": "Pomerol", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau L'Evangile", "producer": "Chateau L'Evangile", "region": "Bordeaux", "appellation": "Pomerol", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Vieux Chateau Certan", "producer": "Vieux Chateau Certan", "region": "Bordeaux", "appellation": "Pomerol", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Smith Haut Lafitte", "producer": "Chateau Smith Haut Lafitte", "region": "Bordeaux", "appellation": "Pessac-Leognan", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Domaine de Chevalier", "producer": "Domaine de Chevalier", "region": "Bordeaux", "appellation": "Pessac-Leognan", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Clos des Lambrays Grand Cru", "producer": "Domaine des Lambrays", "region": "Burgundy", "appellation": "Clos des Lambrays", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Clos de Tart Grand Cru", "producer": "Clos de Tart", "region": "Burgundy", "appellation": "Clos de Tart", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Musigny Grand Cru", "producer": "Domaine Comte Georges de Vogue", "region": "Burgundy", "appellation": "Musigny", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Bonnes-Mares Grand Cru", "producer": "Domaine Comte Georges de Vogue", "region": "Burgundy", "appellation": "Bonnes-Mares", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Richebourg Grand Cru", "producer": "Domaine de la Romanee-Conti", "region": "Burgundy", "appellation": "Richebourg", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Echezeaux Grand Cru", "producer": "Domaine de la Romanee-Conti", "region": "Burgundy", "appellation": "Echezeaux", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Meursault Clos de la Barre", "producer": "Domaine des Comtes Lafon", "region": "Burgundy", "appellation": "Meursault", "type": "White", "format": "Bottle (750ml)"},
    {"name": "Puligny-Montrachet Les Pucelles", "producer": "Domaine Leflaive", "region": "Burgundy", "appellation": "Puligny-Montrachet Premier Cru", "type": "White", "format": "Bottle (750ml)"},
    {"name": "Corton-Charlemagne Grand Cru", "producer": "Bonneau du Martray", "region": "Burgundy", "appellation": "Corton-Charlemagne", "type": "White", "format": "Bottle (750ml)"},
    {"name": "Chablis Les Clos Grand Cru", "producer": "Domaine Raveneau", "region": "Burgundy", "appellation": "Chablis Grand Cru", "type": "White", "format": "Bottle (750ml)"},
    {"name": "Barbaresco", "producer": "Gaja", "region": "Piedmont", "appellation": "Barbaresco", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Sori Tildin", "producer": "Gaja", "region": "Piedmont", "appellation": "Langhe", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Sperss", "producer": "Gaja", "region": "Piedmont", "appellation": "Langhe", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Barolo Monprivato", "producer": "Giuseppe Mascarello", "region": "Piedmont", "appellation": "Barolo", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Barolo Brunate", "producer": "Giuseppe Rinaldi", "region": "Piedmont", "appellation": "Barolo", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Barolo Cannubi Boschis", "producer": "Luciano Sandrone", "region": "Piedmont", "appellation": "Barolo", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Barolo Monvigliero", "producer": "G.B. Burlotto", "region": "Piedmont", "appellation": "Barolo", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Barolo Granbussia Riserva", "producer": "Aldo Conterno", "region": "Piedmont", "appellation": "Barolo", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Brunello di Montalcino Riserva", "producer": "Biondi-Santi", "region": "Tuscany", "appellation": "Brunello di Montalcino", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Brunello di Montalcino Cerretalto", "producer": "Casanova di Neri", "region": "Tuscany", "appellation": "Brunello di Montalcino", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Brunello di Montalcino", "producer": "Poggio di Sotto", "region": "Tuscany", "appellation": "Brunello di Montalcino", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Le Pergole Torte", "producer": "Montevertine", "region": "Tuscany", "appellation": "Toscana IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Flaccianello della Pieve", "producer": "Fontodi", "region": "Tuscany", "appellation": "Toscana IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Redigaffi", "producer": "Tua Rita", "region": "Tuscany", "appellation": "Toscana IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Messorio", "producer": "Le Macchiole", "region": "Tuscany", "appellation": "Toscana IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Paleo Rosso", "producer": "Le Macchiole", "region": "Tuscany", "appellation": "Toscana IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Scrio", "producer": "Le Macchiole", "region": "Tuscany", "appellation": "Toscana IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Saffredi", "producer": "Fattoria Le Pupille", "region": "Tuscany", "appellation": "Maremma Toscana", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Galatrona", "producer": "Petrolo", "region": "Tuscany", "appellation": "Val d'Arno di Sopra", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Cepparello", "producer": "Isole e Olena", "region": "Tuscany", "appellation": "Toscana IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Fontalloro", "producer": "Felsina", "region": "Tuscany", "appellation": "Toscana IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Camartina", "producer": "Querciabella", "region": "Tuscany", "appellation": "Toscana IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "L'Apparita", "producer": "Castello di Ama", "region": "Tuscany", "appellation": "Toscana IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chianti Classico Gran Selezione Vigna del Sorbo", "producer": "Fontodi", "region": "Tuscany", "appellation": "Chianti Classico", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chianti Classico Gran Selezione San Lorenzo", "producer": "Castello di Ama", "region": "Tuscany", "appellation": "Chianti Classico", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Brunello di Montalcino Madonna delle Grazie", "producer": "Il Marroneto", "region": "Tuscany", "appellation": "Brunello di Montalcino", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Brunello di Montalcino Tenuta Nuova", "producer": "Casanova di Neri", "region": "Tuscany", "appellation": "Brunello di Montalcino", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Brunello di Montalcino Riserva Poggio al Vento", "producer": "Col d'Orcia", "region": "Tuscany", "appellation": "Brunello di Montalcino", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Brunello di Montalcino Sugarille", "producer": "Pieve Santa Restituta", "region": "Tuscany", "appellation": "Brunello di Montalcino", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Brunello di Montalcino Vigna Schiena d'Asino", "producer": "Mastrojanni", "region": "Tuscany", "appellation": "Brunello di Montalcino", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Amarone della Valpolicella Monte Lodoletta", "producer": "Dal Forno Romano", "region": "Veneto", "appellation": "Amarone della Valpolicella", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Amarone della Valpolicella", "producer": "Giuseppe Quintarelli", "region": "Veneto", "appellation": "Amarone della Valpolicella", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Montepulciano d'Abruzzo", "producer": "Emidio Pepe", "region": "Abruzzo", "appellation": "Montepulciano d'Abruzzo", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Trebbiano d'Abruzzo", "producer": "Valentini", "region": "Abruzzo", "appellation": "Trebbiano d'Abruzzo", "type": "White", "format": "Bottle (750ml)"},
    {"name": "Etna Rosso Vigna Barbagalli", "producer": "Pietradolce", "region": "Sicily", "appellation": "Etna Rosso", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Cote-Rotie La Landonne", "producer": "E. Guigal", "region": "Rhone", "appellation": "Cote-Rotie", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Cote-Rotie La Mouline", "producer": "E. Guigal", "region": "Rhone", "appellation": "Cote-Rotie", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Hermitage La Chapelle", "producer": "Paul Jaboulet Aine", "region": "Rhone", "appellation": "Hermitage", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateauneuf-du-Pape Hommage a Jacques Perrin", "producer": "Chateau de Beaucastel", "region": "Rhone", "appellation": "Chateauneuf-du-Pape", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Salon Le Mesnil", "producer": "Salon", "region": "Champagne", "appellation": "Champagne", "type": "Sparkling", "format": "Bottle (750ml)"},
    {"name": "Bollinger La Grande Annee", "producer": "Bollinger", "region": "Champagne", "appellation": "Champagne", "type": "Sparkling", "format": "Bottle (750ml)"},
    {"name": "Taittinger Comtes de Champagne", "producer": "Taittinger", "region": "Champagne", "appellation": "Champagne", "type": "Sparkling", "format": "Bottle (750ml)"},
    {"name": "Perrier-Jouet Belle Epoque", "producer": "Perrier-Jouet", "region": "Champagne", "appellation": "Champagne", "type": "Sparkling", "format": "Bottle (750ml)"},
    {"name": "Dominus Estate", "producer": "Dominus Estate", "region": "Napa Valley", "appellation": "Yountville", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Harlan Estate", "producer": "Harlan Estate", "region": "Napa Valley", "appellation": "Napa Valley", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Colgin IX Estate", "producer": "Colgin Cellars", "region": "Napa Valley", "appellation": "Napa Valley", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Insignia", "producer": "Joseph Phelps", "region": "Napa Valley", "appellation": "Napa Valley", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Vega Sicilia Unico", "producer": "Vega Sicilia", "region": "Ribera del Duero", "appellation": "Ribera del Duero", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Pingus", "producer": "Dominio de Pingus", "region": "Ribera del Duero", "appellation": "Ribera del Duero", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Almaviva", "producer": "Almaviva", "region": "Maipo Valley", "appellation": "Puente Alto", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Clos Apalta", "producer": "Casa Lapostolle", "region": "Colchagua Valley", "appellation": "Apalta", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Catena Zapata Adrianna Vineyard Mundus Bacillus Terrae", "producer": "Catena Zapata", "region": "Mendoza", "appellation": "Gualtallary", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Egon Muller Scharzhofberger Riesling Spatlese", "producer": "Egon Muller", "region": "Mosel", "appellation": "Scharzhofberger", "type": "White", "format": "Bottle (750ml)"},
    {"name": "Chateau Gruaud Larose", "producer": "Chateau Gruaud Larose", "region": "Bordeaux", "appellation": "Saint-Julien", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Talbot", "producer": "Chateau Talbot", "region": "Bordeaux", "appellation": "Saint-Julien", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Branaire-Ducru", "producer": "Chateau Branaire-Ducru", "region": "Bordeaux", "appellation": "Saint-Julien", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Saint-Pierre", "producer": "Chateau Saint-Pierre", "region": "Bordeaux", "appellation": "Saint-Julien", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Lagrange", "producer": "Chateau Lagrange", "region": "Bordeaux", "appellation": "Saint-Julien", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Clerc Milon", "producer": "Chateau Clerc Milon", "region": "Bordeaux", "appellation": "Pauillac", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Duhart-Milon", "producer": "Chateau Duhart-Milon", "region": "Bordeaux", "appellation": "Pauillac", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Grand-Puy-Lacoste", "producer": "Chateau Grand-Puy-Lacoste", "region": "Bordeaux", "appellation": "Pauillac", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Haut-Batailley", "producer": "Chateau Haut-Batailley", "region": "Bordeaux", "appellation": "Pauillac", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Batailley", "producer": "Chateau Batailley", "region": "Bordeaux", "appellation": "Pauillac", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau d'Armailhac", "producer": "Chateau d'Armailhac", "region": "Bordeaux", "appellation": "Pauillac", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Giscours", "producer": "Chateau Giscours", "region": "Bordeaux", "appellation": "Margaux", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Lascombes", "producer": "Chateau Lascombes", "region": "Bordeaux", "appellation": "Margaux", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Malescot Saint Exupery", "producer": "Chateau Malescot Saint Exupery", "region": "Bordeaux", "appellation": "Margaux", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Kirwan", "producer": "Chateau Kirwan", "region": "Bordeaux", "appellation": "Margaux", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Prieure-Lichine", "producer": "Chateau Prieure-Lichine", "region": "Bordeaux", "appellation": "Margaux", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau La Mission Haut-Brion", "producer": "Chateau La Mission Haut-Brion", "region": "Bordeaux", "appellation": "Pessac-Leognan", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Pape Clement", "producer": "Chateau Pape Clement", "region": "Bordeaux", "appellation": "Pessac-Leognan", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Malartic-Lagraviere", "producer": "Chateau Malartic-Lagraviere", "region": "Bordeaux", "appellation": "Pessac-Leognan", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Clinet", "producer": "Chateau Clinet", "region": "Bordeaux", "appellation": "Pomerol", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Trotanoy", "producer": "Chateau Trotanoy", "region": "Bordeaux", "appellation": "Pomerol", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Le Pin", "producer": "Chateau Le Pin", "region": "Bordeaux", "appellation": "Pomerol", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Troplong Mondot", "producer": "Chateau Troplong Mondot", "region": "Bordeaux", "appellation": "Saint-Emilion", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Pavie", "producer": "Chateau Pavie", "region": "Bordeaux", "appellation": "Saint-Emilion", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Pavie Macquin", "producer": "Chateau Pavie Macquin", "region": "Bordeaux", "appellation": "Saint-Emilion", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Larcis Ducasse", "producer": "Chateau Larcis Ducasse", "region": "Bordeaux", "appellation": "Saint-Emilion", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateau Coutet", "producer": "Chateau Coutet", "region": "Bordeaux", "appellation": "Barsac", "type": "Dessert", "format": "Half (375ml)"},
    {"name": "Chateau Climens", "producer": "Chateau Climens", "region": "Bordeaux", "appellation": "Barsac", "type": "Dessert", "format": "Half (375ml)"},
    {"name": "Chateau Rieussec", "producer": "Chateau Rieussec", "region": "Bordeaux", "appellation": "Sauternes", "type": "Dessert", "format": "Half (375ml)"},
    {"name": "Chateau Suduiraut", "producer": "Chateau Suduiraut", "region": "Bordeaux", "appellation": "Sauternes", "type": "Dessert", "format": "Half (375ml)"},
    {"name": "Chambertin Grand Cru", "producer": "Domaine Armand Rousseau", "region": "Burgundy", "appellation": "Chambertin", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chambertin Clos de Beze Grand Cru", "producer": "Domaine Armand Rousseau", "region": "Burgundy", "appellation": "Chambertin Clos de Beze", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Gevrey-Chambertin Clos Saint-Jacques", "producer": "Domaine Armand Rousseau", "region": "Burgundy", "appellation": "Gevrey-Chambertin Premier Cru", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Clos Saint-Denis Grand Cru", "producer": "Domaine Dujac", "region": "Burgundy", "appellation": "Clos Saint-Denis", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Clos de la Roche Grand Cru", "producer": "Domaine Dujac", "region": "Burgundy", "appellation": "Clos de la Roche", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chambolle-Musigny Les Amoureuses", "producer": "Domaine Georges Roumier", "region": "Burgundy", "appellation": "Chambolle-Musigny Premier Cru", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Bonnes-Mares Grand Cru Roumier", "producer": "Domaine Georges Roumier", "region": "Burgundy", "appellation": "Bonnes-Mares", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Vosne-Romanee Cros Parantoux", "producer": "Emmanuel Rouget", "region": "Burgundy", "appellation": "Vosne-Romanee Premier Cru", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Nuits-Saint-Georges Aux Murgers", "producer": "Domaine Meo-Camuzet", "region": "Burgundy", "appellation": "Nuits-Saint-Georges Premier Cru", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Volnay Clos des Ducs", "producer": "Marquis d'Angerville", "region": "Burgundy", "appellation": "Volnay Premier Cru", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Meursault Perrieres", "producer": "Domaine des Comtes Lafon", "region": "Burgundy", "appellation": "Meursault Premier Cru", "type": "White", "format": "Bottle (750ml)"},
    {"name": "Meursault Charmes", "producer": "Domaine Roulot", "region": "Burgundy", "appellation": "Meursault Premier Cru", "type": "White", "format": "Bottle (750ml)"},
    {"name": "Chevalier-Montrachet Grand Cru", "producer": "Domaine Leflaive", "region": "Burgundy", "appellation": "Chevalier-Montrachet", "type": "White", "format": "Bottle (750ml)"},
    {"name": "Batard-Montrachet Grand Cru", "producer": "Domaine Leflaive", "region": "Burgundy", "appellation": "Batard-Montrachet", "type": "White", "format": "Bottle (750ml)"},
    {"name": "Pavillon Blanc du Chateau Margaux", "producer": "Chateau Margaux", "region": "Bordeaux", "appellation": "Bordeaux", "type": "White", "format": "Bottle (750ml)"},
    {"name": "Y d'Yquem", "producer": "Chateau d'Yquem", "region": "Bordeaux", "appellation": "Bordeaux", "type": "White", "format": "Bottle (750ml)"},
    {"name": "Cervaro della Sala", "producer": "Castello della Sala", "region": "Umbria", "appellation": "Umbria IGT", "type": "White", "format": "Bottle (750ml)"},
    {"name": "Gaia & Rey", "producer": "Gaja", "region": "Piedmont", "appellation": "Langhe", "type": "White", "format": "Bottle (750ml)"},
    {"name": "San Leonardo", "producer": "Tenuta San Leonardo", "region": "Trentino", "appellation": "Vigneti delle Dolomiti IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Kurni", "producer": "Oasi degli Angeli", "region": "Marche", "appellation": "Marche IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Sagrantino di Montefalco 25 Anni", "producer": "Arnaldo Caprai", "region": "Umbria", "appellation": "Montefalco Sagrantino", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Turriga", "producer": "Argiolas", "region": "Sardinia", "appellation": "Isola dei Nuraghi IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Terra di Lavoro", "producer": "Galardi", "region": "Campania", "appellation": "Roccamonfina IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Serpico", "producer": "Feudi di San Gregorio", "region": "Campania", "appellation": "Irpinia Aglianico", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Radici Taurasi Riserva", "producer": "Mastroberardino", "region": "Campania", "appellation": "Taurasi", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Magma", "producer": "Frank Cornelissen", "region": "Sicily", "appellation": "Terre Siciliane IGT", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Clos Saint-Jacques", "producer": "Armand Rousseau", "region": "Burgundy", "appellation": "Gevrey-Chambertin Premier Cru", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Dom Ruinart Blanc de Blancs", "producer": "Ruinart", "region": "Champagne", "appellation": "Champagne", "type": "Sparkling", "format": "Bottle (750ml)"},
    {"name": "Pol Roger Cuvee Sir Winston Churchill", "producer": "Pol Roger", "region": "Champagne", "appellation": "Champagne", "type": "Sparkling", "format": "Bottle (750ml)"},
    {"name": "Veuve Clicquot La Grande Dame", "producer": "Veuve Clicquot", "region": "Champagne", "appellation": "Champagne", "type": "Sparkling", "format": "Bottle (750ml)"},
    {"name": "Jacques Selosse Initial", "producer": "Jacques Selosse", "region": "Champagne", "appellation": "Champagne", "type": "Sparkling", "format": "Bottle (750ml)"},
    {"name": "Egly-Ouriet Grand Cru Brut", "producer": "Egly-Ouriet", "region": "Champagne", "appellation": "Champagne", "type": "Sparkling", "format": "Bottle (750ml)"},
    {"name": "Chapoutier Ermitage Le Pavillon", "producer": "M. Chapoutier", "region": "Rhone", "appellation": "Hermitage", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chave Hermitage", "producer": "Jean-Louis Chave", "region": "Rhone", "appellation": "Hermitage", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Cornas Reynard", "producer": "Thierry Allemand", "region": "Rhone", "appellation": "Cornas", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateauneuf-du-Pape Reserve des Celestins", "producer": "Henri Bonneau", "region": "Rhone", "appellation": "Chateauneuf-du-Pape", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Chateauneuf-du-Pape Chateau Rayas", "producer": "Chateau Rayas", "region": "Rhone", "appellation": "Chateauneuf-du-Pape", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Bond Estates Vecina", "producer": "Bond Estates", "region": "Napa Valley", "appellation": "Napa Valley", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Bond Estates Melbury", "producer": "Bond Estates", "region": "Napa Valley", "appellation": "Napa Valley", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Bond Estates Pluribus", "producer": "Bond Estates", "region": "Napa Valley", "appellation": "Napa Valley", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Promontory", "producer": "Promontory", "region": "Napa Valley", "appellation": "Napa Valley", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Continuum", "producer": "Continuum Estate", "region": "Napa Valley", "appellation": "Sage Mountain", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Ridge Monte Bello", "producer": "Ridge Vineyards", "region": "Santa Cruz Mountains", "appellation": "Santa Cruz Mountains", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Sine Qua Non Syrah", "producer": "Sine Qua Non", "region": "California", "appellation": "California", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Sine Qua Non Grenache", "producer": "Sine Qua Non", "region": "California", "appellation": "California", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Torbreck RunRig", "producer": "Torbreck", "region": "Barossa Valley", "appellation": "Barossa Valley", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Henschke Hill of Grace", "producer": "Henschke", "region": "Eden Valley", "appellation": "Eden Valley", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Leeuwin Estate Art Series Chardonnay", "producer": "Leeuwin Estate", "region": "Margaret River", "appellation": "Margaret River", "type": "White", "format": "Bottle (750ml)"},
    {"name": "R. Lopez de Heredia Vina Tondonia Reserva", "producer": "R. Lopez de Heredia", "region": "Rioja", "appellation": "Rioja", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "La Rioja Alta Gran Reserva 890", "producer": "La Rioja Alta", "region": "Rioja", "appellation": "Rioja", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Artadi Vina El Pison", "producer": "Artadi", "region": "Rioja", "appellation": "Rioja", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Teso La Monja", "producer": "Bodega Teso La Monja", "region": "Toro", "appellation": "Toro", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Clos Erasmus", "producer": "Clos i Terrasses", "region": "Priorat", "appellation": "Priorat", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "L'Ermita", "producer": "Alvaro Palacios", "region": "Priorat", "appellation": "Priorat", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Egon Muller Scharzhofberger Riesling Auslese", "producer": "Egon Muller", "region": "Mosel", "appellation": "Scharzhofberger", "type": "White", "format": "Bottle (750ml)"},
    {"name": "Donnhoff Niederhauser Hermannshohle Riesling Grosses Gewachs", "producer": "Donnhoff", "region": "Nahe", "appellation": "Niederhauser Hermannshohle", "type": "White", "format": "Bottle (750ml)"},
    {"name": "JJ Prum Wehlener Sonnenuhr Riesling Auslese", "producer": "Joh. Jos. Prum", "region": "Mosel", "appellation": "Wehlener Sonnenuhr", "type": "White", "format": "Bottle (750ml)"},
    {"name": "Vina Cobos Cobos Malbec", "producer": "Vina Cobos", "region": "Mendoza", "appellation": "Mendoza", "type": "Red", "format": "Bottle (750ml)"},
    {"name": "Seña", "producer": "Seña", "region": "Aconcagua Valley", "appellation": "Aconcagua Valley", "type": "Red", "format": "Bottle (750ml)"},
]


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
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        ensure_column(conn, "wines", "owner_share_pct", "REAL NOT NULL DEFAULT 100")
        ensure_column(conn, "wines", "owners_json", "TEXT NOT NULL DEFAULT '[]'")
        ensure_column(conn, "wines", "current_value", "REAL")
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
    current_version = conn.execute("SELECT COALESCE(MAX(catalog_version), 0) FROM wine_catalog").fetchone()[0]
    if current_version >= CATALOG_VERSION:
        return
    conn.execute("DELETE FROM wine_catalog")
    conn.executemany(
        """
        INSERT INTO wine_catalog (name, producer, region, appellation, type, format, catalog_version)
        VALUES (:name, :producer, :region, :appellation, :type, :format, :catalog_version)
        """,
        [{**wine, "catalog_version": CATALOG_VERSION} for wine in CATALOG_WINES],
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


def list_wines() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, name, producer, vintage, quantity, format, type, region, appellation,
                   price, current_value, currency, merchant, order_date, expected_delivery, status,
                   owner_share_pct, owners_json
            FROM wines
            ORDER BY expected_delivery DESC, name ASC
            """
        ).fetchall()
        wines = [wine_from_row(row) for row in rows]
        attach_scores(conn, wines)
    return wines


def list_sales(wine_id: str) -> list[dict]:
    with connect() as conn:
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


def get_summary() -> dict:
    wines = list_wines()
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
    shared_regions: dict[str, int] = {}
    gross_regions: dict[str, int] = {}
    for wine in wines:
        region = wine["region"] or "Unspecified"
        regions[region] = regions.get(region, 0) + personal_quantity(wine)
        gross_regions[region] = gross_regions.get(region, 0) + int(wine["quantity"] or 0)
    for wine in shared_wines:
        region = wine["region"] or "Unspecified"
        shared_regions[region] = shared_regions.get(region, 0) + int(wine["quantity"] or 0)

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
        "shared_regions": [
            {"region": region, "bottles": bottles}
            for region, bottles in sorted(shared_regions.items(), key=lambda item: item[1], reverse=True)[:5]
        ],
        "gross_regions": [
            {"region": region, "bottles": bottles}
            for region, bottles in sorted(gross_regions.items(), key=lambda item: item[1], reverse=True)[:5]
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
               owner_share_pct, owners_json
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
            owner_share_pct, owners_json
        )
        VALUES (
            :id, :name, :producer, :vintage, :quantity, :format, :type, :region, :appellation,
            :price, :current_value, :currency, :merchant, :order_date, :expected_delivery, :status,
            :owner_share_pct, :owners_json
        )
        """,
        data,
    )
    replace_wine_scores(conn, data["id"], scores)
    data["scores"] = scores
    return data


def upsert_wine(payload: dict, wine_id: str | None = None) -> dict:
    data = clean_wine(payload, wine_id)
    scores = data.pop("scores", [])
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO wines (
                id, name, producer, vintage, quantity, format, type, region, appellation,
                price, current_value, currency, merchant, order_date, expected_delivery, status,
                owner_share_pct, owners_json
            )
            VALUES (
                :id, :name, :producer, :vintage, :quantity, :format, :type, :region, :appellation,
                :price, :current_value, :currency, :merchant, :order_date, :expected_delivery, :status,
                :owner_share_pct, :owners_json
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


def replace_all_wines(wines: list[dict]) -> list[dict]:
    cleaned = [clean_wine(wine) for wine in wines]
    with connect() as conn:
        conn.execute("DELETE FROM wines")
        for wine in cleaned:
            insert_wine(conn, wine)
    return list_wines()


class CellarHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/wines":
            self.send_json(list_wines())
            return
        if path == "/api/wine-catalog":
            self.send_json(list_catalog_wines())
            return
        if path == "/api/export":
            self.send_json(list_wines())
            return
        if path == "/api/rates":
            try:
                self.send_json(get_rates(force_refresh=True))
            except ValueError as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_GATEWAY)
            return
        if path.startswith("/api/wines/") and path.endswith("/sales"):
            wine_id = unquote(path.removeprefix("/api/wines/").removesuffix("/sales"))
            self.send_json(list_sales(wine_id))
            return
        if path == "/api/summary":
            try:
                self.send_json(get_summary())
            except ValueError as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_GATEWAY)
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
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
                if not isinstance(payload, list):
                    raise ValueError("Import payload must be a list")
                self.send_json(replace_all_wines(payload))
                return
            self.send_error(HTTPStatus.NOT_FOUND)
        except ValueError as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def do_PUT(self) -> None:
        path = urlparse(self.path).path
        if not path.startswith("/api/wines/"):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        wine_id = unquote(path.removeprefix("/api/wines/"))
        try:
            self.send_json(upsert_wine(self.read_json(), wine_id))
        except ValueError as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path
        if not path.startswith("/api/wines/"):
            self.send_error(HTTPStatus.NOT_FOUND)
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


if __name__ == "__main__":
    parser = ArgumentParser(description="Run the Wine Cellar web app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=4173, type=int)
    args = parser.parse_args()

    init_db()
    server = ThreadingHTTPServer((args.host, args.port), CellarHandler)
    print(f"Wine Cellar running at http://{args.host}:{args.port}/")
    server.serve_forever()
