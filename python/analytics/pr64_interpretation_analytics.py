#!/usr/bin/env python3
"""
PR64: v0.6 Interpretation Analytics (Meaning Distribution & Transition, READ-ONLY)

Purpose:
    Visualize interpretation meaning distribution, structure, and transitions.
    Observe meaning landscape without evaluation or judgment.

Constitutional Constraints:
    - READ-ONLY: No execution logic or decision changes
    - Non-evaluative: No good/bad, correct/wrong vocabulary
    - Non-scoric: No scores, grades, rankings
    - Non-prescriptive: No "should" or recommendations
    - Observation-bound: Only uses interpretation fields
    - v0.4 boundary protection: No confidence_reason analysis

Philosophy:
    PR61/PR63 create and decompose meaning (point, structure).
    PR64 observes meaning as landscape (distribution, transition).

    This is analysis, not optimization.
    This is insight, not recommendation.

Questions PR64 Answers:
    - Which meaning tags exist, how many?
    - Which factors/signals appear, in what structure?
    - How do meanings transition over time?

Questions PR64 Does NOT Answer:
    - Is this good or bad?
    - Did it improve or degrade?
    - What should be done?

Warning-only: Always exits with code 0.
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="PR64: Interpretation Analytics Generator (READ-ONLY)"
    )
    parser.add_argument(
        "--in_file",
        type=str,
        required=True,
        help="Path to interpretation records file (JSONL)",
    )
    parser.add_argument(
        "--out_dir",
        type=str,
        default="analytics_out",
        help="Output directory for analytics (default: analytics_out)",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "csv", "both"],
        default="both",
        help="Output format: json, csv, or both (default: both)",
    )
    return parser.parse_args()


def load_interpretation_records(path: str) -> List[Dict[str, Any]]:
    """
    Load interpretation records from JSONL file.

    Warning-only: Returns empty list if file not found or parse error.

    Args:
        path: Path to JSONL file

    Returns:
        List of interpretation records
    """
    if not os.path.exists(path):
        print(f"[WARNING][PR64] Input file not found: {path}")
        return []

    records = []

    try:
        with open(path, "r") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    record = json.loads(line)
                    records.append(record)
                except json.JSONDecodeError as e:
                    print(f"[WARNING][PR64] Failed to parse line {line_no}: {e}")
                    continue

        print(f"[INFO][PR64] Loaded {len(records)} interpretation records from {path}")
        return records

    except Exception as e:
        print(f"[WARNING][PR64] Failed to read file: {e}")
        return []


def aggregate_meaning_distribution(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate meaning distribution from interpretation records.

    Non-evaluative: Only counts, no judgment.

    Args:
        records: List of interpretation records

    Returns:
        Dict with distribution aggregates
    """
    distribution = {
        "total_records": len(records),
        "meaning_tag_counts": defaultdict(int),
        "meaning_status_counts": defaultdict(int),
        "factor_counts": defaultdict(int),
        "signal_counts": defaultdict(int),
    }

    for record in records:
        # Meaning tag
        tag = record.get("v6_meaning_tag", "UNKNOWN")
        distribution["meaning_tag_counts"][tag] += 1

        # Meaning status
        status = record.get("v6_meaning_status", "UNKNOWN")
        distribution["meaning_status_counts"][status] += 1

        # Factors (v2)
        factors = record.get("v6_meaning_factors", [])
        if isinstance(factors, list):
            for factor in factors:
                distribution["factor_counts"][factor] += 1

        # Signals (v2)
        signals = record.get("v6_meaning_signals", [])
        if isinstance(signals, list):
            for signal in signals:
                distribution["signal_counts"][signal] += 1

    # Convert defaultdict to dict
    distribution["meaning_tag_counts"] = dict(distribution["meaning_tag_counts"])
    distribution["meaning_status_counts"] = dict(distribution["meaning_status_counts"])
    distribution["factor_counts"] = dict(distribution["factor_counts"])
    distribution["signal_counts"] = dict(distribution["signal_counts"])

    return distribution


