# ECU Hunter

Daily search for a used Continental VD56.1 engine ECU (**A3C0320410001 / HW 9815023380 / PSA 9834609880**)
for a Peugeot 3008 1.2 PureTech 130, across Ovoko, B-Parts and eBay, shown as one page.

- **Page**: GitHub Pages (Settings → Pages).
- **Already tried a unit?** Add it to [`data/tried.yaml`](data/tried.yaml) (pencil icon → commit). The page greys it out, even if it's relisted elsewhere.
- **Learned something from a seller?** Add it to [`data/overrides.yaml`](data/overrides.yaml).

How it works: `collector/*.js` read the search results → `pipeline/normalize.py` makes one run file in
`data/runs/` → `pipeline/build.py` grades, de-duplicates and flags new/tried units into `site/data/units.json`
→ the workflow publishes `site/`. Daily procedure: [`AGENT.md`](AGENT.md). Design: [`SPEC.md`](SPEC.md).

Grades: **A** = A3C and HW both exact in the listing · **N** = needs a label photo · **X** = excluded
(diesel, other engine, other A3C, locked, or code only inside a pasted list of dozens of references).
