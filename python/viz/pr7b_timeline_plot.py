#!/usr/bin/env python3
"""
PR7B: Timeline Plot

Purpose: Visualize Regime → BaseAction → Overlay → Weight timeline.
Input: meridian_log.csv
Output: PNG timeline plot

READ-ONLY: No trading logic modification. No CSV schema changes.
"""

import sys
import os
import argparse
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


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


def map_regime_to_numeric(regime: str) -> float:
    """Map regime to numeric value for plotting."""
    regime_map = {
        "stable_range": 0,
        "emerging_trend": 1,
        "volatile_noise": 2,
        "liquidity_stress": 3,
        "regime_transition": 4,
        "post_stress_reset": 5,
        "unknown": 6,
    }
    return regime_map.get(regime, 6)


def map_action_to_numeric(action: str) -> float:
    """Map action to numeric value for plotting."""
    action_map = {
        "HOLD": 0,
        "BUY": 1,
        "SELL": -1,
        "FREEZE": -2,
        "unknown": -3,
    }
    return action_map.get(action, -3)


def create_timeline_plot(df: pd.DataFrame, output_path: str):
    """Create timeline plot with regime, action, weight, and overlay events."""

    # Parse timestamps
    df["timestamp"] = pd.to_datetime(df["timestamp_utc"], errors="coerce")

    # Extract and classify overlay rules
    df["overlay_rule"] = df["decision_reason"].apply(extract_overlay_rule)
    df["overlay_category"] = df["overlay_rule"].apply(classify_overlay_category)

    # Map regimes and actions to numeric values
    df["regime_numeric"] = df["regime"].fillna("unknown").apply(map_regime_to_numeric)
    df["action_numeric"] = df["action_label"].fillna("unknown").apply(map_action_to_numeric)

    # Create figure with subplots
    fig, axes = plt.subplots(4, 1, figsize=(14, 10), sharex=True)
    fig.suptitle("Meridian v0.2 Timeline: Regime → Action → Overlay → Weight", fontsize=14, fontweight="bold")

    # Subplot 1: Regime
    ax1 = axes[0]
    ax1.step(df["timestamp"], df["regime_numeric"], where="post", color="steelblue", linewidth=1.5)
    ax1.set_ylabel("Regime", fontweight="bold")
    ax1.set_yticks([0, 1, 2, 3, 4, 5, 6])
    ax1.set_yticklabels(["STABLE", "EMERGING", "VOLATILE", "LIQUIDITY", "TRANSITION", "POST_STRESS", "UNKNOWN"], fontsize=8)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(-0.5, 6.5)

    # Subplot 2: Action
    ax2 = axes[1]
    action_colors = df["action_numeric"].apply(
        lambda x: "green" if x == 1 else "red" if x == -1 else "orange" if x == -2 else "gray"
    )
    ax2.scatter(df["timestamp"], df["action_numeric"], c=action_colors, alpha=0.6, s=20)
    ax2.axhline(0, color="black", linewidth=0.5, linestyle="--", alpha=0.5)
    ax2.set_ylabel("Action", fontweight="bold")
    ax2.set_yticks([-3, -2, -1, 0, 1])
    ax2.set_yticklabels(["UNKNOWN", "FREEZE", "SELL", "HOLD", "BUY"], fontsize=8)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(-3.5, 1.5)

    # Subplot 3: Target Weight
    ax3 = axes[2]
    ax3.plot(df["timestamp"], df["target_weight"].fillna(0.0), color="purple", linewidth=1.5, alpha=0.7)
    ax3.fill_between(df["timestamp"], 0, df["target_weight"].fillna(0.0), color="purple", alpha=0.2)
    ax3.set_ylabel("Target Weight", fontweight="bold")
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(-0.05, max(1.0, df["target_weight"].max() * 1.1) if not df["target_weight"].isna().all() else 1.0)

    # Subplot 4: Overlay Events (only non-PASS_THROUGH)
    ax4 = axes[3]
    overlay_events = df[df["overlay_category"] != "PASS_THROUGH"].copy()

    # Color map for overlay categories
    overlay_colors = {
        "EMERGENCY_FREEZE": "red",
        "FAIL_CLOSED": "orange",
        "COOLDOWN_HOLD": "blue",
        "MAX_DELTA_CLAMP": "green",
        "MIN_THRESHOLD_HOLD": "cyan",
        "OTHER": "gray",
    }

    for _, row in overlay_events.iterrows():
        category = row["overlay_category"]
        color = overlay_colors.get(category, "gray")
        ax4.axvline(row["timestamp"], color=color, alpha=0.5, linewidth=1.5, linestyle="-")

    # Create legend for overlay colors
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=overlay_colors["EMERGENCY_FREEZE"], label="EMERGENCY_FREEZE"),
        Patch(facecolor=overlay_colors["FAIL_CLOSED"], label="FAIL_CLOSED"),
        Patch(facecolor=overlay_colors["COOLDOWN_HOLD"], label="COOLDOWN_HOLD"),
        Patch(facecolor=overlay_colors["MAX_DELTA_CLAMP"], label="MAX_DELTA_CLAMP"),
        Patch(facecolor=overlay_colors["MIN_THRESHOLD_HOLD"], label="MIN_THRESHOLD_HOLD"),
    ]
    ax4.legend(handles=legend_elements, loc="upper right", fontsize=7)

    ax4.set_ylabel("Overlay Events", fontweight="bold")
    ax4.set_ylim(0, 1)
    ax4.set_yticks([])
    ax4.grid(True, alpha=0.3, axis="x")

    # Format x-axis (time)
    ax4.set_xlabel("Time (UTC)", fontweight="bold")
    ax4.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
    plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # Tight layout
    plt.tight_layout(rect=[0, 0, 1, 0.97])

    # Save
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description="PR7B Timeline Plot: Visualize Meridian decision timeline"
    )
    parser.add_argument("csv_path", help="Path to meridian_log.csv")
    parser.add_argument("--out", default="pr7b_timeline.png", help="Output PNG file (default: pr7b_timeline.png)")
    parser.add_argument("--limit", type=int, help="Limit to first N rows")
    parser.add_argument("--from", dest="from_ts", help="Filter from timestamp (ISO format)")
    parser.add_argument("--to", dest="to_ts", help="Filter to timestamp (ISO format)")

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

    # Filter by timestamp if requested
    if args.from_ts:
        df = df[df["timestamp_utc"] >= args.from_ts]
    if args.to_ts:
        df = df[df["timestamp_utc"] <= args.to_ts]

    # Limit rows if requested
    if args.limit:
        df = df.head(args.limit)

    if df.empty:
        print("Error: No data after filters", file=sys.stderr)
        return 1

    # Create plot
    try:
        create_timeline_plot(df, args.out)
        print(f"✓ Timeline plot saved to: {args.out}")
        print(f"  Rows plotted: {len(df)}")
        print(f"  Period: {df['timestamp_utc'].iloc[0]} to {df['timestamp_utc'].iloc[-1]}")
    except Exception as e:
        print(f"Error creating plot: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
