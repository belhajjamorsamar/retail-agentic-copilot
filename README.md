# retail-agentic-copilot

Système multi-agents (LangGraph) pour la grande distribution : agent service
client basé sur RAG et agent de tarification anti-gaspillage, orchestrés par
un agent superviseur. Projet d'apprentissage agentic AI appliqué au retail,
avec données Open Food Facts et données synthétiques réalistes.

## Contexte et problème métier

Les supermarchés (contexte tunisien : Aziza, Monoprix, Carrefour, MG) font
face à trois problèmes récurrents :

1. Rupture de stock et surstock simultanés par mauvaise anticipation de la demande
2. Gaspillage alimentaire sur les produits proches de la date de péremption (DLC)
3. Service client fragmenté (disponibilité, prix, information produit)

Ce projet répond aux problèmes 2 et 3 avec un système multi-agents réel :
un agent service client (RAG) et un agent anti-gaspillage (pricing
dynamique), orchestrés par un agent superviseur (LangGraph).

## Stack technique

- Orchestration agentique : LangGraph
- LLM : OpenAI GPT-4o-mini
- Vector store : ChromaDB
- Embeddings : text-embedding-3-small
- Validation de données : Pydantic

## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows : venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # puis renseigner OPENAI_API_KEY
```

---

## Phase 1 — Préparation des données ✅

Avant de construire les agents, il faut la matière première : un catalogue
produit réel et des données de contexte magasin (stock, dates de
péremption, historique de ventes). Cette phase est purement de
l'ingénierie de données — aucun LLM n'intervient ici.

### Vue d'ensemble du pipeline

```
1. fetch_catalog.py       → extraction catalogue brut (Open Food Facts API)
2. clean_catalog.py        → nettoyage + validation (Pydantic)
3. synthetic_sales.py       → génération de l'historique de ventes
4. synthetic_inventory.py    → génération du stock et des DLC
```

Chaque script produit un fichier qui sert d'entrée au suivant. Aucun script
ne dépend d'une clé API OpenAI — la Phase 1 fonctionne intégralement sans
coût d'API LLM.

### 1. `fetch_catalog.py` — extraction du catalogue produit

Interroge l'API publique [Open Food Facts](https://world.openfoodfacts.org)
(licence ouverte ODbL) pour récupérer des produits réels par catégorie
(`Dairies`, `Beverages`, `Snacks`).

**Décisions techniques :**
- API v2 structurée (`/api/v2/search`), pas l'ancien endpoint legacy
- Champs limités via `fields=` pour ne récupérer que l'utile (nom, marque,
  catégorie, ingrédients, allergènes) plutôt que l'objet produit complet
- Gestion des erreurs 503 (rate-limit) avec retry et backoff exponentiel
- Déduplication par code-barres (un produit peut apparaître dans plusieurs
  catégories)

**Résultat :** `data/raw/catalog_raw.json` — 117 produits bruts récupérés,
incluant de vrais produits tunisiens identifiables par leur préfixe de
code-barres (`611`), par exemple des marques comme Jaouda ou Sidi Ali.

```bash
python -m src.data_layer.fetch_catalog
```

### 2. `clean_catalog.py` — nettoyage et validation

Les données brutes d'une base communautaire ont des défauts réels observés
concrètement sur ce catalogue : produits sans nom, texte d'ingrédients
corrompu (artefacts OCR), champs manquants.

**Règles de nettoyage appliquées :**
- Rejet des produits sans nom (`product_name` vide)
- Détection de texte corrompu par ratio lettres/caractères (seuil 60%)
- Valeurs par défaut explicites (`"non renseigné"`) plutôt que des champs vides
- Validation finale de chaque produit avec un modèle **Pydantic**
  (`CleanProduct`), qui garantit que chaque produit sauvegardé a la bonne
  forme avant d'aller plus loin dans le pipeline

**Résultat :** `data/raw/catalog_clean.json` — 114 produits propres et
validés (3 rejetés sur 117, ~2.5%).

```bash
python -m src.data_layer.clean_catalog
```

### 3. `synthetic_sales.py` — historique de ventes synthétique

Open Food Facts ne fournit aucune donnée de vente. On génère un historique
réaliste sur 30 jours par produit, avec :
- Une vente moyenne de base différente par catégorie
- Un effet weekend (+30% samedi/dimanche)
- Du bruit aléatoire (±30%) pour éviter des courbes artificiellement lisses

**Transparence** : ces données sont 100% synthétiques et documentées comme
telles — aucune vente réelle de supermarché n'est utilisée.

**Résultat :** `data/synthetic/sales_history.json` — 3420 lignes
(114 produits × 30 jours).

```bash
python -m src.data_layer.synthetic_sales
```

### 4. `synthetic_inventory.py` — stock et dates de péremption

Calcule, pour chaque produit, un stock cohérent avec sa vitesse de vente
réelle (issue de `sales_history.json`), et lui assigne une date de
péremption (DLC).

**Décision de conception clé** : 15% des produits reçoivent volontairement
une DLC très proche (1 à 3 jours), les 85% restants une DLC normale
(15 à 60 jours). Sans ce mécanisme, aucun produit ne serait jamais "à
risque" et l'agent anti-gaspillage (Phase 3) n'aurait rien à traiter en
démo — ce sous-ensemble constitue les cas de test volontaires du système.

**Résultat :** `data/synthetic/inventory.json` — 114 produits, avec stock,
vitesse de vente moyenne, DLC et jours restants avant péremption.

```bash
python -m src.data_layer.synthetic_inventory
```

### Comment les 3 fichiers de données se relient

```
catalog_clean.json      →  qui est ce produit ? (nom, marque, ingrédients)
sales_history.json       →  combien il s'est vendu chaque jour (30 lignes/produit)
inventory.json            →  combien il en reste, et quand il expire (1 ligne/produit)
```

Les trois fichiers sont reliés par le champ `code` / `product_code`. Cette
séparation reflète des rythmes de mise à jour différents dans un vrai
système : le catalogue change rarement, les ventes quotidiennement, le
stock en permanence.

### Sources de données — résumé

| Donnée | Source | Statut |
|---|---|---|
| Catalogue produits | Open Food Facts API v2 | Réelle |
| Historique de ventes | Générateur synthétique | Synthétique, documentée |
| Stock & dates de péremption | Générateur synthétique | Synthétique, documentée |

Aucune donnée interne réelle de supermarché n'est utilisée (propriétaire et
non accessible publiquement). Le scraping de sites de distributeurs
tunisiens (ex. mg.tn) a été explicitement écarté après vérification de
leurs conditions d'utilisation, qui interdisent l'exploitation non
autorisée de leur contenu.

---

## Roadmap

- [x] Phase 0 — Cadrage, architecture, scaffolding
- [x] Phase 1 — Couche de données (catalogue + synthétique)
- [ ] Phase 2 — Agent service client (RAG)
- [ ] Phase 3 — Agent anti-gaspillage
- [ ] Phase 4 — Orchestration (LangGraph)
- [ ] Phase 5 — Évaluation et traçabilité
- [ ] Phase 6 — Interface de démo
- [ ] Phase 7 — Documentation finale

## Structure du projet

```
retail-agentic-copilot/
├── data/
│   ├── raw/                      # catalog_raw.json, catalog_clean.json
│   └── synthetic/                 # sales_history.json, inventory.json
├── src/
│   ├── data_layer/                 # scripts de la Phase 1 (ce document)
│   ├── rag/                         # chunking, embeddings, retrieval (Phase 2)
│   ├── agents/                       # agents service client & anti-gaspillage
│   ├── tools/                         # outils exposés aux agents
│   ├── orchestration/                  # superviseur LangGraph
│   └── utils/                           # logger centralisé
├── tests/
└── config.py
```