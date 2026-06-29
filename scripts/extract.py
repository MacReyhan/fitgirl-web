#!/usr/bin/env python3
"""
FitGirl Link Extractor — GitHub Actions Backend Script
Fetches FuckingFast links from a FitGirl repack page, then uses
undetected-chromedriver to bypass Cloudflare and resolve direct download URLs.
Results are saved as JSON for the web frontend.
"""

import os
import sys
import re
import json
import time
import shutil
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

# ── Configuration ────────────────────────────────────────────────────────────
FITGIRL_URL = os.environ.get("FITGIRL_URL", "")
REQUEST_ID = os.environ.get("REQUEST_ID", "unknown")
SELECTED_INDICES = os.environ.get("SELECTED_INDICES", "")

OUTPUT_DIR = "output"
PUBLISH_DIR = "publish/results"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PUBLISH_DIR, exist_ok=True)


def save_result(data):
    """Save result JSON to both output/ (artifact) and publish/results/ (gh-pages)."""
    filename = f"{REQUEST_ID}.json"
    for directory in [OUTPUT_DIR, PUBLISH_DIR]:
        filepath = os.path.join(directory, filename)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    print(f"[✓] Results saved to {filename}")


def fetch_ff_links(url):
    """Step 1: Scrape the FitGirl page for fuckingfast.co links."""
    print(f"[*] Fetching page: {url}")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    ff_links = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "fuckingfast.co" in href and href not in seen:
            ff_links.append(href)
            seen.add(href)

    print(f"[✓] Found {len(ff_links)} FuckingFast links")
    return ff_links


def extract_direct_links(ff_links):
    """Step 2: Use undetected-chromedriver to resolve direct download URLs."""
    import undetected_chromedriver as uc

    print("[*] Launching headless Chrome via undetected-chromedriver...")

    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    driver = None
    results = []

    try:
        driver = uc.Chrome(options=options, use_subprocess=True)
        total = len(ff_links)

        for i, link in enumerate(ff_links, 1):
            filename = link.split("#")[-1] if "#" in link else link.split("/")[-1]
            print(f"[*] Processing [{i}/{total}]: {filename}")

            entry = {
                "original_url": link,
                "filename": filename,
                "direct_url": None,
                "status": "pending",
            }

            try:
                driver.get(link)
                direct_url = None

                # Wait up to 30 seconds for the window.open redirect
                for attempt in range(30):
                    time.sleep(1)
                    try:
                        page_source = driver.page_source
                        match = re.search(r'window\.open\("([^"]+)"\)', page_source)
                        if match:
                            direct_url = match.group(1)
                            break
                    except Exception:
                        pass

                if direct_url:
                    entry["direct_url"] = direct_url
                    entry["status"] = "success"
                    print(f"    [✓] Resolved: {direct_url[:80]}...")
                else:
                    entry["status"] = "failed"
                    print(f"    [✗] Failed to resolve direct URL")

            except Exception as e:
                entry["status"] = "error"
                entry["error"] = str(e)
                print(f"    [!] Error: {e}")

            results.append(entry)

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

    return results


def main():
    if not FITGIRL_URL:
        save_result({
            "request_id": REQUEST_ID,
            "status": "error",
            "error": "No URL provided",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        sys.exit(1)

    result_data = {
        "request_id": REQUEST_ID,
        "url": FITGIRL_URL,
        "status": "processing",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "links": [],
        "direct_links": [],
    }

    try:
        # Step 1: Fetch links
        ff_links = fetch_ff_links(FITGIRL_URL)

        if not ff_links:
            result_data["status"] = "error"
            result_data["error"] = "No FuckingFast links found on the page"
            save_result(result_data)
            sys.exit(1)

        # Filter by selected indices if provided
        if SELECTED_INDICES.strip():
            indices = [int(x.strip()) for x in SELECTED_INDICES.split(",") if x.strip().isdigit()]
            ff_links = [ff_links[i] for i in indices if 0 <= i < len(ff_links)]
            print(f"[*] Filtered to {len(ff_links)} selected links")

        result_data["links"] = ff_links

        # Step 2: Extract direct links
        extraction_results = extract_direct_links(ff_links)
        result_data["direct_links"] = extraction_results

        # Summary
        success_count = sum(1 for r in extraction_results if r["status"] == "success")
        result_data["status"] = "completed"
        result_data["summary"] = {
            "total": len(extraction_results),
            "success": success_count,
            "failed": len(extraction_results) - success_count,
        }

        print(f"\n[✓] Done! {success_count}/{len(extraction_results)} links resolved successfully.")

    except Exception as e:
        result_data["status"] = "error"
        result_data["error"] = str(e)
        print(f"[!] Fatal error: {e}")

    save_result(result_data)

    # Also copy the frontend files to publish/ so gh-pages always has them
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


if __name__ == "__main__":
    main()
