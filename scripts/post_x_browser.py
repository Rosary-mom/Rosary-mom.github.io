#!/usr/bin/env python3
"""Post X thread via browser (requires logged-in Chrome session)."""
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

THREAD_FILE = Path(__file__).resolve().parent / "gruener-mars-x-thread.json"
CHROME_DATA = Path.home() / "AppData/Local/Google/Chrome/User Data"


def load_tweets():
    return json.loads(THREAD_FILE.read_text(encoding="utf-8"))["tweets"]


def post_thread(page, tweets):
    page.goto("https://x.com/compose/tweet", wait_until="domcontentloaded", timeout=60000)
    time.sleep(3)

    if "login" in page.url.lower():
        raise RuntimeError("Not logged in to X — open Chrome, log in as @RosaryParish, retry.")

    editor = page.locator('[data-testid="tweetTextarea_0"]').first
    editor.wait_for(state="visible", timeout=30000)

    reply_url = None
    for i, text in enumerate(tweets, 1):
        if i > 1:
            page.goto(reply_url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(2)
            reply_btn = page.locator('[data-testid="reply"]').first
            reply_btn.wait_for(state="visible", timeout=20000)
            reply_btn.click()
            time.sleep(1)
            editor = page.locator('[data-testid="tweetTextarea_0"]').first
            editor.wait_for(state="visible", timeout=20000)

        editor.click()
        editor.fill(text)
        time.sleep(0.5)
        post_btn = page.locator('[data-testid="tweetButton"], [data-testid="tweetButtonInline"]').last
        post_btn.wait_for(state="visible", timeout=10000)
        if post_btn.is_disabled():
            raise RuntimeError(f"Tweet {i} post button disabled — text may exceed limit.")
        post_btn.click()
        time.sleep(4)

        # capture latest status link from notification or profile - use compose redirect
        status_links = page.locator('a[href*="/status/"]')
        if status_links.count() > 0:
            href = status_links.first.get_attribute("href")
            reply_url = f"https://x.com{href}" if href.startswith("/") else href
        else:
            # fallback: stay on home and find latest tweet - fragile
            page.goto("https://x.com/RosaryParish", wait_until="domcontentloaded")
            time.sleep(2)
            href = page.locator('article a[href*="/status/"]').first.get_attribute("href")
            reply_url = f"https://x.com{href}" if href and href.startswith("/") else href

        print(f"Posted {i}/7 → {reply_url}")

    return reply_url


def main():
    tweets = load_tweets()
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(CHROME_DATA),
            channel="chrome",
            headless=False,
            args=["--profile-directory=Default"],
            no_viewport=True,
        )
        page = context.pages[0] if context.pages else context.new_page()
        try:
            url = post_thread(page, tweets)
            print(f"\nThread complete. Last post: {url}")
            return 0
        except Exception as e:
            print(f"Browser post failed: {e}", file=sys.stderr)
            return 1
        finally:
            context.close()


if __name__ == "__main__":
    sys.exit(main())