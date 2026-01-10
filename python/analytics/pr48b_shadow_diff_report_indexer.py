#!/usr/bin/env python3
"""
PR48B: v0.5 Shadow Diff Report Index & Archive (TOC + History, READ-ONLY)

Purpose:
    Archive PR48A daily reports into date-organized structure and generate
    index files (Markdown TOC + JSON registry) for navigation and reference.

Constitutional Constraints:
    - READ-ONLY: No execution logic, order, weight, or decision changes
    - Warning-only: Exit code always 0, continues on errors
    - Non-evaluative: No good/bad, win/loss, correct/wrong vocabulary
    - Non-scoric: No scores, grades, rankings, or performance metrics
    - v0.4 boundary protection: No confidence_reason analysis

Input:
    - PR48A reports (md/html files)
    - CLI args: --reports_dir, --in_dir, --out_dir, --day

Output:
    - reports/index.md (human-readable TOC)
    - reports/index.json (machine-readable registry)
    - reports/_archive/YYYY-MM-DD/ (date-organized archives)

Directory Structure:
    reports/
      index.md
      index.json
      _archive/
        2026-01-10/
          shadow_diff_report.md
          shadow_diff_report.html
          meta.json

Allowed Vocabulary:
    - Observation: observed, recorded, present, absent, available, missing
    - Status: AVAILABLE, MISSING, PARTIAL

Forbidden Vocabulary:
    - Evaluation: good/bad, better/worse, correct/wrong
    - Outcome: profit/loss, win/lose, success/failure
    - Scoring: score, grade, rank

Warning-only: Always exits with code 0.
"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="PR48B: Shadow Diff Report Index & Archive (READ-ONLY)"
    )
    parser.add_argument(
        "--reports_dir",
        type=str,
        default="reports",
        help="Reports directory (default: reports)",
    )
    parser.add_argument(
        "--day",
        type=str,
        default=None,
        help="Optional: YYYY-MM-DD to archive specific day only",
    )
    return parser.parse_args()


def validate_day_format(day: str) -> bool:
    """
    Validate YYYY-MM-DD format.

    Warning-only: Returns False if invalid.
    """
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    if not re.match(pattern, day):
        print(f"[WARNING][PR48B] Invalid day format: {day} (expected YYYY-MM-DD)")
        return False
    return True


def scan_reports_directory(reports_dir: str, day_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Scan reports directory for md/html files.

    Returns list of discovered reports with metadata.
    Warning-only: Returns empty list if directory not found.
    """
    if not os.path.isdir(reports_dir):
        print(f"[WARNING][PR48B] Reports directory not found: {reports_dir}")
        return []

    discovered = []

    # Look for pr48a reports in root
    for filename in os.listdir(reports_dir):
        if filename.endswith(".md") or filename.endswith(".html"):
            full_path = os.path.join(reports_dir, filename)

            # Try to infer day from filename or file content
            day = infer_day_from_file(full_path)

            if day_filter and day != day_filter:
                continue

            if day:
                discovered.append({
                    "day": day,
                    "path": full_path,
                    "filename": filename,
                    "format": "md" if filename.endswith(".md") else "html",
                })

    # Look for already archived reports
    archive_dir = os.path.join(reports_dir, "_archive")
    if os.path.isdir(archive_dir):
        for day_dir in os.listdir(archive_dir):
            day_path = os.path.join(archive_dir, day_dir)
            if not os.path.isdir(day_path):
                continue

            if not validate_day_format(day_dir):
                continue

            if day_filter and day_dir != day_filter:
                continue

            # Scan for md/html in this day directory
            for filename in os.listdir(day_path):
                if filename.endswith(".md") or filename.endswith(".html"):
                    full_path = os.path.join(day_path, filename)
                    discovered.append({
                        "day": day_dir,
                        "path": full_path,
                        "filename": filename,
                        "format": "md" if filename.endswith(".md") else "html",
                        "already_archived": True,
                    })

    print(f"[INFO][PR48B] Discovered {len(discovered)} report file(s)")
    return discovered


