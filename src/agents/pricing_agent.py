"""
Agent anti-gaspillage.

Lit l'inventaire (stock + DLC), applique une logique de réduction de prix
par paliers selon le nombre de jours avant péremption, avec un garde-fou
humain au-delà d'un seuil (MAX_AUTO_DISCOUNT_PERCENT) — toute réduction
supérieure à ce seuil est signalée pour validation humaine plutôt
qu'appliquée automatiquement.
"""

import json

from src.utils.logger import get_logger
from config import DISCOUNT_TIERS, DEFAULT_DISCOUNT_PERCENT, MAX_AUTO_DISCOUNT_PERCENT

logger = get_logger(__name__)

INVENTORY_PATH = "data/synthetic/inventory.json"
CATALOG_PATH = "data/raw/catalog_clean.json"


def load_inventory(path: str = INVENTORY_PATH) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_catalog_lookup(path: str = CATALOG_PATH) -> dict[str, dict]:
    """Charge le catalogue et le transforme en dictionnaire indexé par code."""
    with open(path, encoding="utf-8") as f:
        catalog = json.load(f)
    return {p["code"]: p for p in catalog}


def compute_discount_percent(days_until_expiry: int) -> int:
    """Détermine le pourcentage de réduction selon les paliers configurés."""

    applicable_tiers = [
        (days, pct) for days, pct in DISCOUNT_TIERS.items()
        if days_until_expiry <= days
    ]

    if not applicable_tiers:
        return DEFAULT_DISCOUNT_PERCENT

    _, best_percent = min(applicable_tiers, key=lambda t: t[0])
    return best_percent


def evaluate_product(inventory_entry: dict, catalog_lookup: dict) -> dict:
    """Évalue un produit et décide de l'action (réduction auto ou validation humaine)."""

    code = inventory_entry["product_code"]
    days = inventory_entry["days_until_expiry"]
    product = catalog_lookup.get(code, {})

    discount_percent = compute_discount_percent(days)
    requires_human_review = discount_percent > MAX_AUTO_DISCOUNT_PERCENT

    decision = {
        "product_code": code,
        "product_name": product.get("product_name", "Produit inconnu"),
        "days_until_expiry": days,
        "stock_quantity": inventory_entry["stock_quantity"],
        "discount_percent": discount_percent,
        "requires_human_review": requires_human_review,
        "status": "pending_review" if requires_human_review else (
            "discount_applied" if discount_percent > 0 else "no_action"
        ),
    }

    if requires_human_review:
        logger.warning(
            "Validation humaine requise : %s (réduction proposée %d%% > seuil %d%%)",
            decision["product_name"], discount_percent, MAX_AUTO_DISCOUNT_PERCENT,
        )
    elif discount_percent > 0:
        logger.info(
            "Réduction appliquée : %s — %d%% (J-%d)",
            decision["product_name"], discount_percent, days,
        )

    return decision


def evaluate_all_products() -> list[dict]:
    """Évalue tout l'inventaire et retourne la liste des décisions."""
    inventory = load_inventory()
    catalog_lookup = load_catalog_lookup()

    decisions = [evaluate_product(entry, catalog_lookup) for entry in inventory]

    applied = sum(1 for d in decisions if d["status"] == "discount_applied")
    pending = sum(1 for d in decisions if d["status"] == "pending_review")
    logger.info(
        "Évaluation terminée : %d produits, %d réductions auto, %d en attente de validation",
        len(decisions), applied, pending,
    )
    return decisions


def get_products_needing_attention() -> list[dict]:
    """Retourne uniquement les produits nécessitant une action."""
    all_decisions = evaluate_all_products()
    return [d for d in all_decisions if d["status"] != "no_action"]


if __name__ == "__main__":
    decisions = get_products_needing_attention()
    print(f"\n{len(decisions)} produits nécessitent une attention :\n")
    for d in decisions:
        marker = "🔴 VALIDATION HUMAINE" if d["requires_human_review"] else "🟡 AUTO"
        print(f"{marker} — {d['product_name']} (J-{d['days_until_expiry']}) → -{d['discount_percent']}%")