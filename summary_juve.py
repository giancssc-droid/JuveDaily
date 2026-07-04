import feedparser
from datetime import datetime, timezone

RSS_URL = "https://reader.rssground.com/public.php?op=rss&id=4086&is_cat=1&key=4q355x6a4810ed7ed88"

feed = feedparser.parse(RSS_URL)

official = []
incoming = []
outgoing = []
analysis = []
other = []

seen = set()

for entry in feed.entries[:150]:

    title = entry.get("title", "")
    summary = entry.get("summary", "")

    text = f"{title} {summary}"

    text = (
        text
        .replace("�", "")
        .replace("��", "")
        .replace("&nbsp;", " ")
        .strip()
    )

    lower = text.lower()

    if any(x in lower for x in [
        "gjustjuve pinned",
        "pinned",
        "youtu.be",
        "youtube.com"
    ]):
        continue

    if len(text) < 20:
        continue

    clean = title.lower().strip()

    if clean in seen:
        continue

    seen.add(clean)

    # -------------------------
    # OFICIAL
    # -------------------------

    if any(x in lower for x in [
        "@juventusfc",
        "oficial",
        "official",
        "signed",
        "announced",
        "contract until"
    ]):

        official.append(text[:350])
        continue

    # -------------------------
    # ANALISIS
    # -------------------------

    if any(x in lower for x in [
        "carnevali",
        "strategy",
        "project",
        "opinion",
        "analysis"
    ]):

        analysis.append(text[:350])
        continue

    # -------------------------
    # SALIDAS
    # -------------------------

    if any(x in lower for x in [
        "bayern",
        "departure",
        "exit",
        "leave",
        "leaving",
        "wanted by",
        "sale",
        "sold"
    ]):

        outgoing.append(text[:350])
        continue

    # -------------------------
    # ENTRADAS
    # -------------------------

    if any(x in lower for x in [
        "contact",
        "contacts",
        "talks",
        "meeting",
        "offer",
        "interested",
        "interest",
        "target",
        "plan a",
        "negotiating",
        "negotiation",
        "mercato",
        "transfer"
    ]):

        incoming.append(text[:350])
        continue

    other.append(text[:300])

html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Juventus Daily</title>

<style>

body {{
    font-family: Arial, sans-serif;
    max-width: 1200px;
    margin: auto;
    padding: 20px;
    line-height: 1.6;
}}

h1 {{
    text-align:center;
}}

.section {{
    margin-top: 30px;
}}

.card {{
    background: #f7f7f7;
    padding: 12px;
    margin-bottom: 10px;
    border-radius: 6px;
}}

.updated {{
    color: #666;
}}

</style>
</head>

<body>

<h1>Juventus Daily</h1>

<p class="updated">
Actualizado:
{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
</p>
"""

if incoming:
    html += "<div class='section'><h2>🔥 Mercado de Entradas</h2>"
    for item in incoming[:20]:
        html += f"<div class='card'>{item}</div>"
    html += "</div>"

if outgoing:
    html += "<div class='section'><h2>🚪 Mercado de Salidas</h2>"
    for item in outgoing[:20]:
        html += f"<div class='card'>{item}</div>"
    html += "</div>"

if official:
    html += "<div class='section'><h2>⚪ Oficial</h2>"
    for item in official[:15]:
        html += f"<div class='card'>{item}</div>"
    html += "</div>"

if analysis:
    html += "<div class='section'><h2>📰 Análisis</h2>"
    for item in analysis[:15]:
        html += f"<div class='card'>{item}</div>"
    html += "</div>"

if other:
    html += "<div class='section'><h2>📋 Otras Noticias</h2>"
    for item in other[:15]:
        html += f"<div class='card'>{item}</div>"
    html += "</div>"

html += """
</body>
</html>
"""

with open(
    "juventus_daily.html",
    "w",
    encoding="utf-8"
) as f:
    f.write(html)

print("Juventus Daily V3 generado")
