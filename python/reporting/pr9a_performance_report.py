#!/usr/bin/env python3
"""
PR9A: Performance & Risk Summary Report

Purpose: Calculate performance and risk metrics from meridian_log.csv.
Input: meridian_log.csv
Output: stdout + optional Markdown file

READ-ONLY: No trading logic modification. No CSV schema changes.
Deterministic: No network, no randomness.
"""

import sys
import os
import argparse
from datetime import datetime
import pandas as pd
import numpy as np


def extract_overlay_rule(decision_reason: str) -> str:
    """Extract overlay rule from decision_reason field."""
    if not isinstance(decision_reason, str):
        return "unknown"
    parts = decision_reason.split(" | overlay=")
    if len(parts) >= 2:
        return parts[1].strip()
    return "unknown"


def calculate_max_drawdown(equity_series: pd.Series) -> float:
    """
    Calculate maximum drawdown from equity time series.

    Max Drawdown = max((peak - valley) / peak) over all time windows
    Returns percentage (e.g., 15.0 for 15% drawdown)
    """
    if equity_series.empty or equity_series.isna().all():
        return np.nan

    # Calculate running maximum (peak)
    running_max = equity_series.expanding().max()

    # Calculate drawdown at each point
    drawdown = (running_max - equity_series) / running_max

    # Maximum drawdown as percentage
    max_dd = drawdown.max() * 100.0

    return max_dd if not np.isnan(max_dd) else 0.0


def generate_report(df: pd.DataFrame, csv_path: str) -> str:
    """Generate performance and risk summary report."""

    lines = []
    lines.append("=" * 70)
    lines.append("PR9A: Performance & Risk Summary Report")
    lines.append("=" * 70)
    lines.append(f"CSV: {csv_path}")
    lines.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("")

    total_rows = len(df)
    lines.append(f"Total Rows: {total_rows:,}")
    lines.append("")

    # (1) Period
    lines.append("-" * 70)
    lines.append("Period")
    lines.append("-" * 70)

    if "timestamp_utc" in df.columns and total_rows > 0:
        start_ts = df["timestamp_utc"].iloc[0]
        end_ts = df["timestamp_utc"].iloc[-1]
        lines.append(f"Start: {start_ts}")
        lines.append(f"End:   {end_ts}")
    else:
        lines.append(f"Start: N/A")
        lines.append(f"End:   N/A")

    lines.append("")

    # (2) Equity-based Performance
    lines.append("-" * 70)
    lines.append("Equity-Based Performance")
    lines.append("-" * 70)

    has_equity = "equity" in df.columns and not df["equity"].isna().all()

    if has_equity:
        equity = df["equity"].dropna()
        if len(equity) > 0:
            start_equity = equity.iloc[0]
            end_equity = equity.iloc[-1]
            total_return_pct = ((end_equity / start_equity) - 1.0) * 100.0 if start_equity != 0 else 0.0
            max_dd_pct = calculate_max_drawdown(equity)

            lines.append(f"Start Equity:      {start_equity:.6f}")
            lines.append(f"End Equity:        {end_equity:.6f}")
            lines.append(f"Total Return:      {total_return_pct:+.2f}%")
            lines.append(f"Max Drawdown:      {max_dd_pct:.2f}%")
        else:
            lines.append("Performance Section: N/A (equity column has no valid values)")
    else:
        lines.append("Performance Section: N/A (equity column missing or all NaN)")

    lines.append("")
    lines.append("Note: Annualized returns not provided (tick frequency unknown).")
    lines.append("")

    # (3) Exposure / Activity
    lines.append("-" * 70)
    lines.append("Exposure / Activity")
    lines.append("-" * 70)

    if "target_weight" in df.columns:
        weights = df["target_weight"].dropna()
        if len(weights) > 0:
            avg_abs_weight = weights.abs().mean()
            max_abs_weight = weights.abs().max()
            lines.append(f"Avg |Weight|:       {avg_abs_weight:.4f}")
            lines.append(f"Max |Weight|:       {max_abs_weight:.4f}")
        else:
            lines.append(f"Avg |Weight|:       N/A")
            lines.append(f"Max |Weight|:       N/A")
    else:
        lines.append(f"Avg |Weight|:       N/A (column missing)")
        lines.append(f"Max |Weight|:       N/A (column missing)")

    lines.append("")

    # Action counts
    if "action_label" in df.columns:
        action_counts = df["action_label"].fillna("unknown").value_counts()
        lines.append("Action Counts:")
        for action in ["BUY", "SELL", "HOLD", "FREEZE", "unknown"]:
            count = action_counts.get(action, 0)
            pct = (count / total_rows * 100.0) if total_rows > 0 else 0.0
            lines.append(f"  {action:10s}: {count:6d} ({pct:5.1f}%)")

        hold_count = action_counts.get("HOLD", 0)
        hold_ratio = (hold_count / total_rows * 100.0) if total_rows > 0 else 0.0
        lines.append("")
        lines.append(f"HOLD Ratio:         {hold_ratio:.1f}%")
    else:
        lines.append("Action Counts:      N/A (column missing)")

    lines.append("")

    # (4) Regime / Overlay Summary
    lines.append("-" * 70)
    lines.append("Regime Distribution")
    lines.append("-" * 70)

    if "regime" in df.columns:
        regime_counts = df["regime"].fillna("unknown").value_counts()
        for regime, count in regime_counts.items():
            pct = (count / total_rows * 100.0) if total_rows > 0 else 0.0
            lines.append(f"  {regime:25s}: {count:6d} ({pct:5.1f}%)")
    else:
        lines.append("  Regime data: N/A (column missing)")

    lines.append("")
    lines.append("-" * 70)
    lines.append("Safety Overlay Distribution (Top 5)")
    lines.append("-" * 70)

    if "decision_reason" in df.columns:
        df_temp = df.copy()
        df_temp["overlay_rule"] = df_temp["decision_reason"].apply(extract_overlay_rule)
        overlay_counts = df_temp["overlay_rule"].value_counts()

        for overlay, count in overlay_counts.head(5).items():
            pct = (count / total_rows * 100.0) if total_rows > 0 else 0.0
            lines.append(f"  {overlay:30s}: {count:6d} ({pct:5.1f}%)")

        if len(overlay_counts) > 5:
            lines.append(f"  ... and {len(overlay_counts) - 5} more")
    else:
        lines.append("  Overlay data: N/A (column missing)")

    lines.append("")

    # (5) Health Gate Reference
    lines.append("-" * 70)
    lines.append("Data Quality Gate Reference")
    lines.append("-" * 70)
    lines.append("")
    lines.append("IMPORTANT: Run PR8A/PR8B integrity validation before using this report.")
    lines.append("")
    lines.append("Recommended workflow:")
    lines.append("  1. python3 python/validation/pr8a_log_integrity_invariants.py <csv>")
    lines.append("  2. python3 python/tools/pr8b_integrity_gate_runner.py <csv>")
    lines.append("  3. Review this PR9A performance report")
    lines.append("")
    lines.append("PR8A/PR8B ensure data integrity before performance calculation.")
    lines.append("")

    lines.append("=" * 70)
    lines.append("END OF REPORT")
    lines.append("=" * 70)

    return "\n".join(lines)


