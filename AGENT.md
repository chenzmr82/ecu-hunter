# Daily run: instructions for the scheduled Claude task

Goal: every morning, collect today's ECU listings, add them as a new run, and publish the page.
Target: A3C0320410001 + HW 9815023380 (PSA 9834609880). Both A3C and HW must be exact (mechanic's rule).
Garage rule: no immobiliser-locked units. Must ship to Spain.

## 1. Collect (built-in browser on the owner's computer)
For each platform, open its site in the built-in browser and run the matching script with the JavaScript tool:

| Platform | Open first | Script |
|---|---|---|
| Ovoko | https://ovoko.es/ | `collector/ovoko.js` |
| B-Parts | https://www.b-parts.com/es | `collector/bparts.js` |
| eBay | https://www.ebay.es/ | `collector/ebay.js` |

Each returns a JSON string. Save it as `raw/<platform>.json` in the working copy. (If the result is too large
to show inline, the harness saves it to a file; extract the JSON string from that file.)
If a site fails, retry once, then record it as failed (step 2) and carry on. Never bypass a block or captcha.

## 2. Normalise into a run
```
python pipeline/normalize.py --run-at <now, ISO with +01:00> \
  --ovoko raw/ovoko.json --bparts raw/bparts.json --ebay raw/ebay.json [--failed <platform>]
python pipeline/build.py
```
This writes `data/runs/<YYYY-MM-DDTHH-MM>.json` and a local `site/data/units.json` to check.

## 3. Look closer at new candidates (max 15 listing pages per day)
For units that are **NEW/RECENT** and graded **A** or **N** with `psa` or `a3c` present:
- open the listing page; read the seller comment and look at the label photo;
- if the label/comment shows the codes, add `codes_add` (and `codes_verified: true` only when the label photo
  clearly shows both A3C0320410001 and 9815023380) under `offers:` in `data/overrides.yaml`;
- record any immobiliser wording (`immobiliser: unlocked|locked|kit`) and a short `note` quoting the seller.

## 4. Publish
Commit `data/runs/<id>.json` and any change to `data/overrides.yaml` to `main`.
The `Build and publish page` workflow rebuilds `units.json` and deploys GitHub Pages.
`raw/` is never committed.

## 5. Report
Send the owner a short summary: new units today (grade, donor, best price, link), price drops,
anything with `immobiliser: unlocked`, and which sources failed. Include the page link.
