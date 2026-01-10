#!/usr/bin/env python3
"""
PR51: v0.5 Weekly Shadow Diff Digest (7-Day Summary, READ-ONLY)

Purpose:
    Generate weekly summary of shadow diff observations from daily reports.
    Provides human-readable weekly digest without evaluation or judgment.

Constitutional Constraints:
    - READ-ONLY: No execution logic or decision changes
    - Warning-only: Exit code always 0, continues on errors
    - Non-evaluative: No good/bad, win/loss, correct/wrong vocabulary
    - Non-scoric: No scores, grades, rankings
    - Non-prescriptive: No "should" or recommendations
    - v0.4 boundary protection: No confidence_reason analysis

Input Sources (priority order):
    1. reports/index.json (PR48B) - recommended
    2. reports/_archive/ (fallback if index.json unavailable)
    3. analytics_out/ (degraded mode, PR47 outputs only)

Output:
    - reports/weekly/weekly_digest.md (human-readable)
    - reports/weekly/weekly_digest.json (machine-readable)

Window:
    - Default: 7 days ending at latest available day
    - Configurable: --end_day YYYY-MM-DD --days N

Exit Code: Always 0 (warning-only)
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="PR51: Weekly Shadow Diff Digest Generator (READ-ONLY)"
    )

    # Input source (mutually exclusive)
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--reports_dir",
        type=str,
        help="Reports directory with index.json (recommended)",
    )
    source_group.add_argument(
        "--archive_dir",
        type=str,
        help="Archive directory (fallback if no index.json)",
    )
    source_group.add_argument(
        "--analytics_out_dir",
        type=str,
        help="Analytics output directory (degraded mode)",
    )

    # Window configuration
    parser.add_argument(
        "--end_day",
        type=str,
        default=None,
        help="End day (YYYY-MM-DD). Default: latest available",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days in window (default: 7)",
    )

    # Output configuration
    parser.add_argument(
        "--out_dir",
        type=str,
        default="reports/weekly",
        help="Output directory (default: reports/weekly)",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["md", "json", "both"],
        default="both",
        help="Output format (default: both)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce output (warnings still shown)",
    )

    return parser.parse_args()


def get_latest_day_from_index(reports_dir: str) -> Optional[str]:
    """
    Get latest day from reports/index.json.

    Returns YYYY-MM-DD or None if unavailable.
    """
    index_path = os.path.join(reports_dir, "index.json")

    if not os.path.exists(index_path):
        print(f"[WARNING][PR51] index.json not found: {index_path}")
        return None

    try:
        with open(index_path, "r") as f:
            index_data = json.load(f)

        latest_day = index_data.get("latest_day")

        if latest_day and latest_day != "UNKNOWN":
            print(f"[INFO][PR51] Latest day from index.json: {latest_day}")
            return latest_day
        else:
            print(f"[WARNING][PR51] latest_day unavailable in index.json")
            return None

    except Exception as e:
        print(f"[WARNING][PR51] Failed to read index.json: {e}")
        return None


def get_latest_day_from_archive(archive_dir: str) -> Optional[str]:
    """
    Get latest day by scanning archive directory.

    Returns YYYY-MM-DD or None if empty.
    """
    if not os.path.exists(archive_dir):
        print(f"[WARNING][PR51] Archive directory not found: {archive_dir}")
        return None

    try:
        day_dirs = [
            d for d in os.listdir(archive_dir)
            if os.path.isdir(os.path.join(archive_dir, d))
            and d.count("-") == 2  # YYYY-MM-DD format
        ]

        if not day_dirs:
            print(f"[WARNING][PR51] No day directories found in {archive_dir}")
            return None

        # Sort descending and take latest
        day_dirs.sort(reverse=True)
        latest_day = day_dirs[0]

        print(f"[INFO][PR51] Latest day from archive scan: {latest_day}")
        return latest_day

    except Exception as e:
        print(f"[WARNING][PR51] Failed to scan archive: {e}")
        return None


def calculate_date_range(end_day: str, days: int) -> Tuple[str, List[str]]:
    """
    Calculate start day and list of days in window.

    Returns (start_day, [day1, day2, ...])
    """
    try:
        end_date = datetime.strptime(end_day, "%Y-%m-%d")
        start_date = end_date - timedelta(days=days - 1)
        start_day = start_date.strftime("%Y-%m-%d")

        day_list = []
        current_date = start_date
        while current_date <= end_date:
            day_list.append(current_date.strftime("%Y-%m-%d"))
            current_date += timedelta(days=1)

        return start_day, day_list

    except Exception as e:
        print(f"[WARNING][PR51] Failed to calculate date range: {e}")
        # Fallback: return single day
        return end_day, [end_day]


def check_day_coverage(day: str, reports_dir: str, archive_dir: str) -> str:
    """
    Check coverage status for a single day.

    Returns: "AVAILABLE", "PARTIAL", or "MISSING"
    """
    # Check archive directory
    day_archive = os.path.join(archive_dir, day)

    if not os.path.exists(day_archive):
        return "MISSING"

    # Check for md and html
    md_path = os.path.join(day_archive, "shadow_diff_report.md")
    html_path = os.path.join(day_archive, "shadow_diff_report.html")

    md_exists = os.path.exists(md_path)
    html_exists = os.path.exists(html_path)

    if md_exists and html_exists:
        return "AVAILABLE"
    elif md_exists or html_exists:
        return "PARTIAL"
    else:
        return "MISSING"


def load_day_summary_from_pr47(day: str, analytics_out_dir: str) -> Optional[Dict[str, Any]]:
    """
    Load day summary from PR47 CSV (degraded mode).

    Returns dict with counts or None if unavailable.
    """
    csv_path = os.path.join(analytics_out_dir, "pr47_shadow_diff_daily_summary.csv")

    if not os.path.exists(csv_path):
        return None

    try:
        import pandas as pd
        df = pd.read_csv(csv_path)

        # Filter for the specific day
        day_row = df[df["day"] == day]

        if day_row.empty:
            return None

        # Extract counts
        summary = {}
        for col in ["aligned_count", "diverged_count", "unavailable_count"]:
            if col in day_row.columns:
                summary[col] = int(day_row[col].iloc[0])

        return summary

    except Exception as e:
        print(f"[WARNING][PR51] Failed to load day summary from PR47: {e}")
        return None


def aggregate_week(
    day_list: List[str],
    reports_dir: str,
    archive_dir: str,
    analytics_out_dir: Optional[str],
) -> Dict[str, Any]:
    """
    Aggregate observations across the week.

    Returns dict with coverage and aggregates.
    """
    coverage = {
        "days_considered": len(day_list),
        "days_available": 0,
        "days_partial": 0,
        "days_missing": 0,
        "missing_days": [],
    }

    aggregates = {
        "diff_status_counts": defaultdict(int),
        "semantics_tag_counts": defaultdict(int),
        "diff_pair_counts": defaultdict(int),
    }

    # Check each day
    for day in day_list:
        status = check_day_coverage(day, reports_dir, archive_dir)

        if status == "AVAILABLE":
            coverage["days_available"] += 1
        elif status == "PARTIAL":
            coverage["days_partial"] += 1
        else:  # MISSING
            coverage["days_missing"] += 1
            coverage["missing_days"].append(day)

        # Try to load summary if available
        if analytics_out_dir:
            day_summary = load_day_summary_from_pr47(day, analytics_out_dir)
            if day_summary:
                for key, value in day_summary.items():
                    if "aligned" in key.lower():
                        aggregates["diff_status_counts"]["ALIGNED"] += value
                    elif "diverged" in key.lower():
                        aggregates["diff_status_counts"]["DIVERGED"] += value
                    elif "unavailable" in key.lower():
                        aggregates["diff_status_counts"]["UNAVAILABLE"] += value

    # Convert defaultdict to dict for JSON serialization
    aggregates["diff_status_counts"] = dict(aggregates["diff_status_counts"])
    aggregates["semantics_tag_counts"] = dict(aggregates["semantics_tag_counts"])
    aggregates["diff_pair_counts"] = dict(aggregates["diff_pair_counts"])

    return {
        "coverage": coverage,
        "aggregates": aggregates,
    }


def generate_json_digest(
    window: Dict[str, Any],
    coverage: Dict[str, Any],
    aggregates: Dict[str, Any],
    source: Dict[str, str],
) -> Dict[str, Any]:
    """Generate JSON digest."""
    return {
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": source,
        "window": window,
        "coverage": coverage,
        "aggregates": aggregates,
        "notes": [
            "observational only",
            "no evaluations made",
            "no action changes",
        ],
    }


def generate_md_digest(
    window: Dict[str, Any],
    coverage: Dict[str, Any],
    aggregates: Dict[str, Any],
) -> str:
    """Generate Markdown digest."""
    lines = []

    lines.append("# Weekly Shadow Diff Digest (v0.5)")
    lines.append("")
    lines.append(f"**Generated at:** {datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}")
    lines.append("")

    # Window
    lines.append("## Window")
    lines.append("")
    lines.append(f"- **Start day:** {window['start_day']}")
    lines.append(f"- **End day:** {window['end_day']}")
    lines.append(f"- **Days:** {window['days']}")
    lines.append("")

    # Coverage
    lines.append("## Coverage")
    lines.append("")
    lines.append(f"- **Days considered:** {coverage['days_considered']}")
    lines.append(f"- **Days available:** {coverage['days_available']}")
    lines.append(f"- **Days partial:** {coverage['days_partial']}")
    lines.append(f"- **Days missing:** {coverage['days_missing']}")

    if coverage["missing_days"]:
        lines.append("")
        lines.append("**Missing days:**")
        for day in coverage["missing_days"]:
            lines.append(f"- {day}")

    lines.append("")

    # Observed Distributions
    lines.append("## Observed Distributions")
    lines.append("")

    # Diff status
    if aggregates["diff_status_counts"]:
        lines.append("### Decision Diff Status")
        lines.append("")
        for status, count in sorted(aggregates["diff_status_counts"].items()):
            lines.append(f"- **{status}:** {count}")
        lines.append("")
    else:
        lines.append("### Decision Diff Status")
        lines.append("")
        lines.append("No observations recorded.")
        lines.append("")

    # Semantics tags
    if aggregates["semantics_tag_counts"]:
        lines.append("### Semantics Tags")
        lines.append("")
        for tag, count in sorted(aggregates["semantics_tag_counts"].items()):
            lines.append(f"- **{tag}:** {count}")
        lines.append("")

    # Diff pairs
    if aggregates["diff_pair_counts"]:
        lines.append("### Decision Pairs")
        lines.append("")
        for pair, count in sorted(aggregates["diff_pair_counts"].items()):
            lines.append(f"- **{pair}:** {count}")
        lines.append("")

    # Notes
    lines.append("## Notes")
    lines.append("")
    lines.append("- This digest is observational only. No evaluations are made.")
    lines.append("- No action changes or behavior modifications.")
    lines.append("- Observation only, recorded history.")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    """
    Main execution.

    Returns 0 (warning-only, never fails).
    """
    args = parse_args()

    print("=" * 60)
    print("PR51: Weekly Shadow Diff Digest Generator")
    print("=" * 60)
    print()

    # Determine source
    source = {}
    reports_dir = None
    archive_dir = None
    analytics_out_dir = None

    if args.reports_dir:
        reports_dir = args.reports_dir
        archive_dir = os.path.join(reports_dir, "_archive")
        source["type"] = "reports_dir"
        source["reports_dir"] = reports_dir
        source["index_json"] = os.path.join(reports_dir, "index.json")
    elif args.archive_dir:
        archive_dir = args.archive_dir
        reports_dir = os.path.dirname(archive_dir)  # Infer reports_dir
        source["type"] = "archive_dir"
        source["archive_dir"] = archive_dir
    else:  # analytics_out_dir
        analytics_out_dir = args.analytics_out_dir
        source["type"] = "analytics_out_dir (degraded mode)"
        source["analytics_out_dir"] = analytics_out_dir

    print(f"Source: {source['type']}")
    print()

    # Determine end_day
    end_day = args.end_day

    if not end_day:
        if reports_dir:
            end_day = get_latest_day_from_index(reports_dir)

        if not end_day and archive_dir:
            end_day = get_latest_day_from_archive(archive_dir)

        if not end_day:
            # Ultimate fallback: today
            end_day = datetime.utcnow().strftime("%Y-%m-%d")
            print(f"[INFO][PR51] Using fallback end_day: {end_day}")

    print(f"End day: {end_day}")
    print(f"Days: {args.days}")
    print()

    # Calculate window
    start_day, day_list = calculate_date_range(end_day, args.days)

    window = {
        "start_day": start_day,
        "end_day": end_day,
        "days": args.days,
    }

    print(f"Window: {start_day} → {end_day}")
    print()

    # Aggregate week
    print("Aggregating observations...")
    result = aggregate_week(day_list, reports_dir or "", archive_dir or "", analytics_out_dir)

    coverage = result["coverage"]
    aggregates = result["aggregates"]

    print(f"Coverage: {coverage['days_available']} available, {coverage['days_partial']} partial, {coverage['days_missing']} missing")
    print()

    # Generate outputs
    os.makedirs(args.out_dir, exist_ok=True)

    if args.format in ["json", "both"]:
        json_digest = generate_json_digest(window, coverage, aggregates, source)
        json_path = os.path.join(args.out_dir, "weekly_digest.json")

        with open(json_path, "w") as f:
            json.dump(json_digest, f, indent=2)

        print(f"✓ JSON digest: {json_path}")

    if args.format in ["md", "both"]:
        md_digest = generate_md_digest(window, coverage, aggregates)
        md_path = os.path.join(args.out_dir, "weekly_digest.md")

        with open(md_path, "w") as f:
            f.write(md_digest)

        print(f"✓ Markdown digest: {md_path}")

    print()
    print("=" * 60)
    print("Weekly digest generation complete")
    print("=" * 60)
    print("Exit code: 0 (warning-only, never fails)")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
