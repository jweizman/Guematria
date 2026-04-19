import json
import os
import uuid
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, request

try:
    import anthropic
except ImportError:
    anthropic = None

app = Flask(__name__)

DATA_DIR = Path(__file__).parent / "data"
DATA_FILE = DATA_DIR / "psychologists.json"

CLAUDE_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-7")


def _claude_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or anthropic is None:
        return None
    return anthropic.Anthropic(api_key=api_key)


def load_psychologists():
    if not DATA_FILE.exists():
        return []
    with DATA_FILE.open(encoding="utf-8-sig") as f:
        text = f.read().strip()
    if not text:
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        app.logger.error("psychologists.json is corrupt (%s); returning empty list", exc)
        return []
    return data if isinstance(data, list) else []


def save_psychologists(items):
    DATA_DIR.mkdir(exist_ok=True)
    tmp = DATA_FILE.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    tmp.replace(DATA_FILE)


def normalize(payload, pid=None):
    return {
        "id": pid or str(uuid.uuid4()),
        "name": (payload.get("name") or "").strip(),
        "title": (payload.get("title") or "").strip(),
        "specialties": payload.get("specialties") or [],
        "skills": payload.get("skills") or [],
        "bio": payload.get("bio") or "",
        "image_url": payload.get("image_url") or "",
        "verified": bool(payload.get("verified", False)),
        "rating": float(payload.get("rating") or 0),
        "reviews_count": int(payload.get("reviews_count") or 0),
        "next_available": payload.get("next_available") or "",
        "available_today": bool(payload.get("available_today", True)),
        "languages": payload.get("languages") or [],
        "experience_years": int(payload.get("experience_years") or 0),
    }


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat")
def chat_page():
    return render_template("chat.html")


@app.route("/admin")
def admin_page():
    return render_template("admin.html")


# ---------------------------------------------------------------------------
# Psychologist CRUD + search
# ---------------------------------------------------------------------------
@app.route("/api/psychologists", methods=["GET"])
def list_psychologists():
    items = load_psychologists()
    q = (request.args.get("q") or "").strip().lower()
    specialty = (request.args.get("specialty") or "").strip().lower()
    available = request.args.get("available_today")

    if q:
        def matches(p):
            haystack = " ".join([
                p.get("name", ""),
                p.get("title", ""),
                p.get("bio", ""),
                " ".join(p.get("specialties", [])),
                " ".join(p.get("skills", [])),
            ]).lower()
            return q in haystack

        items = [p for p in items if matches(p)]

    if specialty and specialty != "all":
        items = [
            p for p in items
            if specialty in [s.lower() for s in p.get("specialties", [])]
        ]

    if available == "true":
        items = [p for p in items if p.get("available_today")]

    return jsonify(items)


@app.route("/api/psychologists/<pid>", methods=["GET"])
def get_psychologist(pid):
    items = load_psychologists()
    psy = next((p for p in items if p["id"] == pid), None)
    if not psy:
        abort(404)
    return jsonify(psy)


@app.route("/api/psychologists", methods=["POST"])
def create_psychologist():
    data = request.get_json(silent=True) or {}
    new = normalize(data)
    if not new["name"]:
        return jsonify({"error": "Name is required"}), 400
    items = load_psychologists()
    items.append(new)
    save_psychologists(items)
    return jsonify(new), 201


@app.route("/api/psychologists/<pid>", methods=["PUT"])
def update_psychologist(pid):
    data = request.get_json(silent=True) or {}
    items = load_psychologists()
    for i, psy in enumerate(items):
        if psy["id"] == pid:
            items[i] = normalize({**psy, **data}, pid=pid)
            save_psychologists(items)
            return jsonify(items[i])
    abort(404)


@app.route("/api/psychologists/<pid>", methods=["DELETE"])
def delete_psychologist(pid):
    items = load_psychologists()
    remaining = [p for p in items if p["id"] != pid]
    if len(remaining) == len(items):
        abort(404)
    save_psychologists(remaining)
    return "", 204


