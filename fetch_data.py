"""
fetch_data.py
--------------
Descarga los mensajes recientes del canal de Telegram GJustjuve (vía
rss-bridge) y los guarda en data/latest.json, listos para que Gemini los
clasifique por Tier de periodista/diario.
"""

import html
import json
import os
import re
from datetime import datetime, timedelta, timezone

import feedparser

MAX_NEWS_AGE_HOURS = 48
MAX_ITEMS = 200

TIER_1_JOURNALISTS = ["Romeo Agresti", "Fabrizio Romano", "Gianluca Di Marzio"]
TIER_2_JOURNALISTS = [
    "Nicolò Schira", "Giovanni Albanese", "Alfredo Pedullà",
    "Ciro Di Natale", "@_Morik92_",
]
NEWSPAPERS = ["Sky Sport", "Tuttosport", "Gazzetta dello Sport"]

GJUSTJUVE_URL = (
    "https://rss-bridge.org/bridge01/?action=display"
    "&bridge=TelegramBridge&username=GJustjuve&format=Atom"
)

NOISE_PATTERNS = ["pinned", "youtu.be", "youtube.com"]

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "data", "latest.json")


def clean_text(raw: str) -> str:
    text = html.unescape(raw)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\ufffd", "")
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_entry_date(entry):
    for field in ("published_parsed", "updated_parsed"):
        value = getattr(entry, field, None)
        if value:
            return datetime(*value[:6], tzinfo=timezone.utc)
    return None


def fetch_gjustjuve() -> list:
    print("Descargando feed: gjustjuve...")
    cutoff = datetime.now(timezone.utc) - timedelta(hours=MAX_NEWS_AGE_HOURS)
    try:
        parsed = feedparser.parse(GJUSTJUVE_URL)
    except Exception as exc:  # noqa: BLE001
        print(f"[AVISO] No se pudo leer el feed: {exc}")
        return []

    items = []
    for entry in parsed.entries:
        entry_date = parse_entry_date(entry)
        if entry_date and entry_date < cutoff:
            continue

        title = clean_text(getattr(entry, "title", ""))
        summary = clean_text(getattr(entry, "summary", ""))
        text = summary if summary else title
        link = getattr(entry, "link", "")

        lower = text.lower()
        if any(pattern in lower for pattern in NOISE_PATTERNS):
            continue
        if len(text) < 20:
            continue

        items.append({
            "text": text[:700],
            "link": link,
            "published": entry_date.isoformat() if entry_date else None,
        })

    items.sort(key=lambda i: i["published"] or "", reverse=True)
    return items[:MAX_ITEMS]


def dedupe(items: list) -> list:
    seen = set()
    unique = []
    for item in items:
        key = item["text"][:120].lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def main():
    now_utc = datetime.now(timezone.utc)
    now_venezuela = now_utc - timedelta(hours=4)

    items = dedupe(fetch_gjustjuve())

    combined = {
        "generated_at_utc": now_utc.isoformat(),
        "today_venezuela": now_venezuela.strftime("%Y-%m-%d"),
        "today_venezuela_readable": now_venezuela.strftime("%A %d de %B de %Y"),
        "tier_1_journalists": TIER_1_JOURNALISTS,
        "tier_2_journalists": TIER_2_JOURNALISTS,
        "newspapers": NEWSPAPERS,
        "news": items,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    print(f"\nListo. {len(items)} mensajes guardados en {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
