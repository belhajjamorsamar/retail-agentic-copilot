# retail-agentic-copilot

Système multi-agents (LangGraph) pour la grande distribution : agent
service client basé sur RAG et agent de tarification anti-gaspillage,
orchestrés par un agent superviseur, exposés via une API FastAPI et
consommés par un frontend Next.js avec historique de conversations.

## Contexte et problème métier

Les supermarchés (contexte tunisien : Aziza, Monoprix, Carrefour, MG) font
face à trois problèmes récurrents : rupture de stock et surstock
simultanés, gaspillage alimentaire sur les produits proches de la
péremption, et service client fragmenté (disponibilité, prix, allergènes).

Ce projet répond aux problèmes 2 et 3 avec un système multi-agents réel,
exposé via une vraie API et une interface web complète.

## Architecture

```
Frontend (Next.js) — historique, dark/light mode
        │  HTTP
        ▼
API (FastAPI) — /chat, /health
        │
        ▼
Superviseur (LangGraph) — route dynamiquement
   │              │
   ▼              ▼
Agent service   Agent anti-gaspillage
client (RAG)    (règles + guardrail humain)
   │              │
   ▼              ▼
Catalogue        Stock + DLC
893 produits      (synthétique)
```

## Stack technique

- Orchestration agentique : **LangGraph**
- API : **FastAPI** + Uvicorn
- Frontend : **Next.js** (TypeScript, App Router, Tailwind CSS, composants séparés)
- LLM : **Ollama (llama3.2)** en local par défaut, **Groq (llama-3.3-70b-versatile)** en option cloud pour la vitesse — interchangeable via `config.py`
- Embeddings : **sentence-transformers** (paraphrase-multilingual-MiniLM-L12-v2) — 100% local, choisi pour son support multilingue (FR/AR/EN/DE)
- Vector store : **ChromaDB**
- Validation de données : **Pydantic**

### Choix LLM — Ollama vs Groq

Le projet supporte deux fournisseurs LLM, choisis via `LLM_PROVIDER` dans
`config.py`, sans changer le reste du code (centralisé dans `src/utils/llm.py`) :

| | Ollama (local) | Groq (cloud) |
|---|---|---|
| Coût | Gratuit | Gratuit (tier limité) |
| Vitesse | Lente sur CPU | Très rapide (matériel LPU dédié) |
| Dépendance réseau | Aucune | Connexion Internet requise |
| Confidentialité | Totale (rien ne sort de la machine) | Données envoyées à Groq |

Ollama reste la valeur par défaut — Groq est une option de performance,
pas un remplacement définitif.

## Setup

### Backend (Python)

```bash
python -m venv venv
source venv/bin/activate      # Windows : venv\Scripts\activate
pip install -r requirements.txt
```

