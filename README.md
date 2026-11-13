# Meta setup skills for Claude

**Main skill: `meta-test-launch`.** Tell Claude *"run these 10 ads on Meta"* and it sorts them into concepts and builds
the creative test the way a top DTC agency does it: one $100/day ad set per concept inside a "Creative Testing" Sales
campaign, broad + Advantage+ audience, past customers excluded, Purchase optimisation, 7-day click, 4:5 + 9:16 placement
versions, Meta's auto-enhancements off, created paused for review. It also carries the agency's kill / graduate / scale
rules for the weeks after launch (`launch.py review`, read only). Those rules live in `skills/meta-test-launch/playbook.json`,
exported from a learner that watches the agency's real changes every night, so they stay current. The other skills get an
account ready for it.

A skills pack that teaches Claude (Claude Code or the Claude app) how to set up and run Meta
(Facebook + Instagram) advertising for a brand, the way it actually works in practice: who should own
what, how to get API access that doesn't break, how to prove tracking works, how to read the numbers,
and how to launch campaigns safely.

| Skill | Use it for |
|---|---|
| `meta-test-launch` | **Launch a batch of ads as a correctly structured creative test, plus the review rules** |
| `meta-business-setup` | Business portfolio, Page, Instagram, ad account, payment, domain, people and agency access |
| `meta-api-access` | App, system user, asset assignment, non-expiring token, scopes, Standard vs Advanced Access |
| `meta-doctor` | Read-only health check script: token, scopes, ad accounts, pixels, Pages, Instagram links |
| `meta-pixel-capi` | Pixel + Conversions API install, deduplication, match quality, verification |
| `meta-reporting` | Read-only Insights queries, MER vs Meta ROAS, weekly check-in format |
| `meta-ads` | Campaign creation via the Marketing API (dry run first, created paused), browser-only steps, creative crop rules. From [boringmarketer/meta-ads-skill](https://github.com/boringmarketer/meta-ads-skill), MIT |

Suggested order for a new brand: **business-setup → api-access → doctor → pixel-capi → test-launch → reporting**.

## Before you start: connect Meta
Connect Meta's **official Meta Ads connector** in Claude (Settings → Connectors → Meta Ads; in Claude Code `/mcp`) and sign
in with the Facebook account that manages the ad account. The skills use it for everything. The token + script path
(`meta-api-access`, `meta-doctor`, `launch.py`) is only a fallback for setups the connector can't do.

## Install

**Claude Code (plugin):**
```
/plugin marketplace add <this repo's GitHub URL or local path>
/plugin install meta-setup-skills@meta-setup-skills
```

**Claude Code (plain skills folder):** copy each folder in `skills/` into `~/.claude/skills/`
(or `.claude/skills/` inside a project).

**Claude app (claude.ai):** zip a skill folder (for example `skills/meta-business-setup`) and upload it under
Settings → Capabilities → Skills.

Then just ask, for example: *"Set up Meta for our new brand"*, *"Check our Meta token"*,
*"Is our pixel tracking purchases?"*, *"How did Meta ads do this month?"*.

## Token and safety rules built into the skills
- Use a **system-user token** owned by the business with **Never** expiry, not a personal token.
- Keep tokens in a password manager or a git-ignored `.env` (see `.env.example`). Never paste them in chat or commit them.
- Everything reads first. The campaign script defaults to a dry run and creates campaigns **paused**.
- Claude walks the user through payment methods, terms and ownership changes; it doesn't do them for them.

## Health check
```
cp .env.example .env    # fill META_ACCESS_TOKEN
python skills/meta-doctor/scripts/meta_doctor.py --env .env
```
Python 3.9+, no dependencies, GET requests only.

## License
MIT. `skills/meta-ads` keeps its upstream MIT license.
