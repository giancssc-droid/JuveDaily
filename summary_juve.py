import feedparser
from datetime import datetime, timezone

RSS_URL = "https://reader.rssground.com/public.php?op=rss&id=4086&is_cat=1&key=4q355x6a4810ed7ed88"

feed = feedparser.parse(RSS_URL)

players = {
    "Goretzka": [],
    "Kolo Muani": [],
    "Emiliano Martínez": [],
    "Bremer": [],
    "Kessié": [],
    "Sancho": [],
    "Conceição": [],
    "Vlahovic": [],
    "Douglas Luiz": []
}

official = []
analysis = []
other = []

for entry in feed.entries[:100]:

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

    if "@juventusfc" in lower or "oficial" in lower:
        official.append(text[:300])
        continue

    if "carnevali" in lower:
        analysis.append(text[:300])
        continue

    found = False

    keywords = {
        "Goretzka": ["goretzka"],
        "Kolo Muani": ["kolo", "kolomuani"],
        "Emiliano Martínez": ["martinez", "martínez"],
        "Bremer": ["bremer"],
        "Kessié": ["kessie", "kessié"],
        "Sancho": ["sancho"],
        "Conceição": ["conceicao", "conceição"],
        "Vlahovic": ["vlahovic"],
        "Douglas Luiz": ["douglas luiz"]
    }

    for player, words in keywords.items():

        if any(w in lower for w in words):

            players[player].append(text[:350])

            found = True

            break

    if not found:
        other.append(text[:250])

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

.section {{
    margin-top: 30px;
}}

h1 {{
    text-align:center;
}}

h2 {{
    border-bottom: 2px solid #ddd;
    padding-bottom: 5px;
}}

.card {{
    margin-bottom: 15px;
    padding: 10px;
    background: #f7f7f7;
}}

</style>
</head>

<body>

<h1>Juventus Daily</h1>

<p>
Actualizado:
{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
</p>
"""

if official:

    html += "<div class='section'><h2>⚪ Oficial</h2>"

    for item in official[:10]:
        html += f"<div class='card'>{item}</div>"

    html += "</div>"

if analysis:

    html += "<div class='section'><h2>📰 Análisis</h2>"

    for item in analysis[:10]:
        html += f"<div class='card'>{item}</div>"

    html += "</div>"

html += "<div class='section'><h2>🔥 Mercato</h2>"

for player, news in players.items():

    if not news:
        continue

    html += f"<h3>{player}</h3>"

    for item in news[:3]:
        html += f"<div class='card'>{item}</div>"

html += "</div>"

if other:

    html += "<div class='section'><h2>📋 Otras noticias</h2>"

    for item in other[:10]:
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

print("Juventus Daily V2 generado")
