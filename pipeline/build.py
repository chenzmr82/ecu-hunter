"""Build site/data/units.json from all runs + tried.yaml + overrides.yaml.

Stateless: everything (first seen, price drops, gone) is derived from data/runs/*.json,
so re-running gives the same result. Run: python pipeline/build.py
"""
import datetime as dt
import glob
import json
import os
import re
import unicodedata

import yaml

from common import ROOT, load_config, code_match, classify_immobiliser, ACCIDENT_RE, DIESEL_RE, KIT_RE

CFG = load_config()
T = CFG["target"]
GRADE_RANK = {"A": 0, "N": 1, "X": 2}


def load_yaml(name):
    p = os.path.join(ROOT, "data", name)
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_runs():
    runs = []
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "runs", "*.json"))):
        with open(p, encoding="utf-8") as f:
            r = json.load(f)
        r["_at"] = dt.datetime.fromisoformat(r["run_at"])
        runs.append(r)
    runs.sort(key=lambda r: r["_at"])
    return runs


def key(o):
    return "%s:%s" % (o["platform"], o["platform_id"])


def make_of(o):
    t = (o.get("donor") or {}).get("text") or o.get("title") or ""
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().upper()
    for mk in ["PEUGEOT", "CITROEN", "OPEL", "VAUXHALL", "DS", "TOYOTA", "FIAT"]:
        if re.search(r"\b" + mk + r"", t):
            return "OPEL" if mk == "VAUXHALL" else mk
    return None


def seller_stem(o):
    s = re.sub(r"[^a-z]", "", (o.get("seller") or "").lower())
    return s[:6] or None


# ---------------------------------------------------------------- history
def collect_offers(runs):
    """Latest version of every offer + its history across runs."""
    offers = {}
    for r in runs:
        for o in r["offers"]:
            k = key(o)
            h = offers.get(k)
            if h is None:
                h = offers[k] = {"first_seen": r["run_at"], "seen_runs": [], "prices": []}
            h["latest"] = o
            h["last_seen"] = r["run_at"]
            h["seen_runs"].append(r["run_at"])
            p = o.get("total_eur") if o.get("total_eur") is not None else o.get("price_eur")
            if p is not None and (not h["prices"] or h["prices"][-1]["eur"] != p):
                h["prices"].append({"at": r["run_at"], "eur": p})
    return offers


def missed_runs(runs, platform, last_seen):
    """How many later successful runs of this platform did not contain the offer."""
    n = 0
    last = dt.datetime.fromisoformat(last_seen)
    for r in runs:
        if r["_at"] <= last:
            continue
        if (r["sources"].get(platform) or {}).get("ok"):
            n += 1
    return n


# ---------------------------------------------------------------- grading
def grade_offer(o, ov):
    codes = list(o.get("codes") or [])
    codes += [c for c in (ov.get("codes_add") or []) if c not in codes]
    cross = len(o.get("codes_raw") or codes) >= CFG["cross_ref_list_min_codes"] and not ov.get("codes_add")
    d = o.get("donor") or {}
    text = " ".join(filter(None, [o.get("text"), d.get("text"), o.get("engine_code") or ""]))
    reasons = []
    if d.get("fuel") == "diesel" or DIESEL_RE.search(text):
        return "X", ["diésel"], codes, cross
    if d.get("cc") and d["cc"] not in (1199, 1200):
        return "X", ["motor %s cm3" % d["cc"]], codes, cross
    other_a3c = [c for c in codes if c.startswith("A3C") and code_match([c], T["a3c"]) is None]
    a3c = code_match(codes, T["a3c"])
    if other_a3c and a3c != "exact":
        return "X", ["otro A3C: " + other_a3c[0]], codes, cross
    if cross:
        if a3c == "exact":
            return "N", ["códigos solo en lista cruzada"], codes, cross
        return "X", ["lista cruzada de %d códigos" % len(o.get("codes_raw") or codes)], codes, cross
    return None, reasons, codes, cross  # decided at unit level


# ---------------------------------------------------------------- union-find
class UF:
    def __init__(self, keys):
        self.p = {k: k for k in keys}
        self.why = {}

    def find(self, k):
        while self.p[k] != k:
            self.p[k] = self.p[self.p[k]]
            k = self.p[k]
        return k

    def union(self, a, b, why):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra
            self.why.setdefault(ra, []).append(why)
            if rb in self.why:
                self.why[ra] += self.why.pop(rb)


