#!/usr/bin/env python3
"""meta_doctor: read-only health check of a Meta (Facebook/Instagram) setup. Changes nothing.

    META_ACCESS_TOKEN=... python meta_doctor.py [--env path/to/.env] [--json]

Reads the token from META_ACCESS_TOKEN (or META_ACCESS_TOKEN=... in --env; a UTF-8 BOM and CRLF are
stripped). Never prints the token. Checks: who the token is, granted scopes, expiry, businesses, ad accounts
(status, currency, time zone, spend cap), Pages and their linked Instagram accounts, datasets/pixels and when
they last fired, and whether each ad account can use each Instagram account. Standard library only.
"""
import argparse, json, os, sys, time, urllib.error, urllib.parse, urllib.request

API = "https://graph.facebook.com/v21.0"
STATUS = {1: "ACTIVE", 2: "DISABLED", 3: "UNSETTLED (billing)", 7: "PENDING_RISK_REVIEW", 8: "PENDING_SETTLEMENT",
          9: "IN_GRACE_PERIOD", 100: "PENDING_CLOSURE", 101: "CLOSED"}


def token_from(args):
    t = os.environ.get("META_ACCESS_TOKEN", "")
    if args.env:
        for line in open(args.env, encoding="utf-8-sig"):
            line = line.strip().replace("﻿", "")
            if line.startswith("META_ACCESS_TOKEN="):
                t = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not t:
        sys.exit("Set META_ACCESS_TOKEN or pass --env with META_ACCESS_TOKEN=...")
    return t


def get(path, tok, **params):
    params["access_token"] = tok
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    out = []
    while url:
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                d = json.load(r)
        except urllib.error.HTTPError as e:
            try:
                err = json.load(e).get("error", {})
            except Exception:
                err = {"message": str(e)}
            return {"error": f"({err.get('code')}) {err.get('message')}"}
        if not isinstance(d.get("data"), list):
            return d
        out += d["data"]
        url = d.get("paging", {}).get("next")
    return {"data": out}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--env"); ap.add_argument("--json", action="store_true")
    a = ap.parse_args(); tok = token_from(a)
    rep, issues = {}, []

    me = get("me", tok, fields="id,name"); rep["me"] = me
    if "error" in me:
        sys.exit(f"Token rejected: {me['error']}")
    perms = get("me/permissions", tok)
    rep["scopes"] = sorted(p["permission"] for p in perms.get("data", []) if p.get("status") == "granted")
    dbg = get("debug_token", tok, input_token=tok).get("data", {})
    exp = dbg.get("expires_at")
    rep["token"] = {"type": dbg.get("type"), "app": dbg.get("application"), "valid": dbg.get("is_valid"),
                    "expires": "never" if exp == 0 else (time.strftime("%Y-%m-%d", time.gmtime(exp)) if exp else "unknown")}
    if exp not in (0, None):
        issues.append("Token expires; use a system-user token with Never expiry (meta-api-access).")
    if dbg.get("type") == "USER" and "never" != rep["token"]["expires"]:
        issues.append("This is a personal user token; it will die with the person's session.")

    rep["businesses"] = get("me/businesses", tok, fields="id,name,verification_status").get("data", [])

    accts = get("me/adaccounts", tok, fields="id,name,account_status,currency,timezone_name,spend_cap,amount_spent,business{name}")
    rep["ad_accounts"] = []
    for x in accts.get("data", []):
        st = STATUS.get(x.get("account_status"), x.get("account_status"))
        if x.get("account_status") != 1:
            issues.append(f"Ad account {x.get('name')} is {st}.")
        px = get(f"{x['id']}/adspixels", tok, fields="id,name,last_fired_time,is_unavailable")
        ig = get(f"{x['id']}/instagram_accounts", tok, fields="id,username")
        pixels = px.get("data", [])
        if not pixels:
            issues.append(f"No dataset/pixel visible on ad account {x.get('name')}.")
        for p in pixels:
            lf = p.get("last_fired_time")
            if not lf or time.time() - time.mktime(time.strptime(lf[:19], "%Y-%m-%dT%H:%M:%S")) > 7 * 86400:
                issues.append(f"Pixel {p.get('name')} on {x.get('name')} has not fired in 7+ days "
                              f"(last: {lf or 'never'}): broken tracking, or an old pixel to unassign.")
        rep["ad_accounts"].append({"id": x["id"], "name": x.get("name"), "status": st, "currency": x.get("currency"),
                                   "timezone": x.get("timezone_name"), "spend_cap": x.get("spend_cap"),
                                   "business": (x.get("business") or {}).get("name"),
                                   "pixels": [{"id": p["id"], "name": p.get("name"), "last_fired": p.get("last_fired_time")} for p in pixels],
                                   "instagram_usable": [i.get("username") or i["id"] for i in ig.get("data", [])],
                                   "instagram_error": ig.get("error")})

    pages = get("me/accounts", tok, fields="id,name,instagram_business_account{id,username},tasks")
    rep["pages"] = [{"id": p["id"], "name": p.get("name"), "tasks": p.get("tasks"),
                     "instagram": (p.get("instagram_business_account") or {}).get("username")} for p in pages.get("data", [])]
    for p in rep["pages"]:
        if not p["instagram"]:
            issues.append(f"Page {p['name']} has no linked Instagram professional account.")
    if not accts.get("data"):
        issues.append("Token sees no ad accounts: assign the ad account to the system user (meta-api-access §3).")
    for need in ("ads_read",):
        if need not in rep["scopes"] and "ads_management" not in rep["scopes"]:
            issues.append("Token has neither ads_read nor ads_management.")
    rep["issues"] = issues

    if a.json:
        print(json.dumps(rep, indent=1)); return
    print(f"Token: {me.get('name')} ({rep['token']['type']}, app {rep['token']['app']}), expires {rep['token']['expires']}")
    print("Scopes:", ", ".join(rep["scopes"]) or "none")
    for b in rep["businesses"]:
        print(f"Business: {b.get('name')}  verification: {b.get('verification_status')}")
    for x in rep["ad_accounts"]:
        print(f"\nAd account {x['name']} ({x['id']}): {x['status']}, {x['currency']}, {x['timezone']}, owner {x['business']}")
        for p in x["pixels"]:
            print(f"  pixel {p['name']} ({p['id']}) last fired {p['last_fired'] or 'never'}")
        print(f"  Instagram usable for ads: {', '.join(x['instagram_usable']) or 'none'}" + (f"  [{x['instagram_error']}]" if x["instagram_error"] else ""))
    for p in rep["pages"]:
        print(f"\nPage {p['name']} ({p['id']}): Instagram {p['instagram'] or 'NOT LINKED'}; tasks {', '.join(p['tasks'] or [])}")
    print("\nIssues:" if issues else "\nNo issues found.")
    for i in issues:
        print(" -", i)


if __name__ == "__main__":
    main()
