#!/usr/bin/env python3
import os, sys, re, json, time, requests, subprocess
from bs4 import BeautifulSoup
from datetime import datetime, timezone

URL = os.environ.get("FITGIRL_URL", "")
RID = os.environ.get("REQUEST_ID", "unknown")
SEL = os.environ.get("SELECTED_INDICES", "")
os.makedirs("results", exist_ok=True)


def save(d):
    with open(f"results/{RID}.json", "w") as f:
        json.dump(d, f, indent=2)


def get_chrome_version():
    """Detect installed Chrome's major version."""
    try:
        out = subprocess.check_output(["google-chrome", "--version"], text=True).strip()
        # e.g. "Google Chrome 149.0.7827.155"
        match = re.search(r"(\d+)\.", out)
        if match:
            ver = int(match.group(1))
            print(f"[*] Detected Chrome version: {ver} ({out})")
            return ver
    except Exception as e:
        print(f"[!] Could not detect Chrome version: {e}")
    return None


def fetch(url):
    print(f"[*] Fetching: {url}")
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}, timeout=15)
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

    chrome_ver = get_chrome_version()

    print("[*] Launching headless Chrome...")
    opts = uc.ChromeOptions()
    for a in ["--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]:
        opts.add_argument(a)

    driver = None
    results = []

    try:
        # Pass version_main to match the installed Chrome
        driver_kwargs = {
            "options": opts,
            "use_subprocess": True,
        }
        if chrome_ver:
            driver_kwargs["version_main"] = chrome_ver

        driver = uc.Chrome(**driver_kwargs)

        for i, lk in enumerate(ff_links, 1):
            fn = lk.split("#")[-1] if "#" in lk else lk.split("/")[-1]
            print(f"[*] [{i}/{len(ff_links)}] {fn}")
            e = {"original_url": lk, "filename": fn, "direct_url": None, "status": "pending"}

            try:
                driver.get(lk)
                for _ in range(30):
                    time.sleep(1)
                    try:
                        m = re.search(r'window\.open\("([^"]+)"\)', driver.page_source)
                        if m:
                            e["direct_url"] = m.group(1)
                            e["status"] = "success"
                            break
                    except:
                        pass
                else:
                    e["status"] = "failed"

                if e["status"] == "success":
                    print(f"    [✓] {e['direct_url'][:80]}...")
                else:
                    print(f"    [✗] Could not resolve")
            except Exception as x:
                e["status"] = "error"
                e["error"] = str(x)
                print(f"    [!] {x}")

            results.append(e)
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

    return results


def main():
    if not URL:
        save({"request_id": RID, "status": "error", "error": "No URL",
              "timestamp": datetime.now(timezone.utc).isoformat()})
        sys.exit(1)

    d = {"request_id": RID, "url": URL, "status": "processing",
         "timestamp": datetime.now(timezone.utc).isoformat(), "direct_links": []}

    try:
        ff = fetch(URL)
        if not ff:
            d["status"] = "error"
            d["error"] = "No FuckingFast links found"
            save(d)
            sys.exit(1)

        if SEL.strip():
            idx = [int(x) for x in SEL.split(",") if x.strip().isdigit()]
            ff = [ff[i] for i in idx if 0 <= i < len(ff)]

        r = extract(ff)
        d["direct_links"] = r
        ok = sum(1 for x in r if x["status"] == "success")
        d["status"] = "completed"
        d["summary"] = {"total": len(r), "success": ok, "failed": len(r) - ok}
        print(f"\n[✓] {ok}/{len(r)} resolved")
    except Exception as x:
        d["status"] = "error"
        d["error"] = str(x)

    save(d)


if __name__ == "__main__":
    main()
