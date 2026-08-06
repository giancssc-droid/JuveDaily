"""
generate_briefing.py
---------------------
Lee data/latest.json, se lo pasa a la API gratuita de Gemini con
instrucciones de priorización por fuente, y genera el resumen diario
de la Juventus.

Salidas:
1. briefing.md
2. docs/index.html
3. Mensaje enviado por Telegram

Variables de entorno (Secrets en GitHub):
- GEMINI_API_KEY
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID
"""

import json
import os
import time
from datetime import datetime

import requests

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "latest.json")
MD_OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "briefing.md")
HTML_OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "docs", "index.html")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

MODEL = "gemini-2.5-flash"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
)

SECTION_HEADERS = ("📅", "⚪", "⚫", "💰", "🩹", "📅", "🎯", "📰")

SYSTEM_PROMPT = """\
Eres un asistente que redacta un resumen diario de noticias de la Juventus \
en español, para un hincha que quiere estar al día en 30 segundos, sin \
perder tiempo revisando múltiples fuentes.

Recibirás datos crudos en JSON:
- news: lista de noticias, cada una con "source" (de dónde viene), "title", \
  "text" (resumen o contenido), "link" y "published"
- tier_1_journalists: nombres de periodistas de máxima fiabilidad
- tier_2_journalists: nombres de periodistas de fiabilidad media
- today_venezuela: la fecha de HOY en formato YYYY-MM-DD, en hora de Venezuela

Instrucciones de priorización:
1. Si el texto de una noticia menciona a alguno de los tier_1_journalists, \
   dale prioridad alta — son las fuentes más fiables en fichajes y mercado.
2. Si menciona a un tier_2_journalist, dale prioridad media.
3. Si el texto suena a rumor sin atribución clara (sin nombrar periodista \
   ni fuente), o son especulaciones vagas, inclúyelo solo si no hay \
   suficiente contenido de mayor fiabilidad, y márcalo como "🗣️ Rumor" al \
   inicio del bullet.
4. Ignora contenido duplicado o casi idéntico entre fuentes: quédate con \
   la versión más completa o más reciente.
5. Agrupa el contenido en las categorías que correspondan según lo que \
   encuentres (usa solo las que tengan contenido real):
   - 📰 Noticias del club
   - 💰 Mercado de fichajes
   - 🩹 Lesiones y bajas
   - 📅 Calendario y resultados
6. Si una categoría no tiene contenido relevante, NO la incluyas en \
   absoluto — ni el encabezado.
7. Para CADA noticia que incluyas, agrega su link en una línea nueva justo \
   debajo, con este formato exacto: "  🔗 [link]" (dos espacios, el \
   emoji, y el link tal cual viene en el campo "link" del JSON).
8. Termina con "🎯 Prioridad de hoy": 2 a 4 bullets con lo más importante \
   que el hincha debería saber hoy, en orden de importancia. Esta sección \
   NO lleva links.
9. Sé conciso. Cada bullet debe caber idealmente en una o dos líneas cortas.
10. Deja una línea en blanco entre cada bullet dentro de una misma sección.
11. Nada de relleno ni explicaciones de tu proceso. NO uses markdown \
    (nada de asteriscos **, guiones bajos _, ni almohadillas #). Generá \
    texto plano con este formato exacto, incluyendo únicamente las \
    secciones que tengan contenido:

📅 Juventus - [fecha legible]

📰 Noticias del club
- [texto]
  🔗 [link]

💰 Mercado de fichajes
- [texto]
  🔗 [link]

🩹 Lesiones y bajas
- [texto]
  🔗 [link]

📅 Calendario y resultados
- [texto]
  🔗 [link]

🎯 Prioridad de hoy
- ...

Responde ÚNICAMENTE con el resumen en ese formato, sin texto antes ni después.
"""