### Ollama (LLM local, par défaut)

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2
```

### Groq (optionnel, pour la vitesse)

1. Créer une clé gratuite sur https://console.groq.com/keys
2. Ajouter `GROQ_API_KEY=...` dans `.env`
3. Mettre `LLM_PROVIDER = "groq"` dans `config.py`

### Frontend (Next.js)

```bash
cd frontend
npm install
```

## Lancer le projet

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

Catalogue élargi à **893 produits** (11 catégories : Dairies, Beverages,
Snacks, Cereals-and-potatoes, Canned-foods, Breakfasts, Condiments,
Frozen-foods, Meats, Fruits, Vegetables), extraits via l'API Open Food
Facts (`fetch_catalog.py`), nettoyés et validés par Pydantic
(`clean_catalog.py`). Historique de ventes synthétique (26 790 lignes,
`synthetic_sales.py`) et stock/DLC synthétique (893 produits, 156 proches
de la péremption, `synthetic_inventory.py`).

## Phase 2 — Agent service client (RAG) ✅

Pipeline complet : `build_documents.py` → `chunking.py` → `indexing.py`
(910 chunks indexés) → `retrieval.py`. Le retrieval combine **recherche
sémantique** (embeddings + MMR) et **recherche par mot-clé avec expansion
de synonymes multilingues** (ex : "cacahuètes" → "peanut", "arachide") —
corrige une limite observée où la recherche sémantique seule ratait des
termes précis (allergènes).

## Phase 3 — API FastAPI ✅

`POST /chat` expose le superviseur complet (pas juste le RAG seul) —
`GET /health` pour la supervision. CORS configuré pour le frontend.

## Phase 4 — Agent anti-gaspillage ✅

`pricing_agent.py` (calcul déterministe par paliers de réduction, avec
guardrail humain au-delà de 30%) et `pricing_agent_tool.py` (version
agentique). **Décision d'architecture notée** : le tool calling natif
(`bind_tools`) s'est montré peu fiable avec un petit modèle local
(déclenchait l'outil même sur des questions sans rapport) — remplacé par
une classification explicite en 2 étapes, plus robuste.

## Phase 5 — Orchestration (LangGraph) ✅

`supervisor.py` — un vrai `StateGraph` LangGraph, pas un enchaînement de
`if/else` : classification de l'intention, routage conditionnel vers un
ou les deux agents en parallèle, fusion des réponses. Garde-fou
anti-boucle-infinie natif (`recursion_limit`).

## Frontend Next.js ✅

- Historique de conversations multiples, persistant (`localStorage`)
- Renommage de conversation (double-clic ou icône crayon)
- Dark / light mode avec détection de préférence système
- Architecture en composants séparés (`Sidebar`, `ChatHeader`,
  `MessageBubble`, `LoadingBubble`, `ChatInput`, `EmptyState`)
- Indicateur de progression pendant le traitement (les appels LLM enchaînés
  peuvent prendre 1 à 3 minutes en mode Ollama local)

---

## Limites connues (documentées honnêtement)

- **Vitesse** : en mode Ollama (CPU, sans GPU), une question qui active les
  deux agents peut prendre 1 à 3 minutes. Le mode Groq résout ce problème
  au prix d'une dépendance réseau.
- **Retrieval multilingue** : malgré le modèle d'embedding multilingue et
  la recherche hybride, certaines requêtes très spécifiques peuvent encore
  manquer leur cible.
- **Tunisien (derja)** : recherche académique confirmée — le tunisien est
  le dialecte arabe le moins bien supporté par les LLM généralistes
  actuels (GPT-4, Gemini inclus), pas une limite spécifique à ce projet.
  Le système fait un "meilleur effort" via le prompt, sans fluidité garantie.
- **Nuances médicales** : le LLM peut confondre "sans lactose" et "sans
  allergène lait" — à ne jamais utiliser tel quel pour de vraies décisions
  de santé sans validation humaine.
- **Classification imparfaite** : le routage du superviseur (produit vs
  stock) peut occasionnellement se tromper sur des questions ambiguës.

## Sources de données

| Donnée | Source | Statut |
|---|---|---|
| Catalogue produits | Open Food Facts API v2 | Réelle |
| Historique de ventes | Générateur synthétique | Synthétique, documentée |
| Stock & dates de péremption | Générateur synthétique | Synthétique, documentée |

Le scraping de sites de distributeurs tunisiens (ex. mg.tn) a été
explicitement écarté après vérification de leurs conditions d'utilisation.

## Roadmap

- [x] Phase 0 — Cadrage, architecture, scaffolding
- [x] Phase 1 — Couche de données (893 produits)
- [x] Phase 2 — Agent service client (RAG + retrieval hybride)
- [x] Phase 3 — API FastAPI
- [x] Phase 4 — Agent anti-gaspillage
- [x] Phase 5 — Orchestration LangGraph
- [x] Frontend — historique, dark mode, composants
- [ ] Phase 7 — Évaluation formelle (jeu de test, métriques)
- [ ] Phase 8 — Documentation finale et préparation entretien

## Structure du projet

```
retail-agentic-copilot/
├── data/
│   ├── raw/                       # catalog_raw.json, catalog_clean.json
│   └── synthetic/                  # sales_history.json, inventory.json
├── src/
│   ├── data_layer/                  # scripts Phase 1
│   ├── rag/                          # chunking, embeddings, retrieval hybride
│   ├── agents/                        # customer_service_agent, pricing_agent(_tool)
│   ├── api/                            # FastAPI : main, routes, schemas
│   ├── orchestration/                   # supervisor.py (LangGraph)
│   └── utils/                            # logger, llm.py (switch Ollama/Groq)
├── frontend/
│   ├── app/                            # page.tsx (orchestrateur), layout.tsx
│   ├── components/                      # Sidebar, ChatHeader, MessageBubble...
│   ├── lib/                              # storage.ts (localStorage)
│   └── types/                             # chat.ts
├── chroma_db/                          # index vectoriel (généré, gitignored)
├── tests/
└── config.py
```