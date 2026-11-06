"""Turn raw platform snapshots (from collector/*.js) into one run file of common offers.

Usage:
  python pipeline/normalize.py --run-at 2026-11-06T13:30:00+01:00 \
      --ovoko raw/ovoko.json --bparts raw/bparts.json --ebay raw/ebay.json
Writes data/runs/<run-id>.json. A platform that was not checked is simply omitted;
pass --failed ebay to record that a platform was tried and failed.
"""
import argparse
import datetime as dt
import json
import os
import re

from common import ROOT, extract_codes, code_match, load_config, ECU_WORDS, DIESEL_RE

CFG = load_config()
T = CFG["target"]
TARGETS = [T["psa"], T["hw"], T["a3c"]]


def num(s):
    if s is None:
        return None
    s = str(s).replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def relevant(codes, title):
    """Keep exact target codes; keep one-edit near misses only when the listing is an ECU."""
    if any(c in codes for c in TARGETS):
        return True
    near = any(code_match(codes, t) == "near" for t in TARGETS)
    return near and bool(ECU_WORDS.search(title or ""))


def donor_from_text(text):
    text = text or ""
    year = re.search(r"\b(19[89]\d|20[0-3]\d)\b", text)
    kw = re.search(r"(\d{2,3})\s?kW", text, re.I)
    hp = re.search(r"\((\d{2,3}) hp\)|(\d{2,3})\s?CV\b", text, re.I)
    km = re.search(r"([\d\.]{3,9})\s?km\b", text, re.I)
    cc = re.search(r"(\d{4})\s?cm3", text)
    fuel = None
    if DIESEL_RE.search(text):
        fuel = "diesel"
    elif re.search(r"h[ií]brid", text, re.I):
        fuel = "hybrid"
    elif re.search(r"gasolina|petrol|benzin|essence|puretech|\bthp\b|\bvti\b", text, re.I):
        fuel = "petrol"
    kw_v = int(kw.group(1)) if kw else None
    hp_v = int(hp.group(1) or hp.group(2)) if hp else None
    if kw_v is None and hp_v:
        kw_v = round(hp_v * 0.7355)
    km_v = int(km.group(1).replace(".", "")) if km else None
    return {
        "text": re.sub(r"\s+", " ", text).strip(),
        "year": int(year.group(1)) if year else None,
        "kw": kw_v,
        "cc": int(cc.group(1)) if cc else None,
        "km": km_v,
        "fuel": fuel,
    }


def norm_ovoko(raw):
    out = []
    for it in raw["items"]:
        codes = extract_codes(it.get("codes"))
        if not relevant(codes, it.get("title")):
            continue
        out.append({
            "platform": "ovoko",
            "platform_id": it["id"],
            "url": it["url"],
            "title": it.get("title"),
            "seller": (it.get("seller") or "").strip() or None,
            "price_eur": it.get("price"),
            "shipping_eur": None,
            "price_note": "+ envío + tarifa de servicio",
            "total_eur": None,
            "warranty_months": None,
            "return_days": 14,
            "free_returns": True,
            "codes": codes,
            "codes_raw": it.get("codes"),
            "donor": donor_from_text(it.get("donor")),
            "engine_code": None,
            "image": it.get("img"),
            "listed_at": None,
            "text": " ".join(filter(None, [it.get("title"), it.get("donor"), " ".join(it.get("codes") or [])])),
        })
    return out


def norm_bparts(raw):
    out = []
    for it in raw["items"]:
        ref = it.get("reference") or ""
        codes = extract_codes(ref)
        if not relevant(codes, it.get("part")):
            continue
        veh = " ".join(filter(None, [it.get("car_brand"), it.get("car_model"), it.get("car_version")]))
        d = donor_from_text(veh)
        try:
            d["km"] = int(float(it.get("mileage"))) if it.get("mileage") not in (None, "", "-") else None
        except (TypeError, ValueError):
            d["km"] = None
        d["year"] = None  # B-Parts only gives the model's production range, not the donor year
        price = (it.get("pricing") or {}).get("price_final")
        out.append({
            "platform": "bparts",
            "platform_id": it["sku"],
            "url": "https://www.b-parts.com/es/recambios-auto/%s/%s" % (it.get("category_slug"), it.get("slug")),
            "title": it.get("part"),
            "seller": None,
            "seller_code": (re.search(r"([A-Z]\d+)$", it["sku"]) or [None, None])[1] if it.get("sku") else None,
            "price_eur": price,
            "shipping_eur": 0.0,
            "price_note": "envío e IVA incluidos",
            "total_eur": price,
            "warranty_months": it.get("warranty"),
            "return_days": 14,
            "free_returns": None,
            "codes": codes,
            "codes_raw": [x.strip() for x in ref.split("|") if x.strip()],
            "donor": d,
            "engine_code": it.get("engine_code"),
            "image": it.get("main_image"),
            "listed_at": None,
            "text": " ".join(filter(None, [it.get("part"), veh, it.get("engine_code") or "", ref])),
        })
    return out


