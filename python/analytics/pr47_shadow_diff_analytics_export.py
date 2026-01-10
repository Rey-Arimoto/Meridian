#!/usr/bin/env python3
"""
PR47: v0.5 Shadow Diff Analytics Export (Daily Summary, READ-ONLY)

Purpose:
    Aggregate and export v1/v2 decision divergence data from execution logs
    into machine-readable CSV/JSON formats for comparison analysis.

Constitutional Constraints:
    - READ-ONLY: No execution logic, order, or weight changes
    - Warning-only: Exit code always 0, continue on missing columns
    - Non-evaluative: No good/bad, win/loss, correct/wrong vocabulary
    - Non-numeric restriction applies to summary text, not aggregation values
    - v0.4 boundary protection: No featurization of confidence_reason

Input:
    - Execution log CSV (with PR44-46 fields)
    - CLI args: --log_path, --out_dir, --day (optional)

Output:
    - analytics_out/pr47_shadow_diff_daily_summary.csv (daily aggregates)
    - analytics_out/pr47_shadow_diff_overall_summary.json (overall aggregates)

Aggregation Items:
    - Basic metrics: ticks_total, shadow_present_ticks, diff_mode_on_ticks
    - Diff status counts: ALIGNED/DIVERGED/UNAVAILABLE
    - Diff pair counts: v1_vs_v2/v2_vs_v1/UNKNOWN
    - Semantics status counts: AVAILABLE/UNAVAILABLE
    - Semantics tag counts: ALIGNED/DIVERGED_RULE_OVERLAY/DIVERGED_UNKNOWN/NO_SHADOW
    - By regime, by intent_primary (if columns exist)

Warning-only: Always exits with code 0.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="PR47: Shadow Diff Analytics Export (READ-ONLY)"
    )
    parser.add_argument(
        "--log_path",
        type=str,
        default="meridian_phase1_log.csv",
        help="Path to execution log CSV (default: meridian_phase1_log.csv)",
    )
    parser.add_argument(
        "--out_dir",
        type=str,
        default="analytics_out",
        help="Output directory for analytics files (default: analytics_out)",
    )
    parser.add_argument(
        "--day",
        type=str,
        default=None,
        help="Optional: YYYY-MM-DD to filter specific day (default: all dates)",
    )
    return parser.parse_args()


def load_log(log_path: str) -> Optional[pd.DataFrame]:
    """
    Load execution log CSV.

    Returns None if file not found or unreadable (warning-only).
    """
    warnings = []

    if not os.path.exists(log_path):
        warnings.append(f"Log file not found: {log_path}")
        print(f"[WARNING] {warnings[-1]}")
        return None

    try:
        df = pd.read_csv(log_path)
        print(f"[INFO] Loaded {len(df)} rows from {log_path}")
        return df
    except Exception as e:
        warnings.append(f"Failed to read log file: {e}")
        print(f"[WARNING] {warnings[-1]}")
        return None


def extract_date_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract date column from timestamp_utc.

    Warning-only: If timestamp_utc missing, add empty date column.
    """
    if "timestamp_utc" not in df.columns:
        print("[WARNING] timestamp_utc column missing, cannot extract dates")
        df["date"] = "UNKNOWN"
        return df

    try:
        # Parse ISO-8601 timestamp and extract date
        df["date"] = pd.to_datetime(df["timestamp_utc"]).dt.date.astype(str)
    except Exception as e:
        print(f"[WARNING] Failed to parse timestamp_utc: {e}")
        df["date"] = "UNKNOWN"

    return df


