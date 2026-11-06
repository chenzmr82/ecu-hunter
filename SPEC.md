# ECU Hunter — build spec

Daily hunt for a used engine ECU for the owner's Peugeot 3008, published as a page on GitHub Pages that the garage can open each morning.

Status: draft v1, 2026-11-06. Platform findings below were checked by hand on that date.

---

## 1. The target

| Field | Value | Source |
|---|---|---|
| Car | Peugeot 3008 Allure PureTech 130, 1199 cc petrol, 96 kW, first reg. 29-07-2020, type code M/R/HNSU-C1P100 | Registration document |
| Engine family | PureTech 1.2 turbo; HNS = EB2ADTS (130 hp) | Type code + listings |
| ECU | Continental VD56.1, "CMM VD56 CEM0" | ECU label |
| PSA part no. | **9834609880** (main search key) | ECU label |
| Hardware no. | 9815023380 | ECU label |
| Continental no. | A3C0320410001 (sometimes listed as "A3C0320410001VD561") | ECU label |
| Our unit's serial | 201138929 | ECU label |

The same 9834609880 ECU is used across Stellantis 1.2 PureTech cars, so donors can be any of these: Peugeot 208 II / 2008 II / 308 / 3008 / 5008 / Rifter, Citroën C3 / C3 Aircross / C4 SpaceTourer / C5 Aircross, DS 3 Crossback, Opel Corsa F / Crossland X / Grandland X.

### Garage constraints (from the owner, 2026-11-06)
- "the garage did say they can clone the ECU, but still say that they can only do it with non-immopbalizer locked units."
- No price ceiling.
- Must ship to Spain.
- 2026-11-06, from the mechanic, in the owner's words: "My mechanic told me the AC and the HW serial numbers must be exact". Read as: **A3C0320410001** (Continental number) and **HW 9815023380** must both match exactly. ("AC" taken to mean the A3C number. To confirm with the owner.)

---

## 2. Matching rules

Each listing gets one **match grade**:

**Hard rule (mechanic): A3C0320410001 and HW 9815023380 must both be exact.** Codes are normalised before comparing (spaces, dashes and suffixes such as "VD561" removed, upper-cased); after that, the match must be character-for-character. A near miss (a missing or extra digit, e.g. "A3C032041001") is never treated as a match.

| Grade | Rule | Shown? |
|---|---|---|
| A: confirmed | A3C0320410001 **and** 9815023380 both exact, proven by the label photo (read by the job) or both stated in the listing as this unit's own codes (not inside a pasted cross-reference list) | Yes, top |
| N: needs check | 9834609880 listed, but A3C or HW is missing, only in a cross-reference list, or a near miss | Yes, separate section, with an "ask for label photo" button |
| X: excluded | A different A3C or HW (e.g. A3C0600500001 seen on Ovoko), a diesel donor, or 9834609880 only inside a long list of 30+ pasted codes with no label photo | Hidden; behind a toggle |

Within grade A, sort by best total price; donors with engine HNS / EB2ADTS / 96 kW (130 hp) get a "same engine" tag.

The template message asks for the label photo as well as the immobiliser status:
> Hola, ¿pueden enviar una foto de la etiqueta de la centralita (códigos A3C y HW)? ¿Está bloqueada por inmovilizador o está virgen? Gracias.

**Immobiliser status** gets its own field, because listings rarely state it:

- `unlocked`: the listing says *virgen / virgin / IMMO off / desbloqueada / reset*. Highlighted.
- `kit`: sold as a set (ECU + ignition lock/BSI + key). Shown with a "kit" tag. **Open question for the garage**: is a kit useful now that the BSI has already been replaced?
- `locked`: the listing says locked or coded to the donor. **Excluded**, per the garage.
- `unknown`: nothing stated (most listings). Shown with the "ask seller" button (template message above).

**Accident donor**: flagged if the listing or donor photos show the car was in an accident. Shown, not excluded, because an accident does not damage an ECU in the engine bay by default. This can be changed in `config.yaml`.

---

## 3. The three requirements

### 3.1 Tried and returned
- `data/tried.yaml` is edited by hand, either in the GitHub web editor or through a GitHub Issue with the `tried` label (the daily job reads both).
- Fields: `serial`, `platform`, `seller`, `seller_sku`, `listing_url`, `donor` (model/year/km), `bought`, `returned`, `reason`, `notes`.
- A listing is matched to a tried unit in this order: ECU serial (read from the label photo) → seller SKU → seller + donor mileage + year. A match greys the row and adds "Already tried, returned DD/MM: reason", even when the unit is relisted on another platform.

