---
name: meta-pixel-capi
description: "Install and prove Meta pixel + Conversions API tracking on a website or Shopify store: one dataset, browser + server events deduplicated by event_id, domain verified, events prioritized, and verification that does not fool you. Use when setting up tracking, when Meta 'isn't seeing purchases', when ROAS looks wrong, or before scaling spend."
---

# Meta pixel + Conversions API

Tracking is not "installed" until a real purchase shows up in Events Manager **from both the browser and
the server, deduplicated**, with good match quality. Check, report, then fix.

## 1. One dataset
- One dataset (pixel) per website, owned by the brand's Business portfolio and assigned to the ad account.
- Duplicate pixels firing on one site split the data. Find every pixel ID in the page source / tag manager
  and remove the extras.

## 2. Install
**Shopify:** use the official "Facebook & Instagram" sales channel → Data sharing → **Maximum**. That
turns on browser pixel + Conversions API with deduplication, and is the simplest correct setup. Do not
also paste the pixel into the theme or add a second CAPI app (double counting).
**Other sites:** browser pixel (base code + standard events) **and** a server-side CAPI sender (Gateway,
partner integration, or your own server posting to `POST /<dataset_id>/events`).

Server events must include:
- `event_name`, `event_time` (unix seconds), `action_source: "website"`, `event_source_url`
- `event_id` **identical** to the browser event's `eventID` (this is the dedup key)
- `user_data` hashed SHA-256 (lower-cased, trimmed): `em`, `ph`, `fn`, `ln`, `ct`, `st`, `zp`, `country`,
  plus unhashed `client_ip_address`, `client_user_agent`, `fbp` and `fbc` cookies when available
- `custom_data` for Purchase: `value`, `currency`, `content_ids`, `contents`, `order_id`

## 3. Domain and event setup
- Verify the domain (Brand safety → Domains), DNS TXT record preferred.
- Standard events, not custom names, for the funnel: ViewContent, AddToCart, InitiateCheckout, Purchase.

## 4. Verify (the order matters)
1. **Test Events** tab: open the site with the test code, add to cart, check out a test order. Both
   "Browser" and "Server" rows should appear, the second marked *Deduplicated*.
2. **Overview** after 24-48 h: Purchase shows browser + server, **Event Match Quality** ≥ 6 for Purchase.
3. **Reconcile with the store:** Meta-reported purchases for a day vs real orders that day. Meta should
   see most of them; it will never see 100%.

Things that mislead you:
- Purchase events sent with `navigator.sendBeacon` do **not** show in the browser devtools Network tab.
  Use the Meta Pixel Helper extension or Test Events instead of concluding "it doesn't fire".
- Ad blockers and iOS privacy hide browser events; that is why the server side exists.
- "Meta ROAS" is Meta's attribution (default 7-day click / 1-day view) and routinely over-claims versus
  what the store actually received. Judge spend on **MER = total revenue / total ad spend** from the store,
  and use Meta ROAS only to compare ads with each other.

## 5. Report back
| Check | Result |
|---|---|
| Datasets on the site (should be 1) | |
| Browser Purchase seen | |
| Server Purchase seen + deduplicated | |
| Event Match Quality (Purchase) | |
| Domain verified | |
| Meta purchases vs store orders (last 7 days) | |
