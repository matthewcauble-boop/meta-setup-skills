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
The numbers live in **`playbook.json`**, exported from a learner that watches the agency's real changes every night
(kills, raises, cuts, launches) and fits the thresholds that match them. Read it rather than trusting the table
below if they differ; `data_through` says how fresh it is.

Run the read-only review whenever the user asks how the test is going (or on Wed-Fri review days):
`python scripts/launch.py review --brand brand.json`   (needs `floor_roas` = break-even Meta ROAS in brand.json)
It lists every live ad in the testing campaign with spend, purchases, lifetime and 7-day ROAS vs floor, and its
share of the ad set, and says KILL / GRADUATE / RAISE / hold with the reason. It changes nothing: show the user
the moves and make them only on their go-ahead.

| Situation (defaults from playbook.json) | Action |
|---|---|
| No purchase after **$400** | kill the ad |
| Live under 7 days | hold (except the no-purchase rule) |
| $400+ spent and lifetime ROAS < **0.5× floor** | kill |
| Last 7 days $150+ at < **0.7× floor** | kill — the main rule: judge the last week, not lifetime |
| Whole ad set has nothing working | switch off the ad set |
| One ad has ≥40% of the ad set's spend and last 7 days ≥ floor on $100+ | **graduate**: double the ad set ($100 → $200), keep the winner where it is |
| Already graduated, still ≥ floor | raise **+50%** (+40-50%), at most about once every 9 days per ad set |
| Carrying the ad set at 0.7-1× floor | hold |
| Cut | −33% |
| Promo period | scale up into it; pull budgets back 25-60% when it ends |

Typical timing: first decision on a test ad ~4 weeks and ~$450 in; graduates first raised ~11 days in at ~$730
spent. Most test ads get killed; the few graduates carry about half of all test spend.

**Advanced (rare):** proven winners can also be copied by **post ID** (same post, keeps likes/comments) into
a broad "top performers" ad set with a ROAS-goal bid at ~1.15× floor, and into one stacked retargeting ad set
(site visitors, viewers, add-to-cart, checkout starters, IG/FB engagers, 180 days; exclude 180-day buyers).
Do this as a deliberate restructure, not per launch.

## Report back after creating
Table: ad set → ads → status → daily budget, plus total new daily spend and the receipt file path.
