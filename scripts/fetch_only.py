#!/usr/bin/env python3
"""
Quick fetch script — scrapes the FitGirl repack page and returns
available FuckingFast links (no Selenium required).
"""

import os
import sys
import json
import shutil
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

FITGIRL_URL = os.environ.get("FITGIRL_URL", "")
REQUEST_ID = os.environ.get("REQUEST_ID", "unknown")

PUBLISH_DIR = "publish/results"
os.makedirs(PUBLISH_DIR, exist_ok=True)


def main():
    result = {
        "request_id": REQUEST_ID,
        "url": FITGIRL_URL,
        "type": "fetch",
        "status": "processing",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "links": [],
    }

    try:
        if not FITGIRL_URL:
            raise ValueError("No URL provided")

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(FITGIRL_URL, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract page title
        title_tag = soup.find("h1", class_="entry-title")
        if title_tag:
            result["game_title"] = title_tag.get_text(strip=True)

        ff_links = []
        seen = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "fuckingfast.co" in href and href not in seen:
                filename = href.split("#")[-1] if "#" in href else href.split("/")[-1]
                ff_links.append({"url": href, "filename": filename})
                seen.add(href)

        result["links"] = ff_links
        result["status"] = "completed"
        print(f"[✓] Found {len(ff_links)} FuckingFast links")

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        print(f"[!] Error: {e}")

    # Save
    filepath = os.path.join(PUBLISH_DIR, f"{REQUEST_ID}.json")
    with open(filepath, "w") as f:
        json.dump(result, f, indent=2)

    # Copy frontend files
    if os.path.exists("docs"):
        for item in os.listdir("docs"):
            src = os.path.join("docs", item)
            dst = os.path.join("publish", item)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
            elif os.path.isdir(src) and item != "results":
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)

    print(f"[✓] Results saved")


if __name__ == "__main__":
    main()
