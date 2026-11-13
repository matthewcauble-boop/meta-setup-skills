---
name: meta-test-launch
description: "Launch new Meta (Facebook/Instagram) ads the proven DTC way: give it a set of ads (statics and/or videos, copy, landing URL) and it builds the creative test correctly via the Marketing API: one ABO ad set per concept inside a 'Creative Testing' Sales campaign, $100/day, broad + Advantage+ audience, past customers excluded, optimise Purchase, 7-day click attribution, 4:5 + 9:16 placement versions, Meta's auto-enhancements off, created paused for review. Also gives the review rules (when to kill, graduate and scale). Use when someone says 'run these ads', 'launch these 10 ads on Meta', 'set up a creative test', or 'put this batch live'."
---

# Launch a Meta creative test (the proven structure)

This is the structure a high-volume DTC media-buying agency used to spend ~$3k/day profitably, reverse-
engineered from four months of its change history in a live account. The user hands over ads; you set them
up exactly like this, every time.

## The structure (don't improvise)
```
Campaign  "Creative Testing"   objective Sales, ABO (budget on each ad set, none on the campaign)
 ├─ Ad set "<Product> | <Concept> | Statics | Nov 10"   $100/day   3-10 ads of ONE concept
 ├─ Ad set "<Product> | <Concept> | Videos | Nov 10"    $100/day
 └─ ...one ad set per concept, launched together as a batch
```
**Ad set settings** (all of them, every time): optimise for **Purchase** on the site pixel · bid **Lowest cost**
(no cap, no ROAS goal) · attribution **7-day click + 1-day engaged view** · country list (US) · age **18-65** ·
**Advantage+ audience on**, no interests, no lookalikes · **Advantage+ placements** (no placement edits) ·
**exclude the past-customer list** (uploaded customer CSV audience).

**Ads:** Shop Now button, landing page = the product page (with variant if relevant).
- *Static:* one ad = a **4:5 (1080×1350)** image for feeds **plus** a **9:16 (1080×1920)** version for
  Stories/Reels, joined by placement customisation, with one primary text + one headline (the first in the
  list). If only one size exists, ship it with up to 5 texts/headlines, but ask for the other size.
- *Video:* one ad per video (9:16 preferred), with **up to 5 primary texts and 5 headlines**; Meta rotates them.
- Meta's automatic "Advantage+ creative" enhancements (auto-crop, text overlays, music, image "enhancements",
  CTA rewrites…) are **off**, so the ad runs as designed.
- Ad name = `<file name> | MM/DD/YYYY`. Ad set name = `<Product> | <Concept> | <Statics|Videos> | <Mon D>`.

## How to group the user's ads
- **One concept per ad set.** A concept = one idea in 3-10 variations (5 versions of one static, 6 UGC videos
  on one angle). If the user gives "10 ads", sort them into concepts by idea/angle (ask if unclear) — e.g. 10
  ads might be 2 ad sets of 5. Never dump unrelated ads into one ad set, and never add 1 new ad to an old ad
  set (in the reference account all 3 tries died within days).
- **Launch as a batch** (all concepts the same day), roughly every 3-5 weeks, rather than one ad at a time.
- Meta will give most of the money to one ad in each ad set (median 47%). That's expected; leave the
  starved ads on.

## Running it
1. Fill `brand.json` once per ad account (copy `brand.example.json`): ad account, Page, Instagram account,
   pixel, past-customer audience id(s), budget, countries. Find ids with `meta-doctor`.
2. Write `launch.json` for the batch (copy `launch.example.json`): product, landing URL, copy, and each
   concept's ad files. If the user only gave files and a product, draft 3-5 primary texts and 3-5 headlines
   from the product page and show them for approval first.
3. **Dry run and show the user the plan:**
   `python scripts/launch.py plan launch.json --brand brand.json`
4. On approval: `python scripts/launch.py create launch.json --brand brand.json`
   Everything is created **paused**; a receipt JSON lists every id. The user (or you, if they explicitly say
   "turn them on") switches the ad sets on in Ads Manager, or pass `--activate`.
Never spend or activate without the user's go-ahead. Never touch existing ads or ad sets from this skill.

**First live use on a new account:** run `create` on one small concept and check it in Ads Manager (placements
show the 9:16 on Stories/Reels, enhancements off, exclusion present) before launching a big batch. If Meta
rejects an enhancement key (they rename them), delete it from `ENHANCEMENTS_OFF` in the script.

## After launch: the review rules
Judge each ad on three numbers: **spend so far**, **ROAS over the last 7 days vs the break-even floor**, and
**its share of the ad set's spend last 7 days**. "Floor" = the brand's break-even ROAS (e.g. 3.0).
Look every few days; make moves in batches on review days (mostly Wed-Fri).

| Situation | Action |
|---|---|
| No purchase after **$400** spent | kill the ad |
| $400+ spent and lifetime ROAS < **0.5× floor** | kill |
| Last 7 days spent $150+ at < **0.7× floor** | kill (this is the main rule — judge the last week, not lifetime) |
| Whole ad set has nothing working | switch off the ad set |
| One ad has ≥40% of the ad set's spend and last-7-day ROAS ≥ floor on $100+ | **graduate**: raise the ad set budget **2×** ($100 → $200) and keep the winner where it is |
| Graduated ad set, 7-day ROAS ≥ floor | raise **+40-50%**, about once every 9 days per ad set |
| 7-day ROAS between 0.7× and 1× floor | hold |
| A winner's 7-day ROAS drops under ~0.6-0.7× floor (fatigue) | cut or kill, even if lifetime ROAS is great |
| Budget cut | −33% |
| Promo / sale period | scale up into it, pull budgets back 25-60% when it ends |

Typical timing: first decision on a test ad ~3-4 weeks and ~$450 in. Graduates had ~$1,000 spent at ~1.2×
floor about two weeks in. About 1 in 9 test ads graduates, and those carry about half of all test spend.

**Advanced (rare):** proven winners can also be copied by **post ID** (same post, keeps likes/comments) into
a broad "top performers" ad set with a ROAS-goal bid at ~1.15× floor, and into one stacked retargeting ad set
(site visitors, viewers, add-to-cart, checkout starters, IG/FB engagers, 180 days; exclude 180-day buyers).
Do this as a deliberate restructure, not per launch.

## Report back after creating
Table: ad set → ads → status → daily budget, plus total new daily spend and the receipt file path.
