#!/usr/bin/env python3
"""launch.py: turn a folder/list of ads into a Meta creative test, set up the proven way.

    python launch.py plan   launch.json --brand brand.json      # dry run: prints exactly what would be created
    python launch.py create launch.json --brand brand.json      # creates everything PAUSED, writes a receipt
    python launch.py create launch.json --brand brand.json --activate   # same, but turns the new ad sets on

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
    b.setdefault("daily_budget_usd", 100)
    b.setdefault("countries", ["US"])
    b.setdefault("age_min", 18); b.setdefault("age_max", 65)
    b.setdefault("exclude_audience_ids", [])
    b.setdefault("cta", "SHOP_NOW")
    b.setdefault("ads_per_adset_max", 10)
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
    print(f"\nTotal new daily budget: ${total}/day. Everything is created PAUSED unless --activate.")
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["plan", "create"]); ap.add_argument("launch"); ap.add_argument("--brand", required=True)
    ap.add_argument("--activate", action="store_true")
    a = ap.parse_args()
    b = load_brand(a.brand); launch = json.load(open(a.launch, encoding="utf-8-sig"))
    groups = group_assets(launch, b, Path(a.launch).resolve().parent)
    g = Graph(token(b))
    cid = find_campaign(g, b)
    print_plan(groups, b, cid)
    if a.cmd == "create":
        create(groups, b, g, a.activate)


if __name__ == "__main__":
    main()
