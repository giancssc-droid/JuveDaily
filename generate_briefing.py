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

SECTION_HEADERS = ("📅", "⭐", "🥈", "📰")

SYSTEM_PROMPT = """\
Eres un asistente que redacta un resumen diario de noticias de la Juventus \
en español, clasificando cada noticia según quién la reportó.

Recibirás datos crudos en JSON:
- news: lista de mensajes del canal de Telegram GJustjuve, cada uno con \
  "text" (el contenido) y "published"
- tier_1_journalists: nombres de periodistas Tier 1 (máxima fiabilidad)
- tier_2_journalists: nombres de periodistas Tier 2
- newspapers: nombres de diarios/medios a buscar
- today_venezuela: la fecha de HOY en formato YYYY-MM-DD, en hora de Venezuela

Instrucciones de clasificación:
1. Para cada mensaje, busca en su texto si menciona a alguno de los \
   tier_1_journalists. Si es así, clasifícalo en Tier 1, sin importar si \
   también menciona a alguien de tier_2 o algún diario.
2. Si no menciona a nadie de tier_1 pero sí a alguien de tier_2_journalists, \
   clasifícalo en Tier 2.
3. Si no menciona a ningún periodista de las dos listas pero sí a alguno de \
   los newspapers, clasifícalo en Periódicos.
4. Si un mensaje NO menciona a ninguno de estos nombres ni diarios, \
   DESCÁRTALO por completo. No lo incluyas en ninguna categoría.
5. Ignora contenido duplicado o casi idéntico dentro de una misma categoría: \
   quédate con la versión más completa o más reciente.
6. En cada categoría, ordena por fecha (más reciente primero) y quédate \
   como máximo con los 10 más recientes.
7. Si una categoría queda sin ningún mensaje después de filtrar, NO la \
   incluyas en absoluto — ni el encabezado.
8. Cada bullet debe empezar con el/los nombre(s) del periodista o diario \
   que reportó la noticia, envuelto entre comillas angulares dobles «así», \
   seguido de dos puntos y el texto de la noticia en español, claro y \
   conciso, en una o dos líneas. Si un mismo mensaje cita a más de un \
   periodista, poné todos los nombres dentro del mismo «», separados por \
   coma: «Nombre 1, Nombre 2»: texto de la noticia.
9. NO incluyas links ni URLs en el texto.
10. Deja una línea en blanco entre cada bullet dentro de una misma sección.
11. Nada de relleno ni explicaciones de tu proceso. NO uses markdown \
    (nada de asteriscos **, guiones bajos _, ni almohadillas #) — el único \
    formato especial permitido es el «» alrededor del nombre. Generá \
    texto plano con este formato exacto, incluyendo únicamente las \
    secciones que tengan contenido:

📅 Juventus - [fecha legible]

⭐ Tier 1
- «Nombre»: [texto]

🥈 Tier 2
- «Nombre»: [texto]

📰 Periódicos
- «Nombre del diario»: [texto]

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
        if is_header:
            formatted_lines.append(f"<b>{escape_html(line)}</b>")
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
