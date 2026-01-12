#!/usr/bin/env python3
"""
PR124: v1.1 Approval Packet Builder v1 - Smoke Tests

Purpose:
    Validate approval packet builder implementation.
    Packet = Review Unit Carrier (not decision/instruction).

Tests:
    1. Import works
    2. Empty inputs → valid ERROR/UNAVAILABLE packet
    3. Full inputs → AVAILABLE packet
    4. Missing narrative still builds packet
    5. Summary contains no prescriptive language
    6. Token literal detection triggers
    7. Numeric pattern detection triggers
    8. Trading verb detection triggers
    9. Coupling guard triggers ("approved therefore execute")
    10. Warning-only: exit code always 0
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))


def test_packet_import():
    """Test 1: Import works"""
    print("Test 1: Import works")
    try:
        from packet import (
            V11ApprovalPacketSchema,
            build_approval_packet_v1,
            check_packet_record,
            FORBIDDEN_VOCABULARY,
        )
        print("  ✓ Packet imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_empty_inputs_error_packet():
    """Test 2: Empty inputs → valid ERROR/UNAVAILABLE packet"""
    print("\nTest 2: Empty inputs → valid ERROR/UNAVAILABLE packet")
    from packet import build_approval_packet_v1, V11ApprovalPacketSchema

    # Test with no components
    error_packet = build_approval_packet_v1()

    # Validate it's a valid ERROR packet
    if error_packet.get("v11_packet_status") != "ERROR":
        print(f"  ✗ Expected ERROR status, got {error_packet.get('v11_packet_status')}")
        return False

    # Validate structure
    warnings = V11ApprovalPacketSchema.validate_structure(error_packet)
    if len(warnings) > 0:
        print(f"  ✗ ERROR packet has validation warnings: {warnings}")
        return False

    print("  ✓ Empty inputs produce valid ERROR packet")
    return True


def test_full_inputs_available_packet():
    """Test 3: Full inputs → AVAILABLE packet"""
    print("\nTest 3: Full inputs → AVAILABLE packet")
    from packet import build_approval_packet_v1

    # Create full component set
    explain_context = {
        "v11_explain_mode": "ON",
        "v11_explain_status": "AVAILABLE",
        "v11_explain_signals": ["REGIME_MEDIUM", "DRIFT_LOW"],
        "v11_explain_basis": ["v11_regime_level", "v10_drift_level"],
        "v11_explain_artifacts": ["pr110_regime_record", "pr120_drift_record"],
    }

    narrative = {
        "v11_narrative_mode": "ON",
        "v11_narrative_status": "AVAILABLE",
        "v11_narrative_style": "STANDARD",
        "v11_narrative_text": "current regime label indicates elevated uncertainty.",
        "v11_narrative_basis": ["v11_regime_level"],
        "v11_narrative_artifacts": ["pr110_regime_record"],
    }

    preview = {
        "v11_preview_mode": "ON",
        "v11_preview_status": "AVAILABLE",
        "v11_preview_risk_surface": "CONSTRAINED",
        "v11_preview_basis": ["v10_execution_permission"],
        "v11_preview_artifacts": ["pr101_execution_record"],
    }

    approval_gate = {
        "v11_approval_mode": "ON",
        "v11_approval_status": "AVAILABLE",
        "v11_approval_requirement": "REQUIRED",
        "v11_approval_state": "UNREQUESTED",
        "v11_approval_basis": ["v11_regime_level"],
        "v11_approval_artifacts": ["pr110_regime_record"],
    }

    # Build packet
    packet = build_approval_packet_v1(
        explain_context_record=explain_context,
        narrative_record=narrative,
        preview_record=preview,
        approval_gate_record=approval_gate,
    )

    # Validate status
    if packet.get("v11_packet_status") != "AVAILABLE":
        print(f"  ✗ Expected AVAILABLE status, got {packet.get('v11_packet_status')}")
        return False

    # Validate packet_type
    if packet.get("v11_packet_packet_type") != "APPROVAL_PACKET":
        print(f"  ✗ Expected APPROVAL_PACKET type, got {packet.get('v11_packet_packet_type')}")
        return False

    # Validate components present
    components = packet.get("v11_packet_components", {})
    expected_components = ["explain_context", "narrative", "preview", "approval_gate"]
    for component in expected_components:
        if component not in components:
            print(f"  ✗ Missing component: {component}")
            return False

    print(f"  ✓ Full inputs produce AVAILABLE packet")
    print(f"    Summary: {packet.get('v11_packet_summary')}")
    return True


def test_missing_narrative_still_builds():
    """Test 4: Missing narrative still builds packet"""
    print("\nTest 4: Missing narrative still builds packet")
    from packet import build_approval_packet_v1

    # Only provide explain_context
    explain_context = {
        "v11_explain_mode": "ON",
        "v11_explain_status": "AVAILABLE",
        "v11_explain_signals": ["REGIME_MEDIUM"],
        "v11_explain_basis": ["v11_regime_level"],
    }

    packet = build_approval_packet_v1(explain_context_record=explain_context)

    # Should still be AVAILABLE (not ERROR)
    if packet.get("v11_packet_status") != "AVAILABLE":
        print(f"  ✗ Expected AVAILABLE status, got {packet.get('v11_packet_status')}")
        return False

    # Should have explain_context but not narrative
    components = packet.get("v11_packet_components", {})
    if "explain_context" not in components:
        print("  ✗ Missing explain_context component")
        return False

    if "narrative" in components:
        print("  ✗ Unexpected narrative component (should be absent)")
        return False

    print("  ✓ Missing narrative still produces valid packet")
    return True


def test_summary_no_prescriptive_language():
    """Test 5: Summary contains no prescriptive language"""
    print("\nTest 5: Summary contains no prescriptive language")
    from packet import build_approval_packet_v1, FORBIDDEN_VOCABULARY

    narrative = {
        "v11_narrative_mode": "ON",
        "v11_narrative_status": "AVAILABLE",
        "v11_narrative_style": "STANDARD",
        "v11_narrative_text": "test",
        "v11_narrative_basis": [],
    }

    packet = build_approval_packet_v1(narrative_record=narrative)
    summary = packet.get("v11_packet_summary", "").lower()

    # Check for forbidden words
    found_forbidden = []
    for word in FORBIDDEN_VOCABULARY:
        if word.lower() in summary:
            found_forbidden.append(word)

    if found_forbidden:
        print(f"  ✗ Forbidden vocabulary found in summary: {found_forbidden}")
        return False

    print("  ✓ Summary contains only allowed vocabulary")
    return True


def test_token_literal_detection():
    """Test 6: Token literal detection triggers"""
    print("\nTest 6: Token literal detection triggers")
    from packet import check_packet_record

    # Dirty packet with token literals
    dirty_packet = {
        "v11_packet_summary": "packet assembled with SUI and USDC details.",
    }

    warnings = check_packet_record(dirty_packet)

    if len(warnings) == 0:
        print("  ✗ Guards did not detect token literals")
        return False

    print(f"  ✓ Guards detected token literals: {len(warnings)} warnings")
    return True


def test_numeric_pattern_detection():
    """Test 7: Numeric pattern detection triggers"""
    print("\nTest 7: Numeric pattern detection triggers")
    from packet import check_packet_record

    # Dirty packet with numeric patterns
    dirty_packet = {
        "v11_packet_summary": "packet assembled with 5 terms added and 3 removed.",
    }

    warnings = check_packet_record(dirty_packet)

    if len(warnings) == 0:
        print("  ✗ Guards did not detect numeric patterns")
        return False

    print(f"  ✓ Guards detected numeric patterns: {len(warnings)} warnings")
    return True


def test_trading_verb_detection():
    """Test 8: Trading verb detection triggers"""
    print("\nTest 8: Trading verb detection triggers")
    from packet import check_packet_record

    # Dirty packet with trading vocabulary
    dirty_packet = {
        "v11_packet_summary": "approved. execute swap now.",
    }

    warnings = check_packet_record(dirty_packet)

    if len(warnings) == 0:
        print("  ✗ Guards did not detect trading verbs")
        return False

    print(f"  ✓ Guards detected trading verbs: {len(warnings)} warnings")
    return True


def test_coupling_guard_triggers():
    """Test 9: Coupling guard triggers ("approved therefore execute")"""
    print("\nTest 9: Coupling guard triggers")
    from packet import check_packet_record

    # Dirty packet with coupling patterns
    dirty_packet = {
        "v11_packet_summary": "approval requirement REQUIRED therefore execute operation.",
    }

    warnings = check_packet_record(dirty_packet)

    if len(warnings) == 0:
        print("  ✗ Guards did not detect coupling")
        return False

    print(f"  ✓ Guards detected coupling: {len(warnings)} warnings")
    return True


def test_warning_only_behavior():
    """Test 10: Warning-only: exit code always 0"""
    print("\nTest 10: Exit code always 0 (warning-only)")
    from packet import V11ApprovalPacketSchema, check_packet_record

    # Test various error conditions - none should raise
    test_cases = [
        {},  # Empty dict
        {"invalid": "record"},  # Invalid structure
        {"v11_packet_mode": "INVALID"},  # Invalid mode
    ]

    for i, test_case in enumerate(test_cases):
        try:
            # Validation should not raise - just return warnings
            warnings = V11ApprovalPacketSchema.validate_structure(test_case)
            print(f"  ✓ Test case {i+1}: No exception raised, {len(warnings)} warnings returned")
        except Exception as e:
            print(f"  ✗ Test case {i+1}: Exception raised: {e}")
            return False

    # Test check_packet_record doesn't raise
    try:
        warnings = check_packet_record({"v11_packet_summary": "invalid text with SUI token"})
        print(f"  ✓ check_packet_record: No exception raised, {len(warnings)} warnings returned")
    except Exception as e:
        print(f"  ✗ check_packet_record raised exception: {e}")
        return False

    print("  ✓ All error cases handled defensively (warning-only)")
    return True


def main():
    """Run all smoke tests"""
    print("=" * 60)
    print("PR124: v1.1 Approval Packet Builder v1")
    print("Smoke Tests")
    print("=" * 60)
    print()

    tests = [
        test_packet_import,
        test_empty_inputs_error_packet,
        test_full_inputs_available_packet,
        test_missing_narrative_still_builds,
        test_summary_no_prescriptive_language,
        test_token_literal_detection,
        test_numeric_pattern_detection,
        test_trading_verb_detection,
        test_coupling_guard_triggers,
        test_warning_only_behavior,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ✗ Test failed with exception: {e}")
            results.append(False)

    print()
    print("=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)

    # Exit with code 0 even if tests fail (smoke test, not enforcement)
    if all(results):
        print("\n✓ All smoke tests passed")
        sys.exit(0)
    else:
        print("\n✗ Some smoke tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
