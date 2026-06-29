#!/usr/bin/env python3
"""
FitGirl Link Extractor — GitHub Actions Backend
Fetches FuckingFast links then uses undetected-chromedriver to bypass
Cloudflare and resolve direct download URLs.
"""

import os, sys, re, json, time, requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

FITGIRL_URL = os.environ.get("FITGIRL_URL", "")
REQUEST_ID = os.environ.get("REQUEST_ID", "unknown")
SELECTED_INDICES = os.environ.get("SELECTED_INDICES", "")

os.makedirs("results", exist_ok=True)


def save(data):
    with open(f"results/{REQUEST_ID}.json", "w") as f:
        json.dump(data, f, indent=2)


def fetch_links(url):
    print(f"[*] Fetching: {url}")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    seen, links = set(), []
    for a in soup.find_all("a", href=True):
        h = a["href"]
        if "fuckingfast.co" in h and h not in seen:
            links.append(h)
            seen.add(h)
    print(f"[✓] Found {len(links)} links")
    return links


def extract(ff_links):
    import undetected_chromedriver as uc

    print("[*] Launching headless Chrome...")
    opts = uc.ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")

    driver = None
    results = []

    try:
        driver = uc.Chrome(options=opts, use_subprocess=True)

        for i, link in enumerate(ff_links, 1):
            fn = link.split("#")[-1] if "#" in link else link.split("/")[-1]
            print(f"[*] [{i}/{len(ff_links)}] {fn}")
            entry = {"original_url": link, "filename": fn, "direct_url": None, "status": "pending"}

            try:
                driver.get(link)
                direct = None
                for _ in range(30):
                    time.sleep(1)
                    try:
                        m = re.search(r'window\.open\("([^"]+)"\)', driver.page_source)
                        if m:
                            direct = m.group(1)
                            break
                    except:
                        pass

                if direct:
                    entry["direct_url"] = direct
                    entry["status"] = "success"
                    print(f"    [✓] {direct[:80]}...")
                else:
                    entry["status"] = "failed"
                    print(f"    [✗] Could not resolve")
            except Exception as e:
                entry["status"] = "error"
                entry["error"] = str(e)
                print(f"    [!] {e}")

            results.append(entry)
    finally:
        if driver:
            try: driver.quit()
            except: pass

    return results


def main():
    if not FITGIRL_URL:
        save({"request_id": REQUEST_ID, "status": "error", "error": "No URL",
              "timestamp": datetime.now(timezone.utc).isoformat()})
        sys.exit(1)

    data = {"request_id": REQUEST_ID, "url": FITGIRL_URL, "status": "processing",
            "timestamp": datetime.now(timezone.utc).isoformat(), "direct_links": []}

    try:
        ff = fetch_links(FITGIRL_URL)
        if not ff:
            data["status"] = "error"
            data["error"] = "No FuckingFast links found"
            save(data)
            sys.exit(1)

        if SELECTED_INDICES.strip():
            idx = [int(x.strip()) for x in SELECTED_INDICES.split(",") if x.strip().isdigit()]
            ff = [ff[i] for i in idx if 0 <= i < len(ff)]

        results = extract(ff)
        data["direct_links"] = results
        ok = sum(1 for r in results if r["status"] == "success")
        data["status"] = "completed"
        data["summary"] = {"total": len(results), "success": ok, "failed": len(results) - ok}
        print(f"\n[✓] {ok}/{len(results)} resolved")
    except Exception as e:
        data["status"] = "error"
        data["error"] = str(e)

    save(data)


if __name__ == "__main__":
    main()
