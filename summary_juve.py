import feedparser
from datetime import datetime, timezone

RSS_URL = "https://reader.rssground.com/public.php?op=rss&id=4086&is_cat=1&key=4q355x6a4810ed7ed88"

feed = feedparser.parse(RSS_URL)

items = []

for entry in feed.entries[:75]:

    title = entry.get("title", "")
    summary = entry.get("summary", "")

    text = f"{title}\n{summary}"

    if "pinned" in text.lower():
        continue

    if "youtu.be" in text.lower():
        continue

    source = "Mercado"

    lower = text.lower()

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
}}

h1 {{
    text-align: center;
}}

.article {{
    border-bottom: 1px solid #ddd;
    padding: 10px 0;
}}

.source {{
    color: #666;
    font-weight: bold;
}}
</style>
</head>
<body>

<h1>Juventus Daily</h1>

<p>
Actualizado:
{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
</p>

<hr>
"""

for item in items:

    html += f"""
    <div class="article">
        <div class="source">[{item['source']}]</div>
        <h3>{item['title']}</h3>
        <p>{item['summary']}</p>
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

print("Juventus Daily generado")
