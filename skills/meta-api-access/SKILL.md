---
name: meta-api-access
description: "Get durable Graph / Marketing API access to a brand's Meta assets: create the app, the system user, assign assets, generate a non-expiring token with the right permissions, verify it, and store it safely. Also explains Standard vs Advanced Access limits (what an unreviewed app can and cannot do). Use when a script, agent or integration needs to read or manage ads, Pages, Instagram, pixels or catalogs."
---

# Meta API access (system user + token)

Use a **system user token** owned by the business, never a personal user token. Personal tokens die when
the person changes their password, logs out everywhere, leaves the company, or after 60 days.

## 1. The app
- developers.facebook.com → My Apps → Create app → type **Business**, and attach it to the brand's
  Business portfolio. Reuse an existing business app if there is one.
- App settings → Basic: add a Privacy Policy URL and app icon, then switch the app to **Live**.
  Ads created through an app still in Development mode fail ("creative post was created by an app that is
  in development mode").
- Add the products you need: Marketing API (ads), plus Instagram / Messenger / Pages only if used.

## 2. The system user
- Business Settings → Users → System users → Add. Use an **Admin** system user only if it must manage
  other assets' settings; otherwise Employee.
- **Give the system user a role on the app** (Business Settings → Accounts → Apps → the app → Add people
  → the system user → Develop/Manage app). Skipping this is why "Generate token" shows *"No permissions
  available"*.

## 3. Assign assets to the system user
Business Settings → System users → the user → Assign assets:
| Asset | Permission to tick | Why |
|---|---|---|
| Ad account | Manage campaigns (add "View performance" for read-only) | create/edit ads, read insights |
| Page | Ads, plus Content / Messages / Community activity only if needed | ads use the Page as identity |
| Instagram account | Ads (+ Content / Messages if posting or replying) | IG placements, IG posting |
| Dataset (pixel) | Use events dataset (Manage for CAPI setup) | conversions, CAPI |
| Catalog | Manage catalog | catalog ads, product sync |

## 4. Generate the token
System users → the user → Generate new token → pick the app → expiry **Never** → tick only the scopes
you need. Typical sets:
- **Read-only reporting:** `ads_read`, `read_insights`, `business_management` (to list assets).
- **Run ads:** add `ads_management`, `pages_read_engagement`, `pages_show_list`.
- **Pixel / CAPI:** dataset permission above is enough for the Conversions API; no extra scope beyond
  `ads_management`.
- **Instagram posting:** `instagram_basic`, `instagram_content_publish`, `pages_read_engagement`.
- **Comments / DMs:** `instagram_manage_comments`, `pages_manage_engagement`, `instagram_manage_messages`,
  `pages_messaging`.
The token is shown once. Store it immediately (step 6).

## 5. Verify (read-only)
Run the doctor script in `meta-doctor`, or by hand:
```
GET /me?fields=id,name                      -> the system user
GET /me/permissions                          -> granted scopes
GET /debug_token?input_token=T&access_token=T -> expires_at = 0 means never
GET /me/adaccounts?fields=name,account_status,currency,timezone_name
GET /me/accounts?fields=name,instagram_business_account   (Pages + linked IG)
GET /act_<id>/adspixels?fields=name,last_fired_time
```
`account_status` 1 = active, 2 = disabled, 3 = unsettled (billing problem).

## 6. Store it
- Put it in a password manager or secrets store, plus a git-ignored `.env` for local scripts.
- Never paste it in chat, tickets, commits or URLs. If it leaks, regenerate (old one keeps working until
  revoked: revoke it in the system user screen).
- Env files written on Windows often carry a UTF-8 BOM and CRLF line endings; strip both when reading
  (`tr -d '\r\357\273\277'`) or the token silently fails with "Invalid OAuth access token".

## 7. Standard vs Advanced Access (the ceiling)
An app that has not passed App Review only has **Standard Access** to each permission. In practice:
- Works on assets the business owns, through the system user: reading and managing its own ads,
  insights, Page posts, IG posting, reading comments and conversations, replying to comments.
- Often blocked: **sending** Messenger/Instagram DMs at volume, some messaging and lead features, and
  anything touching other businesses' assets. If an endpoint returns "requires advanced access" or
  "(#200) permission not granted" despite the scope being on the token, it is this ceiling, not a bad token.
- Advanced Access needs Business Verification + App Review with a screencast of the use case. Plan weeks.

## Common errors
| Error | Cause |
|---|---|
| "No permissions available" when generating | system user has no role on the app (step 2) |
| (#200) Requires ads_management / ad account permission | scope missing on token, or ad account not assigned to system user |
| "Ad account has no access to this Instagram account" | IG not connected to the ad account (business setup §3) |
| (#100) Param ... not a valid app-scoped ID | assigning a Page to a person who hasn't accepted their invite yet |
| Error 190 / "Session has expired" | personal token; switch to a system user token |
