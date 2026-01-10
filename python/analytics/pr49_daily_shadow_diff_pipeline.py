#!/usr/bin/env python3
"""
PR49: v0.5 Daily Analytics Pipeline Runner (PR47→PR48A→PR48B, READ-ONLY)

Purpose:
    Orchestrate complete analytics pipeline in single command:
    PR47 (export) → PR48A (report) → PR48B (index/archive)

Constitutional Constraints:
    - READ-ONLY: No execution logic, order, weight, or decision changes
    - Warning-only: Exit code always 0, continues on subprocess failures
    - Non-evaluative: No good/bad, win/loss, correct/wrong vocabulary
    - Non-scoric: No scores, grades, rankings
    - v0.4 boundary protection: No confidence_reason analysis

Pipeline Flow:
    1. PR47: Export shadow diff analytics (CSV/JSON)
    2. PR48A: Generate human-readable reports (md/html)
    3. PR48B: Archive and index reports (TOC + registry)

Day Determination:
    1. Use --day if specified
    2. Extract from PR47's overall_summary.json date_range.max_date
    3. Fallback to current UTC date

Input:
    - Execution log CSV (required)
    - CLI args: --log_path, --day, --analytics_out_dir, --reports_dir, --format

Output:
    - PR47: analytics_out_dir/pr47_shadow_diff_*.{csv,json}
    - PR48A: reports_dir/pr48a_shadow_diff_daily_report.{md,html}
    - PR48B: reports_dir/index.{md,json}, reports_dir/_archive/YYYY-MM-DD/

Warning-only: Always exits with code 0.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Optional


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="PR49: Daily Shadow Diff Pipeline Runner (READ-ONLY)"
    )
    parser.add_argument(
        "--log_path",
        type=str,
        required=True,
        help="Path to execution log CSV (required)",
    )
    parser.add_argument(
        "--day",
        type=str,
        default=None,
        help="Optional: YYYY-MM-DD to process specific day",
    )
    parser.add_argument(
        "--analytics_out_dir",
        type=str,
        default="analytics_out",
        help="Output directory for PR47 analytics (default: analytics_out)",
    )
    parser.add_argument(
        "--reports_dir",
        type=str,
        default="reports",
        help="Output directory for PR48A/PR48B reports (default: reports)",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["md", "html", "both"],
        default="both",
        help="Report format for PR48A: md, html, or both (default: both)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce output (warnings still shown)",
    )
    return parser.parse_args()


def run_subprocess(cmd: list, step_name: str, quiet: bool = False) -> bool:
    """
    Run subprocess command.

    Returns True if successful, False otherwise.
    Warning-only: Never raises, always logs output.
    """
    if not quiet:
        print(f"[INFO][PR49] Running {step_name}...")
        print(f"[INFO][PR49] Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        if not quiet or result.returncode != 0:
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)

        if result.returncode != 0:
            print(f"[WARNING][PR49] {step_name} exited with code {result.returncode}")
            return False

        if not quiet:
            print(f"[INFO][PR49] {step_name} completed successfully")
        return True

    except Exception as e:
        print(f"[WARNING][PR49] {step_name} failed with exception: {e}")
        return False


def extract_day_from_pr47_output(analytics_out_dir: str) -> Optional[str]:
    """
    Extract day (YYYY-MM-DD) from PR47 overall_summary.json.

    Returns date_range.max_date if available, None otherwise.
    Warning-only: Returns None on any error.
    """
    json_path = os.path.join(analytics_out_dir, "pr47_shadow_diff_overall_summary.json")

    if not os.path.exists(json_path):
        print(f"[WARNING][PR49] PR47 overall summary not found: {json_path}")
        return None

    try:
        with open(json_path, "r") as f:
            data = json.load(f)

        date_range = data.get("date_range", {})
        max_date = date_range.get("max_date")

        if max_date and max_date != "UNKNOWN":
            print(f"[INFO][PR49] Extracted day from PR47 output: {max_date}")
            return max_date
        else:
            print(f"[WARNING][PR49] max_date unavailable in PR47 output")
            return None

    except Exception as e:
        print(f"[WARNING][PR49] Failed to extract day from PR47 output: {e}")
        return None


def get_fallback_day() -> str:
    """
    Get fallback day (current UTC date).

    Returns YYYY-MM-DD string.
    """
    day = datetime.utcnow().strftime("%Y-%m-%d")
    print(f"[INFO][PR49] Using fallback day (current UTC): {day}")
    return day


def run_pr47_export(log_path: str, analytics_out_dir: str, day: Optional[str], quiet: bool) -> bool:
    """
    Run PR47: Shadow Diff Analytics Export.

    Returns True if successful.
    """
    cmd = [
        sys.executable,
        "python/analytics/pr47_shadow_diff_analytics_export.py",
        "--log_path", log_path,
        "--out_dir", analytics_out_dir,
    ]

    if day:
        cmd.extend(["--day", day])

    return run_subprocess(cmd, "PR47 (Analytics Export)", quiet)


def run_pr48a_report_generator(analytics_out_dir: str, reports_dir: str, day: Optional[str], format: str, quiet: bool) -> bool:
    """
    Run PR48A: Shadow Diff Report Generator.

    Returns True if successful.
    """
    cmd = [
        sys.executable,
        "python/analytics/pr48a_shadow_diff_report_generator.py",
        "--in_dir", analytics_out_dir,
        "--out_dir", reports_dir,
        "--format", format,
    ]

    if day:
        cmd.extend(["--day", day])

    return run_subprocess(cmd, "PR48A (Report Generator)", quiet)


def run_pr48b_indexer(reports_dir: str, day: Optional[str], quiet: bool) -> bool:
    """
    Run PR48B: Shadow Diff Report Indexer.

    Returns True if successful.
    """
    cmd = [
        sys.executable,
        "python/analytics/pr48b_shadow_diff_report_indexer.py",
        "--reports_dir", reports_dir,
    ]

    if day:
        cmd.extend(["--day", day])

    return run_subprocess(cmd, "PR48B (Report Indexer)", quiet)


def main() -> int:
    """
    Main pipeline execution.

    Returns 0 (warning-only, never fails).
    """
    args = parse_args()

    print("=" * 60)
    print("PR49: Daily Shadow Diff Pipeline Runner")
    print("=" * 60)
    print(f"Log path: {args.log_path}")
    print(f"Analytics output: {args.analytics_out_dir}")
    print(f"Reports directory: {args.reports_dir}")
    print(f"Format: {args.format}")
    print(f"Day: {args.day or 'Auto-detect'}")
    print("=" * 60)

    # Validate log path exists
    if not os.path.exists(args.log_path):
        print(f"[WARNING][PR49] Log file not found: {args.log_path}")
        print(f"[WARNING][PR49] Pipeline will run in degraded mode")

    # Step 1: Run PR47 (Analytics Export)
    print()
    print("-" * 60)
    print("Step 1/3: PR47 Analytics Export")
    print("-" * 60)

    pr47_success = run_pr47_export(
        args.log_path,
        args.analytics_out_dir,
        args.day,
        args.quiet,
    )

    if not pr47_success:
        print("[WARNING][PR49] PR47 did not complete successfully")
        print("[WARNING][PR49] Continuing with degraded mode...")

    # Determine day for subsequent steps
    day_for_reports = args.day
    if not day_for_reports and pr47_success:
        # Try to extract from PR47 output
        day_for_reports = extract_day_from_pr47_output(args.analytics_out_dir)

    if not day_for_reports:
        # Fallback to current date
        day_for_reports = get_fallback_day()

    print(f"[INFO][PR49] Day for reports: {day_for_reports}")

    # Step 2: Run PR48A (Report Generator)
    print()
    print("-" * 60)
    print("Step 2/3: PR48A Report Generator")
    print("-" * 60)

    pr48a_success = run_pr48a_report_generator(
        args.analytics_out_dir,
        args.reports_dir,
        day_for_reports,
        args.format,
        args.quiet,
    )

    if not pr48a_success:
        print("[WARNING][PR49] PR48A did not complete successfully")
        print("[WARNING][PR49] Continuing with degraded mode...")

    # Step 3: Run PR48B (Report Indexer)
    print()
    print("-" * 60)
    print("Step 3/3: PR48B Report Indexer")
    print("-" * 60)

    pr48b_success = run_pr48b_indexer(
        args.reports_dir,
        day_for_reports,
        args.quiet,
    )

    if not pr48b_success:
        print("[WARNING][PR49] PR48B did not complete successfully")

    # Summary
    print()
    print("=" * 60)
    print("PR49: Pipeline Complete")
    print("=" * 60)

    if pr47_success and pr48a_success and pr48b_success:
        print("✓ All steps completed successfully")
    else:
        print("⚠ Some steps had warnings (degraded mode)")
        print(f"  PR47: {'✓' if pr47_success else '⚠'}")
        print(f"  PR48A: {'✓' if pr48a_success else '⚠'}")
        print(f"  PR48B: {'✓' if pr48b_success else '⚠'}")

    print()
    print("Output locations:")
    print(f"  Analytics: {args.analytics_out_dir}/")
    print(f"  Reports: {args.reports_dir}/")
    print(f"  Archive: {args.reports_dir}/_archive/{day_for_reports}/")
    print(f"  Index: {args.reports_dir}/index.{{md,json}}")

    print()
    print("=" * 60)
    print("Exit code: 0 (warning-only, pipeline never fails)")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
