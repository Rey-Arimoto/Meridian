#!/usr/bin/env python3
"""
PR8A: Data Health Report

Purpose: Generate data quality report for meridian_log.csv.
Input: meridian_log.csv
Output: stdout + optional Markdown file

READ-ONLY: No trading logic modification. No CSV schema changes.
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


def generate_report(df: pd.DataFrame, csv_path: str) -> str:
    """Generate data health report."""

    lines = []
    lines.append("=" * 70)
    lines.append("PR8A: Data Health Report")
    lines.append("=" * 70)
    lines.append(f"CSV: {csv_path}")
    lines.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("")

    total_rows = len(df)
    lines.append(f"Total Rows: {total_rows:,}")
    lines.append("")

    # Missing/Null Rate
    lines.append("-" * 70)
    lines.append("Missing/Null Rate by Column")
    lines.append("-" * 70)

    critical_columns = [
        "timestamp_utc",
        "regime",
        "base_action",
        "action_label",
        "target_weight",
        "decision_reason",
        "entropy_bp",
    ]

    for col in critical_columns:
        if col in df.columns:
            null_count = df[col].isna().sum()
            null_rate = (null_count / total_rows * 100) if total_rows > 0 else 0.0
            lines.append(f"  {col:25s}: {null_count:6d} ({null_rate:5.1f}%)")
        else:
            lines.append(f"  {col:25s}: MISSING COLUMN")

    lines.append("")

    # Timestamp Anomalies
    lines.append("-" * 70)
    lines.append("Timestamp Anomalies")
    lines.append("-" * 70)

    timestamp_issues = 0

    if "timestamp_utc" in df.columns:
        try:
            timestamps = pd.to_datetime(df["timestamp_utc"], errors="coerce")
            unparseable = timestamps.isna().sum()
            lines.append(f"  Unparseable timestamps:     {unparseable:6d}")
            timestamp_issues += unparseable

            parsed_timestamps = timestamps.dropna()
            if len(parsed_timestamps) > 1:
                diffs = parsed_timestamps.diff().dropna()
                regressions = (diffs < pd.Timedelta(0)).sum()
                lines.append(f"  Timestamp regressions:      {regressions:6d}")
                timestamp_issues += regressions
        except Exception as e:
            lines.append(f"  ERROR: {e}")
            timestamp_issues += 1
    else:
        lines.append(f"  timestamp_utc column missing")
        timestamp_issues += 1

    lines.append("")

    # Weight Anomalies
    lines.append("-" * 70)
    lines.append("Weight Anomalies")
    lines.append("-" * 70)

    weight_issues = 0

    if "target_weight" in df.columns:
        nan_count = df["target_weight"].isna().sum()
        inf_count = np.isinf(df["target_weight"].fillna(0.0)).sum()
        lines.append(f"  NaN values:                 {nan_count:6d}")
        lines.append(f"  Inf values:                 {inf_count:6d}")
        weight_issues += nan_count + inf_count

        valid_weights = df["target_weight"].dropna()
        out_of_bounds = ((valid_weights < -1.0) | (valid_weights > 1.0)).sum()
        lines.append(f"  Out of bounds [-1.0, 1.0]:  {out_of_bounds:6d}")
        weight_issues += out_of_bounds
    else:
        lines.append(f"  target_weight column missing")
        weight_issues += 1

    lines.append("")

    # Overlay Unknown Count
    lines.append("-" * 70)
    lines.append("Overlay Distribution")
    lines.append("-" * 70)

    unknown_overlay_count = 0

    if "decision_reason" in df.columns:
        df_temp = df.copy()
        df_temp["overlay_rule"] = df_temp["decision_reason"].apply(extract_overlay_rule)
        overlay_counts = df_temp["overlay_rule"].value_counts()

        unknown_overlay_count = overlay_counts.get("unknown", 0)

        for overlay, count in overlay_counts.head(10).items():
            pct = count / total_rows * 100
            lines.append(f"  {overlay:30s}: {count:6d} ({pct:5.1f}%)")

        if len(overlay_counts) > 10:
            lines.append(f"  ... and {len(overlay_counts) - 10} more")
    else:
        lines.append(f"  decision_reason column missing")

    lines.append("")

    # Sample Anomalies
    lines.append("-" * 70)
    lines.append("Sample Anomalies (First 5)")
    lines.append("-" * 70)

    anomalies = []

    # Find timestamp anomalies
    if "timestamp_utc" in df.columns:
        try:
            timestamps = pd.to_datetime(df["timestamp_utc"], errors="coerce")
            unparseable_idx = df[timestamps.isna()].index.tolist()[:5]
            for idx in unparseable_idx:
                anomalies.append((idx, "Unparseable timestamp"))
        except:
            pass

    # Find weight anomalies
    if "target_weight" in df.columns:
        nan_idx = df[df["target_weight"].isna()].index.tolist()[:5]
        for idx in nan_idx:
            anomalies.append((idx, "NaN target_weight"))

        valid_weights = df["target_weight"].dropna()
        oob_idx = df[((df["target_weight"] < -1.0) | (df["target_weight"] > 1.0))].index.tolist()[:5]
        for idx in oob_idx:
            weight_val = df.loc[idx, "target_weight"]
            anomalies.append((idx, f"Out-of-bounds weight: {weight_val}"))

    # Show first 5 unique anomalies
    shown = set()
    count = 0
    for idx, issue in anomalies:
        if idx not in shown and count < 5:
            shown.add(idx)
            count += 1
            timestamp = df.loc[idx, "timestamp_utc"] if "timestamp_utc" in df.columns else "unknown"
            lines.append(f"  Row {idx}: {timestamp} - {issue}")

    if count == 0:
        lines.append(f"  No anomalies detected")

    lines.append("")

    # Overall Assessment
    lines.append("-" * 70)
    lines.append("Overall Assessment")
    lines.append("-" * 70)

    total_issues = timestamp_issues + weight_issues
    lines.append(f"Total issues detected: {total_issues}")

    if total_issues == 0:
        lines.append("")
        lines.append("✓ Data Health: HEALTHY")
        lines.append("  All critical integrity checks passed.")
        lines.append("  Explainability outputs can be trusted.")
    else:
        lines.append("")
        lines.append("⚠ Data Health: DEGRADED")
        lines.append(f"  {timestamp_issues} timestamp issues")
        lines.append(f"  {weight_issues} weight issues")
        lines.append("  Review anomalies before trusting explainability outputs.")

    lines.append("")
    lines.append("=" * 70)

    return "\n".join(lines)


def generate_markdown(df: pd.DataFrame, csv_path: str) -> str:
    """Generate Markdown version of report."""

    lines = []
    lines.append("# PR8A: Data Health Report")
    lines.append("")
    lines.append(f"**CSV:** `{csv_path}`")
    lines.append("")
    lines.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("")

    total_rows = len(df)
    lines.append(f"**Total Rows:** {total_rows:,}")
    lines.append("")

    # Missing/Null Rate
    lines.append("## Missing/Null Rate by Column")
    lines.append("")
    lines.append("| Column | Null Count | Null Rate |")
    lines.append("|--------|------------|-----------|")

    critical_columns = [
        "timestamp_utc",
        "regime",
        "base_action",
        "action_label",
        "target_weight",
        "decision_reason",
        "entropy_bp",
    ]

    for col in critical_columns:
        if col in df.columns:
            null_count = df[col].isna().sum()
            null_rate = (null_count / total_rows * 100) if total_rows > 0 else 0.0
            lines.append(f"| {col} | {null_count:,} | {null_rate:.1f}% |")
        else:
            lines.append(f"| {col} | MISSING | N/A |")

    lines.append("")

    # Timestamp Anomalies
    lines.append("## Timestamp Anomalies")
    lines.append("")

    timestamp_issues = 0

    if "timestamp_utc" in df.columns:
        try:
            timestamps = pd.to_datetime(df["timestamp_utc"], errors="coerce")
            unparseable = timestamps.isna().sum()
            lines.append(f"- Unparseable timestamps: {unparseable:,}")
            timestamp_issues += unparseable

            parsed_timestamps = timestamps.dropna()
            if len(parsed_timestamps) > 1:
                diffs = parsed_timestamps.diff().dropna()
                regressions = (diffs < pd.Timedelta(0)).sum()
                lines.append(f"- Timestamp regressions: {regressions:,}")
                timestamp_issues += regressions
        except Exception as e:
            lines.append(f"- ERROR: {e}")
            timestamp_issues += 1
    else:
        lines.append(f"- timestamp_utc column missing")
        timestamp_issues += 1

    lines.append("")

    # Weight Anomalies
    lines.append("## Weight Anomalies")
    lines.append("")

    weight_issues = 0

    if "target_weight" in df.columns:
        nan_count = df["target_weight"].isna().sum()
        inf_count = np.isinf(df["target_weight"].fillna(0.0)).sum()
        lines.append(f"- NaN values: {nan_count:,}")
        lines.append(f"- Inf values: {inf_count:,}")
        weight_issues += nan_count + inf_count

        valid_weights = df["target_weight"].dropna()
        out_of_bounds = ((valid_weights < -1.0) | (valid_weights > 1.0)).sum()
        lines.append(f"- Out of bounds [-1.0, 1.0]: {out_of_bounds:,}")
        weight_issues += out_of_bounds
    else:
        lines.append(f"- target_weight column missing")
        weight_issues += 1

    lines.append("")

    # Overall Assessment
    lines.append("## Overall Assessment")
    lines.append("")

    total_issues = timestamp_issues + weight_issues
    lines.append(f"**Total issues detected:** {total_issues}")
    lines.append("")

    if total_issues == 0:
        lines.append("✓ **Data Health: HEALTHY**")
        lines.append("")
        lines.append("All critical integrity checks passed. Explainability outputs can be trusted.")
    else:
        lines.append("⚠ **Data Health: DEGRADED**")
        lines.append("")
        lines.append(f"- {timestamp_issues} timestamp issues")
        lines.append(f"- {weight_issues} weight issues")
        lines.append("")
        lines.append("Review anomalies before trusting explainability outputs.")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Generated by PR8A: Data Health Report*")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="PR8A: Generate data health report from meridian_log.csv"
    )
    parser.add_argument("csv_path", help="Path to meridian_log.csv")
    parser.add_argument("--out", help="Output Markdown file (optional)")

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
