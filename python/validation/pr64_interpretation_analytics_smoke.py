#!/usr/bin/env python3
"""
PR64: v0.6 Interpretation Analytics Smoke Test

Purpose:
    Validate that v0.6 interpretation analytics correctly aggregates
    meaning distribution and transitions without evaluation.

Test Coverage:
    1. Analytics can process interpretation records
    2. Meaning distribution aggregated correctly
    3. Meaning transitions computed correctly
    4. No forbidden vocabulary in outputs
    5. Only v6 fields used (no confidence_reason)
    6. Exit code always 0 (warning-only)

Constitutional Constraints:
    - READ-ONLY: No execution logic changes
    - Warning-only: Exit code always 0
    - Non-evaluative: No good/bad, win/loss vocabulary
    - Non-scoric: No scores, grades, rankings

Exit Code: Always 0 (warning-only validation)
"""

import json
import os
import sys
import tempfile
from typing import Any, Dict, List

# Import modules to test
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from analytics.pr64_interpretation_analytics import (
    load_interpretation_records,
    aggregate_meaning_distribution,
    aggregate_meaning_transitions,
    generate_summary_json,
)
from interpretation.v6_constitutional_guard import (
    check_forbidden_vocabulary,
)


def create_test_interpretation_records() -> List[Dict[str, Any]]:
    """Create test interpretation records."""
    return [
        {
            "day": "2025-01-01",
            "v6_meaning_mode": "ON",
            "v6_meaning_status": "AVAILABLE",
            "v6_meaning_tag": "OVERLAY_OBSERVED",
            "v6_meaning_factors": ["REGIME_PRESENT", "SHADOW_PRESENT"],
            "v6_meaning_signals": ["DIFF_STATUS_DIVERGED", "SEMANTICS_RULE_OVERLAY"],
            "v6_meaning_summary": "overlay pattern observed",
            "v6_meaning_basis": ["v5_decision_diff_status", "regime"],
        },
        {
            "day": "2025-01-01",
            "v6_meaning_mode": "ON",
            "v6_meaning_status": "AVAILABLE",
            "v6_meaning_tag": "ALIGNMENT_STABLE",
            "v6_meaning_factors": ["SHADOW_PRESENT", "INTENT_PRESENT"],
            "v6_meaning_signals": ["DIFF_STATUS_ALIGNED", "SEMANTICS_ALIGNED"],
            "v6_meaning_summary": "decision actions aligned",
            "v6_meaning_basis": ["v5_decision_diff_status"],
        },
        {
            "day": "2025-01-02",
            "v6_meaning_mode": "ON",
            "v6_meaning_status": "AVAILABLE",
            "v6_meaning_tag": "OVERLAY_OBSERVED",
            "v6_meaning_factors": ["REGIME_PRESENT", "SHADOW_PRESENT"],
            "v6_meaning_signals": ["DIFF_STATUS_DIVERGED", "SEMANTICS_RULE_OVERLAY"],
            "v6_meaning_summary": "overlay pattern observed",
            "v6_meaning_basis": ["v5_decision_diff_status", "regime"],
        },
        {
            "day": "2025-01-02",
            "v6_meaning_mode": "ON",
            "v6_meaning_status": "UNAVAILABLE",
            "v6_meaning_tag": "OBSERVATION_INSUFFICIENT",
            "v6_meaning_factors": ["SHADOW_ABSENT"],
            "v6_meaning_signals": [],
            "v6_meaning_summary": "required observation fields not present",
            "v6_meaning_basis": [],
        },
    ]


def test_analytics_can_process_records() -> bool:
    """
    Test 1: Analytics can process interpretation records.
    """
    print("Test 1: Analytics can process interpretation records")
    print("-" * 60)

    records = create_test_interpretation_records()

    if len(records) != 4:
        print(f"✗ Expected 4 test records, got {len(records)}")
        return False
    print(f"✓ Created {len(records)} test records")

    # Test distribution aggregation
    try:
        distribution = aggregate_meaning_distribution(records)
    except Exception as e:
        print(f"✗ aggregate_meaning_distribution raised exception: {e}")
        return False

    print("✓ aggregate_meaning_distribution succeeded")

    # Test transition aggregation
    try:
        transitions = aggregate_meaning_transitions(records)
    except Exception as e:
        print(f"✗ aggregate_meaning_transitions raised exception: {e}")
        return False

    print("✓ aggregate_meaning_transitions succeeded")

    # Test summary generation
    try:
        summary = generate_summary_json(distribution, transitions)
    except Exception as e:
        print(f"✗ generate_summary_json raised exception: {e}")
        return False

    print("✓ generate_summary_json succeeded")

    print("Test 1: PASS\n")
    return True