def call_gemini(data: dict) -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("Falta GEMINI_API_KEY como Secret en GitHub.")

    user_message = (
        "Aquí están las noticias de hoy. Genera el resumen:\n\n"
        + json.dumps(data, ensure_ascii=False)
    )

    request_body = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": user_message}]}],
        "generationConfig": {
            "maxOutputTokens": 3000,
            "temperature": 0.4,
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }

    max_attempts = 4
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.post(
                GEMINI_URL,
                headers={
                    "x-goog-api-key": GEMINI_API_KEY,
                    "Content-Type": "application/json",
                },
                json=request_body,
                timeout=60,
            )
            if response.status_code in (429, 500, 503) and attempt < max_attempts:
                wait_seconds = attempt * 15
                print(f"[AVISO] Gemini respondió {response.status_code}. Reintentando en {wait_seconds}s...")
                time.sleep(wait_seconds)
                continue
            response.raise_for_status()
            payload = response.json()
            break
        except requests.exceptions.RequestException as exc:
            last_error = exc
            if attempt < max_attempts:
                wait_seconds = attempt * 15
                print(f"[AVISO] Error de red: {exc}. Reintentando en {wait_seconds}s...")
                time.sleep(wait_seconds)
                continue
            raise
    else:
        raise RuntimeError(f"Gemini no respondió tras varios intentos: {last_error}")

    candidates = payload.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"Gemini no devolvió respuesta: {payload}")

    parts = candidates[0].get("content", {}).get("parts", [])
    text = "\n".join(p.get("text", "") for p in parts).strip()
    if not text:
        raise RuntimeError(f"Gemini devolvió una respuesta vacía: {payload}")
    return text


def save_markdown(briefing_text: str):
    with open(MD_OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(briefing_text + "\n")


def save_html(briefing_text: str, today_readable: str):
    os.makedirs(os.path.dirname(HTML_OUTPUT_PATH), exist_ok=True)
    escaped = briefing_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Juventus - Resumen diario</title>
<style>
  body {{
    font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
    background: #12141a;
    color: #f1f1f1;
    max-width: 640px;
    margin: 0 auto;
    padding: 24px 16px 60px;
    line-height: 1.6;
  }}
  pre {{
    white-space: pre-wrap;
    font-family: inherit;
    font-size: 1.05rem;
    background: #1c1f27;
    border-radius: 12px;
    padding: 20px;
  }}
  .updated {{
    color: #8b8f9a;
    font-size: 0.85rem;
    margin-top: 20px;
    text-align: center;
  }}
</style>
</head>
<body>
<pre>{escaped}</pre>
<p class="updated">Actualizado: {today_readable} (hora de Venezuela)</p>
</body>
</html>
"""
    with open(HTML_OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)


def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_for_telegram(raw_text: str) -> str:
    lines = raw_text.split("\n")
    formatted_lines = []
    for line in lines:
        stripped = line.strip()
        is_header = stripped.startswith(SECTION_HEADERS) and not stripped.startswith("•")
        is_link_line = stripped.startswith("🔗")

        if is_header:
            formatted_lines.append(f"<b>{escape_html(line)}</b>")
        elif is_link_line:
            url = stripped.replace("🔗", "", 1).strip()
            indent = line[: len(line) - len(line.lstrip())]
            formatted_lines.append(f'{indent}🔗 <a href="{escape_html(url)}">Leer noticia</a>')
        else:
            formatted_lines.append(escape_html(line))
    return "\n".join(formatted_lines)


def send_telegram(briefing_text: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[INFO] Telegram no configurado, se omite el envío.")
        return

    formatted_text = format_for_telegram(briefing_text)
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    resp = requests.post(
        url,
        json={"chat_id": TELEGRAM_CHAT_ID, "text": formatted_text, "parse_mode": "HTML"},
        timeout=20,
    )
    if resp.ok:
        print("Mensaje enviado por Telegram correctamente.")
    else:
        print(f"[AVISO] Telegram devolvió un error: {resp.status_code} {resp.text}")


def main():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("Generando resumen con la API gratuita de Gemini...")
    briefing_text = call_gemini(data)

    save_markdown(briefing_text)
    save_html(briefing_text, data.get("today_venezuela_readable", datetime.now().isoformat()))
    send_telegram(briefing_text)

    print("\n--- RESUMEN GENERADO ---\n")
    print(briefing_text)


if __name__ == "__main__":
    main()
