---
name: meta-reporting
description: "Pull read-only Meta ad performance with the Marketing API Insights endpoint and turn it into decisions: spend, purchases, ROAS by account, campaign, ad set and ad, over the right date range and attribution window, reconciled against the store (MER). Use when asked 'how are our Meta ads doing', 'what did we spend this month', 'which ads are winning', or for a daily/weekly ads check-in."
---

# Meta reporting (read-only)

Never change anything in the ad account from this skill. Read, summarize, recommend.

## Queries
Base: `GET https://graph.facebook.com/v21.0/act_<AD_ACCOUNT_ID>/insights` with the token.

| Want | Params |
|---|---|
| This month total | `fields=spend,impressions,clicks,actions,action_values,purchase_roas&date_preset=this_month` |
| Custom range | `time_range={"since":"2026-01-01","until":"2026-01-31"}` |
| By day | add `time_increment=1` |
| By campaign / ad set / ad | `level=campaign` (or `adset`, `ad`) plus `fields=campaign_name,...` |
| Only delivering ads | `filtering=[{"field":"ad.effective_status","operator":"IN","value":["ACTIVE"]}]` |
| Breakdown | `breakdowns=age,gender` or `publisher_platform,platform_position` |

- Purchases: in `actions` / `action_values` use `action_type` = `omni_purchase` (or
  `offsite_conversion.fb_pixel_purchase`). Pick one and say which.
- Page through `paging.next` until it is absent. Large `level=ad` pulls: use async jobs
  (`POST .../insights` then poll the report run).
- Dates follow the **ad account's time zone**, not yours.
- Today's numbers are partial and attribution keeps filling in for days; don't judge yesterday finally.

## How to read it
1. **MER first:** store revenue for the period ÷ total ad spend (all platforms). This is the number that
   pays the bills. Compare with the brand's break-even MER (1 ÷ contribution margin before ads).
2. **Meta ROAS second:** useful to rank ads and ad sets against each other, not to judge total
   profitability; it usually over-claims.
3. Spend concentration: which few ads take most of the budget, and are they the ones converting.
4. Fatigue: frequency rising with CTR falling and CPA rising on the same ad over 7-14 days.
5. Learning: ad sets with fewer than ~50 conversions a week stay unstable; don't over-read them.

## Output
- One-line headline: spend, store revenue, MER vs break-even, trend vs last period.
- Table of top campaigns/ad sets: spend, purchases, CPA, ROAS, change vs prior period.
- 2-4 specific recommendations (pause X, scale Y by 20%, refresh creative Z), each with the number that
  justifies it. Leave the actual changes to a human or an explicit approval.