def compute_overall_aggregates(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute overall (all-time) aggregates.

    Warning-only: If required columns missing, use safe defaults.
    """
    aggregates = {
        "ticks_total": len(df),
        "shadow_present_ticks": 0,
        "diff_mode_on_ticks": 0,
        "diff_status_counts": {},
        "diff_pair_counts": {},
        "semantics_status_counts": {},
        "semantics_tag_counts": {},
    }

    # Shadow present (v5_shadow_decision_action exists and not empty)
    if "v5_shadow_decision_action" in df.columns:
        aggregates["shadow_present_ticks"] = int(df["v5_shadow_decision_action"].notna().sum())
    else:
        print("[WARNING] v5_shadow_decision_action column missing")

    # Diff mode ON
    if "v5_decision_diff_mode" in df.columns:
        aggregates["diff_mode_on_ticks"] = int((df["v5_decision_diff_mode"] == "ON").sum())
    else:
        print("[WARNING] v5_decision_diff_mode column missing")

    # Diff status counts (ALIGNED/DIVERGED/UNAVAILABLE)
    if "v5_decision_diff_status" in df.columns:
        aggregates["diff_status_counts"] = {k: int(v) for k, v in df["v5_decision_diff_status"].value_counts().to_dict().items()}
    else:
        print("[WARNING] v5_decision_diff_status column missing")

    # Diff pair counts (v1_vs_v2/v2_vs_v1/UNKNOWN)
    if "v5_decision_diff_pair" in df.columns:
        aggregates["diff_pair_counts"] = {k: int(v) for k, v in df["v5_decision_diff_pair"].value_counts().to_dict().items()}
    else:
        print("[WARNING] v5_decision_diff_pair column missing")

    # Semantics status counts (AVAILABLE/UNAVAILABLE)
    if "v5_decision_diff_semantics_status" in df.columns:
        aggregates["semantics_status_counts"] = {k: int(v) for k, v in df["v5_decision_diff_semantics_status"].value_counts().to_dict().items()}
    else:
        print("[WARNING] v5_decision_diff_semantics_status column missing")

    # Semantics tag counts (ALIGNED/DIVERGED_RULE_OVERLAY/DIVERGED_UNKNOWN/NO_SHADOW)
    if "v5_decision_diff_semantics_tag" in df.columns:
        aggregates["semantics_tag_counts"] = {k: int(v) for k, v in df["v5_decision_diff_semantics_tag"].value_counts().to_dict().items()}
    else:
        print("[WARNING] v5_decision_diff_semantics_tag column missing")

    return aggregates


def compute_daily_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute daily aggregates.

    Returns DataFrame with columns:
        - date
        - ticks_total
        - shadow_present_ticks
        - diff_aligned, diff_diverged, diff_unavailable
        - semantics_aligned, semantics_diverged_rule_overlay, semantics_diverged_unknown, semantics_no_shadow
        - pair_v1_vs_v2, pair_v2_vs_v1, pair_unknown

    Warning-only: Missing columns → 0 counts.
    """
    if "date" not in df.columns:
        print("[WARNING] date column missing, cannot compute daily aggregates")
        return pd.DataFrame()

    # Group by date
    daily = df.groupby("date").agg(ticks_total=("date", "count")).reset_index()

    # Shadow present
    if "v5_shadow_decision_action" in df.columns:
        shadow_counts = df[df["v5_shadow_decision_action"].notna()].groupby("date").size()
        daily = daily.merge(shadow_counts.rename("shadow_present_ticks"), on="date", how="left")
        daily["shadow_present_ticks"] = daily["shadow_present_ticks"].fillna(0).astype(int)
    else:
        daily["shadow_present_ticks"] = 0

    # Diff status counts
    if "v5_decision_diff_status" in df.columns:
        diff_status = df.groupby(["date", "v5_decision_diff_status"]).size().unstack(fill_value=0)
        for status in ["ALIGNED", "DIVERGED", "UNAVAILABLE"]:
            col_name = f"diff_{status.lower()}"
            if status in diff_status.columns:
                daily = daily.merge(diff_status[status].rename(col_name), on="date", how="left")
                daily[col_name] = daily[col_name].fillna(0).astype(int)
            else:
                daily[col_name] = 0
    else:
        daily["diff_aligned"] = 0
        daily["diff_diverged"] = 0
        daily["diff_unavailable"] = 0

    # Semantics tag counts
    if "v5_decision_diff_semantics_tag" in df.columns:
        semantics_tag = df.groupby(["date", "v5_decision_diff_semantics_tag"]).size().unstack(fill_value=0)
        tag_map = {
            "ALIGNED": "semantics_aligned",
            "DIVERGED_RULE_OVERLAY": "semantics_diverged_rule_overlay",
            "DIVERGED_UNKNOWN": "semantics_diverged_unknown",
            "NO_SHADOW": "semantics_no_shadow",
        }
        for tag, col_name in tag_map.items():
            if tag in semantics_tag.columns:
                daily = daily.merge(semantics_tag[tag].rename(col_name), on="date", how="left")
                daily[col_name] = daily[col_name].fillna(0).astype(int)
            else:
                daily[col_name] = 0
    else:
        daily["semantics_aligned"] = 0
        daily["semantics_diverged_rule_overlay"] = 0
        daily["semantics_diverged_unknown"] = 0
        daily["semantics_no_shadow"] = 0

    # Pair counts
    if "v5_decision_diff_pair" in df.columns:
        pair = df.groupby(["date", "v5_decision_diff_pair"]).size().unstack(fill_value=0)
        pair_map = {
            "v1_vs_v2": "pair_v1_vs_v2",
            "v2_vs_v1": "pair_v2_vs_v1",
            "UNKNOWN": "pair_unknown",
        }
        for pair_name, col_name in pair_map.items():
            if pair_name in pair.columns:
                daily = daily.merge(pair[pair_name].rename(col_name), on="date", how="left")
                daily[col_name] = daily[col_name].fillna(0).astype(int)
            else:
                daily[col_name] = 0
    else:
        daily["pair_v1_vs_v2"] = 0
        daily["pair_v2_vs_v1"] = 0
        daily["pair_unknown"] = 0

    return daily


def compute_regime_breakdown(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Compute breakdown by regime.

    Returns dict: {regime: {diff_status_counts, semantics_tag_counts}}

    Warning-only: If regime column missing, return empty dict.
    """
    if "regime" not in df.columns:
        print("[WARNING] regime column missing, skipping regime breakdown")
        return {}

    breakdown = {}

    for regime in df["regime"].unique():
        regime_df = df[df["regime"] == regime]

        regime_agg = {
            "ticks_total": len(regime_df),
            "diff_status_counts": {},
            "semantics_tag_counts": {},
        }

        if "v5_decision_diff_status" in df.columns:
            regime_agg["diff_status_counts"] = {k: int(v) for k, v in regime_df["v5_decision_diff_status"].value_counts().to_dict().items()}

        if "v5_decision_diff_semantics_tag" in df.columns:
            regime_agg["semantics_tag_counts"] = {k: int(v) for k, v in regime_df["v5_decision_diff_semantics_tag"].value_counts().to_dict().items()}

        breakdown[str(regime)] = regime_agg

    return breakdown


def compute_intent_breakdown(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Compute breakdown by intent_primary.

    Returns dict: {intent: {diff_status_counts, semantics_tag_counts}}

    Warning-only: If intent_primary column missing, return empty dict.
    """
    if "intent_primary" not in df.columns:
        print("[WARNING] intent_primary column missing, skipping intent breakdown")
        return {}

    breakdown = {}

    for intent in df["intent_primary"].unique():
        intent_df = df[df["intent_primary"] == intent]

        intent_agg = {
            "ticks_total": len(intent_df),
            "diff_status_counts": {},
            "semantics_tag_counts": {},
        }

        if "v5_decision_diff_status" in df.columns:
            intent_agg["diff_status_counts"] = {k: int(v) for k, v in intent_df["v5_decision_diff_status"].value_counts().to_dict().items()}

        if "v5_decision_diff_semantics_tag" in df.columns:
            intent_agg["semantics_tag_counts"] = {k: int(v) for k, v in intent_df["v5_decision_diff_semantics_tag"].value_counts().to_dict().items()}

        breakdown[str(intent)] = intent_agg

    return breakdown


def export_daily_csv(daily: pd.DataFrame, out_path: str) -> None:
    """Export daily aggregates to CSV."""
    try:
        daily.to_csv(out_path, index=False)
        print(f"[INFO] Exported daily summary to {out_path}")
    except Exception as e:
        print(f"[WARNING] Failed to export daily CSV: {e}")


def export_overall_json(
    overall: Dict[str, Any],
    regime_breakdown: Dict[str, Dict[str, Any]],
    intent_breakdown: Dict[str, Dict[str, Any]],
    log_path: str,
    out_path: str,
    df: pd.DataFrame,
) -> None:
    """Export overall aggregates to JSON."""
    try:
        # Extract date range
        if "date" in df.columns and len(df) > 0:
            dates = df["date"].unique()
            min_date = min(dates)
            max_date = max(dates)
        else:
            min_date = "UNKNOWN"
            max_date = "UNKNOWN"

        output = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "input_log_path": log_path,
            "date_range": {
                "min_date": str(min_date),
                "max_date": str(max_date),
            },
            "totals": overall,
            "breakdowns": {
                "by_regime": regime_breakdown,
                "by_intent_primary": intent_breakdown,
            },
        }

        with open(out_path, "w") as f:
            json.dump(output, f, indent=2)

        print(f"[INFO] Exported overall summary to {out_path}")
    except Exception as e:
        print(f"[WARNING] Failed to export overall JSON: {e}")


def main() -> int:
    """
    Main execution.

    Returns 0 (warning-only, never fails).
    """
    args = parse_args()

    print("=" * 60)
    print("PR47: Shadow Diff Analytics Export (READ-ONLY)")
    print("=" * 60)
    print(f"Log path: {args.log_path}")
    print(f"Output directory: {args.out_dir}")
    print(f"Day filter: {args.day if args.day else 'None (all dates)'}")
    print("=" * 60)

    # Load log
    df = load_log(args.log_path)
    if df is None or len(df) == 0:
        print("[WARNING] No data to process, exiting gracefully")
        return 0

    # Extract date column
    df = extract_date_column(df)

    # Filter by day if specified
    if args.day:
        df = df[df["date"] == args.day]
        print(f"[INFO] Filtered to {len(df)} rows for day {args.day}")
        if len(df) == 0:
            print(f"[WARNING] No data found for day {args.day}, exiting gracefully")
            return 0

    # Compute aggregates
    print("[INFO] Computing overall aggregates...")
    overall = compute_overall_aggregates(df)

    print("[INFO] Computing daily aggregates...")
    daily = compute_daily_aggregates(df)

    print("[INFO] Computing regime breakdown...")
    regime_breakdown = compute_regime_breakdown(df)

    print("[INFO] Computing intent breakdown...")
    intent_breakdown = compute_intent_breakdown(df)

    # Create output directory
    Path(args.out_dir).mkdir(parents=True, exist_ok=True)

    # Export files
    daily_csv_path = os.path.join(args.out_dir, "pr47_shadow_diff_daily_summary.csv")
    overall_json_path = os.path.join(args.out_dir, "pr47_shadow_diff_overall_summary.json")

    if not daily.empty:
        export_daily_csv(daily, daily_csv_path)
    else:
        print("[WARNING] Daily aggregates empty, skipping CSV export")

    export_overall_json(
        overall=overall,
        regime_breakdown=regime_breakdown,
        intent_breakdown=intent_breakdown,
        log_path=args.log_path,
        out_path=overall_json_path,
        df=df,
    )

    print("=" * 60)
    print("PR47: Export complete (warning-only, exit code 0)")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
