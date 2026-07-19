import json
import time
import requests # librairie EXTERNE (installée via pip) — sert à appeler des API/sites web


from src.utils.logger import get_logger  # notre fonction logger centralisée, créée dans src/utils/logger.py

logger = get_logger(__name__)  # crée un logger propre à CE fichier précis
BASE_URL = "https://world.openfoodfacts.org/api/v2/search"  # l'adresse de base de l'API qu'on va interroger

HEADERS = {
    "User-Agent": "RetailAgenticCopilot/0.1"
    # Open Food Facts demande de s'identifier dans chaque requête, sinon ils peuvent bloquer nos appels
}

FIELDS = "code,product_name,brands,categories_tags_en,quantity,image_url,ingredients_text,allergens"# on ne demande QUE ces champs à l'API — pas tout le produit (qui a 50+ champs inutiles pour nous)

CATEGORIES = [
    "Dairies", "Beverages", "Snacks",
    "Cereals-and-potatoes", "Canned-foods", "Breakfasts",
    "Condiments", "Frozen-foods", "Meats", "Fruits", "Vegetables",
]# les catégories de produits qu'on veut récupérer —

PAGE_SIZE = 100       # combien de produits on demande par catégorie en un seul appel API
MAX_RETRIES = 3        # nombre max de tentatives si l'API ne répond pas correctement
SECONDS_BETWEEN_CALLS = 9  # pause entre deux catégories, pour respecter la limite de requêtes/minute
def fetch_category(category: str, page_size: int = PAGE_SIZE) -> list[dict]:
    """Récupère une page de produits pour une catégorie donnée, avec retry."""

    params = {
        "categories_tags_en": category,
        "fields": FIELDS,
        "page_size": page_size,
    }

    for attempt in range(1, MAX_RETRIES + 1):
        # ↑ boucle qui va essayer jusqu'à MAX_RETRIES fois (donc 3 fois, vu notre constante)

        response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=15)

        if response.status_code == 503:
            # ↑ 503 = "serveur occupé, trop de requêtes" (le bug qu'on a vu en vrai)
            wait = 2 ** attempt * 5
            # ↑ backoff exponentiel : tentative 1 → 10s, tentative 2 → 20s, tentative 3 → 40s
            logger.warning(
                "503 reçu pour '%s' — retry dans %ss (%s/%s)",
                category, wait, attempt, MAX_RETRIES,
            )
            time.sleep(wait)
            continue
            # ↑ "continue" = on retourne au début de la boucle "for", donc on retente

        data = response.json()
        products = data.get("products", [])
        logger.info("Catégorie '%s' : %d produits récupérés", category, len(products))
        return products
        # ↑ si on arrive ici, ça a marché : on sort de la fonction avec le résultat

    logger.error("Échec définitif pour '%s' après %s tentatives", category, MAX_RETRIES)
    return []
    # ↑ si on a épuisé les 3 tentatives sans succès, on renvoie une liste vide
    #   plutôt que de faire planter tout le script


def build_catalog(categories: list[str] = CATEGORIES) -> list[dict]:
    """Construit le catalogue complet en itérant sur les catégories."""

    catalog: list[dict] = []
    # ↑ liste vide au départ, qui va accueillir TOUS les produits de TOUTES les catégories

    seen_codes: set[str] = set()
    # ↑ un "set" (ensemble) qui va mémoriser les codes-barres déjà vus,
    #   pour ne pas ajouter deux fois le même produit

    for i, category in enumerate(categories):
        # ↑ enumerate() donne à la fois l'index (i = 0, 1, 2...) ET la valeur (category)
        #   utile ici pour savoir si on est à la dernière catégorie (voir plus bas)

        products = fetch_category(category)
        # on appelle la fonction qu'on vient de finir, pour CETTE catégorie précise

        for product in products:
            code = product.get("code")
            if code and code not in seen_codes:
                # ↑ on ajoute seulement si le produit a un code ET n qu'one l'a pas déjà vu
                product["_source_category"] = category
                # ↑ on note d'où vient ce produit, utile pour du debug plus tard
                catalog.append(product)
                seen_codes.add(code)
                # ↑ on marque ce code comme "déjà vu"

        if i < len(categories) - 1:
            # ↑ si on n'est PAS à la dernière catégorie de la liste...
            time.sleep(SECONDS_BETWEEN_CALLS)
            # ↑ ...on attend avant de passer à la suivante (respect du rate-limit)
            # Pas besoin d'attendre après la DERNIÈRE catégorie, il n'y a rien après

    return catalog


def save_raw_catalog(catalog: list[dict], output_path: str = "data/raw/catalog_raw.json") -> None:
    """Sauvegarde le catalogue brut dans un fichier JSON."""
    from pathlib import Path

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # ↑ crée le dossier data/raw/ s'il n'existe pas déjà (exist_ok=True = pas d'erreur s'il existe)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
        # ↑ écrit le catalogue en JSON dans le fichier
        #   ensure_ascii=False = garde les accents lisibles (é, à...) plutôt que \u00e9
        #   indent=2 = formatage lisible, pas tout sur une seule ligne

    logger.info("Catalogue sauvegardé : %s (%d produits)", path, len(catalog))




if __name__ == "__main__":
    catalog = build_catalog()
    save_raw_catalog(catalog)