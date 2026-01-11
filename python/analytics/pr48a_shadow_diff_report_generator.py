#!/usr/bin/env python3
"""
PR48A: v0.5 Shadow Diff Human-Readable Report Generator (Daily Markdown/HTML, READ-ONLY)

Purpose:
    Generate human-readable Markdown/HTML reports from PR47 analytics outputs.
    Makes comparison history readable and shareable without judgment.

Constitutional Constraints:
    - READ-ONLY: No execution logic, order, weight, or decision changes
    - Warning-only: Exit code always 0, continues on missing files
    - Non-evaluative: No good/bad, win/loss, correct/wrong vocabulary
    - Non-scoric: No scores, grades, rankings, or performance metrics
    - Non-judgment: Divergence is observation, not problem
    - v0.4 boundary protection: No confidence_reason analysis or featurization

Input:
    - PR47 outputs: overall_summary.json (required), daily_summary.csv (optional)
    - CLI args: --in_dir, --overall_json, --daily_csv, --out_dir, --day, --format

Output:
    - Markdown report: pr48a_shadow_diff_daily_report.md
    - HTML report: pr48a_shadow_diff_daily_report.html (optional)

Allowed Vocabulary:
    - Observation: observed, recorded, present, absent, aligned, diverged, unavailable
    - Classification: semantics tag labels (PR46)
    - Aggregation: count, total, distribution, breakdown

Forbidden Vocabulary:
    - Evaluation: good/bad, better/worse, correct/wrong, superior/inferior
    - Outcome: profit/loss, win/lose, success/failure, pnl
    - Scoring: score, grade, rank, accuracy

Warning-only: Always exits with code 0.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="PR48A: Shadow Diff Human-Readable Report Generator (READ-ONLY)"
    )
    parser.add_argument(
        "--in_dir",
        type=str,
        default=None,
        help="PR47 output directory (auto-detect JSON/CSV)",
    )
    parser.add_argument(
        "--overall_json",
        type=str,
        default=None,
        help="Path to overall summary JSON (overrides in_dir)",
    )
    parser.add_argument(
        "--daily_csv",
        type=str,
        default=None,
        help="Path to daily summary CSV (overrides in_dir)",
    )
    parser.add_argument(
        "--out_dir",
        type=str,
        default="analytics_out",
        help="Output directory for reports (default: analytics_out)",
    )
    parser.add_argument(
        "--day",
        type=str,
        default=None,
        help="Optional: YYYY-MM-DD to filter specific day",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["md", "html", "both"],
        default="both",
        help="Output format: md, html, or both (default: both)",
    )
    return parser.parse_args()


def resolve_input_paths(args: argparse.Namespace) -> tuple[Optional[str], Optional[str]]:
    """
    Resolve input file paths from args.

    Returns (overall_json_path, daily_csv_path).
    Warning-only: If files not found, returns None.
    """
    overall_json = None
    daily_csv = None

    # Priority 1: Explicit paths
    if args.overall_json:
        overall_json = args.overall_json if os.path.exists(args.overall_json) else None
        if overall_json is None:
            print(f"[WARNING][PR48A] Overall JSON not found: {args.overall_json}")

    if args.daily_csv:
        daily_csv = args.daily_csv if os.path.exists(args.daily_csv) else None
        if daily_csv is None:
            print(f"[WARNING][PR48A] Daily CSV not found: {args.daily_csv}")

    # Priority 2: Auto-detect from in_dir
    if args.in_dir and os.path.isdir(args.in_dir):
        if overall_json is None:
            candidate = os.path.join(args.in_dir, "pr47_shadow_diff_overall_summary.json")
            if os.path.exists(candidate):
                overall_json = candidate
            else:
                print(f"[WARNING][PR48A] Overall JSON not found in in_dir: {candidate}")

        if daily_csv is None:
            candidate = os.path.join(args.in_dir, "pr47_shadow_diff_daily_summary.csv")
            if os.path.exists(candidate):
                daily_csv = candidate
            else:
                print(f"[INFO][PR48A] Daily CSV not found in in_dir: {candidate}")

    return overall_json, daily_csv


def load_overall_json(path: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Load overall summary JSON.

    Warning-only: Returns None if file not found or parse error.
    """
    if path is None:
        print("[WARNING][PR48A] Overall JSON path is None")
        return None

    try:
        with open(path, "r") as f:
            data = json.load(f)
        print(f"[INFO][PR48A] Loaded overall JSON: {path}")
        return data
    except Exception as e:
        print(f"[WARNING][PR48A] Failed to load overall JSON: {e}")
        return None


