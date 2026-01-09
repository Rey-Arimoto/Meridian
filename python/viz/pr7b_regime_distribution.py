#!/usr/bin/env python3
"""
PR7B: Regime Distribution

Purpose: Visualize regime distribution.
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


def create_regime_distribution(df: pd.DataFrame, output_path: str):
    """Create histogram of regime distribution."""

    # Fill missing regimes with "unknown"
    df["regime"] = df["regime"].fillna("unknown")

    # Count regimes
    regime_counts = Counter(df["regime"])

    # Sort regimes for consistent display
    preferred_order = [
        "stable_range",
        "emerging_trend",
        "volatile_noise",
        "liquidity_stress",
        "regime_transition",
        "post_stress_reset",
        "unknown",
    ]
    regimes = [r for r in preferred_order if r in regime_counts]
    # Add any other regimes not in preferred order
    for r in regime_counts:
        if r not in regimes:
            regimes.append(r)

    counts = [regime_counts[r] for r in regimes]

    # Color map
    color_map = {
        "stable_range": "lightgreen",
        "emerging_trend": "gold",
        "volatile_noise": "orange",
        "liquidity_stress": "red",
        "regime_transition": "darkred",
        "post_stress_reset": "lightblue",
        "unknown": "gray",
    }
    colors = [color_map.get(r, "gray") for r in regimes]

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))

    bars = ax.bar(regimes, counts, color=colors, alpha=0.8, edgecolor="black")

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

    ax.set_xlabel("Regime", fontweight="bold", fontsize=12)
    ax.set_ylabel("Count", fontweight="bold", fontsize=12)
    ax.set_title("Regime Distribution", fontweight="bold", fontsize=14)
    ax.grid(True, alpha=0.3, axis="y")

    # Rotate x-axis labels for readability
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    return regime_counts


def main():
    parser = argparse.ArgumentParser(
        description="PR7B Regime Distribution: Visualize regime distribution"
    )
    parser.add_argument("csv_path", help="Path to meridian_log.csv")
    parser.add_argument("--out", default="pr7b_regime_dist.png", help="Output PNG file (default: pr7b_regime_dist.png)")

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

    # Create distribution plot
    try:
        regime_counts = create_regime_distribution(df, args.out)
        print(f"✓ Regime distribution saved to: {args.out}")
        print(f"\nRegime Distribution:")
        for regime, count in sorted(regime_counts.items(), key=lambda x: -x[1]):
            pct = count / len(df) * 100
            print(f"  {regime:20s}: {count:6d} ({pct:5.1f}%)")
    except Exception as e:
        print(f"Error creating distribution plot: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
