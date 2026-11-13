#!/usr/bin/env python3
"""launch.py: turn a folder/list of ads into a Meta creative test, set up the proven way.

    python launch.py plan   launch.json --brand brand.json      # dry run: prints exactly what would be created
    python launch.py create launch.json --brand brand.json      # creates everything PAUSED, writes a receipt
    python launch.py create launch.json --brand brand.json --activate   # same, but turns the new ad sets on
    python launch.py review --brand brand.json                  # read only: kill / graduate / hold per live ad

Structure it builds (see ../SKILL.md for the why):
  campaign  "Creative Testing" (Sales objective, ABO: no campaign budget). Reused if it already exists.
  ad set    one per CONCEPT: "<product> | <concept> | <Statics|Videos> | <Mon D>", $100/day, lowest cost,
            optimise Purchase on the pixel, 7-day click + 1-day engaged-view, broad + Advantage+ audience,
            Advantage+ placements, past customers excluded.
  ads       3-10 per ad set. Statics: 4:5 for feeds + 9:16 for Stories/Reels in ONE ad (placement asset
            customisation). Videos: one ad per video with up to 5 primary texts + 5 headlines. Meta's
            automatic "Advantage+ creative" enhancements are switched off. CTA Shop Now.

Standard library only. Token from META_ACCESS_TOKEN or brand.json "token_env_file". Never prints the token.
"""
import argparse, datetime as dt, json, mimetypes, os, sys, time, urllib.error, urllib.parse, urllib.request, uuid
from pathlib import Path

API = "https://graph.facebook.com/v21.0"
PLAYBOOK = json.load(open(Path(__file__).resolve().parent.parent / "playbook.json", encoding="utf-8"))
VIDEO_EXT = {".mp4", ".mov", ".m4v"}
IMAGE_EXT = {".jpg", ".jpeg", ".png"}
# Meta's automatic creative "enhancements" switched off (the reference account opts out of all of them).
ENHANCEMENTS_OFF = ["adapt_to_placement", "add_text_overlay", "advantage_plus_creative", "description_automation",
                    "enhance_cta", "image_animation", "image_auto_crop", "image_background_gen",
                    "image_brightness_and_contrast", "image_enhancement", "image_templates", "image_uncrop",
                    "music_generation", "text_optimizations", "text_generation", "video_auto_crop", "video_uncrop",
                    "product_extensions", "site_extensions", "reveal_details_over_time", "show_summary"]


# ---------------------------------------------------------------- config
def load_brand(path):
    b = json.load(open(path, encoding="utf-8-sig"))
    need = ["ad_account_id", "page_id", "pixel_id"]
    miss = [k for k in need if not b.get(k)]
    if miss: sys.exit(f"brand.json is missing {miss}")
    b.setdefault("campaign_name", "Creative Testing")
    b.setdefault("daily_budget_usd", PLAYBOOK["launch"]["daily_budget_usd"])
    b.setdefault("floor_roas", None)
    b.setdefault("countries", ["US"])
    b.setdefault("age_min", 18); b.setdefault("age_max", 65)
    b.setdefault("exclude_audience_ids", [])
    b.setdefault("cta", "SHOP_NOW")
    b.setdefault("ads_per_adset_max", PLAYBOOK["launch"]["ads_per_adset_range"][1])
    return b


def token(b):
    t = os.environ.get("META_ACCESS_TOKEN", "")
    envf = b.get("token_env_file")
    if not t and envf:
        for line in open(Path(envf).expanduser(), encoding="utf-8-sig"):
            line = line.strip().replace("﻿", "")
            if line.startswith("META_ACCESS_TOKEN="): t = line.split("=", 1)[1].strip().strip('"\'')
    if not t: sys.exit("No token: set META_ACCESS_TOKEN or brand.json token_env_file")
    return t


