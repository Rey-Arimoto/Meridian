#!/usr/bin/env python3
"""
PR10: Production Log Ops & Canonical Pipeline

Purpose: Canonical 1-command pipeline for real log operations.
- Copy input log to artifacts with timestamp isolation
- Run PR8B integrity gate runner on the fixed copy
- Prevent log mixing, overwrite, and collision

READ-ONLY: No trading logic modification. No CSV schema changes.
Deterministic: No network, no randomness.
"""

import sys
import os
import argparse
import subprocess
import shutil
from datetime import datetime
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="PR10: Canonical pipeline - Copy log to artifacts, run PR8B gate runner"
    )
    parser.add_argument("--log", required=True, help="Path to input log CSV (required)")
    parser.add_argument("--prefix", default="meridian", help="Output file prefix (default: meridian)")
    parser.add_argument("--limit", type=int, help="Top-N decisions for reports (optional, passed to PR8B)")
    parser.add_argument("--from", dest="from_ts", help="Filter from timestamp (optional, passed to PR8B)")
    parser.add_argument("--to", dest="to_ts", help="Filter to timestamp (optional, passed to PR8B)")
    parser.add_argument("--debug", action="store_true", help="Show diagnostic information")

    args = parser.parse_args()

    # Diagnostic: Show which Python is being used (only if --debug or MERIDIAN_DEBUG=1)
    if args.debug or os.environ.get("MERIDIAN_DEBUG"):
        print(f"Python executable: {sys.executable}")
        print("")

    print("=" * 70)
    print("PR10: Production Log Ops & Canonical Pipeline")
    print("=" * 70)
    print(f"Input log: {args.log}")
    print(f"Prefix: {args.prefix}")
    print(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("")

    # Step 1: Validate input log exists
    if not os.path.exists(args.log):
        print(f"✗ ERROR: Input log not found: {args.log}")
        return 1

    print(f"✓ Input log exists: {args.log}")
    print("")

    # Step 2: Create timestamped output directory
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_dir = Path("artifacts") / f"_{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"✓ Created output directory: {out_dir}")
    print("")

    # Step 3: Copy input log to output directory (fixed copy)
    fixed_log_path = out_dir / "input_log.csv"

    try:
        shutil.copy2(args.log, fixed_log_path)
        print(f"✓ Copied input log to: {fixed_log_path}")
        print("  (This fixed copy will be used for all processing)")
        print("")
    except Exception as e:
        print(f"✗ ERROR: Failed to copy input log: {e}")
        return 1

    # Step 4: Build PR8B command
    pr8b_script = "python/tools/pr8b_integrity_gate_runner.py"

    cmd = [
        sys.executable,
        pr8b_script,
        str(fixed_log_path),
        "--out-dir", str(out_dir),
        "--prefix", args.prefix,
    ]

    # Pass through optional arguments
    if args.limit:
        cmd.extend(["--limit", str(args.limit)])
    if args.from_ts:
        cmd.extend(["--from", args.from_ts])
    if args.to_ts:
        cmd.extend(["--to", args.to_ts])
    if args.debug:
        cmd.append("--debug")

    # Step 5: Execute PR8B integrity gate runner
    print("=" * 70)
    print("Executing PR8B Integrity Gate Runner")
    print("=" * 70)
    print(f"Command: {' '.join(cmd)}")
    print("")

    try:
        result = subprocess.run(
            cmd,
            timeout=600,  # 10 minute timeout
        )

        exit_code = result.returncode

        # Step 6: Report results
        print("")
        print("=" * 70)
        print("PR10: Pipeline Complete")
        print("=" * 70)

        if exit_code == 0:
            print("")
            print("✓ PIPELINE SUCCESS")
            print("")
            print(f"Output directory: {out_dir.absolute()}")
            print(f"Fixed input log:  {fixed_log_path}")
            print("")
            print("Generated artifacts:")

            # List all files in output directory
            if out_dir.exists():
                for item in sorted(out_dir.iterdir()):
                    if item.is_file():
                        size = item.stat().st_size
                        if size < 1024:
                            size_str = f"{size} bytes"
                        elif size < 1024 * 1024:
                            size_str = f"{size / 1024:.1f} KB"
                        else:
                            size_str = f"{size / (1024 * 1024):.1f} MB"
                        print(f"  - {item.name} ({size_str})")

            print("")
            print("Next steps:")
            print(f"  1. Review reports in: {out_dir.absolute()}")
            print(f"  2. Open dashboard: {out_dir / f'{args.prefix}_dashboard.html'}")
            print(f"  3. Share performance report: {out_dir / f'{args.prefix}_performance.md'}")
        else:
            print("")
            print("✗ PIPELINE FAILED")
            print(f"  PR8B exited with code: {exit_code}")
            print("")
            print(f"Output directory: {out_dir.absolute()}")
            print(f"Check health report for diagnostics: {out_dir / f'{args.prefix}_health.md'}")

        print("")
        print("=" * 70)

        return exit_code

    except subprocess.TimeoutExpired:
        print("")
        print("✗ ERROR: PR8B timed out (exceeded 10 minutes)")
        return 1
    except Exception as e:
        print("")
        print(f"✗ ERROR: Pipeline execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
