#!/usr/bin/env python3
"""Export the learned agency playbook into skills/meta-test-launch/playbook.json (numbers only, no names or ids).

    python tools/export_playbook.py --lifecycle <lifecycle_rules.json> [--secondary <admimic lifecycle.json>]

The source is the nightly learner that watches the agency's real changes (lifecycle_rules.json). This copies the
rule thresholds and the medians behind them, strips every ad, ad set, audience and account name, and stamps the
date. launch.py reads playbook.json for its defaults and for `review`.
"""
import argparse, datetime as dt, json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "skills" / "meta-test-launch" / "playbook.json"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--lifecycle", required=True); ap.add_argument("--secondary")
    a = ap.parse_args()
    L = json.load(open(a.lifecycle, encoding="utf-8"))
    th = L["model"]["rules"]["thresholds_all"]
    launch, kill, grad, scale, first, deliv = L["launch"], L["kill"], L["graduate"], L["scale"], L["first_decision"], L["delivery"]
    tgt = max(launch["targeting"], key=lambda t: t["n_ad_sets"])
    pb = {
        "source": "learned nightly from a DTC agency's real Meta changes (account names and ids removed)",
        "data_through": L.get("data_through"), "exported": dt.date.today().isoformat(),
        "launch": {
            "daily_budget_usd": launch["launch_budget_median"],
            "ads_per_adset_median": launch["ads_per_ad_set_median"], "ads_per_adset_range": launch["ads_per_ad_set_range"],
            "days_between_batches_median": sorted(launch["batch_gap_days"])[len(launch["batch_gap_days"]) // 2],
            "test_adsets_observed": launch["test_ad_sets"],
            "age": tgt["age"], "advantage_audience": bool(tgt["advantage_audience"]),
            "exclude_past_customers": bool(tgt["exclusions"]),
            "bid_strategy": launch["bidding"][0]["bid_strategy"], "optimization": launch["bidding"][0]["optimization"],
            "single_ads_added_to_old_adsets": len(launch.get("added_to_existing", [])),
        },
        "delivery": {"top_ad_share_of_adset_spend_median": deliv["top_ad_share_of_ad_set_spend_median"]},
        "review_rules": {
            "kill_no_purchase_after_spend": th["zero_kill_spend"],
            "kill_lifetime_spend_min": th["kill_spend"], "kill_lifetime_roas_below_x_floor": th["kill_rel"],
            "kill_7d_spend_min": th["kill_s7"], "kill_7d_roas_below_x_floor": th["kill_r7"],
            "graduate_7d_spend_min": th["up_s7"], "graduate_7d_roas_at_least_x_floor": th["up_r7"],
            "graduate_share_of_adset_spend_min": th["up_share"],
            "first_raise_step": 2.0,
            "raise_step_median": scale["up_step_median"], "cut_step_median": scale["down_step_median"],
            "days_between_raises_median": scale["days_between_raises_median"],
            "min_days_before_roas_kill": 7,
        },
        "timing": {
            "first_decision_days_median": first["days_median"], "first_decision_spend_median": round(first["spend_median"]),
            "kill_spend_median": round(kill["spend_median"]), "graduated": grad["n_graduated"],
            "graduate_first_raise_spend_median": round(grad["first_raise_spend_median"]),
            "graduate_first_raise_days_median": grad["first_raise_days_median"],
        },
        "rule_accuracy_holdout": {k: L["model"]["rules"]["holdout"]["by_class"]["kill"][k] for k in ("precision", "recall")},
    }
    if a.secondary:
        S = json.load(open(a.secondary, encoding="utf-8"))["summary"]
        pb["second_account"] = {k: S.get(k) for k in ("cells_per_launch", "days_between_launches", "ads_at_launch",
                                                       "start_budget", "kill_spend", "first_move_day", "up_size", "down_size")}
    txt = json.dumps(pb, indent=1)
    for bad in ("moon", "birthdate", "akm", "act_"):
        assert bad not in txt.lower(), f"private word '{bad}' leaked into playbook"
    OUT.write_text(txt + "\n", encoding="utf-8")
    print("wrote", OUT, "data through", pb["data_through"])


if __name__ == "__main__":
    main()