### 3.2 Same unit on several platforms (de-duplication)
Yards cross-list their stock, often at very different prices. Seen on 2026-11-06:
- **Saumina SKU SAU115896** (Opel Crossland X 2020 ECU + lock kit): Ovoko **€379 + €24.94 shipping** vs eBay.es **€576.64 + €23.74**. Same unit, about €200 apart.
- **Peugeot 208, 74,102 km donor, codes 9834609880 / 9815023380 / A3C0320410001**: Ovoko (Desguaces Boyacá, €272 + €9.06) and B-Parts (BP38377662M11, €308.68 including shipping and VAT). Very likely the same unit.

Units are grouped in this order:
1. ECU serial from the label photo (definitive)
2. Seller SKU found in the listing (definitive)
3. Same seller + same donor mileage + same donor year (strong)
4. Same donor mileage + model + codes, seller unknown (likely; marked "probable duplicate")

Each unit is **one row**. Every platform offer is shown inside it with its own price, shipping, fees, warranty and link, sorted by total price delivered to Spain.

### 3.3 New in the last 24/48 h
- Each unit stores `first_seen`, plus `first_seen` for each offer.
- Badges: **NEW** (< 24 h), **RECENT** (24–48 h), **PRICE ↓** (an offer dropped since yesterday), **GONE** (not seen for 2 runs; kept greyed for 7 days, then archived).
- The top of the page has a "New today" strip.

---

## 4. Sources

| Platform | Stock found 2026-11-06 for 9834609880 | Terms | How the job reads it |
|---|---|---|---|
| **Ovoko** (ovoko.es) | 129 listings (dismantled parts) | 14-day free returns with free return shipping; some listings add a 1-year warranty (filter "Solo con garantía de 1 año"); a service fee is added at checkout | Its robots.txt blocks automated search and its terms forbid copying content. **v1**: one low-volume search per code per day from the owner's own browser (`collector/ovoko.js`, ~1 page/s). **Planned**: switch to Ovoko "Guardar búsqueda" email alerts → Gmail once the owner creates the saved search. |
| **B-Parts** (b-parts.com/es) | 79 listings | 12-month warranty on all parts; 14-day returns; price includes shipping and VAT | Search URL `/es/recambios-auto/search?reference=9834609880`, sorted by "más recientes". Works in a normal browser; blocked for simple fetchers. To test from GitHub Actions/Playwright in build step 1. |
| **eBay** (.es, plus .fr/.de/.it shipping to ES) | 73 on ebay.es | Per seller; Spanish professional yards (CAT) are legally bound to give ≥ 12 months | **eBay Browse API** (official, free developer key) with a ship-to-ES filter. Backup: eBay saved-search emails → Gmail. |
| Opisto (FR) | not yet tested | Per-yard terms (French CAT network) | Test in build step 1 |
| Recambioverde (ES) | not yet tested (search URL returned 404) | Spanish CAT network | Test in build step 1 |
| Stellantis Sustainera | Sells used Stellantis parts through Ovoko and eBay | — | Covered by the Ovoko and eBay sources |
| Wallapop / Milanuncios | Optional | Private sellers have no warranty; a professional seller still owes 12 months | robots.txt blocks automated search; off by default |

Legal background (Spain, per RACE): a used part bought from a professional seller or CAT must carry at least 12 months' guarantee, with a CAT certificate on the invoice. A private sale only gives a 6-month hidden-defects claim. If the garage buys the part, the purchase is business-to-business and the consumer rules may not apply. Check who is named on the invoice. (Not legal advice.)

---

## 5. Architecture (GitHub)

As built (v1, 2026-11-06):
```
ecu-hunter/                      (GitHub repo; GitHub Pages serves /site)
├── README.md · SPEC.md · AGENT.md (daily procedure for the scheduled task)
├── config.json                  target codes, thresholds, ask-seller message
├── collector/                   browser scripts, one per platform (same-origin, low volume)
│   ├── ovoko.js  bparts.js  ebay.js
├── pipeline/
│   ├── common.py                code extraction, exact/near matching, immobiliser wording
│   ├── normalize.py             raw → data/runs/<run>.json (common offer schema)
│   ├── build.py                 all runs + tried + overrides → site/data/units.json (stateless)
│   └── test_pipeline.py
├── data/
│   ├── runs/2026-11-06T13-30.json   one file per daily run (the only history; first run = baseline)
│   ├── tried.yaml               hand-edited: units already tried/returned
│   └── overrides.yaml           hand-edited facts: seller replies, label photos, forced (un)merges
├── site/  index.html · app.js · style.css   (units.json built in CI)
└── .github/workflows/pages.yml  on push: tests → build → deploy Pages
```
NEW/RECENT on the first (baseline) run uses eBay's own listing date; from the second run on, it uses first-seen.