def generate_markdown(df: pd.DataFrame, csv_path: str) -> str:
    """Generate Markdown version of performance report."""

    lines = []
    lines.append("# PR9A: Performance & Risk Summary Report")
    lines.append("")
    lines.append(f"**CSV:** `{csv_path}`")
    lines.append("")
    lines.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("")

    total_rows = len(df)
    lines.append(f"**Total Rows:** {total_rows:,}")
    lines.append("")

    # Period
    lines.append("## Period")
    lines.append("")

    if "timestamp_utc" in df.columns and total_rows > 0:
        start_ts = df["timestamp_utc"].iloc[0]
        end_ts = df["timestamp_utc"].iloc[-1]
        lines.append(f"- **Start:** {start_ts}")
        lines.append(f"- **End:** {end_ts}")
    else:
        lines.append(f"- **Start:** N/A")
        lines.append(f"- **End:** N/A")

    lines.append("")

    # Equity-based Performance
    lines.append("## Equity-Based Performance")
    lines.append("")

    has_equity = "equity" in df.columns and not df["equity"].isna().all()

    if has_equity:
        equity = df["equity"].dropna()
        if len(equity) > 0:
            start_equity = equity.iloc[0]
            end_equity = equity.iloc[-1]
            total_return_pct = ((end_equity / start_equity) - 1.0) * 100.0 if start_equity != 0 else 0.0
            max_dd_pct = calculate_max_drawdown(equity)

            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| Start Equity | {start_equity:.6f} |")
            lines.append(f"| End Equity | {end_equity:.6f} |")
            lines.append(f"| Total Return | {total_return_pct:+.2f}% |")
            lines.append(f"| Max Drawdown | {max_dd_pct:.2f}% |")
        else:
            lines.append("**Performance Section:** N/A (equity column has no valid values)")
    else:
        lines.append("**Performance Section:** N/A (equity column missing or all NaN)")

    lines.append("")
    lines.append("*Note: Annualized returns not provided (tick frequency unknown).*")
    lines.append("")

    # Exposure / Activity
    lines.append("## Exposure / Activity")
    lines.append("")

    if "target_weight" in df.columns:
        weights = df["target_weight"].dropna()
        if len(weights) > 0:
            avg_abs_weight = weights.abs().mean()
            max_abs_weight = weights.abs().max()

            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| Avg \\|Weight\\| | {avg_abs_weight:.4f} |")
            lines.append(f"| Max \\|Weight\\| | {max_abs_weight:.4f} |")
        else:
            lines.append("**Weight Metrics:** N/A")
    else:
        lines.append("**Weight Metrics:** N/A (column missing)")

    lines.append("")

    # Action counts
    if "action_label" in df.columns:
        action_counts = df["action_label"].fillna("unknown").value_counts()

        lines.append("### Action Counts")
        lines.append("")
        lines.append("| Action | Count | Percentage |")
        lines.append("|--------|-------|------------|")

        for action in ["BUY", "SELL", "HOLD", "FREEZE", "unknown"]:
            count = action_counts.get(action, 0)
            pct = (count / total_rows * 100.0) if total_rows > 0 else 0.0
            lines.append(f"| {action} | {count:,} | {pct:.1f}% |")

        lines.append("")

        hold_count = action_counts.get("HOLD", 0)
        hold_ratio = (hold_count / total_rows * 100.0) if total_rows > 0 else 0.0
        lines.append(f"**HOLD Ratio:** {hold_ratio:.1f}%")
    else:
        lines.append("**Action Counts:** N/A (column missing)")

    lines.append("")

    # Regime Distribution
    lines.append("## Regime Distribution")
    lines.append("")

    if "regime" in df.columns:
        regime_counts = df["regime"].fillna("unknown").value_counts()

        lines.append("| Regime | Count | Percentage |")
        lines.append("|--------|-------|------------|")

        for regime, count in regime_counts.items():
            pct = (count / total_rows * 100.0) if total_rows > 0 else 0.0
            lines.append(f"| {regime} | {count:,} | {pct:.1f}% |")
    else:
        lines.append("**Regime Data:** N/A (column missing)")

    lines.append("")

    # Safety Overlay Distribution
    lines.append("## Safety Overlay Distribution (Top 5)")
    lines.append("")

    if "decision_reason" in df.columns:
        df_temp = df.copy()
        df_temp["overlay_rule"] = df_temp["decision_reason"].apply(extract_overlay_rule)
        overlay_counts = df_temp["overlay_rule"].value_counts()

        lines.append("| Overlay Rule | Count | Percentage |")
        lines.append("|--------------|-------|------------|")

        for overlay, count in overlay_counts.head(5).items():
            pct = (count / total_rows * 100.0) if total_rows > 0 else 0.0
            lines.append(f"| {overlay} | {count:,} | {pct:.1f}% |")

        if len(overlay_counts) > 5:
            lines.append("")
            lines.append(f"*... and {len(overlay_counts) - 5} more overlay rules*")
    else:
        lines.append("**Overlay Data:** N/A (column missing)")

    lines.append("")

    # Health Gate Reference
    lines.append("## Data Quality Gate Reference")
    lines.append("")
    lines.append("**IMPORTANT:** Run PR8A/PR8B integrity validation before using this report.")
    lines.append("")
    lines.append("**Recommended workflow:**")
    lines.append("")
    lines.append("1. `python3 python/validation/pr8a_log_integrity_invariants.py <csv>`")
    lines.append("2. `python3 python/tools/pr8b_integrity_gate_runner.py <csv>`")
    lines.append("3. Review this PR9A performance report")
    lines.append("")
    lines.append("PR8A/PR8B ensure data integrity before performance calculation.")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Generated by PR9A: Performance & Risk Summary Report*")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="PR9A: Generate performance and risk summary from meridian_log.csv"
    )
    parser.add_argument("csv_path", help="Path to meridian_log.csv")
    parser.add_argument("--out", help="Output Markdown file (optional)")
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

    # Apply timestamp filter if provided
    if args.from_ts or args.to_ts:
        if "timestamp_utc" in df.columns:
            try:
                timestamps = pd.to_datetime(df["timestamp_utc"], errors="coerce")
                df = df[~timestamps.isna()].copy()
                df["_ts_parsed"] = pd.to_datetime(df["timestamp_utc"])

                if args.from_ts:
                    from_dt = pd.to_datetime(args.from_ts)
                    df = df[df["_ts_parsed"] >= from_dt]

                if args.to_ts:
                    to_dt = pd.to_datetime(args.to_ts)
                    df = df[df["_ts_parsed"] <= to_dt]

                df = df.drop(columns=["_ts_parsed"])

                if df.empty:
                    print("Warning: No rows match timestamp filter", file=sys.stderr)
            except Exception as e:
                print(f"Warning: Timestamp filter failed: {e}", file=sys.stderr)

    # Generate text report (stdout)
    text_report = generate_report(df, args.csv_path)
    print(text_report)

    # Generate Markdown if requested
    if args.out:
        md_report = generate_markdown(df, args.csv_path)
        with open(args.out, "w") as f:
            f.write(md_report)
        print(f"\n✓ Markdown report written to: {args.out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
