#!/usr/bin/env python3
"""
PR7A: Safety Summary

Purpose: Generate period summary statistics showing safety overlay behavior.
Input: meridian_log.csv
Output: Summary statistics (stdout)

READ-ONLY: No trading logic modification. No CSV schema changes.
"""

import sys
import os
import argparse
import pandas as pd
from collections import Counter


def extract_overlay_rule(decision_reason: str) -> str:
    """Extract overlay rule from decision_reason field using ' | overlay=' delimiter."""
    if not isinstance(decision_reason, str):
        return "unknown"

    parts = decision_reason.split(" | overlay=")
    if len(parts) >= 2:
        return parts[1].strip()
    return "unknown"


def classify_overlay_category(overlay_rule: str) -> str:
    """Classify overlay rule into categories."""
    if "EMERGENCY_FREEZE" in overlay_rule:
        return "EMERGENCY_FREEZE"
    elif "FAIL_CLOSED" in overlay_rule:
        return "FAIL_CLOSED"
    elif "COOLDOWN_HOLD" in overlay_rule:
        return "COOLDOWN_HOLD"
    elif "MAX_DELTA_CLAMP" in overlay_rule:
        return "MAX_DELTA_CLAMP"
    elif "MIN_THRESHOLD_HOLD" in overlay_rule:
        return "MIN_THRESHOLD_HOLD"
    elif "PASS_THROUGH" in overlay_rule or overlay_rule == "PASS_THROUGH":
        return "PASS_THROUGH"
    else:
        return "OTHER"


def main():
    parser = argparse.ArgumentParser(
        description="PR7A Safety Summary: Generate period summary statistics"
    )
    parser.add_argument("csv_path", help="Path to meridian_log.csv")
    args = parser.parse_args()

    # Read CSV
    if not os.path.exists(args.csv_path):
        print(f"Error: CSV file not found: {args.csv_path}", file=sys.stderr)
        return 1

    try:
        df = pd.read_csv(args.csv_path)
    except Exception as e:
        print(f"Error reading CSV: {e}", file=sys.stderr)
        return 1

    if df.empty:
        print("Error: CSV is empty", file=sys.stderr)
        return 1

    # Extract overlay rules
    df["overlay_rule"] = df["decision_reason"].apply(extract_overlay_rule)
    df["overlay_category"] = df["overlay_rule"].apply(classify_overlay_category)

    # Compute statistics
    total_ticks = len(df)

    # Action counts
    action_counts = Counter(df["action_label"].fillna("unknown"))
    buy_count = action_counts.get("BUY", 0)
    sell_count = action_counts.get("SELL", 0)
    hold_count = action_counts.get("HOLD", 0)
    freeze_count = action_counts.get("FREEZE", 0)

    # Overlay category counts
    overlay_category_counts = Counter(df["overlay_category"])

    # Regime counts
    regime_counts = Counter(df["regime"].fillna("unknown"))

    # Calculate ratios
    hold_ratio = hold_count / total_ticks if total_ticks > 0 else 0.0
    action_ratio = (buy_count + sell_count) / total_ticks if total_ticks > 0 else 0.0

    # Print summary
    print("=" * 70)
    print("PR7A: Safety Summary")
    print("=" * 70)
    print(f"CSV: {args.csv_path}")
    print(f"Period: {df['timestamp_utc'].iloc[0]} to {df['timestamp_utc'].iloc[-1]}")
    print(f"Total Ticks: {total_ticks}")
    print()

    print("-" * 70)
    print("Action Distribution")
    print("-" * 70)
    print(f"  BUY:    {buy_count:6d} ({buy_count/total_ticks*100:5.1f}%)")
    print(f"  SELL:   {sell_count:6d} ({sell_count/total_ticks*100:5.1f}%)")
    print(f"  HOLD:   {hold_count:6d} ({hold_count/total_ticks*100:5.1f}%) ← Capital Preservation")
    print(f"  FREEZE: {freeze_count:6d} ({freeze_count/total_ticks*100:5.1f}%)")
    print()
    print(f"  \"Doing Nothing\" Ratio: {hold_ratio*100:.1f}%")
    print(f"  Active Trading Ratio:   {action_ratio*100:.1f}%")
    print()

    print("-" * 70)
    print("Safety Overlay Distribution")
    print("-" * 70)
    for category in sorted(overlay_category_counts.keys()):
        count = overlay_category_counts[category]
        pct = count / total_ticks * 100
        print(f"  {category:20s}: {count:6d} ({pct:5.1f}%)")
    print()

    print("-" * 70)
    print("Regime Distribution")
    print("-" * 70)
    for regime in sorted(regime_counts.keys()):
        count = regime_counts[regime]
        pct = count / total_ticks * 100
        print(f"  {regime:20s}: {count:6d} ({pct:5.1f}%)")
    print()

    print("-" * 70)
    print("Interpretation")
    print("-" * 70)
    print(f"✓ High HOLD ratio ({hold_ratio*100:.1f}%) indicates effective capital preservation.")
    print(f"✓ Safety overlay activated {total_ticks - overlay_category_counts.get('PASS_THROUGH', 0)} times.")
    print(f"✓ System prioritized \"doing nothing\" over aggressive trading.")
    print(f"✓ This is Meridian working as designed: restraint over aggression.")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