### Who runs the daily job
Some steps need judgment, not just a script: reading the label in a photo, telling a real code match from a pasted cross-reference list, spotting "virgen" or "bloqueada" in free text, and judging probable duplicates. So the daily job is a **Claude scheduled task at 07:00 Madrid time** that:
1. Reads new Ovoko and eBay alert emails from a Gmail label (`ecu-hunter`).
2. Calls the eBay API, then runs the B-Parts search (and Opisto/Recambioverde if enabled).
3. Opens each new or changed listing, reads the label photo, grades it, and classifies its immobiliser status.
4. Runs the de-duplication and tried matching, then writes `units.json`, `offers.jsonl` and the run log.
5. Commits to the repo. `pages.yml` redeploys the page.
6. Optionally emails the owner (and the garage) a 5-line summary with the page link: new units, price drops, anything graded A.

The scripted parts (adapters, merge, page) are plain Python/JS in the repo, so they can also run from GitHub Actions (`collect.yml`) if a source turns out to be scriptable.

If a source fails, the page still builds and the run log says "B-Parts not checked today". Each source is also capped at a few page loads per day.

---

## 6. Data model

```yaml
Offer:
  platform: ovoko | bparts | ebay | opisto | recambioverde
  url, platform_id, seller, seller_sku
  price_eur, shipping_eur_to_es, fees_eur, total_eur
  warranty_months, return_days, free_returns: bool
  codes: [..]            # main code first
  codes_main: str        # the code the seller lists as the part number
  donor: {make, model, year, engine_code, kw, fuel, km, vin_partial}
  label_photo_url, serial_from_label
  immobiliser: unlocked | kit | locked | unknown
  accident_donor: bool | null
  a3c_read, hw_read      # as read from label photo or listing
  a3c_exact, hw_exact: bool
  codes_source: label_photo | listing_own | cross_ref_list
  grade: A | N | X
  first_seen, last_seen, price_history: [{date, total_eur}]

Unit:
  unit_id                # serial | sku | hash(seller, km, year)
  dedupe_confidence: definitive | strong | probable
  offers: [Offer]        # sorted by total_eur
  best_total_eur
  badges: [NEW, RECENT, PRICE_DOWN, GONE, TRIED]
  tried: {returned, reason} | null
```

---

## 7. The page

- **Header**: target codes, last run time, and which sources were checked today.
- **"New today" strip**: units with NEW or RECENT badges.
- **Main table**, one row per unit: label photo thumbnail · grade · donor (model, year, engine, km) · immobiliser tag · best total price to Spain · offer chips per platform (price + warranty + return days, each linking out) · badges.
- **Filters**: hide "needs check" · hide unknown immobiliser · ≥ 12-month warranty only · show excluded (grade X).
- Each row shows the A3C and HW codes as read, with a ✓ when both are exact.
- Tried units are greyed with the return reason. Gone units are shown faded for 7 days.
- Spanish/English toggle (Spanish by default, for the garage). Works on a phone.
- GitHub Pages sites are public. The page holds only public listing data: no plate, no full VIN, no names.

---

## 8. Build plan

1. **Test the sources**: confirm the eBay API key, Ovoko saved search + Gmail label, and B-Parts access from GitHub Actions vs the browser. Test Opisto and Recambioverde.
2. **Adapters + schema**: normalise offers from the working sources; first full snapshot.
3. **Merge**: de-duplication, tried matching, badges; check against today's known duplicates (SAU115896; the 74,102 km 208).
4. **Page**: static site + Pages deploy.
5. **Schedule**: Claude scheduled task at 07:00; first live run; check the run log.
6. **Hand-over**: send the link to the garage; the owner seeds `tried.yaml`.

---

## 9. Open questions

1. **Units already tried and returned**: platform, seller, rough date, why returned, and label photos or serials if available. This seeds `tried.yaml`.
2. **Garage, about cloning**: does their clone copy the full software (any exact A3C + HW unit is fine, whatever the donor's power), or only the immobiliser data (then prefer "same engine" HNS / 130 hp donors)?
3. **Garage, about kits**: are ECU + lock/BSI + key kits useful now that the BSI has been replaced?
4. **GitHub**: which account/repo name? (No GitHub account is linked to this session yet.)
5. **eBay developer key**: the owner registers at developer.ebay.com (free); the key is stored as a GitHub secret, never in the repo.
6. **Daily email**: to the owner only, or to the garage as well? Which address?
