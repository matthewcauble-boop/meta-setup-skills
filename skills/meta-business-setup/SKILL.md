---
name: meta-business-setup
description: "Set up (or audit) a brand's Meta Business portfolio from scratch: Business Manager ownership, Facebook Page, Instagram account, ad account, payment method, domain verification, people and partner (agency) access. Use when someone says 'set up Meta', 'set up Facebook/Instagram ads for a new brand', 'give my agency access', 'who owns our ad account', or before any API, pixel or campaign work."
---

# Meta business setup

The goal is one Business portfolio that **the brand owns**, with every asset inside it, and everyone else
(agencies, freelancers, apps) holding *partner* or *role* access that can be removed without losing anything.
Most "Meta is broken" problems later (can't create ads, pixel not attributable, agency left with the
ad account) trace back to a step done out of order here.

Work through the checklist in order. For each step: check the current state first, report it, and only
then change anything. Never accept terms, add payment methods, or change ownership for the user; walk
them through those screens.

## 0. Gather before starting
- Legal business name, address, website domain, a business email on that domain.
- Who should be **admins** (at least two real people, so one lost login doesn't lock the business).
- Which outside parties need access (agency, freelancer, app) and to what.
- Whether a Page, Instagram account, ad account or pixel **already exist** anywhere (old agency, personal
  ad account, another portfolio). Moving an existing asset beats creating a duplicate: a new pixel starts
  with zero history and a new ad account starts with no spending history.

## 1. Business portfolio (business.facebook.com → Settings)
- Create it from a real person's Facebook profile (Meta requires one). That person becomes admin.
- Add a second admin immediately. Turn on two-factor authentication for everyone (Security Center).
- Fill in Business info (legal name, address, website). Business verification (Security Center →
  Verification) is needed for higher API access, more ad accounts and messaging features; start it early,
  it can take days and needs a document that shows the legal name and address.

## 2. Facebook Page
- If the Page exists elsewhere, **request access** or **claim** it (Accounts → Pages → Add) rather than
  creating a new one. Claiming needs an admin of the Page to approve.
- Page must be published; fill name, category, profile/cover, website.

## 3. Instagram account
- Convert to a Professional (Business) account and link it to the Page (Instagram app → Settings →
  Account type and tools, or Page settings → Linked accounts).
- In Business Settings → Accounts → Instagram accounts → Add, then **Connect assets → the ad account**.
  Skipping this makes ad creation fail later with "Ad account has no access to this Instagram account".

## 4. Ad account
- Create it *inside* the portfolio (Accounts → Ad accounts → Add → Create), currency and time zone
  chosen carefully: **neither can be changed later**. Use the time zone the business reports in.
- If an agency created the ad account in *their* portfolio, it belongs to them. Ask them to transfer it
  only if Meta allows; otherwise create a new one in the brand's portfolio and keep the old one for history.
- Payment method: the brand adds its own card or invoice line under Billing. Do not enter card details on
  the user's behalf.
- Set an account spending limit if the user wants a hard cap.

## 5. Pixel / dataset and domain
- Events Manager → Connect data → Web → create one dataset (pixel) for the website, owned by the portfolio.
  One per website; don't create a second because the first "looks broken" — debug it (see meta-pixel-capi).
- Brand safety → Domains → add the domain and verify it (DNS TXT record is the most durable; meta-tag or
  file upload break when the site is redeployed).
- Assign the dataset to the ad account (dataset → Settings → Connected assets).

## 6. People and partners
- People: give staff the smallest role that works ("Partial access" with task permissions per asset).
- Partners (agencies): Users → Partners → Add → **their Business ID**. Then share specific assets with
  the partner (ad account: Manage campaigns; Page: Ads / Content; dataset: Use dataset). The agency then
  assigns its own people. Removing the partner later removes all their people at once.
- Never hand out personal logins. Never make an agency an admin of the brand's portfolio.

## 7. Commerce / catalog (only if selling products)
- Commerce Manager → create a catalog owned by the portfolio, or connect the store's native channel
  (Shopify: the "Facebook & Instagram" sales channel creates and syncs it).
- Share the catalog with the ad account and the dataset (for dynamic/Advantage+ catalog ads).

## 8. Final audit (report this table back)
| Asset | Exists | Owned by this portfolio | Shared with | Notes |
|---|---|---|---|---|
| Business portfolio | | | admins: | 2FA on? verified? |
| Page | | | | |
| Instagram | | | connected to ad account? | |
| Ad account | | | | currency / time zone / payment |
| Dataset (pixel) | | | ad account? | domain verified? |
| Catalog | | | | |
| Partners | | | | what each can touch |

Next: `meta-api-access` (system user + token) if anything will be automated, then `meta-pixel-capi`.