def aggregate_meaning_transitions(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate meaning transitions over time.

    Non-evaluative: Only observes transitions, no judgment.

    Args:
        records: List of interpretation records (must have timestamp/day)

    Returns:
        Dict with transition aggregates
    """
    # Group by day
    by_day = defaultdict(list)

    for record in records:
        # Try to extract day from timestamp or day field
        day = record.get("day", "UNKNOWN")

        if day == "UNKNOWN" and "timestamp" in record:
            # Try to parse timestamp
            try:
                ts = record["timestamp"]
                if isinstance(ts, str):
                    # Parse ISO format
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    day = dt.strftime("%Y-%m-%d")
            except Exception:
                pass

        by_day[day].append(record)

    # Aggregate per day
    daily_distributions = {}

    for day, day_records in sorted(by_day.items()):
        day_dist = {
            "day": day,
            "record_count": len(day_records),
            "meaning_tag_counts": defaultdict(int),
            "meaning_status_counts": defaultdict(int),
        }

        for record in day_records:
            tag = record.get("v6_meaning_tag", "UNKNOWN")
            day_dist["meaning_tag_counts"][tag] += 1

            status = record.get("v6_meaning_status", "UNKNOWN")
            day_dist["meaning_status_counts"][status] += 1

        # Convert to dict
        day_dist["meaning_tag_counts"] = dict(day_dist["meaning_tag_counts"])
        day_dist["meaning_status_counts"] = dict(day_dist["meaning_status_counts"])

        daily_distributions[day] = day_dist

    # Compute transitions (day-to-day)
    transitions = []
    days_sorted = sorted([d for d in by_day.keys() if d != "UNKNOWN"])

    for i in range(len(days_sorted) - 1):
        day1 = days_sorted[i]
        day2 = days_sorted[i + 1]

        dist1 = daily_distributions[day1]["meaning_tag_counts"]
        dist2 = daily_distributions[day2]["meaning_tag_counts"]

        # Compute simple transition observation
        transition = {
            "from_day": day1,
            "to_day": day2,
            "from_distribution": dist1,
            "to_distribution": dist2,
        }

        transitions.append(transition)

    return {
        "daily_distributions": daily_distributions,
        "transitions": transitions,
        "days_observed": len(daily_distributions),
    }


def generate_summary_json(
    distribution: Dict[str, Any],
    transitions: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate overall summary JSON.

    Non-evaluative: Only aggregates, no judgment.

    Args:
        distribution: Meaning distribution aggregates
        transitions: Meaning transition aggregates

    Returns:
        Summary dict
    """
    return {
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "analytics_type": "interpretation_analytics_v0.6",
        "distribution": distribution,
        "transitions": transitions,
        "notes": [
            "observational only",
            "no evaluations made",
            "no action changes",
            "meaning distribution and transition visibility",
        ],
    }


def export_json(data: Dict[str, Any], out_path: str) -> None:
    """Export JSON analytics."""
    try:
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[INFO][PR64] Exported JSON analytics: {out_path}")
    except Exception as e:
        print(f"[WARNING][PR64] Failed to export JSON: {e}")


def export_csv_distribution(distribution: Dict[str, Any], out_dir: str) -> None:
    """Export distribution as CSV tables."""
    try:
        # Meaning tag distribution
        tag_counts = distribution["meaning_tag_counts"]
        if tag_counts:
            tag_df = pd.DataFrame([
                {"meaning_tag": tag, "count": count}
                for tag, count in sorted(tag_counts.items())
            ])
            tag_path = os.path.join(out_dir, "pr64_meaning_tag_distribution.csv")
            tag_df.to_csv(tag_path, index=False)
            print(f"[INFO][PR64] Exported meaning tag distribution CSV: {tag_path}")

        # Factor distribution
        factor_counts = distribution["factor_counts"]
        if factor_counts:
            factor_df = pd.DataFrame([
                {"factor": factor, "count": count}
                for factor, count in sorted(factor_counts.items())
            ])
            factor_path = os.path.join(out_dir, "pr64_factor_distribution.csv")
            factor_df.to_csv(factor_path, index=False)
            print(f"[INFO][PR64] Exported factor distribution CSV: {factor_path}")

        # Signal distribution
        signal_counts = distribution["signal_counts"]
        if signal_counts:
            signal_df = pd.DataFrame([
                {"signal": signal, "count": count}
                for signal, count in sorted(signal_counts.items())
            ])
            signal_path = os.path.join(out_dir, "pr64_signal_distribution.csv")
            signal_df.to_csv(signal_path, index=False)
            print(f"[INFO][PR64] Exported signal distribution CSV: {signal_path}")

    except Exception as e:
        print(f"[WARNING][PR64] Failed to export distribution CSV: {e}")


def export_csv_transitions(transitions: Dict[str, Any], out_dir: str) -> None:
    """Export transitions as CSV table."""
    try:
        daily_dists = transitions["daily_distributions"]

        if daily_dists:
            # Create daily summary table
            rows = []
            for day in sorted(daily_dists.keys()):
                dist = daily_dists[day]
                row = {
                    "day": day,
                    "record_count": dist["record_count"],
                }

                # Add meaning tag counts as columns
                for tag, count in dist["meaning_tag_counts"].items():
                    row[f"tag_{tag}"] = count

                rows.append(row)

            daily_df = pd.DataFrame(rows)
            daily_path = os.path.join(out_dir, "pr64_daily_meaning_distribution.csv")
            daily_df.to_csv(daily_path, index=False)
            print(f"[INFO][PR64] Exported daily distribution CSV: {daily_path}")

    except Exception as e:
        print(f"[WARNING][PR64] Failed to export transitions CSV: {e}")


def main() -> int:
    """
    Main execution.

    Returns 0 (warning-only, never fails).
    """
    args = parse_args()

    print("=" * 60)
    print("PR64: Interpretation Analytics Generator")
    print("=" * 60)
    print(f"Input file: {args.in_file}")
    print(f"Output directory: {args.out_dir}")
    print(f"Format: {args.format}")
    print("=" * 60)

    # Load interpretation records
    print("[INFO][PR64] Loading interpretation records...")
    records = load_interpretation_records(args.in_file)

    if len(records) == 0:
        print("[WARNING][PR64] No records loaded. Generating empty analytics.")

    # Aggregate meaning distribution
    print("[INFO][PR64] Aggregating meaning distribution...")
    distribution = aggregate_meaning_distribution(records)

    print(f"  Total records: {distribution['total_records']}")
    print(f"  Meaning tags: {len(distribution['meaning_tag_counts'])} types")
    print(f"  Factors: {len(distribution['factor_counts'])} types")
    print(f"  Signals: {len(distribution['signal_counts'])} types")

    # Aggregate meaning transitions
    print("[INFO][PR64] Aggregating meaning transitions...")
    transitions = aggregate_meaning_transitions(records)

    print(f"  Days observed: {transitions['days_observed']}")
    print(f"  Transitions observed: {len(transitions['transitions'])}")

    # Generate summary
    summary = generate_summary_json(distribution, transitions)

    # Create output directory
    Path(args.out_dir).mkdir(parents=True, exist_ok=True)

    # Export outputs
    if args.format in ["json", "both"]:
        json_path = os.path.join(args.out_dir, "pr64_interpretation_analytics.json")
        export_json(summary, json_path)

    if args.format in ["csv", "both"]:
        export_csv_distribution(distribution, args.out_dir)
        export_csv_transitions(transitions, args.out_dir)

    print("=" * 60)
    print("PR64: Interpretation analytics generation complete")
    print("=" * 60)
    print("Analytics provide observational visibility only.")
    print("No evaluations, judgments, or recommendations made.")
    print("=" * 60)
    print("Exit code: 0 (warning-only, never fails)")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
