import feedparser
from datetime import datetime, timezone

RSS_URL = "https://reader.rssground.com/public.php?op=rss&id=4086&is_cat=1&key=4q355x6a4810ed7ed88"

feed = feedparser.parse(RSS_URL)

items = []
seen_titles = set()

for entry in feed.entries[:100]:

    title = entry.get("title", "")
    summary = entry.get("summary", "")

    # Limpiar caracteres raros
    title = (
        title
        .replace("�", "")
        .replace("��", "")
        .replace("&nbsp;", " ")
        .strip()
    )

    summary = (
        summary
        .replace("�", "")
        .replace("��", "")
        .replace("&nbsp;", " ")
        .strip()
    )

    text = f"{title}\n{summary}"
    lower = text.lower()

    # Ignorar basura
    if any(x in lower for x in [
        "gjustjuve pinned",
        "pinned",
        "youtu.be",
        "youtube.com"
    ]):
        continue

    # Eliminar duplicados
    clean_title = title.lower().strip()

    if clean_title in seen_titles:
        continue

    seen_titles.add(clean_title)

    # Detectar fuente
    source = "Noticias"

    if "@romeoagresti" in lower:
        source = "Agresti"

    elif "fabrizio romano" in lower:
        source = "Romano"

    elif "@juventusfc" in lower:
        source = "Official"

    elif "@tuttosport" in lower:
        source = "Tuttosport"

    elif "albanese" in lower:
        source = "Albanese"

    elif any(x in lower for x in [
        "goretzka",
        "kolomuani",
        "kolo muani",
        "bremer",
        "martinez",
        "martínez",
        "kessie",
        "kessié"
    ]):
        source = "Mercato"

    items.append({
        "source": source,
        "title": title,
        "summary": summary
    })

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
    line-height: 1.5;
}}

h1 {{
    text-align: center;
}}

.updated {{
    color: #666;
    margin-bottom: 20px;
}}

.article {{
    border-bottom: 1px solid #ddd;
    padding: 15px 0;
}}

.source {{
    font-weight: bold;
    color: #555;
    margin-bottom: 5px;
}}

.title {{
    font-size: 22px;
    font-weight: bold;
    margin-bottom: 10px;
}}

.summary {{
    white-space: pre-wrap;
}}

</style>

</head>

<body>

<h1>Juventus Daily</h1>

<div class="updated">
Actualizado:
{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
</div>

<hr>
"""

for item in items:

    html += f"""
    <div class="article">

        <div class="source">
            [{item['source']}]
        </div>

        <div class="title">
            {item['title']}
        </div>

        <div class="summary">
            {item['summary']}
        </div>

    </div>
    """

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

print(
    f"Juventus Daily generado con {len(items)} noticias"
)