def load_daily_csv(path: Optional[str]) -> Optional[pd.DataFrame]:
    """
    Load daily summary CSV.

    Warning-only: Returns None if file not found or parse error.
    """
    if path is None:
        print("[INFO][PR48A] Daily CSV path is None (optional)")
        return None

    try:
        df = pd.read_csv(path)
        print(f"[INFO][PR48A] Loaded daily CSV: {path} ({len(df)} rows)")
        return df
    except Exception as e:
        print(f"[WARNING][PR48A] Failed to load daily CSV: {e}")
        return None


def generate_markdown_report(
    overall: Optional[Dict[str, Any]],
    daily: Optional[pd.DataFrame],
    day_filter: Optional[str],
) -> str:
    """
    Generate Markdown report from PR47 outputs.

    Non-evaluative: Uses only observation and classification vocabulary.
    """
    lines = []

    # Header
    lines.append("# Shadow Diff Daily Report")
    lines.append("")
    lines.append(f"**Generated at:** {datetime.utcnow().isoformat()}Z")
    lines.append("")

    if overall:
        lines.append(f"**Source:** PR47 outputs")
        lines.append(f"- Input log: `{overall.get('input_log_path', 'UNAVAILABLE')}`")
        date_range = overall.get("date_range", {})
        lines.append(f"- Date range: {date_range.get('min_date', 'UNKNOWN')} to {date_range.get('max_date', 'UNKNOWN')}")
    else:
        lines.append("**Source:** UNAVAILABLE (degraded mode)")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")

    if overall:
        totals = overall.get("totals", {})
        lines.append(f"**Ticks Total:** {totals.get('ticks_total', 0)}")
        lines.append(f"**Shadow Present Ticks:** {totals.get('shadow_present_ticks', 0)}")
        lines.append(f"**Diff Mode ON Ticks:** {totals.get('diff_mode_on_ticks', 0)}")
        lines.append("")

        # Diff status counts
        diff_status = totals.get("diff_status_counts", {})
        if diff_status:
            lines.append("**Diff Status Distribution:**")
            for status, count in sorted(diff_status.items()):
                lines.append(f"- {status}: {count}")
            lines.append("")

        # Semantics tag counts
        semantics_tags = totals.get("semantics_tag_counts", {})
        if semantics_tags:
            lines.append("**Semantics Tag Distribution:**")
            for tag, count in sorted(semantics_tags.items()):
                lines.append(f"- {tag}: {count}")
            lines.append("")

        # Observation statement (non-evaluative)
        diverged_count = diff_status.get("DIVERGED", 0)
        aligned_count = diff_status.get("ALIGNED", 0)
        if diverged_count > 0 or aligned_count > 0:
            lines.append(f"Divergence events were observed ({diverged_count} diverged, {aligned_count} aligned).")
        else:
            lines.append("No divergence data available.")
    else:
        lines.append("Overall summary UNAVAILABLE (degraded mode).")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Breakdown
    lines.append("## Breakdown")
    lines.append("")

    if overall:
        breakdowns = overall.get("breakdowns", {})

        # Diff pair counts
        pair_counts = overall.get("totals", {}).get("diff_pair_counts", {})
        if pair_counts:
            lines.append("**Diff Pair Distribution:**")
            for pair, count in sorted(pair_counts.items()):
                lines.append(f"- {pair}: {count}")
            lines.append("")

        # By regime
        by_regime = breakdowns.get("by_regime", {})
        if by_regime:
            lines.append("**By Regime:**")
            lines.append("")
            for regime, data in sorted(by_regime.items()):
                lines.append(f"### {regime}")
                lines.append(f"- Ticks: {data.get('ticks_total', 0)}")
                diff_counts = data.get("diff_status_counts", {})
                if diff_counts:
                    lines.append("- Diff Status:")
                    for status, count in sorted(diff_counts.items()):
                        lines.append(f"  - {status}: {count}")
                lines.append("")

        # By intent_primary
        by_intent = breakdowns.get("by_intent_primary", {})
        if by_intent:
            lines.append("**By Intent Primary:**")
            lines.append("")
            for intent, data in sorted(by_intent.items()):
                lines.append(f"### {intent}")
                lines.append(f"- Ticks: {data.get('ticks_total', 0)}")
                diff_counts = data.get("diff_status_counts", {})
                if diff_counts:
                    lines.append("- Diff Status:")
                    for status, count in sorted(diff_counts.items()):
                        lines.append(f"  - {status}: {count}")
                lines.append("")
    else:
        lines.append("Breakdown UNAVAILABLE (degraded mode).")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Daily Section (if available and day filter specified)
    if daily is not None and day_filter:
        lines.append("## Daily Summary")
        lines.append("")
        daily_filtered = daily[daily["date"] == day_filter]
        if len(daily_filtered) > 0:
            lines.append(f"**Date:** {day_filter}")
            lines.append("")
            row = daily_filtered.iloc[0]
            lines.append(f"- Ticks Total: {row.get('ticks_total', 0)}")
            lines.append(f"- Shadow Present: {row.get('shadow_present_ticks', 0)}")
            lines.append(f"- Diff Aligned: {row.get('diff_aligned', 0)}")
            lines.append(f"- Diff Diverged: {row.get('diff_diverged', 0)}")
            lines.append(f"- Diff Unavailable: {row.get('diff_unavailable', 0)}")
            lines.append("")
        else:
            lines.append(f"No data found for day: {day_filter}")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Interpretation (v0.6)
    lines.append("## Interpretation (v0.6)")
    lines.append("")

    if overall and "v6_interpretation" in overall:
        v6_interp = overall["v6_interpretation"]

        # Meaning status distribution
        meaning_status = v6_interp.get("meaning_status_counts", {})
        if meaning_status:
            lines.append("**Meaning Status Distribution:**")
            for status, count in sorted(meaning_status.items()):
                lines.append(f"- {status}: {count}")
            lines.append("")

        # Meaning tag distribution
        meaning_tags = v6_interp.get("meaning_tag_counts", {})
        if meaning_tags:
            lines.append("**Meaning Tag Distribution:**")
            for tag, count in sorted(meaning_tags.items()):
                lines.append(f"- {tag}: {count}")
            lines.append("")

        # Interpretation note
        lines.append("Interpretation layer maps observations to structural meaning types.")
        lines.append("No evaluations or judgments are made.")
    else:
        lines.append("v0.6 interpretation data UNAVAILABLE (degraded mode).")
        lines.append("")
        lines.append("Interpretation layer provides structural meaning without evaluation.")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Notes (Constitutional constraints)
    lines.append("## Notes")
    lines.append("")
    lines.append("**Constitutional Constraints:**")
    lines.append("")
    lines.append("- This report is observational only. No evaluations are made.")
    lines.append("- This report is generated from recorded history.")
    lines.append("- No behavior changes. Observation only.")
    lines.append("- Divergence is observation, not judgment.")
    lines.append("- No numeric assessments are assigned.")
    lines.append("")

    lines.append("---")
    lines.append("")

    # Appendices
    lines.append("## Appendices")
    lines.append("")
    lines.append("**Field Sources:**")
    lines.append("")
    lines.append("- PR44: Shadow Mode (dual record logging)")
    lines.append("- PR45: Shadow Diff Logging (machine-readable comparison)")
    lines.append("- PR46: Diff Semantics Tagging (divergence classification)")
    lines.append("- PR47: Shadow Diff Analytics Export (daily aggregation)")
    lines.append("- PR60: v0.6 Interpretation Schema (structural meaning types)")
    lines.append("- PR61: v0.6 Interpretation Engine v1 (static structural mapping)")
    lines.append("")

    if overall is None:
        lines.append("**Degraded Mode:**")
        lines.append("")
        lines.append("- Overall summary JSON was unavailable.")
        lines.append("- Report generated with available data only.")
        lines.append("")

    return "\n".join(lines)


