#!/usr/bin/env python3
"""
PR125: v1.1 Human Review Renderer v1 - Smoke Tests

Purpose:
    Validate human review renderer implementation.
    Render = Display Shape (not instruction/conclusion).

Tests:
    1. Import works
    2. Empty/invalid packet → ERROR render
    3. Full packet → AVAILABLE render
    4. Markdown output contains required headings
    5. No forbidden vocabulary in output
    6. Token literal detection triggers
    7. Numeric pattern detection triggers
    8. Warning-only: exit code always 0
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))


def test_render_import():
    """Test 1: Import works"""
    print("Test 1: Import works")
    try:
        from render import (
            V11ReviewRenderSchema,
            render_review_packet_v1,
            check_render_record,
            FORBIDDEN_VOCABULARY,
        )
        print("  ✓ Render imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_empty_packet_error_render():
    """Test 2: Empty/invalid packet → ERROR render"""
    print("\nTest 2: Empty/invalid packet → ERROR render")
    from render import render_review_packet_v1, V11ReviewRenderSchema

    # Test with no packet
    error_render = render_review_packet_v1(None)

    # Validate it's a valid ERROR render
    if error_render.get("v11_render_status") != "ERROR":
        print(f"  ✗ Expected ERROR status, got {error_render.get('v11_render_status')}")
        return False

    # Validate structure
    warnings = V11ReviewRenderSchema.validate_structure(error_render)
    if len(warnings) > 0:
        print(f"  ✗ ERROR render has validation warnings: {warnings}")
        return False

    print("  ✓ Empty packet produces valid ERROR render")
    return True


def test_full_packet_available_render():
    """Test 3: Full packet → AVAILABLE render"""
    print("\nTest 3: Full packet → AVAILABLE render")
    from render import render_review_packet_v1

    # Create full packet
    packet = {
        "v11_packet_status": "AVAILABLE",
        "v11_packet_summary": "test",
        "v11_packet_components": {
            "explain_context": {
                "v11_explain_signals": ["REGIME_MEDIUM", "DRIFT_LOW"],
            },
            "narrative": {
                "v11_narrative_text": "current regime label indicates elevated uncertainty.",
            },
            "preview": {
                "v11_preview_status": "AVAILABLE",
                "v11_preview_risk_surface": "CONSTRAINED",
            },
            "approval_gate": {
                "v11_approval_requirement": "REQUIRED",
                "v11_approval_state": "UNREQUESTED",
            },
        },
        "v11_packet_basis": ["v11_regime_level"],
        "v11_packet_artifacts": ["pr110_regime_record"],
    }

    render = render_review_packet_v1(packet, fmt="MARKDOWN", style="STANDARD")

    # Validate status
    if render.get("v11_render_status") != "AVAILABLE":
        print(f"  ✗ Expected AVAILABLE status, got {render.get('v11_render_status')}")
        return False

    # Validate output exists
    output = render.get("v11_render_output", "")
    if not output or len(output) == 0:
        print("  ✗ Render output is empty")
        return False

    print(f"  ✓ Full packet produces AVAILABLE render")
    print(f"    Output length: {len(output)} chars")
    return True


def test_markdown_contains_headings():
    """Test 4: Markdown output contains required headings"""
    print("\nTest 4: Markdown output contains required headings")
    from render import render_review_packet_v1

    packet = {
        "v11_packet_status": "AVAILABLE",
        "v11_packet_summary": "test",
        "v11_packet_components": {
            "explain_context": {
                "v11_explain_signals": ["REGIME_MEDIUM"],
            },
        },
        "v11_packet_basis": [],
    }

    render = render_review_packet_v1(packet, fmt="MARKDOWN", style="STANDARD")
    output = render.get("v11_render_output", "")

    # Check for required headings
    required_headings = [
        "# Approval Packet (READ-ONLY)",
        "## Labels",
    ]

    missing_headings = []
    for heading in required_headings:
        if heading not in output:
            missing_headings.append(heading)

    if missing_headings:
        print(f"  ✗ Missing headings: {missing_headings}")
        return False

    print("  ✓ Markdown contains required headings")
    return True


def test_no_forbidden_vocabulary():
    """Test 5: No forbidden vocabulary in output"""
    print("\nTest 5: No forbidden vocabulary in output")
    from render import render_review_packet_v1, FORBIDDEN_VOCABULARY

    packet = {
        "v11_packet_status": "AVAILABLE",
        "v11_packet_summary": "test",
        "v11_packet_components": {
            "explain_context": {
                "v11_explain_signals": ["REGIME_HIGH"],
            },
        },
        "v11_packet_basis": [],
    }

    render = render_review_packet_v1(packet, fmt="MARKDOWN", style="STANDARD")
    output = render.get("v11_render_output", "").lower()

    # Check for forbidden words
    found_forbidden = []
    for word in FORBIDDEN_VOCABULARY:
        if word.lower() in output:
            found_forbidden.append(word)

    if found_forbidden:
        print(f"  ✗ Forbidden vocabulary found: {found_forbidden}")
        return False

    print("  ✓ Output contains only allowed vocabulary")
    return True


def test_token_literal_detection():
    """Test 6: Token literal detection triggers"""
    print("\nTest 6: Token literal detection triggers")
    from render import check_render_record

    # Dirty render with token literals
    dirty_render = {
        "v11_render_output": "# Approval Packet\n\nSUI and USDC detected.",
    }

    warnings = check_render_record(dirty_render)

    if len(warnings) == 0:
        print("  ✗ Guards did not detect token literals")
        return False

    print(f"  ✓ Guards detected token literals: {len(warnings)} warnings")
    return True


def test_numeric_pattern_detection():
    """Test 7: Numeric pattern detection triggers"""
    print("\nTest 7: Numeric pattern detection triggers")
    from render import check_render_record

    # Dirty render with numeric patterns
    dirty_render = {
        "v11_render_output": "# Approval Packet\n\nDetected 5 terms added.",
    }

    warnings = check_render_record(dirty_render)

    if len(warnings) == 0:
        print("  ✗ Guards did not detect numeric patterns")
        return False

    print(f"  ✓ Guards detected numeric patterns: {len(warnings)} warnings")
    return True


def test_warning_only_behavior():
    """Test 8: Warning-only: exit code always 0"""
    print("\nTest 8: Exit code always 0 (warning-only)")
    from render import V11ReviewRenderSchema, check_render_record

    # Test various error conditions - none should raise
    test_cases = [
        {},  # Empty dict
        {"invalid": "record"},  # Invalid structure
        {"v11_render_mode": "INVALID"},  # Invalid mode
    ]

    for i, test_case in enumerate(test_cases):
        try:
            # Validation should not raise - just return warnings
            warnings = V11ReviewRenderSchema.validate_structure(test_case)
            print(f"  ✓ Test case {i+1}: No exception raised, {len(warnings)} warnings returned")
        except Exception as e:
            print(f"  ✗ Test case {i+1}: Exception raised: {e}")
            return False

    # Test check_render_record doesn't raise
    try:
        warnings = check_render_record({"v11_render_output": "invalid text with SUI token"})
        print(f"  ✓ check_render_record: No exception raised, {len(warnings)} warnings returned")
    except Exception as e:
        print(f"  ✗ check_render_record raised exception: {e}")
        return False

    print("  ✓ All error cases handled defensively (warning-only)")
    return True


def main():
    """Run all smoke tests"""
    print("=" * 60)
    print("PR125: v1.1 Human Review Renderer v1")
    print("Smoke Tests")
    print("=" * 60)
    print()

    tests = [
        test_render_import,
        test_empty_packet_error_render,
        test_full_packet_available_render,
        test_markdown_contains_headings,
        test_no_forbidden_vocabulary,
        test_token_literal_detection,
        test_numeric_pattern_detection,
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
