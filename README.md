# ECU Hunter

Daily search for a used Continental VD56.1 engine ECU (**A3C0320410001 / HW 9815023380 / PSA 9834609880**)
for a Peugeot 3008 1.2 PureTech 130, across Ovoko, B-Parts and eBay, shown as one page:
**https://chenzmr82.github.io/ecu-hunter/**

## How it runs (no laptop needed)
- Every morning at **06:39 Madrid time** (07:39 in summer) the **Daily ECU search** workflow runs on GitHub:
  it collects listings, saves a run in `data/runs/`, rebuilds and republishes the page, and adds a comment to
  the **Informe diario ECU** issue (GitHub emails you on each comment).
- Run it now: **Actions → Daily ECU search → Run workflow**.
- Editing `data/tried.yaml` or `data/overrides.yaml` republishes the page within a minute.

## Sources
| Platform | How | Notes |
|---|---|---|
| Ovoko | exact-code search `?q=<code>&exact=1` + listing pages for seller comments | the form its robots.txt allows; max 25 comment pages/day |
| B-Parts | reference search | prices include shipping and VAT; 12-month warranty |
| eBay | **official Browse API** | eBay's robots.txt blocks search pages, so eBay needs a free API key (below). Until then eBay shows the 6 Nov snapshot only |

### Turning on eBay
1. Create a free account at https://developer.ebay.com and a **Production** keyset (App ID = client ID, Cert ID = client secret).
2. In this repo: **Settings → Secrets and variables → Actions → New repository secret**:
   `EBAY_CLIENT_ID` and `EBAY_CLIENT_SECRET`.
3. The next daily run picks them up.

## Marking units
- **Already tried a unit?** Add it to [`data/tried.yaml`](data/tried.yaml) (pencil icon → commit). It's greyed out even if relisted elsewhere.
- **Learned something from a seller?** Add it to [`data/overrides.yaml`](data/overrides.yaml).

## Grades
**A** = A3C and HW both exact in the listing or seller comment · **N** = needs a label photo · **X** = excluded
(diesel, other engine, other A3C, locked, or code only inside a pasted list of dozens of references).

Code: `collector/collect.py` (daily, server-side) · `pipeline/normalize.py` · `pipeline/build.py` ·
`pipeline/report.py` · `site/`. Design: [`SPEC.md`](SPEC.md). Manual/browser collection: [`AGENT.md`](AGENT.md).
