#!/usr/bin/env python3
"""
PR118: v1.0 Meridian CLI v1 (READ-ONLY)

Purpose:
    One-command end-to-end pipeline execution with human-readable digest.
    CLI = Display (not instruction/recommendation).

Constitutional Constraints:
    - READ-ONLY: No execution, no signing, no transaction construction
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - CLI = display only (not instruction)
    - Warning-only: Exit code always 0

CLI Philosophy:
    CLI ≠ Instruction
    CLI ≠ Recommendation
    CLI = Display

    CLI provides:
    - One-command end-to-end execution
    - Human-readable structural digest
    - Constitutional boundary enforcement

    CLI does NOT:
    - Recommend actions
    - Execute trades
    - Provide instructions
    - Display sensitive data

Commands:
    meridian demo --case A          Run demo with golden fixture case A
    meridian demo --case B          Run demo with golden fixture case B
    meridian run --config FILE      Run with provider config (future)
"""

import argparse
import sys
from typing import Any, Dict


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="meridian",
        description="Meridian v1.0 Intelligence Native Market Pipeline (READ-ONLY)",
        epilog="Constitutional guarantees: READ-ONLY, no execution, no sensitive data",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Demo command
    demo_parser = subparsers.add_parser(
        "demo", help="Run demo with golden fixtures"
    )
    demo_parser.add_argument(
        "--case",
        choices=["A", "B"],
        default="A",
        help="Golden test case (A=stable_low, B=high_variation)",
    )
    demo_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # Run command (placeholder for future)
    run_parser = subparsers.add_parser(
        "run", help="Run with provider config (future)"
    )
    run_parser.add_argument(
        "--config", type=str, help="Provider configuration file"
    )
    run_parser.add_argument(
        "--window", type=str, help="Observation window specification"
    )
    run_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args()

    # Handle commands
    if args.command == "demo":
        return run_demo_command(args)
    elif args.command == "run":
        return run_run_command(args)
    else:
        parser.print_help()
        return 0


def run_demo_command(args) -> int:
    """
    Run demo command with golden fixtures.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (always 0)
    """
    print("=" * 60)
    print("Meridian v1.0 Demo")
    print("=" * 60)
    print()

    case_name = f"case_{args.case}"
    print(f"Running golden test case: {case_name}")
    print()

    # Run regression harness (which runs full pipeline)
    try:
        from regression import run_golden_regression_v1

        result = run_golden_regression_v1(case_name)
    except Exception as e:
        print(f"Error running pipeline: {e}")
        return 0  # Warning-only

    # Check result status
    if result.get("status") == "ERROR":
        print(f"Pipeline error: {result.get('error_info')}")
        return 0  # Warning-only

    # Get actual bundle
    actual_bundle = result.get("actual_bundle")
    if not actual_bundle:
        # If match is True, regression harness doesn't return actual_bundle
        # Need to re-run to get bundle
        try:
            from orchestrator import run_pipeline_v1
            from bundle import build_artifact_bundle_v1
            import json
            from pathlib import Path

            # Load mock observations
            fixture_dir = (
                Path(__file__).parent.parent / "fixtures" / "golden" / "v1.0"
            )
            observations_file = fixture_dir / f"mock_observations_{case_name}.json"

            with open(observations_file, "r") as f:
                mock_observations = json.load(f)

            # Run pipeline
            orchestrator_output = run_pipeline_v1(
                onchain_analytics=mock_observations
            )
            actual_bundle = build_artifact_bundle_v1(orchestrator_output)
        except Exception as e:
            print(f"Error regenerating bundle: {e}")
            return 0  # Warning-only

    # Render digest
    try:
        from cli.v10_digest_renderer_v1 import render_digest

        if args.format == "json":
            digest = render_digest(actual_bundle, format="json")
        else:
            digest = render_digest(actual_bundle, format="text")

        print(digest)
    except Exception as e:
        print(f"Error rendering digest: {e}")
        return 0  # Warning-only

    # Report match status
    if result.get("match") is True:
        print()
        print("✓ Output matches expected golden fixture")
    elif result.get("match") is False:
        print()
        print("⚠ Output differs from expected golden fixture")
        print(f"Diff: {result.get('diff_summary')}")

    print()
    print("=" * 60)
    print("Demo complete (READ-ONLY, no execution)")
    print("=" * 60)

    return 0  # Warning-only


def run_run_command(args) -> int:
    """
    Run command with provider config (placeholder for future).

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (always 0)
    """
    print("=" * 60)
    print("Meridian v1.0 Run")
    print("=" * 60)
    print()
    print("⚠ Run command not yet implemented")
    print("Use 'meridian demo --case A' for demo mode")
    print()
    print("=" * 60)

    return 0  # Warning-only


if __name__ == "__main__":
    sys.exit(main())
