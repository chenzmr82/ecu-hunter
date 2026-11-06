"""Server-side collector for GitHub Actions (no browser, no laptop).

Only uses URL forms the sites' robots.txt allows (checked 2026-11-06):
  - Ovoko:   /buscar?q=<code>&exact=1[&page=N]   ("Allow: /*?q=*&exact=1"), and /parte/<id> listing pages
  - B-Parts: /es/recambios-auto/search?reference=<code>&page=N   (not disallowed)
  - eBay:    official Browse API only (search pages /sch/ are disallowed). Needs repo secrets
             EBAY_CLIENT_ID and EBAY_CLIENT_SECRET; skipped when they are missing.

Writes raw/<platform>.json, then data/runs/<run>.json via pipeline/normalize.py, and enriches
new Ovoko listings with the seller comment (max COMMENT_CAP pages per run).
Usage: python collector/collect.py
"""
import base64
import datetime as dt
import glob
import json
import os
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
import normalize  # noqa: E402
from common import extract_codes, code_match, load_config  # noqa: E402

CFG = load_config()
T = CFG["target"]
CODES = [T["psa"], T["a3c"], T["hw"]]
UA = "ECUHunter/1.0 (personal parts search; +https://github.com/chenzmr82/ecu-hunter)"
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"})
PAUSE = 1.2
COMMENT_CAP = 25
RAW = os.path.join(ROOT, "raw")


def get(url, **kw):
    r = S.get(url, timeout=30, **kw)
    r.raise_for_status()
    time.sleep(PAUSE)
    return r


def num(s):
    return float(s.replace(".", "").replace(",", ".")) if s else None


# ------------------------------------------------------------------ Ovoko
def ovoko():
    items, counts = {}, {}
    for q in CODES:
        for page in range(1, 13):
            url = "https://ovoko.es/buscar?q=%s&exact=1" % q + ("&page=%d" % page if page > 1 else "")
            html = get(url).text
            if page == 1:
                m = re.search(r"(\d+)\s*piezas encontradas", html)
                counts[q] = int(m.group(1)) if m else None
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select('a[data-testid="item-card-horizontal-container"]')
            if not cards:
                break
            for c in cards:
                href = c.get("href", "")
                if "match_type=partial" in href:
                    continue
                pid = href.split("/")[2].split("-")[0].upper()
                veh = c.select_one('[data-testid="vehicle-details"]')
                seller = c.select_one('[data-testid="seller-info-title"]')
                area = c.select_one('[class*="areaPrice"]') or c
                pm = re.search(r"([\d\.]+,\d{2})\s*€", area.get_text(" "))
                img = c.find("img")
                title = c.find("p")
                items.setdefault(pid, {
                    "query": q,
                    "url": "https://ovoko.es" + href.split("?")[0],
                    "id": pid,
                    "title": title.get_text(strip=True) if title else None,
                    "donor": re.sub(r"\s+", " ", veh.get_text(" ")).replace("Tomado de:", "").strip() if veh else "",
                    "codes": [x.get_text(strip=True) for x in c.select('[data-testid="product-code"]')],
                    "seller": seller.get_text(strip=True) if seller else None,
                    "price": num(pm.group(1)) if pm else None,
                    "img": img.get("src") if img else None,
                })
            if len(cards) < 15:
                break
    return {"platform": "ovoko", "fetched_at": now_iso(), "counts": counts, "items": list(items.values())}


def ovoko_comment(url):
    soup = BeautifulSoup(get(url).text, "html.parser")
    pre = soup.select_one("pre.notes-container")
    return pre.get_text("\n", strip=True) if pre else ""


# ------------------------------------------------------------------ B-Parts
def bparts():
    items, counts = {}, {}
    for q in CODES:
        for page in range(1, 21):
            html = get("https://www.b-parts.com/es/recambios-auto/search?reference=%s&page=%d" % (q, page)).text
            soup = BeautifulSoup(html, "html.parser")
            node = soup.find("script", id="__NEXT_DATA__")
            if not node:
                break
            queries = json.loads(node.string)["props"]["pageProps"]["dehydratedState"]["queries"]
            data = next((x["state"]["data"] for x in queries
                         if isinstance((x.get("state") or {}).get("data"), dict)
                         and isinstance(x["state"]["data"].get("results"), list)), None)
            if not data:
                break
            if page == 1:
                counts[q] = data.get("results_total")
            res = data["results"]
            if not res:
                break
            for r in res:
                r = dict(r)
                r.pop("images", None)
                r.pop("listWithImages", None)
                r["_query"] = q
                items.setdefault(r["sku"], r)
            if page >= (data.get("page_total") or 1):
                break
    return {"platform": "bparts", "fetched_at": now_iso(), "counts": counts, "items": list(items.values())}