def markdown_to_html(markdown: str) -> str:
    """
    Convert Markdown to simple HTML.

    Minimal conversion: headings, lists, bold, code.
    """
    lines = markdown.split("\n")
    html_lines = []

    html_lines.append("<!DOCTYPE html>")
    html_lines.append("<html>")
    html_lines.append("<head>")
    html_lines.append("<meta charset='utf-8'>")
    html_lines.append("<title>Shadow Diff Daily Report</title>")
    html_lines.append("<style>")
    html_lines.append("body { font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; }")
    html_lines.append("h1 { border-bottom: 2px solid #333; }")
    html_lines.append("h2 { border-bottom: 1px solid #666; margin-top: 30px; }")
    html_lines.append("h3 { margin-top: 20px; }")
    html_lines.append("code { background: #f4f4f4; padding: 2px 6px; }")
    html_lines.append("ul { line-height: 1.6; }")
    html_lines.append("hr { margin: 30px 0; }")
    html_lines.append("</style>")
    html_lines.append("</head>")
    html_lines.append("<body>")

    in_list = False
    for line in lines:
        # Headings
        if line.startswith("# "):
            html_lines.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("## "):
            html_lines.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("### "):
            html_lines.append(f"<h3>{line[4:]}</h3>")
        # Horizontal rule
        elif line.strip() == "---":
            html_lines.append("<hr>")
        # List items
        elif line.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            # Handle bold and code in list items
            content = line[2:]
            content = content.replace("**", "<strong>").replace("**", "</strong>")
            content = content.replace("`", "<code>").replace("`", "</code>")
            html_lines.append(f"<li>{content}</li>")
        # End list if not list item
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            if line.strip():
                # Handle bold and code in paragraphs
                content = line
                content = content.replace("**", "<strong>").replace("**", "</strong>")
                content = content.replace("`", "<code>").replace("`", "</code>")
                html_lines.append(f"<p>{content}</p>")
            else:
                html_lines.append("<br>")

    if in_list:
        html_lines.append("</ul>")

    html_lines.append("</body>")
    html_lines.append("</html>")

    return "\n".join(html_lines)