def dedupe(offers, overrides):
    keys = list(offers)
    uf = UF(keys)
    lat = {k: offers[k]["latest"] for k in keys}
    blocked = {frozenset(x) for x in (overrides.get("not_same_unit") or [])}

    def u(a, b, why, conf):
        if frozenset((a, b)) in blocked:
            return
        uf.union(a, b, {"why": why, "confidence": conf, "pair": [a, b]})

    # 1. manual
    for grp in overrides.get("same_unit") or []:
        for b in grp[1:]:
            if grp[0] in uf.p and b in uf.p:
                u(grp[0], b, "manual", "definitive")
    # 2. serials (from overrides: label photo read)
    by_serial = {}
    for k, ov in (overrides.get("offers") or {}).items():
        if k in uf.p and ov.get("serial"):
            by_serial.setdefault(str(ov["serial"]), []).append(k)
    for ks in by_serial.values():
        for b in ks[1:]:
            u(ks[0], b, "número de serie", "definitive")
    # 3. seller SKU: an Ovoko stock id quoted in another listing
    ovoko_ids = {lat[k]["platform_id"]: k for k in keys if lat[k]["platform"] == "ovoko"}
    for k in keys:
        if lat[k]["platform"] == "ovoko":
            continue
        for tok in re.findall(r"\b[A-Z]{2,4}\d{3,7}\b", (lat[k].get("title") or "").upper()):
            if tok in ovoko_ids:
                u(ovoko_ids[tok], k, "SKU del vendedor %s" % tok, "definitive")
    # 4. same internal reference number + same seller family
    refs = {}
    for k in keys:
        st = seller_stem(lat[k])
        if not st:
            continue
        for tok in set(re.findall(r"(?<![\d])\d{5,8}(?!\d)", lat[k].get("title") or "")):
            refs.setdefault((st, tok), []).append(k)
    for (st, tok), ks in refs.items():
        for b in ks[1:]:
            u(ks[0], b, "misma referencia interna %s" % tok, "strong")
    # 5. same donor mileage + make, across platforms
    bykm = {}
    for k in keys:
        d = lat[k].get("donor") or {}
        km = d.get("km")
        if km and km >= 1000 and km < 900000:
            bykm.setdefault((make_of(lat[k]), km), []).append(k)
    for (mk, km), ks in bykm.items():
        if not mk:
            continue
        for b in ks[1:]:
            a = ks[0]
            if lat[a]["platform"] == lat[b]["platform"]:
                continue
            ya, yb = lat[a]["donor"].get("year"), lat[b]["donor"].get("year")
            if ya and yb and abs(ya - yb) > 1:
                continue
            u(a, b, "mismo kilometraje %s km" % format(km, ",").replace(",", "."), "probable")
    groups = {}
    for k in keys:
        groups.setdefault(uf.find(k), []).append(k)
    return groups, uf.why


# ---------------------------------------------------------------- tried
def tried_match(unit_offers, serials, tried):
    for t in tried:
        for k, o in unit_offers:
            if t.get("platform") and t.get("platform_id") and k == "%s:%s" % (t["platform"], t["platform_id"]):
                return t
            if t.get("serial") and str(t["serial"]) in serials:
                return t
            km = (o.get("donor") or {}).get("km")
            if t.get("seller") and t.get("km") and o.get("seller") and km:
                if t["seller"].lower()[:6] in o["seller"].lower() and int(t["km"]) == km:
                    return t
    return None


# ---------------------------------------------------------------- garage ticks (Google Sheet)
def load_garage_ticks():
    """Keys ticked 'Probada por el taller' on the page. Best effort: empty if unreachable."""
    url = CFG.get("tested_endpoint")
    if not url:
        return {}
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=20) as r:
            return {x["key"]: x for x in json.load(r).get("tested", [])}
    except Exception as e:  # offline build, sandbox, Google hiccup
        print("garage ticks not loaded:", e)
        return {}