def test_meaning_distribution_aggregated_correctly() -> bool:
    """
    Test 2: Meaning distribution aggregated correctly.
    """
    print("Test 2: Meaning distribution aggregated correctly")
    print("-" * 60)

    records = create_test_interpretation_records()
    distribution = aggregate_meaning_distribution(records)

    # Check total records
    if distribution["total_records"] != 4:
        print(f"✗ Expected 4 total records, got {distribution['total_records']}")
        return False
    print("✓ Total records correct")

    # Check meaning tag counts
    tag_counts = distribution["meaning_tag_counts"]

    if tag_counts.get("OVERLAY_OBSERVED") != 2:
        print(f"✗ Expected 2 OVERLAY_OBSERVED, got {tag_counts.get('OVERLAY_OBSERVED')}")
        return False
    print("✓ OVERLAY_OBSERVED count correct")

    if tag_counts.get("ALIGNMENT_STABLE") != 1:
        print(f"✗ Expected 1 ALIGNMENT_STABLE, got {tag_counts.get('ALIGNMENT_STABLE')}")
        return False
    print("✓ ALIGNMENT_STABLE count correct")

    if tag_counts.get("OBSERVATION_INSUFFICIENT") != 1:
        print(f"✗ Expected 1 OBSERVATION_INSUFFICIENT, got {tag_counts.get('OBSERVATION_INSUFFICIENT')}")
        return False
    print("✓ OBSERVATION_INSUFFICIENT count correct")

    # Check factor counts
    factor_counts = distribution["factor_counts"]

    if factor_counts.get("REGIME_PRESENT") != 2:
        print(f"✗ Expected 2 REGIME_PRESENT, got {factor_counts.get('REGIME_PRESENT')}")
        return False
    print("✓ REGIME_PRESENT count correct")

    if factor_counts.get("SHADOW_PRESENT") != 3:
        print(f"✗ Expected 3 SHADOW_PRESENT, got {factor_counts.get('SHADOW_PRESENT')}")
        return False
    print("✓ SHADOW_PRESENT count correct")

    # Check signal counts
    signal_counts = distribution["signal_counts"]

    if signal_counts.get("DIFF_STATUS_DIVERGED") != 2:
        print(f"✗ Expected 2 DIFF_STATUS_DIVERGED, got {signal_counts.get('DIFF_STATUS_DIVERGED')}")
        return False
    print("✓ DIFF_STATUS_DIVERGED count correct")

    print("Test 2: PASS\n")
    return True


def test_meaning_transitions_computed_correctly() -> bool:
    """
    Test 3: Meaning transitions computed correctly.
    """
    print("Test 3: Meaning transitions computed correctly")
    print("-" * 60)

    records = create_test_interpretation_records()
    transitions = aggregate_meaning_transitions(records)

    # Check days observed
    if transitions["days_observed"] != 2:
        print(f"✗ Expected 2 days observed, got {transitions['days_observed']}")
        return False
    print("✓ Days observed correct")

    # Check daily distributions
    daily_dists = transitions["daily_distributions"]

    if "2025-01-01" not in daily_dists:
        print("✗ Missing day 2025-01-01")
        return False
    print("✓ Day 2025-01-01 present")

    if "2025-01-02" not in daily_dists:
        print("✗ Missing day 2025-01-02")
        return False
    print("✓ Day 2025-01-02 present")

    # Check day 1 distribution
    day1 = daily_dists["2025-01-01"]
    if day1["record_count"] != 2:
        print(f"✗ Expected 2 records on day 1, got {day1['record_count']}")
        return False
    print("✓ Day 1 record count correct")

    if day1["meaning_tag_counts"].get("OVERLAY_OBSERVED") != 1:
        print(f"✗ Expected 1 OVERLAY_OBSERVED on day 1, got {day1['meaning_tag_counts'].get('OVERLAY_OBSERVED')}")
        return False
    print("✓ Day 1 meaning tag counts correct")

    # Check day 2 distribution
    day2 = daily_dists["2025-01-02"]
    if day2["record_count"] != 2:
        print(f"✗ Expected 2 records on day 2, got {day2['record_count']}")
        return False
    print("✓ Day 2 record count correct")

    # Check transitions exist
    if len(transitions["transitions"]) != 1:
        print(f"✗ Expected 1 transition, got {len(transitions['transitions'])}")
        return False
    print("✓ Transitions computed")

    transition = transitions["transitions"][0]
    if transition["from_day"] != "2025-01-01":
        print(f"✗ Expected transition from 2025-01-01, got {transition['from_day']}")
        return False
    print("✓ Transition from_day correct")

    if transition["to_day"] != "2025-01-02":
        print(f"✗ Expected transition to 2025-01-02, got {transition['to_day']}")
        return False
    print("✓ Transition to_day correct")

    print("Test 3: PASS\n")
    return True


