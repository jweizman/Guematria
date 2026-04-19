# The Serene Path

Flask platform that connects clients with psychologists. The site shows a
profile card per practitioner with their specialties and skills, offers
client-side search and filtering, and a chat that uses the Anthropic Claude
API to recommend the most relevant psychologist to the visitor.

## Architecture

- **Frontend**: three pages (Tailwind via CDN, Material You design)
  - `/` — home page with search, specialty filters and the list of
    practitioners available today.
  - `/chat` — client chat: describe your situation and the AI recommends
    1 to 3 practitioners from the catalog.
  - `/admin` — CRUD management of psychologist profiles.
- **Backend**: Flask with simple JSON storage (`data/psychologists.json`).
- **AI**: Anthropic Claude (`claude-opus-4-7` by default). Without an API
  key, a keyword-based matcher is used as a fallback.

## Install

```bash
pip install -r requirements.txt
```

## Configuration

```bash
export ANTHROPIC_API_KEY="sk-ant-..."       # required for AI matching
export ANTHROPIC_MODEL="claude-opus-4-7"     # optional, defaults to claude-opus-4-7
```

## Run

```bash
python app.py
```

Then open http://localhost:5000

## API

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/api/psychologists` | List, query params: `q`, `specialty`, `available_today` |
| GET | `/api/psychologists/<id>` | Single practitioner |
| POST | `/api/psychologists` | Create |
| PUT | `/api/psychologists/<id>` | Update |
| DELETE | `/api/psychologists/<id>` | Delete |
| GET | `/api/specialties` | List of specialties currently in the catalog |
| POST | `/api/match` | Body: `{"message": "..."}`. Returns `{reply, matches[]}`. |

## Data

Psychologists are persisted in `data/psychologists.json`. Four sample
profiles are provided out of the box.
