#!/usr/bin/env python3
"""
PR7B: Overlay Histogram

Purpose: Visualize overlay rule distribution.
Input: meridian_log.csv
Output: PNG histogram

READ-ONLY: No trading logic modification. No CSV schema changes.
"""

import sys
import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt
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


def create_overlay_histogram(df: pd.DataFrame, output_path: str):
    """Create histogram of overlay rule distribution."""

    # Extract and classify overlay rules
    df["overlay_rule"] = df["decision_reason"].apply(extract_overlay_rule)
    df["overlay_category"] = df["overlay_rule"].apply(classify_overlay_category)

    # Count overlay categories
    overlay_counts = Counter(df["overlay_category"])

    # Sort categories for consistent display
    categories = [
        "PASS_THROUGH",
        "COOLDOWN_HOLD",
        "MAX_DELTA_CLAMP",
        "MIN_THRESHOLD_HOLD",
        "FAIL_CLOSED",
        "EMERGENCY_FREEZE",
        "OTHER",
    ]
    categories = [c for c in categories if c in overlay_counts]

    counts = [overlay_counts[c] for c in categories]

    # Color map
    color_map = {
        "PASS_THROUGH": "lightgray",
        "COOLDOWN_HOLD": "steelblue",
        "MAX_DELTA_CLAMP": "green",
        "MIN_THRESHOLD_HOLD": "cyan",
        "FAIL_CLOSED": "orange",
        "EMERGENCY_FREEZE": "red",
        "OTHER": "gray",
    }
    colors = [color_map.get(c, "gray") for c in categories]

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))

    bars = ax.bar(categories, counts, color=colors, alpha=0.8, edgecolor="black")

    # Add count labels on bars
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{int(count)}",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    ax.set_xlabel("Overlay Rule", fontweight="bold", fontsize=12)
    ax.set_ylabel("Count", fontweight="bold", fontsize=12)
    ax.set_title("Safety Overlay Distribution", fontweight="bold", fontsize=14)
    ax.grid(True, alpha=0.3, axis="y")

    # Rotate x-axis labels for readability
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    return overlay_counts


def main():
    parser = argparse.ArgumentParser(
        description="PR7B Overlay Histogram: Visualize overlay rule distribution"
    )
    parser.add_argument("csv_path", help="Path to meridian_log.csv")
    parser.add_argument("--out", default="pr7b_overlay_hist.png", help="Output PNG file (default: pr7b_overlay_hist.png)")

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

    # Create histogram
    try:
        overlay_counts = create_overlay_histogram(df, args.out)
        print(f"✓ Overlay histogram saved to: {args.out}")
        print(f"\nOverlay Distribution:")
        for category, count in sorted(overlay_counts.items(), key=lambda x: -x[1]):
            pct = count / len(df) * 100
            print(f"  {category:20s}: {count:6d} ({pct:5.1f}%)")
    except Exception as e:
        print(f"Error creating histogram: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
