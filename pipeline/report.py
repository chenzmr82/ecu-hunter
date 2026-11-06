"""Write a short daily report (Markdown) from site/data/units.json -> report.md.
Posted as a comment on the 'Informe diario' issue by the daily workflow, so GitHub emails it."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "https://chenzmr82.github.io/ecu-hunter/"


def price(u):
    return ("%.2f €" % u["best_total_eur"]) if u.get("best_total_eur") is not None else "precio ¿?"


def line(u):
    o = u["offers"][0]
    d = u["donor"]
    bits = [b for b in [d.get("engine_code"), d.get("kw") and "%s kW" % d["kw"],
                        d.get("km") and "{:,} km".format(d["km"]).replace(",", ".")] if b]
    plats = ", ".join("[%s](%s)" % (x["platform"], x["url"]) for x in u["offers"][:4] if not x.get("gone"))
    imm = {"unlocked": " · **VIRGEN**", "kit": " · kit", "locked": " · bloqueada"}.get(u["immobiliser"], "")
    return "- **%s** %s — %s%s%s · %s" % (u["grade"], (d.get("text") or "")[:70], price(u),
                                          (" · " + " · ".join(bits)) if bits else "", imm, plats)


def main():
    with open(os.path.join(ROOT, "site", "data", "units.json"), encoding="utf-8") as f:
        d = json.load(f)
    units = [u for u in d["units"] if u["grade"] != "X" and not u.get("tried") and not u.get("tested_by_garage")]
    new = [u for u in units if set(u["badges"]) & {"NEW"}]
    drops = [u for u in units if "PRICE_DOWN" in u["badges"]]
    virgin = [u for u in units if u["immobiliser"] == "unlocked"]
    src = ", ".join("%s %s" % (k, ("✓ %s" % v.get("kept")) if v.get("ok") else "✗") for k, v in d["sources"].items())
    out = ["**%s** · A: %d · por verificar: %d · fuentes: %s" % (
        d["last_run_at"][:16].replace("T", " "), d["counts"]["A"], d["counts"]["N"], src)]
    out.append("\n**Nuevas hoy (%d)**" % len(new))
    out += [line(u) for u in sorted(new, key=lambda u: (u["grade"], u.get("best_total_eur") or 1e9))[:25]] or ["- ninguna"]
    if drops:
        out.append("\n**Bajadas de precio (%d)**" % len(drops))
        out += [line(u) for u in drops[:10]]
    if virgin:
        out.append("\n**Virgen / desbloqueada (%d)**" % len(virgin))
        out += [line(u) for u in virgin[:10]]
    out.append("\n[Ver la página](%s)" % PAGE)
    with open(os.path.join(ROOT, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
