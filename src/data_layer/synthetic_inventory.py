"""
Génération synthétique du stock et des dates de péremption (DLC).

Objectif : pour chaque produit du catalogue, calculer un stock cohérent
avec sa vitesse de vente réelle (sales_history.json), et lui assigner une
date de péremption — avec un sous-ensemble volontairement proche de la
péremption, pour donner de vrais cas à traiter à l'agent anti-gaspillage.

Transparence : données 100% synthétiques.
"""

import json
import random
from datetime import date, timedelta
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)

CATALOG_PATH = "data/raw/catalog_clean.json"
SALES_PATH = "data/synthetic/sales_history.json"
OUTPUT_PATH = "data/synthetic/inventory.json"

DAYS_OF_STOCK_COVERAGE = 10
PROPORTION_NEAR_EXPIRY = 0.15
NEAR_EXPIRY_DAYS_RANGE = (1, 3)
NORMAL_EXPIRY_DAYS_RANGE = (15, 60)

def get_average_daily_sales(product_code: str, sales_history: list[dict]) -> float:
    """Calcule la vente moyenne par jour d'un produit, à partir de son historique."""

    product_sales = [
        row["quantity_sold"]
        for row in sales_history
        if row["product_code"] == product_code
    ]
    # ↑ "list comprehension" : on parcourt sales_history, et pour chaque ligne
    #   qui correspond à CE produit précis, on garde juste le nombre vendu

    if not product_sales:
        return 0.0
    # ↑ sécurité : si jamais aucun historique n'existe pour ce produit
    #   (ne devrait pas arriver, mais on ne veut jamais planter)

    return sum(product_sales) / len(product_sales)
    # ↑ la moyenne = somme de toutes les ventes / nombre de jours


def generate_inventory_for_product(product_code: str, avg_daily_sales: float) -> dict:
    """Calcule le stock et la date de péremption d'un produit."""

    stock_quantity = max(1, round(avg_daily_sales * DAYS_OF_STOCK_COVERAGE))
    # ↑ le stock = vitesse de vente x nombre de jours qu'on veut couvrir
    #   max(1, ...) : jamais un stock de 0, même pour un produit qui se vend très peu

    is_near_expiry = random.random() < PROPORTION_NEAR_EXPIRY
    # ↑ random.random() donne un nombre entre 0 et 1. Si ce nombre tombe
    #   sous 0.15, ce produit fait partie des 15% "proches de la péremption"
    #   C'est comme tirer à pile ou face, mais avec 15% de chances côté pile

    if is_near_expiry:
        days_until_expiry = random.randint(*NEAR_EXPIRY_DAYS_RANGE)
        # ↑ randint(1, 3) → un nombre entier au hasard entre 1 et 3 inclus
    else:
        days_until_expiry = random.randint(*NORMAL_EXPIRY_DAYS_RANGE)

    expiry_date = date.today() + timedelta(days=days_until_expiry)

    return {
        "product_code": product_code,
        "stock_quantity": stock_quantity,
        "avg_daily_sales": round(avg_daily_sales, 1),
        "expiry_date": expiry_date.isoformat(),
        "days_until_expiry": days_until_expiry,
    }    
def generate_all_inventory(
    catalog_path: str = CATALOG_PATH,
    sales_path: str = SALES_PATH,
) -> list[dict]:
    """Génère l'inventaire (stock + DLC) pour tous les produits du catalogue."""

    with open(catalog_path, encoding="utf-8") as f:
        catalog = json.load(f)

    with open(sales_path, encoding="utf-8") as f:
        sales_history = json.load(f)
    # ↑ on charge les DEUX fichiers dont on a besoin : le catalogue ET les ventes

    inventory = []
    for product in catalog:
        code = product["code"]

        avg_sales = get_average_daily_sales(code, sales_history)
        # ↑ étape 1 : on calcule la vitesse de vente de CE produit
        #   (la fonction qu'on a écrite en premier)

        entry = generate_inventory_for_product(code, avg_sales)
        # ↑ étape 2 : on en déduit son stock et sa DLC
        #   (la fonction qu'on vient d'écrire juste avant)

        inventory.append(entry)

    near_expiry_count = sum(1 for e in inventory if e["days_until_expiry"] <= 3)
    # ↑ juste pour le log : on compte combien de produits sont vraiment
    #   proches de la péremption, pour vérifier que ça correspond à peu
    #   près à 15% de 114 (donc environ 17)

    logger.info(
        "Inventaire généré : %d produits (%d proches de la péremption)",
        len(inventory), near_expiry_count,
    )
    return inventory


def save_inventory(inventory: list[dict], output_path: str = OUTPUT_PATH) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(inventory, f, ensure_ascii=False, indent=2)

    logger.info("Inventaire sauvegardé : %s (%d produits)", path, len(inventory))

if __name__ == "__main__":
    inventory = generate_all_inventory()
    save_inventory(inventory)