# The Serene Path

Plateforme Flask de mise en relation avec des psychologues. Le site présente
une fiche par praticien avec ses spécialités et compétences, propose une
recherche/filtrage côté client, et un chat qui utilise l'API Anthropic Claude
pour orienter le visiteur vers le psychologue le plus pertinent.

## Architecture

- **Frontend** : trois pages (Tailwind via CDN, design Material You)
  - `/` — accueil avec recherche, filtres par spécialité et liste des
    praticiens disponibles aujourd'hui.
  - `/chat` — chat client : décrivez votre situation, l'IA analyse et propose
    1 à 3 praticiens du catalogue.
  - `/admin` — gestion CRUD des fiches psychologues.
- **Backend** : Flask + stockage JSON simple (`data/psychologists.json`).
- **IA** : Anthropic Claude (`claude-opus-4-7` par défaut). À défaut de clé,
  un matching par mots-clés est utilisé en repli.

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

```bash
export ANTHROPIC_API_KEY="sk-ant-..."     # requis pour le matching IA
export ANTHROPIC_MODEL="claude-opus-4-7"   # optionnel, défaut: claude-opus-4-7
```

## Lancement

```bash
python app.py
```

Puis ouvrir http://localhost:5000

## API

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/api/psychologists` | Liste, paramètres : `q`, `specialty`, `available_today` |
| GET | `/api/psychologists/<id>` | Fiche d'un praticien |
| POST | `/api/psychologists` | Création |
| PUT | `/api/psychologists/<id>` | Mise à jour |
| DELETE | `/api/psychologists/<id>` | Suppression |
| GET | `/api/specialties` | Liste des spécialités présentes |
| POST | `/api/match` | Body : `{"message": "..."}`. Retourne `{reply, matches[]}`. |

## Données

Les psychologues sont persistés dans `data/psychologists.json`. Quatre fiches
exemple sont fournies à l'installation.
