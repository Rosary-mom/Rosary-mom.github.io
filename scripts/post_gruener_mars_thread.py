#!/usr/bin/env python3
"""Post Grüner Mars X thread via API v2 (tweepy). Requires env vars in .env.x"""
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
THREAD_FILE = SCRIPT_DIR / "gruener-mars-x-thread.json"
ENV_FILE = SCRIPT_DIR / ".env.x"


def load_env():
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def load_tweets():
    data = json.loads(THREAD_FILE.read_text(encoding="utf-8"))
    tweets = data["tweets"]
    for i, t in enumerate(tweets, 1):
        if len(t) > 280:
            print(f"WARN: Tweet {i} has {len(t)} chars (limit 280)", file=sys.stderr)
    return tweets


def copy_to_clipboard(text: str):
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", f"Set-Clipboard -Value @'\n{text}\n'@"],
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def format_thread_for_clipboard(tweets):
    parts = []
    for i, t in enumerate(tweets, 1):
        parts.append(f"--- POST {i}/7 ---\n{t}")
    return "\n\n".join(parts)


def post_thread(tweets):
    import tweepy

    required = [
        "X_API_KEY",
        "X_API_SECRET",
        "X_ACCESS_TOKEN",
        "X_ACCESS_TOKEN_SECRET",
    ]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)} (see scripts/.env.x.example)")

    client = tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
    )

    reply_to = None
    urls = []
    for i, text in enumerate(tweets, 1):
        resp = client.create_tweet(text=text, in_reply_to_tweet_id=reply_to)
        tweet_id = resp.data["id"]
        reply_to = tweet_id
        url = f"https://x.com/i/web/status/{tweet_id}"
        urls.append(url)
        print(f"Posted {i}/7: {url}")

    return urls


def main():
    load_env()
    tweets = load_tweets()
    clipboard_text = format_thread_for_clipboard(tweets)

    if copy_to_clipboard(clipboard_text):
        print("Thread copied to clipboard.")

    if "--copy-only" in sys.argv:
        return 0

    try:
        urls = post_thread(tweets)
        print("\nThread live:")
        for u in urls:
            print(u)
        return 0
    except Exception as e:
        print(f"X API post failed: {e}", file=sys.stderr)
        print("Thread is in clipboard — paste manually on X.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())