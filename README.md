# retail-agentic-copilot

Système multi-agents (LangGraph) pour la grande distribution : agent service
client basé sur RAG et agent de tarification anti-gaspillage, orchestrés par
un agent superviseur, exposés via une API FastAPI et consommés par un
frontend Next.js. Projet d'apprentissage agentic AI appliqué au retail,
100% local et gratuit (embeddings HuggingFace, LLM via Ollama).

## Contexte et problème métier

Les supermarchés (contexte tunisien : Aziza, Monoprix, Carrefour, MG) font
face à trois problèmes récurrents : rupture de stock et surstock simultanés,
gaspillage alimentaire sur les produits proches de la péremption, et service
client fragmenté (disponibilité, prix, information produit).

Ce projet répond aux problèmes 2 et 3 avec un système multi-agents réel,
exposé via une vraie API et une interface web — pas un simple script.

## Architecture

```
Frontend (Next.js)
        │  HTTP
        ▼
API (FastAPI) — /chat, /health
        │
        ▼
Superviseur (LangGraph — à venir)
   │              │
   ▼              ▼
Agent service   Agent anti-gaspillage
client (RAG)    (à venir)
   │              │
   ▼              ▼
Catalogue        Stock + DLC
produits          (synthétique)
```

## Stack technique

- Orchestration agentique : LangGraph (à venir)
- API : FastAPI + Uvicorn
- Frontend : Next.js (TypeScript, App Router, Tailwind CSS)
- LLM : Ollama (llama3.2) — 100% local, gratuit
- Embeddings : sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2) — 100% local
- Vector store : ChromaDB
- Validation de données : Pydantic

**Choix assumé** : le projet utilise exclusivement des modèles locaux et
gratuits (Ollama + HuggingFace) plutôt que des API payantes (OpenAI),
après avoir rencontré des blocages d'accès sur les modèles OpenAI. Ce choix
a un coût en précision (documenté ci-dessous, section Limites connues)
mais élimine toute dépendance à un compte payant.

## Setup

### Backend (Python)

```bash
python -m venv venv
source venv/bin/activate      # Windows : venv\Scripts\activate
pip install -r requirements.txt
```

### Ollama (LLM local)

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2
```

### Frontend (Next.js)

```bash
cd frontend
npm install
```

## Lancer le projet (3 serveurs en parallèle)

```bash
# Terminal 1 — API FastAPI
uvicorn src.api.main:app --port 8000

# Terminal 2 — Frontend Next.js
cd frontend && npm run dev

# Ollama tourne en service de fond après installation (port 11434)
```

Puis ouvrir `http://localhost:3000`.

---

## Phase 1 — Préparation des données ✅

Voir le détail complet des scripts (`fetch_catalog.py`, `clean_catalog.py`,
`synthetic_sales.py`, `synthetic_inventory.py`) : extraction du catalogue
Open Food Facts (114 produits propres), génération de l'historique de
ventes (3420 lignes) et du stock/DLC synthétiques (15% de produits
volontairement proches de la péremption, pour donner de vrais cas de test
à l'agent anti-gaspillage).

## Phase 2 — Agent service client (RAG) ✅

Pipeline complet : `build_documents.py` (catalogue → documents LangChain)
→ `chunking.py` (découpage avec filet de sécurité, `RecursiveCharacterTextSplitter`)
→ `indexing.py` (embeddings locaux + stockage ChromaDB) → `retrieval.py`
(recherche par similarité + MMR) → `customer_service_agent.py` (génération
de réponse avec Ollama, citation systématique des sources).

**Limites connues (documentées honnêtement)** : le modèle d'embedding
local, plus léger qu'un modèle propriétaire comme celui d'OpenAI, montre
des résultats moins précis sur des requêtes très spécifiques (allergènes
précis). Testé et comparé entre `all-MiniLM-L6-v2` (anglais) et
`paraphrase-multilingual-MiniLM-L12-v2` (multilingue) — ce dernier
améliore nettement les résultats sur le catalogue multilingue (français/
arabe/anglais/allemand), sans éliminer complètement la limite. Point à
approfondir en Phase 7 (évaluation).

## Phase 3 — API FastAPI ✅

Expose l'agent service client via une API REST :

- `POST /chat` — reçoit `{"question": "..."}`, retourne `{"answer": "...", "sources": [...]}`
- `GET /health` — vérification de disponibilité du service

Documentation interactive auto-générée disponible sur `http://localhost:8000/docs`.
CORS configuré pour n'autoriser que le frontend (`localhost:3000`).

## Frontend Next.js (en cours)

Interface de chat simple (TypeScript, App Router, Tailwind CSS) qui
consomme l'API `/chat` et affiche la réponse avec les produits sources
cités, sous forme de tags.

---

## Roadmap mise à jour

- [x] Phase 0 — Cadrage, architecture, scaffolding
- [x] Phase 1 — Couche de données
- [x] Phase 2 — Agent service client (RAG)
- [x] Phase 3 — API FastAPI
- [ ] Phase 4 — Agent anti-gaspillage
- [ ] Phase 5 — Orchestration multi-agents (LangGraph)
- [ ] Phase 6 — Frontend Next.js (finalisation)
- [ ] Phase 7 — Évaluation et traçabilité
- [ ] Phase 8 — Documentation finale et préparation entretien

## Structure du projet

```
retail-agentic-copilot/
├── data/
│   ├── raw/                      # catalog_raw.json, catalog_clean.json
│   └── synthetic/                 # sales_history.json, inventory.json
├── src/
│   ├── data_layer/                 # scripts de la Phase 1
│   ├── rag/                         # chunking, embeddings, retrieval (Phase 2)
│   ├── agents/                       # customer_service_agent.py
│   ├── api/                           # FastAPI : main.py, routes.py, schemas.py
│   ├── tools/                          # outils exposés aux agents (à venir)
│   ├── orchestration/                   # superviseur LangGraph (à venir)
│   └── utils/                            # logger centralisé
├── frontend/                          # Next.js (TypeScript, App Router)
├── chroma_db/                          # index vectoriel (généré, gitignored)
├── tests/
└── config.py
```

## Sources de données

| Donnée | Source | Statut |
|---|---|---|
| Catalogue produits | Open Food Facts API v2 | Réelle |
| Historique de ventes | Générateur synthétique | Synthétique, documentée |
| Stock & dates de péremption | Générateur synthétique | Synthétique, documentée |

Aucune donnée interne réelle de supermarché n'est utilisée. Le scraping de
sites de distributeurs tunisiens (ex. mg.tn) a été explicitement écarté
après vérification de leurs conditions d'utilisation.