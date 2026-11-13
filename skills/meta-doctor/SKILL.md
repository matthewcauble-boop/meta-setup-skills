---
name: meta-doctor
description: "Run a read-only health check of a Meta setup from an access token: who the token belongs to, scopes, expiry, businesses, ad accounts (status, currency, time zone), datasets/pixels and when they last fired, Pages, linked Instagram accounts, and which Instagram accounts each ad account can use, with a list of problems and the fix for each. Use first whenever Meta API calls fail, after setting up a new token, or when auditing a brand's Meta setup."
---

# Meta doctor

Run:
```
META_ACCESS_TOKEN=... python scripts/meta_doctor.py          # human summary
python scripts/meta_doctor.py --env path/to/.env --json      # machine-readable
```
Python 3.9+, standard library only. It only makes GET requests and never prints the token.

Then, for each line under **Issues**, point the user to the fix:
| Issue | Fix |
|---|---|
| Token expires / personal user token | `meta-api-access` §2-4: system user, Never expiry |
| Sees no ad accounts | assign the ad account to the system user (`meta-api-access` §3) |
| Ad account DISABLED / UNSETTLED | Billing → payment method, or Account Quality for a disabled account |
| No pixel on ad account | `meta-business-setup` §5, then `meta-pixel-capi` |
| Pixel last fired days ago / never | tracking broken: `meta-pixel-capi` §4 |
| Page has no linked Instagram | `meta-business-setup` §3 |
| Instagram not usable by ad account | Business Settings → Instagram accounts → Connect assets → ad account |
| Missing scope | regenerate token with the scope (`meta-api-access` §4) |

Report the summary to the user without the token, and without account IDs if the output will be shared
outside the business.