# ---------------------------------------------------------------------------
# Specialties (used by the filter chips on the homepage)
# ---------------------------------------------------------------------------
@app.route("/api/specialties", methods=["GET"])
def list_specialties():
    items = load_psychologists()
    seen = []
    for p in items:
        for s in p.get("specialties", []):
            if s not in seen:
                seen.append(s)
    return jsonify(seen)


# ---------------------------------------------------------------------------
# Matching via OpenAI
# ---------------------------------------------------------------------------
@app.route("/api/match", methods=["POST"])
def match():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    psychologists = load_psychologists()
    if not psychologists:
        return jsonify({
            "reply": "No psychologist has been registered yet.",
            "matches": [],
        })

    client = _claude_client()
    if client is None:
        matches = _keyword_match(user_message, psychologists)
        reply = (
            "Here are a few practitioners who could be a good fit. "
            "(Set ANTHROPIC_API_KEY for smarter matching.)"
        )
        return jsonify({"reply": reply, "matches": matches})

    catalog = [
        {
            "id": p["id"],
            "name": p["name"],
            "title": p.get("title", ""),
            "specialties": p.get("specialties", []),
            "skills": p.get("skills", []),
            "bio": (p.get("bio") or "")[:400],
            "languages": p.get("languages", []),
            "available_today": bool(p.get("available_today", False)),
        }
        for p in psychologists
    ]

    system_prompt = (
        "You are the caring assistant for The Serene Path, a platform that "
        "connects clients with psychologists. Based on the client's message, "
        "rate every psychologist in the catalog on how well they fit the "
        "client's situation and return the top 3. Be empathetic but concise "
        "(2-3 sentences max). "
        "Reply STRICTLY in valid JSON with this schema: "
        '{"reply": "<empathetic message for the client>", '
        '"matches": [{"id": "<psychologist_id>", '
        '"relevance_score": <integer 0-100>, '
        '"reason": "<why this match>"}]}. '
        "relevance_score must reflect clinical fit only, ignoring availability. "
        "Never invent an id that is not in the catalog. "
        "Return nothing else than this JSON."
    )

    user_prompt = (
        f"Client message: {user_message}\n\n"
        f"Catalog: {json.dumps(catalog, ensure_ascii=False)}"
    )

    try:
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = next(
            (b.text for b in message.content if getattr(b, "type", "") == "text"),
            "",
        )
        result = json.loads(_extract_json(text))
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Anthropic request failed: {exc}"}), 502

    by_id = {p["id"]: p for p in psychologists}
    hydrated = []
    for rank, m in enumerate(result.get("matches") or []):
        psy = by_id.get(m.get("id"))
        if not psy:
            continue
        score = m.get("relevance_score")
        try:
            score = int(score)
        except (TypeError, ValueError):
            score = max(0, 100 - rank * 10)
        hydrated.append({
            **psy,
            "reason": m.get("reason", ""),
            "relevance_score": score,
        })

    # Primary sort: relevance. Secondary: available today comes first when
    # two matches are equally relevant.
    hydrated.sort(
        key=lambda p: (-p["relevance_score"], 0 if p.get("available_today") else 1)
    )

    return jsonify({"reply": result.get("reply", ""), "matches": hydrated})


def _extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip().rstrip("`").strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    return text or "{}"


def _keyword_match(message, psychologists):
    msg = message.lower()
    scored = []
    for p in psychologists:
        haystack = " ".join([
            p.get("name", ""),
            p.get("title", ""),
            " ".join(p.get("specialties", [])),
            " ".join(p.get("skills", [])),
            p.get("bio", ""),
        ]).lower()
        score = sum(1 for w in msg.split() if len(w) > 3 and w in haystack)
        if score:
            scored.append((score, p))
    scored.sort(
        key=lambda x: (-x[0], 0 if x[1].get("available_today") else 1)
    )
    return [
        {**p, "reason": "Keyword match", "relevance_score": score * 10}
        for score, p in scored[:3]
    ]


if __name__ == "__main__":
    if not DATA_FILE.exists():
        save_psychologists([])
    app.run(debug=True, host="0.0.0.0", port=5000)