# ---------------------------------------------------------------- main
def main():
    runs = load_runs()
    if not runs:
        raise SystemExit("no runs in data/runs")
    now = runs[-1]["_at"]
    baseline = runs[0]["run_at"]
    overrides = load_yaml("overrides.yaml")
    ov_offers = overrides.get("offers") or {}
    tried = (load_yaml("tried.yaml") or {}).get("tried") or []
    garage = load_garage_ticks()

    offers = collect_offers(runs)
    groups, why = dedupe(offers, overrides)

    units = []
    for root, ks in groups.items():
        items = []
        for k in ks:
            h = offers[k]
            o = dict(h["latest"])
            ov = ov_offers.get(k) or {}
            g, reasons, codes, cross = grade_offer(o, ov)
            gone = missed_runs(runs, o["platform"], h["last_seen"]) >= CFG["gone_after_missed_runs"]
            o.update({
                "key": k, "first_seen": h["first_seen"], "last_seen": h["last_seen"],
                "prices": h["prices"], "gone": gone, "codes_all": codes, "cross_ref": cross,
                "offer_grade": g, "offer_reasons": reasons, "override": ov or None,
                "price_down": len(h["prices"]) > 1 and h["prices"][-1]["eur"] < h["prices"][-2]["eur"],
            })
            items.append((k, o))

        live = [o for _, o in items if not o["gone"]] or [o for _, o in items]
        # unit-level codes: union of each listing's own codes
        own = []
        for o in live:
            if not o["cross_ref"]:
                own += [c for c in o["codes_all"] if c not in own]
        ovs = [o["override"] or {} for o in live]
        a3c = code_match(own, T["a3c"])
        hw = code_match(own, T["hw"])
        psa = code_match(own, T["psa"])
        if any(v.get("codes_verified") for v in ovs):
            a3c = hw = "exact"
        x_reasons = [r for o in live if o["offer_grade"] == "X" for r in o["offer_reasons"]]
        text = " ".join(filter(None, [o.get("text") for o in live] + [v.get("note", "") for v in ovs]))
        imm = next((v["immobiliser"] for v in ovs if v.get("immobiliser")), None) or classify_immobiliser(text)

        if live and all(o["offer_grade"] == "X" for o in live):
            grade, reasons = "X", sorted(set(x_reasons))
        elif imm == "locked":
            grade, reasons = "X", ["bloqueada por inmovilizador"]
        elif a3c == "exact" and hw == "exact":
            grade, reasons = "A", []
        else:
            grade = "N"
            reasons = []
            if a3c != "exact":
                reasons.append("A3C casi igual (verificar)" if a3c == "near" else "falta A3C")
            if hw != "exact":
                reasons.append("HW casi igual (verificar)" if hw == "near" else "falta HW")
            reasons += [r for o in live if o["offer_grade"] == "N" for r in o["offer_reasons"]]

        # donor summary from the most informative listing
        def info(o):
            d = o.get("donor") or {}
            return sum(1 for f in ("year", "kw", "km") if d.get(f)) + (1 if o.get("engine_code") else 0)
        best = max(live, key=info)
        d = best.get("donor") or {}
        engine = next((o.get("engine_code") for o in live if o.get("engine_code")), None)
        same_engine = any(
            (o.get("donor") or {}).get("kw") == T["same_kw"]
            or any(e in (o.get("engine_code") or "") for e in T["same_engine"])
            or re.search(r"\b13[01] ?(hp|cv)\b|puretech 130|thp 130", o.get("text") or "", re.I)
            for o in live)
        serials = {str(v["serial"]) for v in ovs if v.get("serial")}
        t = tried_match(items, serials, tried)

        first_seen = min((o["first_seen"] for _, o in items), key=dt.datetime.fromisoformat)
        listed = [o["listed_at"] for _, o in items if o.get("listed_at")]
        listed_at = min(listed, key=dt.datetime.fromisoformat) if listed else None
        fresh_ref = None
        if dt.datetime.fromisoformat(first_seen) > dt.datetime.fromisoformat(baseline):
            fresh_ref = first_seen
        elif listed_at:
            fresh_ref = listed_at
        badges = []
        if fresh_ref:
            age_h = (now - dt.datetime.fromisoformat(fresh_ref)).total_seconds() / 3600
            if age_h <= CFG["new_hours"]:
                badges.append("NEW")
            elif age_h <= CFG["recent_hours"]:
                badges.append("RECENT")
        if any(o["price_down"] for o in live):
            badges.append("PRICE_DOWN")
        all_gone = all(o["gone"] for _, o in items)
        if all_gone:
            badges.append("GONE")
            last = max((o["last_seen"] for _, o in items), key=dt.datetime.fromisoformat)
            if (now - dt.datetime.fromisoformat(last)).days > CFG["gone_keep_days"]:
                continue
        if t:
            badges.append("TRIED")

        def sort_price(o):
            p = o.get("total_eur") if o.get("total_eur") is not None else o.get("price_eur")
            return (o["gone"], p if p is not None else 1e9)
        offers_out = []
        for o in sorted([o for _, o in items], key=sort_price):
            offers_out.append({k2: o.get(k2) for k2 in (
                "key", "platform", "platform_id", "url", "title", "seller", "ships_from", "non_eu",
                "price_eur", "shipping_eur", "total_eur", "price_note", "warranty_months", "return_days",
                "free_returns", "listed_at", "first_seen", "last_seen", "gone", "price_down", "prices", "image")})
            offers_out[-1]["codes"] = o["codes_all"]
            offers_out[-1]["cross_ref"] = o["cross_ref"]
        live_out = [o for o in offers_out if not o["gone"]] or offers_out
        totals = [o["total_eur"] if o["total_eur"] is not None else o["price_eur"] for o in live_out
                  if (o["total_eur"] if o["total_eur"] is not None else o["price_eur"]) is not None]
        conf = None
        if len(items) > 1:
            order = {"definitive": 0, "strong": 1, "probable": 2}
            ws = why.get(root, [])
            conf = max((w["confidence"] for w in ws), key=lambda c: order[c]) if ws else "probable"
        units.append({
            "id": root,
            "grade": grade,
            "reasons": reasons,
            "a3c": a3c or "missing",
            "hw": hw or "missing",
            "psa": psa or "missing",
            "code_score": sum(1 for c in (a3c, hw, psa) if c == "exact"),
            "codes_seen": own,
            "immobiliser": imm,
            "kit": bool(KIT_RE.search(text)) or imm == "kit",
            "accident": bool(ACCIDENT_RE.search(text)),
            "same_engine": bool(same_engine),
            "donor": {"text": d.get("text"), "year": d.get("year"), "kw": d.get("kw"), "km": d.get("km"),
                      "engine_code": engine, "make": make_of(best)},
            "image": next((o["image"] for o in offers_out if o.get("image")), None),
            "offers": offers_out,
            "platforms": sorted({o["platform"] for o in live_out}),
            "best_total_eur": min(totals) if totals else None,
            "best_total_known": any(o["total_eur"] is not None for o in live_out),
            "first_seen": first_seen,
            "listed_at": listed_at,
            "badges": badges,
            "tried": t,
            "tested_by_garage": next((garage[k] for k in ks if k in garage), None),
            "dedupe": {"confidence": conf, "why": sorted({w["why"] for w in why.get(root, [])})} if conf else None,
            "notes": [v["note"] for v in ovs if v.get("note")],
            "seller_comments": [{"platform": o["platform"], "text": o["comment"][:400]} for o in live if o.get("comment")],
        })

    units.sort(key=lambda u: (GRADE_RANK[u["grade"]], bool(u["tried"]), "GONE" in u["badges"], -u["code_score"],
                              0 if ("NEW" in u["badges"] or "RECENT" in u["badges"]) else 1,
                              u["best_total_eur"] if u["best_total_eur"] is not None else 1e9))
    last = runs[-1]
    out = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "last_run_at": last["run_at"],
        "baseline_run_at": baseline,
        "runs": len(runs),
        "sources": last["sources"],
        "target": T,
        "ask_seller_message_es": CFG["ask_seller_message_es"],
        "counts": {g: sum(1 for u in units if u["grade"] == g) for g in "ANX"},
        "units": units,
    }
    os.makedirs(os.path.join(ROOT, "site", "data"), exist_ok=True)
    with open(os.path.join(ROOT, "site", "data", "units.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("units:", len(units), out["counts"])


if __name__ == "__main__":
    main()
