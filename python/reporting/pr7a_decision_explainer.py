#!/usr/bin/env python3
"""
PR7A: Decision Explainer

Purpose: Explain each tick's decision in natural language.
Input: meridian_log.csv
Output: Human-readable explanation (stdout or --out file)

READ-ONLY: No trading logic modification. No CSV schema changes.
"""

import sys
import os
import argparse
from datetime import datetime
import pandas as pd


def extract_overlay_rule(decision_reason: str) -> str:
    """Extract overlay rule from decision_reason field using ' | overlay=' delimiter."""
    if not isinstance(decision_reason, str):
        return "unknown"

    parts = decision_reason.split(" | overlay=")
    if len(parts) >= 2:
        return parts[1].strip()
    return "unknown"


def explain_tick(row: pd.Series, index: int) -> str:
    """Generate natural language explanation for a single tick."""

    # Extract fields (fail-closed: default to "unknown" if missing)
    timestamp = row.get("timestamp_utc", "unknown")
    entropy_bp = row.get("entropy_bp", "unknown")
    regime = row.get("regime", "unknown")
    base_action = row.get("base_action", "unknown")
    target_weight = row.get("target_weight", "unknown")
    action_label = row.get("action_label", "unknown")
    decision_reason = row.get("decision_reason", "unknown")

    # Extract overlay rule from decision_reason
    overlay_rule = extract_overlay_rule(decision_reason)

    # Build explanation
    lines = []
    lines.append(f"{'='*70}")
    lines.append(f"Tick #{index + 1} | {timestamp}")
    lines.append(f"{'='*70}")

    # Market state
    lines.append(f"\n[Market State]")
    lines.append(f"  Entropy: {entropy_bp} bp")
    lines.append(f"  Regime: {regime}")

    # Constitutional decision
    lines.append(f"\n[Constitutional Decision]")
    lines.append(f"  Base Action: {base_action}")
    lines.append(f"  Policy Reason: {decision_reason}")

    # Safety overlay
    lines.append(f"\n[Safety Overlay]")
    lines.append(f"  Overlay Rule: {overlay_rule}")
    lines.append(f"  Final Target Weight: {target_weight}")
    lines.append(f"  Executed Action: {action_label}")

    # Explanation (emphasize "doing nothing" as positive)
    lines.append(f"\n[Explanation]")

    if action_label == "HOLD":
        lines.append(f"  ✓ DOING NOTHING (Capital Preservation)")
        lines.append(f"    The system chose NOT to trade. This is a positive outcome:")

        if "COOLDOWN_HOLD" in overlay_rule:
            lines.append(f"    - Cooldown protection prevented premature action")
            lines.append(f"    - Protecting against overtrading and slippage")
        elif "MIN_THRESHOLD_HOLD" in overlay_rule:
            lines.append(f"    - Change too small to justify transaction costs")
            lines.append(f"    - Avoiding unnecessary capital churn")
        elif "EMERGENCY_FREEZE" in overlay_rule:
            lines.append(f"    - Emergency freeze protected capital during crisis")
            lines.append(f"    - Constitutional safety mechanism activated")
        elif "FAIL_CLOSED" in overlay_rule:
            lines.append(f"    - Fail-closed safety: defaulted to zero exposure")
            lines.append(f"    - Preventing action under uncertainty")
        elif base_action == "PAUSE":
            lines.append(f"    - Regime indicated PAUSE: no action taken")
            lines.append(f"    - Constitutional restraint during uncertainty")
        else:
            lines.append(f"    - No change needed: optimal weight already achieved")

    elif action_label == "BUY":
        lines.append(f"  → BUYING (Increasing Exposure)")
        lines.append(f"    Regime: {regime} → BaseAction: {base_action}")

        if "MAX_DELTA_CLAMP" in overlay_rule:
            lines.append(f"    - Overlay clamped the increase for safety")
            lines.append(f"    - Gradual position building prevents overexposure")
        else:
            lines.append(f"    - Policy decision executed within safety bounds")

    elif action_label == "SELL":
        lines.append(f"  → SELLING (Decreasing Exposure)")
        lines.append(f"    Regime: {regime} → BaseAction: {base_action}")

        if "MAX_DELTA_CLAMP" in overlay_rule:
            lines.append(f"    - Overlay clamped the decrease for safety")
            lines.append(f"    - Gradual unwinding prevents panic selling")
        else:
            lines.append(f"    - Policy decision executed within safety bounds")

    elif action_label == "FREEZE":
        lines.append(f"  ⚠ EMERGENCY FREEZE (Constitutional Halt)")
        lines.append(f"    - Critical entropy threshold exceeded")
        lines.append(f"    - All positions frozen to protect capital")
        lines.append(f"    - This is the system working as designed")

    else:
        lines.append(f"  Status: {action_label}")

    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="PR7A Decision Explainer: Explain each tick's decision in natural language"
    )
    parser.add_argument("csv_path", help="Path to meridian_log.csv")
    parser.add_argument("--limit", type=int, help="Limit to first N rows")
    parser.add_argument("--from", dest="from_ts", help="Filter from timestamp (ISO format)")
    parser.add_argument("--to", dest="to_ts", help="Filter to timestamp (ISO format)")
    parser.add_argument("--out", help="Output file (default: stdout)")

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

    # Filter by timestamp if requested
    if args.from_ts:
        df = df[df["timestamp_utc"] >= args.from_ts]
    if args.to_ts:
        df = df[df["timestamp_utc"] <= args.to_ts]

    # Limit rows if requested
    if args.limit:
        df = df.head(args.limit)

    if df.empty:
        print("No data to explain (empty CSV or filters matched no rows)", file=sys.stderr)
        return 1

    # Generate explanations
    explanations = []
    explanations.append("=" * 70)
    explanations.append("PR7A: Decision Explainer")
    explanations.append("=" * 70)
    explanations.append(f"CSV: {args.csv_path}")
    explanations.append(f"Rows: {len(df)}")
    explanations.append("")

    for idx, row in df.iterrows():
        explanations.append(explain_tick(row, idx))

    # Output
    output_text = "\n".join(explanations)

    if args.out:
        with open(args.out, "w") as f:
            f.write(output_text)
        print(f"Explanation written to: {args.out}")
    else:
        print(output_text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
