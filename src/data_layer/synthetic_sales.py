"""
Génération de l'historique de ventes synthétique.

Objectif : simuler des ventes réalistes par produit sur les 30 derniers
jours, avec une saisonnalité simple (effet weekend). Ces données serviront
de base à synthetic_inventory.py pour calculer une vitesse d'écoulement
par produit (utile pour l'agent anti-gaspillage en Phase 3).

Transparence : ces données sont 100% synthétiques, aucune vente réelle.
"""

import json
import random
from datetime import date, timedelta
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)

INPUT_PATH = "data/raw/catalog_clean.json"
OUTPUT_PATH = "data/synthetic/sales_history.json"

DAYS_OF_HISTORY = 30

BASE_DAILY_SALES = {
    "Dairies": 8,
    "Beverages": 12,
    "Snacks": 6,
}
DEFAULT_BASE_SALES = 5

WEEKEND_MULTIPLIER = 1.3
NOISE_RANGE = 0.3


def generate_sales_for_product(product_code: str, category: str) -> list[dict]:
    """Génère l'historique de ventes d'un produit sur DAYS_OF_HISTORY jours."""

    base_sales = BASE_DAILY_SALES.get(category, DEFAULT_BASE_SALES)

    history = []
    today = date.today()

    for days_ago in range(DAYS_OF_HISTORY):
        day = today - timedelta(days=days_ago)
        is_weekend = day.weekday() >= 5
        multiplier = WEEKEND_MULTIPLIER if is_weekend else 1.0
        noise = 1 + random.uniform(-NOISE_RANGE, NOISE_RANGE)
        quantity_sold = max(0, round(base_sales * multiplier * noise))

        history.append({
            "product_code": product_code,
            "date": day.isoformat(),
            "quantity_sold": quantity_sold,
        })

    return history


def generate_all_sales(catalog_path: str = INPUT_PATH) -> list[dict]:
    """Génère l'historique de ventes pour tous les produits du catalogue propre."""

    with open(catalog_path, encoding="utf-8") as f:
        catalog = json.load(f)

    all_sales = []
    for product in catalog:
        code = product["code"]
        category = product["category"]
        product_sales = generate_sales_for_product(code, category)
        all_sales.extend(product_sales)

    logger.info(
        "Historique de ventes généré : %d lignes pour %d produits",
        len(all_sales), len(catalog),
    )
    return all_sales


def save_sales_history(sales: list[dict], output_path: str = OUTPUT_PATH) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(sales, f, ensure_ascii=False, indent=2)

    logger.info("Historique de ventes sauvegardé : %s (%d lignes)", path, len(sales))


if __name__ == "__main__":
    sales = generate_all_sales()
    save_sales_history(sales)