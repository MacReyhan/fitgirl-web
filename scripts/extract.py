#!/usr/bin/env python3
import os, sys, re, json, time, requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

URL = os.environ.get("FITGIRL_URL", "")
RID = os.environ.get("REQUEST_ID", "unknown")
SEL = os.environ.get("SELECTED_INDICES", "")
os.makedirs("results", exist_ok=True)

def save(d):
    with open(f"results/{RID}.json", "w") as f: json.dump(d, f, indent=2)

def fetch(url):
    r = requests.get(url, headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    seen, out = set(), []
    for a in soup.find_all("a", href=True):
        h = a["href"]
        if "fuckingfast.co" in h and h not in seen: out.append(h); seen.add(h)
    return out

def extract(links):
    import undetected_chromedriver as uc
    opts = uc.ChromeOptions()
    for a in ["--headless=new","--no-sandbox","--disable-dev-shm-usage","--disable-gpu"]: opts.add_argument(a)
    drv = uc.Chrome(options=opts, use_subprocess=True)
    res = []
    try:
        for i, lk in enumerate(links, 1):
            fn = lk.split("#")[-1] if "#" in lk else lk.split("/")[-1]
            print(f"[{i}/{len(links)}] {fn}")
            e = {"original_url":lk,"filename":fn,"direct_url":None,"status":"pending"}
            try:
                drv.get(lk)
                for _ in range(30):
                    time.sleep(1)
                    try:
                        m = re.search(r'window\.open\("([^"]+)"\)', drv.page_source)
                        if m: e["direct_url"]=m.group(1); e["status"]="success"; break
                    except: pass
                else: e["status"]="failed"
            except Exception as x: e["status"]="error"; e["error"]=str(x)
            res.append(e)
    finally:
        try: drv.quit()
        except: pass
    return res

def main():
    d = {"request_id":RID,"url":URL,"status":"processing","timestamp":datetime.now(timezone.utc).isoformat(),"direct_links":[]}
    try:
        ff = fetch(URL)
        if SEL.strip():
            idx = [int(x) for x in SEL.split(",") if x.strip().isdigit()]
            ff = [ff[i] for i in idx if 0<=i<len(ff)]
        r = extract(ff)
        d["direct_links"]=r
        ok=sum(1 for x in r if x["status"]=="success")
        d["status"]="completed"; d["summary"]={"total":len(r),"success":ok,"failed":len(r)-ok}
    except Exception as x:
        d["status"]="error"; d["error"]=str(x)
    save(d)

if __name__=="__main__": main()
