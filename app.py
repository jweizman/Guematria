import re
import unicodedata

import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

SEFARIA_API = "https://www.sefaria.org/api/v3/texts/{ref}"

GEMATRIA_VALUES = {
    "א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5, "ו": 6, "ז": 7, "ח": 8, "ט": 9,
    "י": 10, "כ": 20, "ך": 20, "ל": 30, "מ": 40, "ם": 40, "נ": 50, "ן": 50,
    "ס": 60, "ע": 70, "פ": 80, "ף": 80, "צ": 90, "ץ": 90,
    "ק": 100, "ר": 200, "ש": 300, "ת": 400,
}


def strip_nikud(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def clean_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def compute_gematria(word: str) -> int:
    clean = strip_nikud(word)
    return sum(GEMATRIA_VALUES.get(ch, 0) for ch in clean)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chapter")
def chapter():
    ref = request.args.get("ref", "Genesis.1").strip()
    try:
        resp = requests.get(
            SEFARIA_API.format(ref=ref),
            params={"version": "hebrew", "return_format": "text_only"},
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        return jsonify({"error": f"Sefaria request failed: {exc}"}), 502

    data = resp.json()
    versions = data.get("versions") or []
    if not versions:
        return jsonify({"error": "No Hebrew text found for this reference."}), 404

    raw_verses = versions[0].get("text") or []
    verses = []
    for i, verse in enumerate(raw_verses, start=1):
        text = clean_html(verse) if isinstance(verse, str) else ""
        words = [w for w in re.split(r"\s+", text.strip()) if w]
        verses.append({"number": i, "words": words})

    return jsonify({
        "ref": data.get("ref", ref),
        "heRef": data.get("heRef", ""),
        "verses": verses,
    })


@app.route("/api/gematria")
def gematria():
    word = request.args.get("word", "")
    stripped = strip_nikud(word)
    letters = [
        {"letter": ch, "value": GEMATRIA_VALUES[ch]}
        for ch in stripped if ch in GEMATRIA_VALUES
    ]
    return jsonify({
        "word": word,
        "stripped": stripped,
        "letters": letters,
        "total": sum(item["value"] for item in letters),
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
