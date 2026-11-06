# ECU Hunter

Daily search for a used Continental VD56.1 engine ECU (**A3C0320410001 / HW 9815023380 / PSA 9834609880**)
for a Peugeot 3008 1.2 PureTech 130, across Ovoko, B-Parts and eBay, shown as one page:
**https://chenzmr82.github.io/ecu-hunter/**

## How it runs (no laptop needed)
- The **Daily ECU search** workflow runs on GitHub every morning at **06:39 Madrid time** (07:39 in summer):
  it collects listings, saves a run in `data/runs/`, rebuilds and republishes the page, and adds a comment to
  the **Informe diario ECU** issue (GitHub emails you on each comment).
- **Status (6 Nov 2026): paused** (Actions → Daily ECU search → *Enable workflow*). Re-enable it once the eBay key is in.
- Run it by hand: **Actions → Daily ECU search → Run workflow**.
- Editing `data/tried.yaml` or `data/overrides.yaml` republishes the page within a minute.
- The page currently shows the **6 Nov snapshot** of all three platforms.

## Sources
| Platform | Daily from GitHub? | Notes |
|---|---|---|
| eBay | **Yes, once the API key is added** (below) | official Browse API; eBay's robots.txt blocks search pages for bots |
| Ovoko | **No**: answers `403 Forbidden` to servers | planned: Ovoko saved-search email alerts, read from Gmail by a cloud task |
| B-Parts | **No**: answers `403 Forbidden` to servers | ask for professional/data access |

`collector/collect.py` still contains the Ovoko and B-Parts readers (robots-allowed URL forms only); they report
`FAILED: 403` in the run log and the run carries on with the sources that work.

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
