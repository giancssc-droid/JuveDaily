import feedparser
import html
import re

from datetime import datetime, timezone, timedelta
from feedgen.feed import FeedGenerator

RSS_URL = "https://reader.rssground.com/public.php?op=rss&id=4086&is_cat=1&key=4q355x6a4810ed7ed88"

LIMIT_HOURS = 12

feed = feedparser.parse(RSS_URL)

now = datetime.now(timezone.utc)

news = []

for entry in feed.entries:

    try:
        updated = datetime(
            *entry.updated_parsed[:6],
            tzinfo=timezone.utc
        )

        if updated < now - timedelta(hours=LIMIT_HOURS):
            continue

    except:
        continue

    summary = entry.get("summary", "")
    link = entry.get("link", "")

    text = html.unescape(summary)

    text = re.sub(r"<[^>]+>", "", text)

    text = text.replace("�", "")
    text = text.replace("��", "")

    text = text.replace("\n", " ")

    text = re.sub(r"\s+", " ", text)

    lower = text.lower()

    if any(x in lower for x in [
        "pinned",
        "youtu.be",
        "youtube.com",
        "video del anuncio",
        "gjustjuve pinned"
    ]):
        continue

    if len(text.strip()) < 20:
        continue

    news.append({
        "date": updated,
        "text": text,
        "link": link
    })

news.sort(
    key=lambda x: x["date"],
    reverse=True
)

# eliminar duplicados

unique = []
seen = set()

for item in news:

    key = item["text"][:120].lower()

    if key in seen:
        continue

    seen.add(key)

    unique.append(item)

news = unique

# ==========================
# HTML
# ==========================

html_output = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Juventus Daily</title>

<style>

body {{
    font-family: Arial, sans-serif;
    max-width: 1000px;
    margin: auto;
    padding: 20px;
    line-height: 1.6;
}}

h1 {{
    text-align:center;
}}

.card {{
    background:#f7f7f7;
    padding:15px;
    margin-bottom:15px;
    border-radius:8px;
}}

.date {{
    color:#666;
    font-size:14px;
}}

.link {{
    margin-top:10px;
}}

</style>
</head>

<body>

<h1>Juventus Daily</h1>

<p>
Últimas {LIMIT_HOURS} horas<br>
Actualizado: {now.strftime('%Y-%m-%d %H:%M UTC')}
</p>

<hr>
"""

for item in news[:50]:

    html_output += f"""
    <div class="card">

        <div class="date">
        {item['date'].strftime('%Y-%m-%d %H:%M')}
        </div>

        <p>
        {item['text']}
        </p>

        <div class="link">
        <a href="{item['link']}" target="_blank">
        Abrir en Telegram
        </a>
        </div>

    </div>
    """

html_output += """
</body>
</html>
"""

with open(
    "juventus_daily.html",
    "w",
    encoding="utf-8"
) as f:
    f.write(html_output)

# ==========================
# RSS XML
# ==========================

fg = FeedGenerator()

fg.title("Juventus Daily")
fg.description("Juventus Daily Feed - Últimas 12 horas")
fg.link(
    href="https://giancssc-droid.github.io/JuveDaily/"
)

for item in news[:50]:

    fe = fg.add_entry()

    fe.title(item["text"][:120])

    fe.description(item["text"])

    fe.link(
        href=item["link"]
    )

    fe.guid(
        item["link"]
    )

    fe.pubDate(
        item["date"]
    )

fg.rss_file(
    "juventus_daily.xml"
)

print(
    f"Generadas {len(news)} noticias"
)
