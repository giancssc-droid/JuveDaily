"""
fetch_data.py
--------------
Descarga toda la información cruda de noticias de la Juventus y la guarda
en data/latest.json.

Fuentes:
1. TuttoJuve.com — sitio periodístico dedicado a la Juventus (TMW Network)
2. JuveFC.com — sitio de noticias en inglés
3. GJustjuve — canal de Telegram con noticias y citas de fuentes de referencia
   (vía rss-bridge, fechas reales e inmutables de Telegram)
"""

import html
import json
import os
import re
from datetime import datetime, timedelta, timezone

import feedparser

# --------------------------------------------------------------------------
# CONFIGURACIÓN
# --------------------------------------------------------------------------

# Ventana de frescura por fuente. JuveFC tiene una ventana más corta porque
# hay sospecha de que a veces refresca fechas de artículos viejos.
MAX_NEWS_AGE_HOURS = {
    "tuttojuve": 24,
    "gjustjuve": 24,
}
MAX_ITEMS_PER_SOURCE = 25

TIER_1_JOURNALISTS = ["Fabrizio Romano", "Gianluca Di Marzio", "Romeo Agresti"]
TIER_2_JOURNALISTS = ["Matteo Moretto", "Giovanni Albanese"]

RSS_SOURCES = {
    "tuttojuve": "https://www.tuttojuve.com/rss",
    "gjustjuve": (
        "https://rss-bridge.org/bridge01/?action=display"
        "&bridge=TelegramBridge&username=GJustjuve&format=Atom"
    ),
}

NOISE_PATTERNS = [
    "pinned",
    "youtu.be",
    "youtube.com",
    "video del anuncio",
    "gjustjuve pinned",
]

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


def fetch_source(source_name: str, url: str) -> list:
    print(f"Descargando feed: {source_name}...")
    max_age = MAX_NEWS_AGE_HOURS.get(source_name, 24)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age)
    try:
        parsed = feedparser.parse(url)
    except Exception as exc:  # noqa: BLE001
        print(f"[AVISO] No se pudo leer el feed {source_name}: {exc}")
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
            "source": source_name,
            "title": title[:200],
            "text": text[:600],
            "link": link,
            "published": entry_date.isoformat() if entry_date else None,
        })

    items.sort(key=lambda i: i["published"] or "", reverse=True)
    return items[:MAX_ITEMS_PER_SOURCE]


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

    all_items = []
    for name, url in RSS_SOURCES.items():
        all_items.extend(fetch_source(name, url))

    all_items = dedupe(all_items)
    all_items.sort(key=lambda i: i["published"] or "", reverse=True)

    combined = {
        "generated_at_utc": now_utc.isoformat(),
        "today_venezuela": now_venezuela.strftime("%Y-%m-%d"),
        "today_venezuela_readable": now_venezuela.strftime("%A %d de %B de %Y"),
        "tier_1_journalists": TIER_1_JOURNALISTS,
        "tier_2_journalists": TIER_2_JOURNALISTS,
        "news": all_items,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    print(f"\nListo. {len(all_items)} noticias guardadas en {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