# ------------------------------------------------------------------ eBay (official API)
def ebay_api():
    cid, sec = os.environ.get("EBAY_CLIENT_ID"), os.environ.get("EBAY_CLIENT_SECRET")
    if not cid or not sec:
        return None
    tok = requests.post(
        "https://api.ebay.com/identity/v1/oauth2/token",
        headers={"Authorization": "Basic " + base64.b64encode(("%s:%s" % (cid, sec)).encode()).decode(),
                 "Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"},
        timeout=30)
    tok.raise_for_status()
    h = {"Authorization": "Bearer " + tok.json()["access_token"],
         "X-EBAY-C-MARKETPLACE-ID": "EBAY_ES",
         "X-EBAY-C-ENDUSERCTX": "contextualLocation=country=ES",
         "User-Agent": UA}
    items, counts = {}, {}
    for q in CODES + ["A3C032041001"]:
        r = requests.get("https://api.ebay.com/buy/browse/v1/item_summary/search", headers=h, timeout=30,
                         params={"q": q, "limit": 200, "sort": "newlyListed", "filter": "deliveryCountry:ES"})
        r.raise_for_status()
        d = r.json()
        counts[q] = d.get("total")
        for it in d.get("itemSummaries") or []:
            m = re.search(r"/itm/(?:[^/]+/)?(\d+)", it.get("itemWebUrl", ""))
            iid = m.group(1) if m else it.get("legacyItemId") or it.get("itemId")
            ship = None
            so = it.get("shippingOptions") or []
            if so and so[0].get("shippingCost"):
                ship = float(so[0]["shippingCost"]["value"])
            items.setdefault(iid, {
                "query": q, "id": iid, "title": it.get("title"),
                "price": float(it["price"]["value"]) if it.get("price") else None,
                "ship": ship,
                "seller": (it.get("seller") or {}).get("username"),
                "country": (it.get("itemLocation") or {}).get("country"),
                "img": (it.get("image") or {}).get("imageUrl"),
                "created": it.get("itemCreationDate"),
                "condition": it.get("condition"),
                "url": "https://www.ebay.es/itm/%s" % iid,
            })
        time.sleep(PAUSE)
    return {"platform": "ebay", "source": "browse_api", "fetched_at": now_iso(), "counts": counts,
            "items": list(items.values())}


# ------------------------------------------------------------------ helpers
def now_iso():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def madrid_now():
    # Europe/Madrid: CET (+1) / CEST (+2, last Sunday of March to last Sunday of October)
    utc = dt.datetime.now(dt.timezone.utc)
    y = utc.year

    def last_sunday(month):
        d = dt.datetime(y, month, 31, 1, tzinfo=dt.timezone.utc)
        return d - dt.timedelta(days=(d.weekday() + 1) % 7)
    off = 2 if last_sunday(3) <= utc < last_sunday(10) else 1
    return utc.astimezone(dt.timezone(dt.timedelta(hours=off))).replace(microsecond=0)


def previous_offers():
    prev = {}
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "runs", "*.json"))):
        with open(p, encoding="utf-8") as f:
            for o in json.load(f)["offers"]:
                prev["%s:%s" % (o["platform"], o["platform_id"])] = o
    return prev


def main():
    os.makedirs(RAW, exist_ok=True)
    run_at = madrid_now()
    status, files = {}, {}
    for name, fn in [("ovoko", ovoko), ("bparts", bparts), ("ebay", ebay_api)]:
        try:
            raw = fn()
            if raw is None:
                status[name] = "SKIPPED: no eBay API key (repo secrets EBAY_CLIENT_ID / EBAY_CLIENT_SECRET)"
                continue
            path = os.path.join(RAW, name + ".json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(raw, f, ensure_ascii=False)
            files[name] = path
            status[name] = "ok: %d items %s" % (len(raw["items"]), raw.get("counts"))
        except Exception as e:  # keep going; record failure in the run
            status[name] = "FAILED: %s" % e
    print(json.dumps(status, ensure_ascii=False, indent=1))

    run = {"run_at": run_at.isoformat(), "sources": {}, "offers": [], "collector": "github-actions"}
    for name, path in files.items():
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        if name == "ovoko":
            offers = normalize.norm_ovoko(raw)
        elif name == "bparts":
            offers = normalize.norm_bparts(raw)
        else:
            offers = normalize.norm_ebay_api(raw, run_at)
        run["sources"][name] = {"ok": True, "raw_items": len(raw["items"]), "kept": len(offers),
                                "fetched_at": raw.get("fetched_at")}
        run["offers"].extend(offers)
    for name, st in status.items():
        if name not in files:
            run["sources"][name] = {"ok": False, "error": st[:200]}

    # carry forward seller comments already read; read new ones (capped)
    prev = previous_offers()
    todo = []
    for o in run["offers"]:
        k = "%s:%s" % (o["platform"], o["platform_id"])
        p = prev.get(k) or {}
        if p.get("comment_checked"):
            o["comment"] = p.get("comment", "")
            o["comment_checked"] = p["comment_checked"]
        elif o["platform"] == "ovoko":
            missing = code_match(o["codes"], T["a3c"]) != "exact" or code_match(o["codes"], T["hw"]) != "exact"
            short = len(o.get("codes_raw") or []) < CFG["cross_ref_list_min_codes"]
            if missing and short:
                todo.append(o)
    todo.sort(key=lambda o: -sum(c in o["codes"] for c in CODES))  # most promising first
    for o in todo[:COMMENT_CAP]:
        try:
            o["comment"] = ovoko_comment(o["url"])
            o["comment_checked"] = run_at.isoformat()
        except Exception as e:
            print("comment failed", o["url"], e)
    for o in run["offers"]:
        if o.get("comment"):
            o["codes"] += [c for c in extract_codes(o["comment"]) if c not in o["codes"]]
            o["codes_raw"] = (o.get("codes_raw") or []) + ["comment"]
            o["text"] = (o.get("text") or "") + " " + o["comment"]

    os.makedirs(os.path.join(ROOT, "data", "runs"), exist_ok=True)
    out = os.path.join(ROOT, "data", "runs", run_at.strftime("%Y-%m-%dT%H-%M") + ".json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(run, f, ensure_ascii=False, indent=1)
    print("wrote", out, {k: v.get("kept") for k, v in run["sources"].items()},
          "comments read:", min(len(todo), COMMENT_CAP))
    if not any(v.get("ok") for v in run["sources"].values()):
        sys.exit("no source succeeded")


if __name__ == "__main__":
    main()
