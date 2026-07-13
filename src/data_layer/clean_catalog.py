"""
Nettoyage du catalogue brut Open Food Facts.

Règles de nettoyage (basées sur les vrais problèmes qu'on a observés dans
data/raw/catalog_raw.json) :
1. Retirer les produits sans nom (product_name vide)
2. Détecter et retirer les ingredients_text corrompus (texte OCR cassé)
3. Valeur par défaut pour quantity manquante
4. Valider chaque produit nettoyé avec Pydantic avant de le garder
"""

import json
import re
from pathlib import Path

from pydantic import BaseModel, ValidationError

from src.utils.logger import get_logger

logger = get_logger(__name__)

INPUT_PATH = "data/raw/catalog_raw.json"
OUTPUT_PATH = "data/raw/catalog_clean.json"

# Seuil de détection de texte corrompu : un texte d'ingrédients normal est
# presque entièrement composé de lettres. En dessous de ce ratio (60% de
# lettres), on considère que le texte est probablement du bruit OCR.
MIN_LETTER_RATIO = 0.6


class CleanProduct(BaseModel):
    """Forme exacte qu'un produit doit avoir après nettoyage."""
    code: str
    product_name: str
    brand: str
    category: str
    quantity: str
    ingredients_text: str
    allergens: str


def load_raw_catalog(path: str = INPUT_PATH) -> list[dict]:
    """Charge le catalogue brut depuis le fichier JSON."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def is_ingredients_text_valid(text: str) -> bool:
    """Détecte un texte d'ingrédients corrompu (OCR cassé, ex: 'OBD1 999 999...').

    On calcule le ratio lettres / caractères totaux (hors espaces). Un texte
    normal a un ratio élevé ; un texte corrompu, plein de chiffres et de
    symboles, a un ratio bas.
    """
    if not text:
        return False  # texte vide = invalide, mais géré séparément (voir clean_product)

    letters = re.sub(r"[^a-zA-ZÀ-ÿ]", "", text)  # garde uniquement les lettres (accents inclus)
    no_space = text.replace(" ", "")
    if not no_space:
        return False

    ratio = len(letters) / len(no_space)
    return ratio >= MIN_LETTER_RATIO


def clean_product(raw: dict) -> CleanProduct | None:
    """Nettoie un produit brut. Retourne None si le produit doit être rejeté."""

    name = (raw.get("product_name") or "").strip()
    if not name:
        return None  # règle 1 : pas de nom = rejeté

    ingredients = (raw.get("ingredients_text") or "").strip()
    if ingredients and not is_ingredients_text_valid(ingredients):
        ingredients = ""  # règle 2 : texte corrompu → on le vide plutôt que rejeter tout le produit

    quantity = (raw.get("quantity") or "").strip()
    if not quantity:
        quantity = "non renseigné"  # règle 3 : valeur par défaut

    try:
        return CleanProduct(
            code=raw.get("code", ""),
            product_name=name,
            brand=(raw.get("brands") or "non renseigné").strip(),
            category=raw.get("_source_category", "non renseigné"),
            quantity=quantity,
            ingredients_text=ingredients or "non renseigné",
            allergens=(raw.get("allergens") or "non renseigné").strip() or "non renseigné",
        )
    except ValidationError as exc:
        # si malgré tout un produit ne respecte pas le modèle, on le logue et on le rejette
        logger.warning("Produit rejeté par Pydantic (code=%s) : %s", raw.get("code"), exc)
        return None


def clean_catalog(raw_catalog: list[dict]) -> list[CleanProduct]:
    """Applique le nettoyage à tout le catalogue."""
    cleaned = []
    rejected = 0

    for raw in raw_catalog:
        product = clean_product(raw)
        if product is not None:
            cleaned.append(product)
        else:
            rejected += 1

    logger.info(
        "Nettoyage terminé : %d produits gardés, %d rejetés (sur %d)",
        len(cleaned), rejected, len(raw_catalog),
    )
    return cleaned


def save_clean_catalog(products: list[CleanProduct], output_path: str = OUTPUT_PATH) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = [p.model_dump() for p in products]
    # ↑ model_dump() convertit un objet Pydantic en dictionnaire normal, pour pouvoir le sauvegarder en JSON

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info("Catalogue propre sauvegardé : %s (%d produits)", path, len(products))


if __name__ == "__main__":
    raw = load_raw_catalog()
    clean = clean_catalog(raw)
    save_clean_catalog(clean)