"""
Fetches latest cybersecurity news headlines from public RSS feeds.
Outputs headline + summary only (not full article text) -- these get
rewritten into an original script, never re-published verbatim.

Dedup strategy (belt and suspenders, since RSS links can carry
tracking params and the same story sometimes shows up reworded):
  1. Normalize the link (strip query string/fragment) before comparing.
  2. Also normalize the title (lowercase, strip punctuation/whitespace)
     and compare against previously posted titles, so the same story
     re-syndicated under a different URL still gets caught.
"""

import feedparser
import json
import os
import re
from datetime import datetime, timedelta
from urllib.parse import urlsplit, urlunsplit

# Public RSS feeds -- these are legitimate, publicly published feeds
# meant for syndication/reading, not scraping full content
FEEDS = {
    "The Hacker News": "https://feeds.feedburner.com/TheHackersNews",
    "BleepingComputer": "https://www.bleepingcomputer.com/feed/",
    "Krebs on Security": "https://krebsonsecurity.com/feed/",
}

POSTED_FILE = "posted.json"


def normalize_link(url):
    """Strip query string and fragment so tracking params don't defeat dedup."""
    if not url:
        return ""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/"), "", ""))


def normalize_title(title):
    """Lowercase, strip punctuation/extra whitespace for fuzzy title matching."""
    t = title.lower()
    t = re.sub(r"[^a-z0-9\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def load_posted(path=POSTED_FILE):
    """Returns (set_of_links, set_of_titles) already turned into videos."""
    if not os.path.exists(path):
        return set(), set()
    with open(path) as f:
        data = json.load(f)
    links = {entry["link"] for entry in data}
    titles = {entry["title"] for entry in data}
    return links, titles


def mark_posted(link, title, path=POSTED_FILE):
    """Record a story as posted (normalized link + title). Keeps last 500."""
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
    else:
        data = []

    data.append({
        "link": normalize_link(link),
        "title": normalize_title(title),
    })
    data = data[-500:]

    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def fetch_latest(max_age_hours=8, max_items_per_feed=8, posted_links=None, posted_titles=None):
    """Fetch recent, not-yet-posted headlines across all feeds."""
    cutoff = datetime.now() - timedelta(hours=max_age_hours)
    posted_links = posted_links or set()
    posted_titles = posted_titles or set()

    all_items = []
    seen_this_run = set()  # catches duplicates across feeds within the same run too

    for source, url in FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:max_items_per_feed]:
            raw_link = entry.get("link", "")
            raw_title = entry.get("title", "")
            norm_link = normalize_link(raw_link)
            norm_title = normalize_title(raw_title)

            if norm_link in posted_links or norm_title in posted_titles:
                continue
            if norm_link in seen_this_run or norm_title in seen_this_run:
                continue

            published = entry.get("published_parsed")
            if published:
                pub_dt = datetime(*published[:6])
                if pub_dt < cutoff:
                    continue

            seen_this_run.add(norm_link)
            seen_this_run.add(norm_title)

            all_items.append({
                "source": source,
                "title": raw_title,
                # summary field only -- short snippet, not full article body
                "summary": entry.get("summary", "")[:300],
                "link": raw_link,
                "published": entry.get("published", ""),
            })

    return all_items


def save_daily_batch(items, path="daily_news.json"):
    with open(path, "w") as f:
        json.dump(items, f, indent=2)
    print(f"Saved {len(items)} headlines to {path}")


if __name__ == "__main__":
    posted_links, posted_titles = load_posted()
    items = fetch_latest(posted_links=posted_links, posted_titles=posted_titles)
    for i, item in enumerate(items, 1):
        print(f"{i}. [{item['source']}] {item['title']}")
    save_daily_batch(items)
