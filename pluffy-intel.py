import json
import os
import time

import feedparser
import requests
from dotenv import load_dotenv


load_dotenv()

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
DB_PATH = os.getenv("DB_PATH", "pluffy_intel_posted.json")

DEFAULT_FEEDS = {
    "CyberWire": "https://www.cyberwire.com/rss",
    "BleepingComputer": "https://www.bleepingcomputer.com/feed/",
    "The Hacker News": "https://thehackernews.com/feeds/posts/default",
}


def parse_feeds():
    raw_value = os.getenv("RSS_FEEDS") or os.getenv("RSS_FEED_URL")
    if not raw_value:
        return DEFAULT_FEEDS

    try:
        parsed = json.loads(raw_value)
        if isinstance(parsed, dict):
            return parsed
    except (TypeError, ValueError):
        pass

    feeds = {}
    for line in raw_value.splitlines():
        if not line.strip():
            continue
        if "|" in line:
            site, url = [part.strip() for part in line.split("|", 1)]
        elif "," in line:
            site, url = [part.strip() for part in line.split(",", 1)]
        else:
            continue
        if site and url:
            feeds[site] = url

    return feeds or DEFAULT_FEEDS


RSS_FEEDS = parse_feeds()


def load_posted():
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (OSError, ValueError, json.JSONDecodeError):
            return []
    return []


def save_posted(posted):
    directory = os.path.dirname(DB_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(posted, f)


def send_alert(site, title, link, summary="Click link to read full article."):
    if not WEBHOOK_URL:
        raise ValueError("WEBHOOK_URL environment variable is not set.")

    clean_summary = summary[:250] + "..." if summary and len(summary) > 250 else (summary or "Click link to read full article.")
    payload = {
        "username": os.getenv("DISCORD_USERNAME", "Pluffy Intel"),
        "avatar_url": os.getenv("DISCORD_AVATAR_URL", "https://i.imgur.com/8N4I4B0.png"),
        "embeds": [
            {
                "title": title,
                "url": link,
                "color": int(os.getenv("DISCORD_COLOR", "3447003"), 16) if os.getenv("DISCORD_COLOR", "3447003").startswith("0x") else int(os.getenv("DISCORD_COLOR", "3447003")),
                "description": clean_summary,
                "footer": {"text": f"Source: {site} • Cyber Trends"},
            }
        ],
    }

    response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
    response.raise_for_status()


def run():
    posted = load_posted()

    for site, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:2]:
            link = getattr(entry, "link", None)
            if not link or link in posted:
                continue
            summary = getattr(entry, "summary", None) or getattr(entry, "description", None) or "Click link to read full article."
            send_alert(site, entry.title, link, summary)
            posted.append(link)
            time.sleep(2)

    save_posted(posted)


if __name__ == "__main__":
    try:
        print("[+] Fetching latest Pluffy Intel...")
        run()
        print("[+] Done! Pluffy Intel has been updated and sent to Discord.")
    except Exception as exc:
        print(f"[-] Error: {exc}", flush=True)
        raise SystemExit(1)