def infer_day_from_file(file_path: str) -> Optional[str]:
    """
    Infer day (YYYY-MM-DD) from file content or metadata.

    Warning-only: Returns None if cannot infer.
    """
    try:
        with open(file_path, "r") as f:
            content = f.read(2000)  # Read first 2000 chars

        # Look for date patterns in content
        # Pattern 1: "Date range: YYYY-MM-DD to YYYY-MM-DD"
        match = re.search(r"Date range:\s*(\d{4}-\d{2}-\d{2})", content)
        if match:
            return match.group(1)

        # Pattern 2: "Date: YYYY-MM-DD" or "**Date:** YYYY-MM-DD"
        match = re.search(r"\*\*Date:\*\*\s*(\d{4}-\d{2}-\d{2})", content)
        if match:
            return match.group(1)

        # Pattern 3: Any YYYY-MM-DD in first 500 chars
        match = re.search(r"(\d{4}-\d{2}-\d{2})", content[:500])
        if match:
            return match.group(1)

    except Exception as e:
        print(f"[WARNING][PR48B] Could not infer day from {file_path}: {e}")

    return None


def archive_report(report: Dict[str, Any], reports_dir: str) -> Dict[str, str]:
    """
    Archive report file to _archive/YYYY-MM-DD/.

    Returns dict with archived paths {md: ..., html: ...}.
    Warning-only: Returns empty dict if archiving fails.
    """
    day = report["day"]
    archive_day_dir = os.path.join(reports_dir, "_archive", day)

    try:
        Path(archive_day_dir).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[WARNING][PR48B] Failed to create archive directory: {e}")
        return {}

    # Skip if already archived
    if report.get("already_archived"):
        return {}

    # Determine canonical filename
    canonical_name = f"shadow_diff_report.{report['format']}"
    dest_path = os.path.join(archive_day_dir, canonical_name)

    try:
        shutil.copy2(report["path"], dest_path)
        print(f"[INFO][PR48B] Archived {report['format']} for {day}: {dest_path}")
        return {report["format"]: dest_path}
    except Exception as e:
        print(f"[WARNING][PR48B] Failed to archive {report['path']}: {e}")
        return {}


def generate_meta_json(day: str, reports_dir: str) -> None:
    """
    Generate meta.json for archived day.

    Warning-only: Fails silently if cannot write.
    """
    meta_path = os.path.join(reports_dir, "_archive", day, "meta.json")

    meta = {
        "day": day,
        "archived_at": datetime.utcnow().isoformat() + "Z",
        "source": {
            "generator": "pr48a_shadow_diff_report_generator",
            "inputs": [
                "pr47_shadow_diff_overall_summary.json",
                "pr47_shadow_diff_daily_summary.csv",
            ],
        },
    }

    try:
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)
        print(f"[INFO][PR48B] Generated meta.json: {meta_path}")
    except Exception as e:
        print(f"[WARNING][PR48B] Failed to write meta.json: {e}")


def collect_archive_inventory(reports_dir: str) -> List[Dict[str, Any]]:
    """
    Collect inventory of all archived days.

    Returns list of day records with paths and status.
    """
    archive_dir = os.path.join(reports_dir, "_archive")
    if not os.path.isdir(archive_dir):
        print(f"[INFO][PR48B] No archive directory found")
        return []

    inventory = []

    for day_name in sorted(os.listdir(archive_dir)):
        day_path = os.path.join(archive_dir, day_name)
        if not os.path.isdir(day_path):
            continue

        if not validate_day_format(day_name):
            continue

        # Collect paths
        md_path = os.path.join(day_path, "shadow_diff_report.md")
        html_path = os.path.join(day_path, "shadow_diff_report.html")
        meta_path = os.path.join(day_path, "meta.json")

        has_md = os.path.exists(md_path)
        has_html = os.path.exists(html_path)
        has_meta = os.path.exists(meta_path)

        # Determine status
        if has_md:
            status = "AVAILABLE"
        elif has_html:
            status = "PARTIAL"  # HTML without MD
        else:
            status = "MISSING"

        # Build relative paths
        rel_md = os.path.relpath(md_path, reports_dir) if has_md else None
        rel_html = os.path.relpath(html_path, reports_dir) if has_html else None
        rel_meta = os.path.relpath(meta_path, reports_dir) if has_meta else None

        inventory.append({
            "day": day_name,
            "paths": {
                "md": rel_md,
                "html": rel_html,
                "meta": rel_meta,
            },
            "status": status,
        })

    print(f"[INFO][PR48B] Collected inventory: {len(inventory)} day(s)")
    return inventory


