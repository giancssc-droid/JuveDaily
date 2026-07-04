import feedparser

RSS_URL = "https://reader.rssground.com/public.php?op=rss&id=4086&is_cat=1&key=4q355x6a4810ed7ed88"

feed = feedparser.parse(RSS_URL)

entry = feed.entries[0]

print("TITLE")
print(entry.get("title"))

print("\nSUMMARY")
print(entry.get("summary"))

print("\nCONTENT")
print(entry.get("content"))
