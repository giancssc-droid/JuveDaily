import feedparser

RSS_URL = "https://reader.rssground.com/public.php?op=rss&id=4086&is_cat=1&key=4q355x6a4810ed7ed88"

feed = feedparser.parse(RSS_URL)

print("TOTAL:", len(feed.entries))

for entry in feed.entries[:10]:

    print("=" * 80)

    print("TITLE:")
    print(entry.get("title"))

    print()

    print("PUBLISHED:")
    print(entry.get("published"))

    print()

    print("UPDATED:")
    print(entry.get("updated"))

    print()

    print("LINK:")
    print(entry.get("link"))

    print()

    print("AVAILABLE FIELDS:")
    print(list(entry.keys()))