MONTHS = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6, "jul": 7,
          "ago": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dic": 12}
COUNTRIES = ("España|Francia|Alemania|Italia|Portugal|Polonia|Lituania|Letonia|Estonia|Países Bajos|"
             "Bélgica|Luxemburgo|Reino Unido|Irlanda|Eslovaquia|República Checa|Chequia|Rumanía|Bulgaria|"
             "Hungría|Austria|Eslovenia|Croacia|Grecia|Dinamarca|Suecia|Finlandia|Noruega|Suiza|"
             "Ucrania|Turquía|Serbia|China|Estados Unidos|Japón")
NON_EU = {"Reino Unido", "Noruega", "Suiza", "Ucrania", "Turquía", "Serbia", "China", "Estados Unidos", "Japón"}
DATE_RE = re.compile(r"(ene|feb|mar|abr|may|jun|jul|ago|sept|sep|oct|nov|dic)-(\d{1,2}) (\d{2}):(\d{2})")


def ebay_date(s, run_at):
    m = DATE_RE.search(s or "")
    if not m:
        return None
    month, day = MONTHS[m.group(1)], int(m.group(2))
    d = dt.datetime(run_at.year, month, day, int(m.group(3)), int(m.group(4)), tzinfo=run_at.tzinfo)
    if d > run_at + dt.timedelta(hours=12):  # eBay omits the year; a future date means last year
        d = d.replace(year=run_at.year - 1)
    return d.isoformat()


def norm_ebay(raw, run_at):
    out = []
    for it in raw["items"]:
        line = " ".join(it.get("lines") or []).replace("\xa0", " ")
        title = (it.get("title") or line.split("Se abre en")[0]).replace("Se abre en una nueva ventana o pestaña", "").strip()
        title = title.split("Se abre en")[0].strip()
        # only the part after the title carries price/shipping/seller
        rest = line.split("Se abre en una nueva ventana o pestaña", 1)[-1]
        if re.search(r"servicio|service|fichero|software", title, re.I):
            continue
        codes = extract_codes(title)
        if not relevant(codes, title):
            continue
        price = num((re.search(r"([\d\.]+,\d{2}) EUR", rest) or [None, None])[1])
        if re.search(r"(Env[ií]o|Entrega) gratis", rest):
            ship = 0.0
        else:
            ship = num((re.search(r"\+ ?([\d\.]+,\d{2}) EUR de env[ií]o", rest) or [None, None])[1])
        m = re.search(r"\d{2}:\d{2}([\w\.\-]+)\s+\d{1,3}(,\d)?% positivo", rest)
        if not m:
            m = re.search(r"([a-z0-9][\w\.\-]*)\s+\d{1,3}(,\d)?% positivo", rest)
        seller = m.group(1) if m else None
        frm = (re.search(r"desde (" + COUNTRIES + ")", rest) or [None, None])[1]
        out.append({
            "platform": "ebay",
            "platform_id": it["id"],
            "url": "https://www.ebay.es/itm/%s" % it["id"],
            "title": title,
            "seller": seller,
            "ships_from": frm or "España",
            "non_eu": (frm or "España") in NON_EU,
            "price_eur": price,
            "shipping_eur": ship,
            "price_note": None if ship is not None else "+ envío",
            "total_eur": round(price + ship, 2) if price is not None and ship is not None else None,
            "warranty_months": None,
            "return_days": None,
            "free_returns": "Devoluciones gratuitas" in rest,
            "codes": codes,
            "codes_raw": codes,
            "donor": donor_from_text(title),
            "engine_code": None,
            "image": it.get("img") if (it.get("img") or "").startswith("https://i.ebayimg") else None,
            "listed_at": ebay_date(rest, run_at),
            "text": title,
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-at", required=True)
    ap.add_argument("--ovoko")
    ap.add_argument("--bparts")
    ap.add_argument("--ebay")
    ap.add_argument("--failed", nargs="*", default=[])
    a = ap.parse_args()
    run_at = dt.datetime.fromisoformat(a.run_at)
    run = {"run_at": run_at.isoformat(), "sources": {}, "offers": []}
    for name, path, fn in [("ovoko", a.ovoko, norm_ovoko), ("bparts", a.bparts, norm_bparts), ("ebay", a.ebay, None)]:
        if not path:
            continue
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        offers = norm_ebay(raw, run_at) if name == "ebay" else fn(raw)
        run["sources"][name] = {"ok": True, "raw_items": len(raw.get("items", [])), "kept": len(offers),
                                "fetched_at": raw.get("fetched_at")}
        run["offers"].extend(offers)
    for name in a.failed:
        run["sources"][name] = {"ok": False}
    os.makedirs(os.path.join(ROOT, "data", "runs"), exist_ok=True)
    rid = run_at.strftime("%Y-%m-%dT%H-%M")
    path = os.path.join(ROOT, "data", "runs", rid + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(run, f, ensure_ascii=False, indent=1)
    print(path, {k: v.get("kept") for k, v in run["sources"].items()})


if __name__ == "__main__":
    main()
