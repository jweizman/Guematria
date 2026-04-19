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

Set your Anthropic API key with either a `.env` file (recommended) or
environment variables.

**Option A — `.env` file** (auto-loaded by python-dotenv):

```
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-opus-4-7
```

Copy `.env.example` to `.env` and fill in your key.

**Option B — shell environment variables:**

```bash
# macOS / Linux
export ANTHROPIC_API_KEY="sk-ant-..."

# Windows PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-..."

# Windows cmd.exe
set ANTHROPIC_API_KEY=sk-ant-...
```

### Verifying the LLM is active

On startup, the server prints one of:

```
[The Serene Path] LLM matching enabled via claude-opus-4-7
[The Serene Path] LLM DISABLED (ANTHROPIC_API_KEY is not set). Using keyword fallback.
```

You can also hit `GET /api/health` at any time:

```json
{"anthropic_installed": true, "api_key_set": true, "llm_ready": true, "model": "claude-opus-4-7"}
```

`POST /api/match` responses include a `"source"` field: `"claude"` when
the LLM answered, `"fallback"` when the keyword matcher did.

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