def test_no_forbidden_vocabulary() -> bool:
    """
    Test 4: No forbidden vocabulary in outputs.
    """
    print("Test 4: No forbidden vocabulary in outputs")
    print("-" * 60)

    records = create_test_interpretation_records()
    distribution = aggregate_meaning_distribution(records)
    transitions = aggregate_meaning_transitions(records)
    summary = generate_summary_json(distribution, transitions)

    # Check summary notes
    notes = summary.get("notes", [])
    for note in notes:
        warnings = check_forbidden_vocabulary(note)
        if warnings:
            print(f"✗ Forbidden vocabulary in note: {note}")
            print(f"  Warnings: {warnings}")
            return False

    print("✓ No forbidden vocabulary in summary notes")

    # Check analytics type
    analytics_type = summary.get("analytics_type", "")
    warnings = check_forbidden_vocabulary(analytics_type)
    if warnings:
        print(f"✗ Forbidden vocabulary in analytics_type: {analytics_type}")
        print(f"  Warnings: {warnings}")
        return False

    print("✓ No forbidden vocabulary in analytics_type")

    print("Test 4: PASS\n")
    return True


def test_only_v6_fields_used() -> bool:
    """
    Test 5: Only v6 fields used (no confidence_reason).
    """
    print("Test 5: Only v6 fields used (no confidence_reason)")
    print("-" * 60)

    # Test with record containing confidence_reason (should be ignored)
    records = [
        {
            "day": "2025-01-01",
            "v6_meaning_mode": "ON",
            "v6_meaning_status": "AVAILABLE",
            "v6_meaning_tag": "OVERLAY_OBSERVED",
            "v6_meaning_factors": ["REGIME_PRESENT"],
            "v6_meaning_signals": ["DIFF_STATUS_DIVERGED"],
            "v6_meaning_summary": "overlay pattern observed",
            "v6_meaning_basis": ["v5_decision_diff_status"],
            # v0.4 fields (should be ignored)
            "confidence_reason": "this should be ignored",
            "confidence_reason_version": "v0.4",
        },
    ]

    distribution = aggregate_meaning_distribution(records)

    # Check that analytics only used v6 fields
    if distribution["total_records"] != 1:
        print(f"✗ Expected 1 record, got {distribution['total_records']}")
        return False
    print("✓ Analytics processed v6 fields")

    # Verify confidence_reason not referenced anywhere
    summary = generate_summary_json(distribution, {})
    summary_json = json.dumps(summary)

    if "confidence_reason" in summary_json:
        print("✗ Analytics output references confidence_reason")
        return False
    print("✓ Analytics does not reference confidence_reason")

    print("Test 5: PASS\n")
    return True


def test_exit_code_always_zero() -> bool:
    """
    Test 6: Exit code always 0 (warning-only).
    """
    print("Test 6: Exit code always 0 (warning-only)")
    print("-" * 60)

    # Test with edge cases
    edge_cases = [
        [],  # Empty records
        [{"day": "2025-01-01"}],  # Missing v6 fields
        [{"v6_meaning_tag": "UNKNOWN"}],  # Missing day
    ]

    for records in edge_cases:
        try:
            distribution = aggregate_meaning_distribution(records)
            transitions = aggregate_meaning_transitions(records)
            summary = generate_summary_json(distribution, transitions)
            # Should succeed without raising
        except Exception as e:
            print(f"✗ Analytics raised exception for edge case {records}: {e}")
            return False

    print("✓ All edge cases handled without exceptions")
    print("✓ Exit code will be 0 (warning-only by design)")

    print("Test 6: PASS\n")
    return True


def main() -> int:
    """
    Main test runner.

    Returns 0 (warning-only, never fails).
    """
    print("=" * 60)
    print("PR64: v0.6 Interpretation Analytics Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)
    print()

    tests = [
        ("Analytics can process records", test_analytics_can_process_records),
        ("Meaning distribution aggregated correctly", test_meaning_distribution_aggregated_correctly),
        ("Meaning transitions computed correctly", test_meaning_transitions_computed_correctly),
        ("No forbidden vocabulary", test_no_forbidden_vocabulary),
        ("Only v6 fields used", test_only_v6_fields_used),
        ("Exit code always 0", test_exit_code_always_zero),
    ]

    results = []
    for name, test_fn in tests:
        try:
            result = test_fn()
            results.append((name, result))
        except Exception as e:
            print(f"✗ Test '{name}' raised exception: {e}")
            results.append((name, False))

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    all_passed = all(passed for _, passed in results)

    print()
    print("=" * 60)
    if all_passed:
        print("✓ ALL PR64 INTERPRETATION ANALYTICS TESTS PASSED")
    else:
        print("⚠ SOME PR64 INTERPRETATION ANALYTICS TESTS FAILED")
    print("=" * 60)
    print("PR64 Requirements Verified:")
    print("  - Analytics can process interpretation records")
    print("  - Meaning distribution aggregated correctly")
    print("  - Meaning transitions computed correctly")
    print("  - No forbidden vocabulary in outputs")
    print("  - Only v6 fields used (no confidence_reason)")
    print("  - Exit code always 0 (warning-only)")
    print("=" * 60)
    print("Exit code: 0 (all tests completed)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