def export_markdown(content: str, out_path: str) -> None:
    """Export Markdown report."""
    try:
        with open(out_path, "w") as f:
            f.write(content)
        print(f"[INFO][PR48A] Exported Markdown report: {out_path}")
    except Exception as e:
        print(f"[WARNING][PR48A] Failed to export Markdown: {e}")


def export_html(markdown: str, out_path: str) -> None:
    """Export HTML report."""
    try:
        html = markdown_to_html(markdown)
        with open(out_path, "w") as f:
            f.write(html)
        print(f"[INFO][PR48A] Exported HTML report: {out_path}")
    except Exception as e:
        print(f"[WARNING][PR48A] Failed to export HTML: {e}")


def main() -> int:
    """
    Main execution.

    Returns 0 (warning-only, never fails).
    """
    args = parse_args()

    print("=" * 60)
    print("PR48A: Shadow Diff Human-Readable Report Generator")
    print("=" * 60)
    print(f"Input directory: {args.in_dir or 'None'}")
    print(f"Output directory: {args.out_dir}")
    print(f"Day filter: {args.day or 'None'}")
    print(f"Format: {args.format}")
    print("=" * 60)

    # Resolve input paths
    overall_json_path, daily_csv_path = resolve_input_paths(args)

    # Load inputs
    overall = load_overall_json(overall_json_path)
    daily = load_daily_csv(daily_csv_path)

    # Generate Markdown report
    print("[INFO][PR48A] Generating Markdown report...")
    markdown_content = generate_markdown_report(overall, daily, args.day)

    # Create output directory
    Path(args.out_dir).mkdir(parents=True, exist_ok=True)

    # Export reports
    if args.format in ["md", "both"]:
        md_path = os.path.join(args.out_dir, "pr48a_shadow_diff_daily_report.md")
        export_markdown(markdown_content, md_path)

    if args.format in ["html", "both"]:
        html_path = os.path.join(args.out_dir, "pr48a_shadow_diff_daily_report.html")
        export_html(markdown_content, html_path)

    print("=" * 60)
    print("PR48A: Report generation complete (warning-only, exit code 0)")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
