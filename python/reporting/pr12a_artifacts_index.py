#!/usr/bin/env python3
"""
PR12A: Artifacts Index & Reader Entry Point

Purpose: Generate index.md as entry point for artifacts directory.
Input: --out-dir (required), --prefix (optional)
Output: index.md in out-dir

READ-ONLY: No trading logic modification. No CSV schema changes.
Deterministic: No network, no randomness.
"""

import sys
import os
import argparse
from datetime import datetime
from pathlib import Path


def check_file_exists(out_dir: Path, filename: str) -> bool:
    """Check if file exists in output directory."""
    return (out_dir / filename).exists()


def get_file_size(out_dir: Path, filename: str) -> str:
    """Get human-readable file size."""
    file_path = out_dir / filename
    if not file_path.exists():
        return "N/A"

    size = file_path.stat().st_size
    if size < 1024:
        return f"{size} bytes"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / (1024 * 1024):.1f} MB"


def generate_index(out_dir: Path, prefix: str, log_path: str = None, blocked: bool = False) -> str:
    """Generate index.md content."""

    lines = []

    # Title
    lines.append(f"# Meridian Artifacts Index")
    lines.append("")
    lines.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("")

    if blocked:
        lines.append("> **⚠ WARNING: Artifact generation was BLOCKED by PR8B integrity gate.**")
        lines.append(">")
        lines.append("> Some reports may be missing or incomplete.")
        lines.append("> Review the health report for diagnostic information.")
        lines.append("")

    if log_path:
        lines.append(f"**Input Log:** `{log_path}`")
        lines.append("")

    # Recommended Reading Order
    lines.append("## Recommended Reading Order")
    lines.append("")
    lines.append("For best understanding of system behavior, review artifacts in this order:")
    lines.append("")

    # 1. Data Quality Gate
    health_exists = check_file_exists(out_dir, f"{prefix}_health.md")
    lines.append("### 1. Data Quality Gate (PR8A/PR8B)")
    lines.append("")
    if health_exists:
        lines.append(f"- [**{prefix}_health.md**]({prefix}_health.md) ✅")
    else:
        lines.append(f"- **{prefix}_health.md** ❌ N/A")
    lines.append("")
    lines.append("Verify data integrity before interpreting performance metrics.")
    lines.append("")

    # 2. Performance & Risk Summary
    perf_exists = check_file_exists(out_dir, f"{prefix}_performance.md")
    lines.append("### 2. Performance & Risk Summary (PR9A/PR11A)")
    lines.append("")
    if perf_exists:
        lines.append(f"- [**{prefix}_performance.md**]({prefix}_performance.md) ✅")
    else:
        lines.append(f"- **{prefix}_performance.md** ❌ N/A")
    lines.append("")
    lines.append("Interpretation-stable metrics: equity-based performance, exposure, decision stability, regime-based analysis.")
    lines.append("")

    # 3. Investor Report
    investor_exists = check_file_exists(out_dir, f"{prefix}_investor_report.md")
    lines.append("### 3. Investor Report (PR7A)")
    lines.append("")
    if investor_exists:
        lines.append(f"- [**{prefix}_investor_report.md**]({prefix}_investor_report.md) ✅")
    else:
        lines.append(f"- **{prefix}_investor_report.md** ❌ N/A")
    lines.append("")
    lines.append("Concise summary of key decision-making metrics and entropy regime distribution.")
    lines.append("")

    # 4. Visualizations
    timeline_exists = check_file_exists(out_dir, f"{prefix}_timeline.png")
    overlay_exists = check_file_exists(out_dir, f"{prefix}_overlay_hist.png")
    regime_exists = check_file_exists(out_dir, f"{prefix}_regime_dist.png")

    lines.append("### 4. Visualizations (PR7B)")
    lines.append("")
    if timeline_exists:
        lines.append(f"- [**{prefix}_timeline.png**]({prefix}_timeline.png) ✅")
    else:
        lines.append(f"- **{prefix}_timeline.png** ❌ N/A")

    if overlay_exists:
        lines.append(f"- [**{prefix}_overlay_hist.png**]({prefix}_overlay_hist.png) ✅")
    else:
        lines.append(f"- **{prefix}_overlay_hist.png** ❌ N/A")

    if regime_exists:
        lines.append(f"- [**{prefix}_regime_dist.png**]({prefix}_regime_dist.png) ✅")
    else:
        lines.append(f"- **{prefix}_regime_dist.png** ❌ N/A")
    lines.append("")
    lines.append("Visual timeline, overlay distribution, and regime breakdown.")
    lines.append("")

    # 5. Dashboard
    dashboard_exists = check_file_exists(out_dir, f"{prefix}_dashboard.html")
    lines.append("### 5. Interactive Dashboard (PR7C)")
    lines.append("")
    if dashboard_exists:
        lines.append(f"- [**{prefix}_dashboard.html**]({prefix}_dashboard.html) ✅")
    else:
        lines.append(f"- **{prefix}_dashboard.html** ❌ N/A")
    lines.append("")
    lines.append("Interactive HTML dashboard with embedded visualizations.")
    lines.append("")

    # Artifacts Inventory
    lines.append("---")
    lines.append("")
    lines.append("## Artifacts Inventory")
    lines.append("")
    lines.append("Complete list of generated artifacts:")
    lines.append("")
    lines.append("| File | Status | Size |")
    lines.append("|------|--------|------|")

    # List all expected artifacts
    expected_files = [
        f"{prefix}_health.md",
        f"{prefix}_performance.md",
        f"{prefix}_investor_report.md",
        f"{prefix}_timeline.png",
        f"{prefix}_overlay_hist.png",
        f"{prefix}_regime_dist.png",
        f"{prefix}_dashboard.html",
        "input_log.csv",
    ]

    for filename in expected_files:
        exists = check_file_exists(out_dir, filename)
        status = "✅" if exists else "❌ N/A"
        size = get_file_size(out_dir, filename) if exists else "N/A"
        lines.append(f"| `{filename}` | {status} | {size} |")

    lines.append("")

    # Notes
    lines.append("---")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- All tick-based durations are reported in ticks, not time.")
    lines.append("- Performance metrics require valid `equity` column in the log.")
    lines.append("- Regime-based analysis requires `regime` column in the log.")
    lines.append("- PR8B integrity gate blocks report generation if data quality issues are detected.")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Generated by PR12A: Artifacts Index & Reader Entry Point*")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="PR12A: Generate artifacts index.md"
    )
    parser.add_argument("--out-dir", required=True, help="Artifacts output directory (required)")
    parser.add_argument("--prefix", default="meridian", help="Output file prefix (default: meridian)")
    parser.add_argument("--log", help="Path to input log (optional, for display only)")
    parser.add_argument("--blocked", action="store_true", help="Mark as blocked by PR8B gate")

    args = parser.parse_args()

    # Validate output directory exists
    out_dir = Path(args.out_dir)
    if not out_dir.exists():
        print(f"Error: Output directory not found: {args.out_dir}", file=sys.stderr)
        return 1

    # Generate index
    index_content = generate_index(out_dir, args.prefix, args.log, args.blocked)

    # Write index.md
    index_path = out_dir / "index.md"
    try:
        with open(index_path, "w") as f:
            f.write(index_content)

        print(f"✓ Generated index: {index_path}")
        return 0

    except Exception as e:
        print(f"Error writing index.md: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
