# meta-ads-skill

A skill that teaches an AI coding agent — Claude Code, Cursor, or anything that
reads Markdown instructions — how to set up Meta (Facebook/Instagram) Marketing
API access, publish campaigns programmatically, drive the parts of the UI that
have no API, and verify conversion tracking in a way that actually holds up.

Everything in here was learned by getting it wrong in production first. The API
rejections are real rejections with their real causes, the permission chain is
the one that actually unblocks token generation, and there is a whole section on
verification because three separate confidently-wrong conclusions came out of
measuring with instruments that structurally could not see the thing being
measured.

## Why this exists

Meta's Marketing API docs describe the endpoints. They do not tell you:

- that a system user needs a **role on the app** before it can generate a token,
  and that the failure gives you no hint which of four grants is missing
- that a **Development-mode app** blocks ad *creative* creation only, so it fails
  at the very end of a long script
- that `fbq.loaded` is set by the inline stub and is `true` even when the real
  library was blocked by your CSP
- that `navigator.sendBeacon` — which `fbevents` uses whenever an `eventID` is
  present — is invisible to devtools Network *and* to
  `performance.getEntriesByType('resource')`
- that Meta crops a 1080×1920 asset by ~420px per end for square feed
  placements, which is where most impressions land

Each of those cost hours. They are all written down here.

## Install

### Claude Code

```bash
git clone https://github.com/boringmarketer/meta-ads-skill.git ~/.claude/skills/meta-ads
```

Restart Claude Code. It picks up `SKILL.md` and loads it when you ask about Meta
ads. For a single project instead, clone to `.claude/skills/meta-ads/`.

### Any other agent

Clone it anywhere and point the agent at `SKILL.md`:

```
Read SKILL.md in ./meta-ads-skill and follow it.
```

The reference files are plain Markdown, linked from `SKILL.md` by relative path.

## What's inside

```
SKILL.md                      entry point — routes by task, carries the core content
reference/setup.md            nothing → working token, in the order that works
reference/publishing.md       the API objects, field by field, with real rejections
reference/browser.md          the steps with no API, and how an agent should drive them
reference/tracking.md         pixel + Conversions API, and what each instrument can see
reference/creative.md         crop-safe zones, native-look captions, Special Ad Categories
scripts/preflight.mjs         checks every grant in the chain. Writes nothing.
scripts/campaign.mjs          config-driven campaign builder. Creates PAUSED.
scripts/campaign.example.json the config shape
scripts/verify-tracking.js    console snippet: did fbevents actually load?
```

## Quick start

```bash
export META_ADS_TOKEN='...'            # system user token, ads_management
export META_AD_ACCOUNT_ID='act_123...'
export META_PIXEL_ID='123...'          # optional but recommended

node scripts/preflight.mjs
```

`preflight` checks the token, scopes, ad account status, payment method,
available Pages, pixel last-fired time, and Instagram connection — and tells you
which grant is missing rather than making you infer it from a 400.

Then:

```bash
cp scripts/campaign.example.json my-campaign.json
$EDITOR my-campaign.json

node scripts/campaign.mjs --config my-campaign.json           # dry run, no writes
node scripts/campaign.mjs --config my-campaign.json --apply   # creates PAUSED
```

Nothing spends money until you enable it in Ads Manager yourself.

## Safety

The scripts are built so an agent can run them without risk of surprise spend:

- **Everything is created `PAUSED`.** Enabling is a separate human action.
- **Dry run is the default.** `--apply` is required to write anything.
- **Budgets are range-checked** before they are sent. Meta takes budgets in minor
  currency units, so sending dollars is a 100× overspend — the assertion catches
  it.
- **`preflight` writes nothing at all.**
- **Copy guards** are configurable regexes that fail the run, for categories with
  content rules (Employment and Credit forbid earnings claims).

A never-expiring `ads_management` token can spend money. Keep it in the
environment, never in the repo, and rotate it if it ever lands in a transcript,
a log, or a screenshot.

## Contributing

Corrections welcome, particularly where Meta has changed something — the API
moves and parts of this will rot. Issues and PRs both fine.

## License

MIT
