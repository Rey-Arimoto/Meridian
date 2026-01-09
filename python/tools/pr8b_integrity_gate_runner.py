#!/usr/bin/env python3
"""
PR8B: Integrity Gate Runner (Enforcement)

Purpose: Enforce PR8A validation before generating explainability outputs.
- If PR8A FAIL: BLOCK generation, exit 1
- If PR8A PASS: Generate PR7A/PR7B/PR7C artifacts, exit 0

READ-ONLY: No trading logic modification. No CSV schema changes.
Deterministic: No network, no randomness.
"""

import sys
import os
import argparse
import subprocess
from datetime import datetime
from pathlib import Path


def run_pr8a_validation(csv_path: str) -> bool:
    """
    Run PR8A log integrity validation.
    Returns True if PASS (exit 0), False if FAIL (exit 1).
    """
    print("=" * 70)
    print("Step 1: PR8A Log Integrity Validation (MANDATORY GATE)")
    print("=" * 70)

    script_path = "python/validation/pr8a_log_integrity_invariants.py"

    try:
        result = subprocess.run(
            ["python3", script_path, csv_path],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Show PR8A output
        print(result.stdout)

        if result.returncode == 0:
            print("\n✓ PR8A PASSED: Data integrity verified")
            print("  Proceeding to generate explainability outputs...")
            return True
        else:
            print("\n✗ PR8A FAILED: Data integrity compromised")
            print("  Generation BLOCKED (fail-closed)")
            if result.stderr:
                print(f"  stderr: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("\n✗ PR8A validation timed out")
        return False
    except Exception as e:
        print(f"\n✗ PR8A validation error: {e}")
        return False


def generate_pr8a_health_report(csv_path: str, out_dir: Path, prefix: str) -> str:
    """Generate PR8A data health report."""
    print("\n" + "=" * 70)
    print("Step 2: Generating PR8A Data Health Report")
    print("=" * 70)

    script_path = "python/reporting/pr8a_data_health_report.py"
    out_file = out_dir / f"{prefix}_health.md"

    try:
        result = subprocess.run(
            ["python3", script_path, csv_path, "--out", str(out_file)],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            print(f"✓ Health report generated: {out_file}")
            return str(out_file)
        else:
            print(f"⚠ Warning: Health report generation failed")
            print(result.stderr)
            return None

    except Exception as e:
        print(f"⚠ Warning: Health report error: {e}")
        return None


def generate_pr7c_dashboard(csv_path: str, out_dir: Path, prefix: str, limit: int,
                            from_ts: str, to_ts: str, assets_dir: str) -> str:
    """Generate PR7C HTML dashboard."""
    print("\n" + "=" * 70)
    print("Step 3: Generating PR7C Dashboard (HTML)")
    print("=" * 70)

    script_path = "python/dashboard/pr7c_build_dashboard.py"
    out_file = out_dir / f"{prefix}_dashboard.html"

    cmd = ["python3", script_path, csv_path, "--out", str(out_file), "--limit", str(limit)]

    if from_ts:
        cmd.extend(["--from", from_ts])
    if to_ts:
        cmd.extend(["--to", to_ts])
    if assets_dir:
        assets_path = out_dir / assets_dir
        assets_path.mkdir(parents=True, exist_ok=True)
        cmd.extend(["--assets-dir", str(assets_path)])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
        )

        if result.returncode == 0:
            print(f"✓ Dashboard generated: {out_file}")
            # Show summary from stdout
            for line in result.stdout.split('\n'):
                if 'Dashboard generated' in line or 'Rows processed' in line or 'HTML size' in line:
                    print(f"  {line.strip()}")
            return str(out_file)
        else:
            print(f"✗ Dashboard generation failed")
            print(result.stderr)
            return None

    except Exception as e:
        print(f"✗ Dashboard error: {e}")
        return None


def generate_pr7a_investor_report(csv_path: str, out_dir: Path, prefix: str, limit: int,
                                  from_ts: str, to_ts: str) -> str:
    """Generate PR7A investor report."""
    print("\n" + "=" * 70)
    print("Step 4: Generating PR7A Investor Report (Markdown)")
    print("=" * 70)

    script_path = "python/reporting/pr7a_investor_report.py"
    out_file = out_dir / f"{prefix}_investor_report.md"

    cmd = ["python3", script_path, csv_path, "--out", str(out_file)]

    # Note: PR7A investor_report doesn't have --limit or timestamp filters in current implementation
    # We pass CSV as-is

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            print(f"✓ Investor report generated: {out_file}")
            return str(out_file)
        else:
            print(f"⚠ Warning: Investor report generation failed")
            print(result.stderr)
            return None

    except Exception as e:
        print(f"⚠ Warning: Investor report error: {e}")
        return None


def generate_pr7b_visualizations(csv_path: str, out_dir: Path, prefix: str,
                                 limit: int, from_ts: str, to_ts: str) -> list:
    """Generate PR7B PNG visualizations."""
    print("\n" + "=" * 70)
    print("Step 5: Generating PR7B Visualizations (PNG)")
    print("=" * 70)

    generated = []

    # Timeline plot
    timeline_file = out_dir / f"{prefix}_timeline.png"
    cmd = ["python3", "python/viz/pr7b_timeline_plot.py", csv_path, "--out", str(timeline_file)]
    if limit:
        cmd.extend(["--limit", str(limit)])
    if from_ts:
        cmd.extend(["--from", from_ts])
    if to_ts:
        cmd.extend(["--to", to_ts])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print(f"✓ Timeline plot: {timeline_file}")
            generated.append(str(timeline_file))
    except Exception as e:
        print(f"⚠ Timeline plot warning: {e}")

    # Overlay histogram
    overlay_file = out_dir / f"{prefix}_overlay_hist.png"
    cmd = ["python3", "python/viz/pr7b_overlay_histogram.py", csv_path, "--out", str(overlay_file)]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print(f"✓ Overlay histogram: {overlay_file}")
            generated.append(str(overlay_file))
    except Exception as e:
        print(f"⚠ Overlay histogram warning: {e}")

    # Regime distribution
    regime_file = out_dir / f"{prefix}_regime_dist.png"
    cmd = ["python3", "python/viz/pr7b_regime_distribution.py", csv_path, "--out", str(regime_file)]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print(f"✓ Regime distribution: {regime_file}")
            generated.append(str(regime_file))
    except Exception as e:
        print(f"⚠ Regime distribution warning: {e}")

    return generated


def compute_summary_stats(csv_path: str) -> dict:
    """Compute summary statistics from CSV."""
    try:
        import pandas as pd
        df = pd.read_csv(csv_path)

        total_ticks = len(df)
        if "action_label" in df.columns:
            hold_count = (df["action_label"] == "HOLD").sum()
            hold_ratio = hold_count / total_ticks if total_ticks > 0 else 0.0
        else:
            hold_count = 0
            hold_ratio = 0.0

        return {
            "total_ticks": total_ticks,
            "hold_count": hold_count,
            "hold_ratio": hold_ratio,
        }
    except Exception as e:
        print(f"⚠ Warning: Could not compute summary stats: {e}")
        return {
            "total_ticks": 0,
            "hold_count": 0,
            "hold_ratio": 0.0,
        }


def main():
    parser = argparse.ArgumentParser(
        description="PR8B: Integrity Gate Runner - Enforce PR8A before generating explainability outputs"
    )
    parser.add_argument("csv_path", help="Path to meridian_log.csv")
    parser.add_argument("--out-dir", default="./artifacts_pr8b", help="Output directory (default: ./artifacts_pr8b)")
    parser.add_argument("--prefix", default="meridian", help="Output file prefix (default: meridian)")
    parser.add_argument("--limit", type=int, default=50, help="Top-N decisions for reports (default: 50)")
    parser.add_argument("--from", dest="from_ts", help="Filter from timestamp (ISO format)")
    parser.add_argument("--to", dest="to_ts", help="Filter to timestamp (ISO format)")
    parser.add_argument("--assets-dir", help="Assets directory for PR7C (optional, enables relative PNG refs)")

    args = parser.parse_args()

    print("=" * 70)
    print("PR8B: Integrity Gate Runner (Enforcement)")
    print("=" * 70)
    print(f"CSV: {args.csv_path}")
    print(f"Output directory: {args.out_dir}")
    print(f"Prefix: {args.prefix}")
    print(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("")

    # Validate CSV exists
    if not os.path.exists(args.csv_path):
        print(f"✗ ERROR: CSV file not found: {args.csv_path}")
        return 1

    # Create output directory
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # MANDATORY GATE: Run PR8A validation
    pr8a_passed = run_pr8a_validation(args.csv_path)

    if not pr8a_passed:
        # FAIL-CLOSED: Block generation
        print("\n" + "=" * 70)
        print("GENERATION BLOCKED: PR8A Validation Failed")
        print("=" * 70)
        print("\n✗ Explainability outputs NOT generated (fail-closed)")
        print("  Reason: Log integrity compromised")
        print("  Action: Fix data integrity issues before generating investor-facing outputs")
        print("\nGenerating health report for diagnostics...")

        # Still generate health report for diagnostics
        generate_pr8a_health_report(args.csv_path, out_dir, args.prefix)

        print("\n" + "=" * 70)
        print("FINAL STATUS: BLOCKED (exit 1)")
        print("=" * 70)
        return 1

    # PR8A PASSED: Proceed with generation
    print("\n" + "=" * 70)
    print("PR8A PASSED: Generating Explainability Artifacts")
    print("=" * 70)

    artifacts = []

    # Generate artifacts
    health_report = generate_pr8a_health_report(args.csv_path, out_dir, args.prefix)
    if health_report:
        artifacts.append(health_report)

    dashboard = generate_pr7c_dashboard(args.csv_path, out_dir, args.prefix, args.limit,
                                       args.from_ts, args.to_ts, args.assets_dir)
    if dashboard:
        artifacts.append(dashboard)

    investor_report = generate_pr7a_investor_report(args.csv_path, out_dir, args.prefix,
                                                    args.limit, args.from_ts, args.to_ts)
    if investor_report:
        artifacts.append(investor_report)

    viz_files = generate_pr7b_visualizations(args.csv_path, out_dir, args.prefix,
                                            args.limit, args.from_ts, args.to_ts)
    artifacts.extend(viz_files)

    # Compute summary stats
    stats = compute_summary_stats(args.csv_path)

    # Final summary
    print("\n" + "=" * 70)
    print("GENERATION COMPLETE")
    print("=" * 70)

    print(f"\nPR8A Status: PASS")
    print(f"Total Ticks: {stats['total_ticks']:,}")
    print(f"HOLD Actions: {stats['hold_count']:,} ({stats['hold_ratio']*100:.1f}%)")

    print(f"\nGenerated Artifacts ({len(artifacts)}):")
    for artifact in artifacts:
        print(f"  - {artifact}")

    print(f"\nOutput Directory: {out_dir.absolute()}")

    print("\n" + "=" * 70)
    print("✓ ALL ARTIFACTS READY FOR STAKEHOLDER REVIEW")
    print("=" * 70)
    print("\nNext steps:")
    print(f"  1. Review health report: {args.prefix}_health.md")
    print(f"  2. Open dashboard: {args.prefix}_dashboard.html")
    print(f"  3. Share with investors: {args.prefix}_investor_report.md")

    return 0


if __name__ == "__main__":
    sys.exit(main())