# ---------------------------------------------------------------- graph
class Graph:
    def __init__(self, tok): self.tok = tok

    def _do(self, method, path, params=None, files=None):
        params = dict(params or {}); params["access_token"] = self.tok
        url = f"{API}/{path}"
        if method == "GET":
            req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params))
        elif files:
            b = "----lx" + uuid.uuid4().hex; body = b""
            for k, v in params.items():
                body += f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
            for k, p in files.items():
                body += (f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{Path(p).name}\"\r\n"
                         f"Content-Type: {mimetypes.guess_type(p)[0] or 'application/octet-stream'}\r\n\r\n").encode()
                body += Path(p).read_bytes() + b"\r\n"
            body += f"--{b}--\r\n".encode()
            req = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": f"multipart/form-data; boundary={b}"})
        else:
            enc = {k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in params.items()}
            req = urllib.request.Request(url, data=urllib.parse.urlencode(enc).encode(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=600) as r: return json.load(r)
        except urllib.error.HTTPError as e:
            try: err = json.load(e).get("error", {})
            except Exception: err = {"message": str(e)}
            raise SystemExit(f"Meta API error on {method} {path}: ({err.get('code')}/{err.get('error_subcode')}) "
                             f"{err.get('error_user_msg') or err.get('message')}")

    def get(self, path, **p): return self._do("GET", path, p)
    def post(self, path, files=None, **p): return self._do("POST", path, p, files)


# ---------------------------------------------------------------- plan
def group_assets(launch, b, base=Path('.')):
    """Return [{concept, format, ads:[{name, kind, feed, vertical, video, bodies, titles, url}]}]."""
    out = []
    defaults = {k: launch.get(k) for k in ("product", "url", "bodies", "titles", "description")}
    for c in launch["concepts"]:
        ads = []
        for a in c["ads"]:
            a = {**{k: c.get(k, defaults[k]) for k in defaults}, **a}
            if "video" in a: kind = "video"
            elif "feed" in a: kind = "static"
            else: sys.exit(f"ad {a} needs 'feed' (+ optional 'vertical') or 'video'")
            for k in ("feed", "vertical", "video"):
                if a.get(k):
                    p = Path(a[k]).expanduser()
                    a[k] = str(p if p.is_absolute() else (base / p).resolve())
                    if not Path(a[k]).exists(): sys.exit(f"file not found: {a[k]}")
            if not a.get("url"): sys.exit(f"ad {a.get('name') or a.get('feed') or a.get('video')}: no url")
            stem = Path(a.get("feed") or a.get("video")).stem
            a["name"] = a.get("name") or f"{stem} | {dt.date.today():%m/%d/%Y}"
            a["kind"] = kind
            a["bodies"] = (a.get("bodies") or [])[:5]; a["titles"] = (a.get("titles") or [])[:5]
            if not a["bodies"]: sys.exit(f"ad {a['name']}: needs at least one primary text (bodies)")
            ads.append(a)
        if not 1 <= len(ads) <= b["ads_per_adset_max"]:
            sys.exit(f"concept {c['concept']}: {len(ads)} ads; keep 3-{b['ads_per_adset_max']} per ad set (split the concept)")
        kinds = {a["kind"] for a in ads}
        fmt = "Videos" if kinds == {"video"} else "Statics" if kinds == {"static"} else "Mixed"
        product = c.get("product") or launch.get("product") or "Product"
        name = c.get("adset_name") or f"{product} | {c['concept']} | {fmt} | {dt.date.today():%b} {dt.date.today().day}"
        out.append({"concept": c["concept"], "adset_name": name, "format": fmt, "ads": ads,
                    "daily_budget_usd": c.get("daily_budget_usd", b["daily_budget_usd"])})
    return out


def targeting(b):
    t = {"geo_locations": {"countries": b["countries"], "location_types": ["home", "recent"]},
         "age_min": b["age_min"], "age_max": b["age_max"],
         "targeting_automation": {"advantage_audience": 1}}
    if b["exclude_audience_ids"]:
        t["excluded_custom_audiences"] = [{"id": i} for i in b["exclude_audience_ids"]]
    return t


def image_size(path):
    """(width, height) for PNG/JPEG without third-party libraries, or None."""
    with open(path, "rb") as f:
        head = f.read(26)
        if head[:8] == b"\x89PNG\r\n\x1a\n": return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")
        if head[:2] != b"\xff\xd8": return None
        f.seek(2)
        while True:
            m = f.read(4)
            if len(m) < 4 or m[0] != 0xFF: return None
            seg = int.from_bytes(m[2:4], "big")
            if m[1] in (0xC0, 0xC1, 0xC2):
                d = f.read(5); return int.from_bytes(d[3:5], "big"), int.from_bytes(d[1:3], "big")
            f.seek(seg - 2, 1)


def check_assets(groups):
    """Warnings about sizes and ratios."""
    warn = []
    for g in groups:
        for a in g["ads"]:
            for key, want, label in (("feed", 4 / 5, "4:5"), ("vertical", 9 / 16, "9:16")):
                p = a.get(key)
                if not p: continue
                wh = image_size(p)
                if not wh: warn.append(f"{Path(p).name}: can't read size (use JPG or PNG)"); continue
                w, h = wh
                if abs(w / h - want) > 0.03: warn.append(f"{Path(p).name}: {w}x{h} is not {label} (expected for the {key} slot)")
                elif w < 1000: warn.append(f"{Path(p).name}: {w}x{h} is small; use 1080 px wide")
            if a["kind"] == "static" and not a.get("vertical"):
                warn.append(f"{Path(a['feed']).name}: no 9:16 version; Stories/Reels will crop the 4:5")
            if a.get("video") and Path(a["video"]).stat().st_size < 200_000:
                warn.append(f"{Path(a['video']).name}: file is tiny, check it's the real video")
    return warn


def print_plan(groups, b, campaign_id):
    print(f"Ad account {b['ad_account_id']}  |  campaign: {b['campaign_name']} "
          f"({'exists, ' + campaign_id if campaign_id else 'will be CREATED: Sales, ad set budgets'})")
    print(f"Ad set settings: ${b['daily_budget_usd']}/day, lowest cost, optimise Purchase on pixel {b['pixel_id']}, "
          f"7-day click + 1-day engaged view, {','.join(b['countries'])} {b['age_min']}-{b['age_max']}, Advantage+ audience, "
          f"Advantage+ placements, excluding {len(b['exclude_audience_ids'])} customer audience(s)")
    total = 0
    for g in groups:
        total += g["daily_budget_usd"]
        print(f"\n  AD SET  {g['adset_name']}   ${g['daily_budget_usd']}/day   {len(g['ads'])} ads")
        for a in g["ads"]:
            files = f"feed={Path(a['feed']).name}" + (f" + vertical={Path(a['vertical']).name}" if a.get("vertical") else " (no 9:16 version)") \
                if a["kind"] == "static" else f"video={Path(a['video']).name}"
            txt = "1 text + 1 headline (4:5 + 9:16 pair)" if a["kind"] == "static" and a.get("vertical")                 else f"{len(a['bodies'])} texts / {len(a['titles'])} headlines"
            print(f"    AD  {a['name']}  [{files}]  {txt}  -> {a['url']}")
    print(f"\nTotal new daily budget: ${total:,.0f}/day (about ${total * 7:,.0f}/week). Everything is created PAUSED unless --activate.")
    w = check_assets(groups)
    if w:
        print("\nCreative check:"); [print("  -", x) for x in w]
    warn = [g["adset_name"] for g in groups if len(g["ads"]) < 3]
    if warn: print("Note: fewer than 3 ads in", warn, "- tests work best with 3-10 variations of one concept.")
    if not b["exclude_audience_ids"]: print("Note: no past-customer exclusion set (brand.json exclude_audience_ids).")


# ---------------------------------------------------------------- create
def find_campaign(g, b):
    r = g.get(f"{b['ad_account_id']}/campaigns", fields="id,name,effective_status", limit=200)
    for c in r.get("data", []):
        if c["name"] == b["campaign_name"] and c["effective_status"] not in ("DELETED", "ARCHIVED"):
            return c["id"]
    return None


def creative_spec(g, b, a):
    feats = {k: {"enroll_status": "OPT_OUT"} for k in ENHANCEMENTS_OFF}
    dof = {"creative_features_spec": feats}
    ident = {"page_id": b["page_id"]}
    if b.get("instagram_user_id"): ident["instagram_user_id"] = b["instagram_user_id"]
    if a["kind"] == "video":
        vid = g.post(f"{b['ad_account_id']}/advideos", files={"source": str(Path(a["video"]).expanduser())},
                     name=Path(a["video"]).name)["id"]
        for _ in range(60):  # wait for processing so a thumbnail exists
            st = g.get(vid, fields="status,picture")
            if st.get("status", {}).get("video_status") == "ready" and st.get("picture"): break
            time.sleep(10)
        vd = {"video_id": vid, "image_url": st.get("picture"),
              "call_to_action": {"type": b["cta"], "value": {"link": a["url"]}},
              "message": a["bodies"][0]}
        if a["titles"]: vd["title"] = a["titles"][0]
        spec = {"object_story_spec": {**ident, "video_data": vd}, "degrees_of_freedom_spec": dof}
        if len(a["bodies"]) > 1 or len(a["titles"]) > 1:  # multiple text options, Meta rotates them
            spec["asset_feed_spec"] = {"bodies": [{"text": t} for t in a["bodies"]],
                                       "titles": [{"text": t} for t in a["titles"]],
                                       "optimization_type": "DEGREES_OF_FREEDOM"}
        return spec
    # static
    def up(p):
        r = g.post(f"{b['ad_account_id']}/adimages", files={"filename": str(Path(p).expanduser())})
        return next(iter(r["images"].values()))["hash"]
    feed = up(a["feed"])
    if not a.get("vertical"):
        ld = {"image_hash": feed, "link": a["url"], "message": a["bodies"][0],
              "call_to_action": {"type": b["cta"], "value": {"link": a["url"]}}}
        if a["titles"]: ld["name"] = a["titles"][0]
        if a.get("description"): ld["description"] = a["description"]
        spec = {"object_story_spec": {**ident, "link_data": ld}, "degrees_of_freedom_spec": dof}
        if len(a["bodies"]) > 1 or len(a["titles"]) > 1:
            spec["asset_feed_spec"] = {"bodies": [{"text": t} for t in a["bodies"]], "titles": [{"text": t} for t in a["titles"]],
                                       "optimization_type": "DEGREES_OF_FREEDOM"}
        return spec
    vert = up(a["vertical"])
    lab = lambda n: [{"name": n}]
    rule = lambda img, prio, extra: {"customization_spec": extra, "image_label": {"name": img}, "body_label": {"name": "b"},
                                     "title_label": {"name": "t"}, "link_url_label": {"name": "u"}, "priority": prio}
    afs = {"images": [{"hash": feed, "adlabels": lab("feed")}, {"hash": vert, "adlabels": lab("vertical")}],
           "bodies": [{"text": a["bodies"][0], "adlabels": lab("b")}],
           "titles": [{"text": (a["titles"] or [" "])[0], "adlabels": lab("t")}],
           "link_urls": [{"website_url": a["url"], "adlabels": lab("u")}],
           "call_to_action_types": [b["cta"]], "ad_formats": ["SINGLE_IMAGE"], "optimization_type": "PLACEMENT",
           "asset_customization_rules": [
               rule("vertical", 1, {"publisher_platforms": ["facebook", "instagram", "messenger"],
                                    "facebook_positions": ["story", "facebook_reels"],
                                    "instagram_positions": ["story", "reels", "profile_reels"],
                                    "messenger_positions": ["story"]}),
               rule("feed", 2, {})]}
    if a.get("description"):
        afs["descriptions"] = [{"text": a["description"], "adlabels": lab("d")}]
        for r_ in afs["asset_customization_rules"]: r_["description_label"] = {"name": "d"}
    return {"object_story_spec": ident, "asset_feed_spec": afs, "degrees_of_freedom_spec": dof}


def create(groups, b, g, activate):
    status = "ACTIVE" if activate else "PAUSED"
    receipt = {"time": dt.datetime.now().isoformat(timespec="seconds"), "ad_account": b["ad_account_id"], "adsets": []}
    cid = find_campaign(g, b)
    if not cid:
        cid = g.post(f"{b['ad_account_id']}/campaigns", name=b["campaign_name"], objective="OUTCOME_SALES",
                     special_ad_categories=[], status="ACTIVE", buying_type="AUCTION")["id"]
        print("created campaign", b["campaign_name"], cid)
    receipt["campaign_id"] = cid
    for grp in groups:
        asid = g.post(f"{b['ad_account_id']}/adsets", name=grp["adset_name"], campaign_id=cid, status=status,
                      daily_budget=int(grp["daily_budget_usd"] * 100), billing_event="IMPRESSIONS",
                      optimization_goal="OFFSITE_CONVERSIONS", bid_strategy="LOWEST_COST_WITHOUT_CAP",
                      promoted_object={"pixel_id": b["pixel_id"], "custom_event_type": "PURCHASE"},
                      attribution_spec=[{"event_type": "CLICK_THROUGH", "window_days": 7},
                                        {"event_type": "ENGAGED_VIDEO_VIEW", "window_days": 1}],
                      targeting=targeting(b))["id"]
        print("created ad set", grp["adset_name"], asid)
        rec = {"name": grp["adset_name"], "id": asid, "ads": []}
        for a in grp["ads"]:
            spec = creative_spec(g, b, a)
            crid = g.post(f"{b['ad_account_id']}/adcreatives", name=a["name"], **spec)["id"]
            adid = g.post(f"{b['ad_account_id']}/ads", name=a["name"], adset_id=asid, creative={"creative_id": crid},
                          status="ACTIVE")["id"]  # ads ACTIVE; the ad set's status decides whether they run
            print("   created ad", a["name"], adid)
            rec["ads"].append({"name": a["name"], "id": adid, "creative_id": crid})
        receipt["adsets"].append(rec)
    out = Path(f"launch-receipt-{dt.datetime.now():%Y%m%d-%H%M%S}.json"); out.write_text(json.dumps(receipt, indent=1))
    print(f"\nDone. Ad sets are {status}. Receipt: {out}")
    if not activate: print("Review them in Ads Manager, then switch the ad sets on (or rerun with --activate next time).")


# ---------------------------------------------------------------- review (read only)
def purchases(row, key):
    for x in row.get(key) or []:
        if x["action_type"] in ("omni_purchase", "offsite_conversion.fb_pixel_purchase"): return float(x["value"])
    return 0.0


def review(b, g):
    floor = b.get("floor_roas")
    if not floor: sys.exit("set floor_roas (break-even Meta ROAS) in brand.json for review")
    R = PLAYBOOK["review_rules"]
    cid = find_campaign(g, b)
    if not cid: sys.exit(f"campaign {b['campaign_name']} not found")
    f = "ad_id,ad_name,adset_id,adset_name,spend,actions,action_values"
    life = {r["ad_id"]: r for r in g.get(f"{cid}/insights", level="ad", fields=f, date_preset="maximum", limit=500).get("data", [])}
    wk = {r["ad_id"]: r for r in g.get(f"{cid}/insights", level="ad", fields=f, date_preset="last_7d", limit=500).get("data", [])}
    ads = {a["id"]: a for a in g.get(f"{cid}/ads", fields="id,effective_status,created_time,adset{daily_budget}", limit=500).get("data", [])
           if a["effective_status"] == "ACTIVE"}
    live = set(ads)
    launch_budget = PLAYBOOK["launch"]["daily_budget_usd"]
    min_days = PLAYBOOK["review_rules"].get("min_days_before_roas_kill", 7)
    s7_set = {}
    for r in wk.values(): s7_set[r["adset_id"]] = s7_set.get(r["adset_id"], 0) + float(r["spend"])
    rows = []
    for aid, L in life.items():
        if aid not in live: continue
        W = wk.get(aid, {}); sp = float(L["spend"]); val = purchases(L, "action_values"); n = purchases(L, "actions")
        s7 = float(W.get("spend", 0)); v7 = purchases(W, "action_values")
        rel = (val / sp / floor) if sp else 0; r7 = (v7 / s7 / floor) if s7 else 0
        share = s7 / s7_set[L["adset_id"]] if s7_set.get(L["adset_id"]) else 0
        age = (dt.datetime.now(dt.timezone.utc) - dt.datetime.strptime(ads[aid]["created_time"][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc)).days
        budget = float((ads[aid].get("adset") or {}).get("daily_budget") or 0) / 100
        if n == 0 and sp >= R["kill_no_purchase_after_spend"]: act = f"KILL (no sale after ${sp:,.0f})"
        elif age < min_days: act = f"hold (only {age} days live)"
        elif sp >= R["kill_lifetime_spend_min"] and rel < R["kill_lifetime_roas_below_x_floor"]: act = f"KILL (lifetime {rel:.2f}x floor)"
        elif s7 >= R["kill_7d_spend_min"] and r7 < R["kill_7d_roas_below_x_floor"]: act = f"KILL (last 7 days {r7:.2f}x floor)"
        elif s7 >= R["graduate_7d_spend_min"] and r7 >= R["graduate_7d_roas_at_least_x_floor"] and share >= R["graduate_share_of_adset_spend_min"]:
            act = (f"GRADUATE: ad set ${budget:,.0f} -> ${budget * R['first_raise_step']:,.0f}/day" if budget and budget < 2 * launch_budget
                   else f"RAISE ad set ${budget:,.0f} -> ${budget * R['raise_step_median']:,.0f}/day if not raised in {R['days_between_raises_median']}+ days")                   + f" ({r7:.2f}x floor, {share:.0%} of ad set)"
        elif s7 >= R["kill_7d_spend_min"] and r7 < R["graduate_7d_roas_at_least_x_floor"] and share >= R["graduate_share_of_adset_spend_min"]:
            act = f"hold (carrying the ad set at {r7:.2f}x floor; kill under {R['kill_7d_roas_below_x_floor']}x)"
        else: act = "hold"
        rows.append((L["adset_name"], L["ad_name"], sp, n, rel, s7, r7, share, act))
    rows.sort(key=lambda r: (r[0], -r[2]))
    print(f"Review of {b['campaign_name']} (floor ROAS {floor}); rules from playbook.json, data through {PLAYBOOK['data_through']}")
    cur = None
    for r in rows:
        if r[0] != cur: cur = r[0]; print(f"\n{cur}")
        print(f"  {r[1][:48]:48} spent ${r[2]:>7,.0f}  buys {r[3]:>4.0f}  life {r[4]:.2f}x  7d ${r[5]:>6,.0f} {r[6]:.2f}x  share {r[7]:>4.0%}  -> {r[8]}")
    print("\nRead only: nothing was changed. Raise graduates 2x first, then +40-50% about every "
          f"{R['days_between_raises_median']} days; cuts {R['cut_step_median']:.0%} of budget.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["plan", "create", "review"]); ap.add_argument("launch", nargs="?"); ap.add_argument("--brand", required=True)
    ap.add_argument("--activate", action="store_true")
    a = ap.parse_args()
    b = load_brand(a.brand)
    if a.cmd == "review":
        return review(b, Graph(token(b)))
    if not a.launch: sys.exit("plan/create need a launch.json")
    launch = json.load(open(a.launch, encoding="utf-8-sig"))
    groups = group_assets(launch, b, Path(a.launch).resolve().parent)
    g = Graph(token(b))
    cid = find_campaign(g, b)
    print_plan(groups, b, cid)
    if a.cmd == "create":
        create(groups, b, g, a.activate)


if __name__ == "__main__":
    main()