def generate_index_json(inventory: List[Dict[str, Any]], reports_dir: str) -> None:
    """
    Generate index.json (machine-readable registry).

    Warning-only: Fails silently if cannot write.
    """
    index_path = os.path.join(reports_dir, "index.json")

    # Find latest day
    latest_day = None
    if inventory:
        available_days = [item["day"] for item in inventory if item["status"] == "AVAILABLE"]
        if available_days:
            latest_day = max(available_days)

    index_data = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "root_dir": reports_dir,
        "days": inventory,
        "latest_day": latest_day,
    }

    try:
        with open(index_path, "w") as f:
            json.dump(index_data, f, indent=2)
        print(f"[INFO][PR48B] Generated index.json: {index_path}")
    except Exception as e:
        print(f"[WARNING][PR48B] Failed to write index.json: {e}")


def generate_index_md(inventory: List[Dict[str, Any]], reports_dir: str) -> None:
    """
    Generate index.md (human-readable TOC).

    Warning-only: Fails silently if cannot write.
    """
    index_path = os.path.join(reports_dir, "index.md")

    lines = []

    # Header
    lines.append("# Shadow Diff Reports (v0.5)")
    lines.append("")

    # Latest day
    available_days = [item["day"] for item in inventory if item["status"] == "AVAILABLE"]
    if available_days:
        latest = max(available_days)
        lines.append(f"**Latest:** {latest}")
    else:
        lines.append("**Latest:** None")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Archive section
    lines.append("## Archive")
    lines.append("")

    if not inventory:
        lines.append("No reports archived.")
    else:
        for item in sorted(inventory, key=lambda x: x["day"], reverse=True):
            day = item["day"]
            has_md = item["paths"]["md"] is not None
            has_html = item["paths"]["html"] is not None

            formats = []
            if has_md:
                formats.append("[markdown]({})".format(item["paths"]["md"]))
            if has_html:
                formats.append("[html]({})".format(item["paths"]["html"]))

            if formats:
                format_str = " / ".join(formats)
                lines.append(f"- **{day}** — {format_str}")
            else:
                lines.append(f"- **{day}** — (missing)")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Notes
    lines.append("## Notes")
    lines.append("")
    lines.append("- This index is generated from archived reports.")
    lines.append("- Reports are observational only. No evaluations are made.")
    lines.append("- Archive structure: `_archive/YYYY-MM-DD/`")
    lines.append("")

    content = "\n".join(lines)

    try:
        with open(index_path, "w") as f:
            f.write(content)
        print(f"[INFO][PR48B] Generated index.md: {index_path}")
    except Exception as e:
        print(f"[WARNING][PR48B] Failed to write index.md: {e}")


def main() -> int:
    """
    Main execution.

    Returns 0 (warning-only, never fails).
    """
    args = parse_args()

    print("=" * 60)
    print("PR48B: Shadow Diff Report Index & Archive")
    print("=" * 60)
    print(f"Reports directory: {args.reports_dir}")
    print(f"Day filter: {args.day or 'None (all days)'}")
    print("=" * 60)

    # Scan for reports
    discovered_reports = scan_reports_directory(args.reports_dir, args.day)

    # Group by day
    days_to_archive = {}
    for report in discovered_reports:
        day = report["day"]
        if day not in days_to_archive:
            days_to_archive[day] = []
        days_to_archive[day].append(report)

    # Archive each day
    for day, reports in days_to_archive.items():
        print(f"[INFO][PR48B] Processing day: {day}")

        # Archive reports
        for report in reports:
            archive_report(report, args.reports_dir)

        # Generate meta.json
        generate_meta_json(day, args.reports_dir)

    # Collect inventory from archive
    inventory = collect_archive_inventory(args.reports_dir)

    # Generate index files
    generate_index_json(inventory, args.reports_dir)
    generate_index_md(inventory, args.reports_dir)

    print("=" * 60)
    print("PR48B: Indexing complete (warning-only, exit code 0)")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
