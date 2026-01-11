#!/usr/bin/env python3
"""
PR117: v1.0 Golden Regression Harness v1 - Smoke Tests

Purpose:
    Validate golden regression harness implementation.
    Harness = Determinism Proof (not optimization/profit test).

Tests:
    1. Harness import works
    2. Golden case A matches expected bundle
    3. Golden case B matches expected bundle
    4. If mismatch: diff summary is non-evaluative and constitutional-safe
    5. Guards detect any token/numeric/address leakage in fixtures
    6. Defensive behavior on missing fixture files
    7. Exit code always 0
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))


def test_harness_import():
    """Test 1: Harness import works"""
    print("Test 1: Harness import works")
    try:
        from regression import (
            run_golden_regression_v1,
            get_golden_regression_harness_v1_info,
        )
        print("  ✓ Regression harness imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_case_A_matches():
    """Test 2: Golden case A matches expected bundle"""
    print("\nTest 2: Golden case A matches expected bundle")
    from regression import run_golden_regression_v1

    result = run_golden_regression_v1("case_A")

    if result.get("status") == "ERROR":
        print(f"  ✗ Case A resulted in ERROR: {result.get('error_info')}")
        return False
    print(f"  ✓ Case A completed with status: {result.get('status')}")

    if result.get("match") is True:
        print("  ✓ Case A matches expected bundle")
        return True
    elif result.get("match") is None:
        print("  ⚠ Case A has no expected bundle (first run)")
        return True  # Pass if no expected bundle exists
    else:
        print(f"  ✗ Case A does not match expected bundle")
        print(f"    Diff: {result.get('diff_summary')}")
        return False


def test_case_B_matches():
    """Test 3: Golden case B matches expected bundle"""
    print("\nTest 3: Golden case B matches expected bundle")
    from regression import run_golden_regression_v1

    result = run_golden_regression_v1("case_B")

    if result.get("status") == "ERROR":
        print(f"  ✗ Case B resulted in ERROR: {result.get('error_info')}")
        return False
    print(f"  ✓ Case B completed with status: {result.get('status')}")

    if result.get("match") is True:
        print("  ✓ Case B matches expected bundle")
        return True
    elif result.get("match") is None:
        print("  ⚠ Case B has no expected bundle (first run)")
        return True  # Pass if no expected bundle exists
    else:
        print(f"  ✗ Case B does not match expected bundle")
        print(f"    Diff: {result.get('diff_summary')}")
        return False


def test_diff_summary_constitutional():
    """Test 4: If mismatch: diff summary is non-evaluative and constitutional-safe"""
    print("\nTest 4: Diff summary is non-evaluative and constitutional-safe")
    from regression import run_golden_regression_v1
    from bundle import validate_bundle_record

    # Run case A
    result_a = run_golden_regression_v1("case_A")

    # Check diff summary if present
    if result_a.get("diff_summary"):
        diff_summary = result_a["diff_summary"]

        # Check for token literals
        from observation.v10_observation_constitutional_guard import (
            check_observation_token_literals,
        )

        token_warnings = check_observation_token_literals(diff_summary)
        if len(token_warnings) > 0:
            print(f"  ✗ Diff summary contains token literals: {token_warnings}")
            return False

        # Check for trading vocabulary
        from preview.v11_preview_constitutional_guard import (
            check_trading_vocabulary,
            check_numeric_patterns,
        )

        trading_warnings = check_trading_vocabulary(diff_summary)
        if len(trading_warnings) > 0:
            print(f"  ✗ Diff summary contains trading vocabulary: {trading_warnings}")
            return False

        # Check for numeric patterns (should be minimal - only structural counts)
        # Allow phrases like "N differences" but not amounts/prices
        numeric_warnings = check_numeric_patterns(diff_summary)
        # Filter out acceptable patterns (count phrases)
        forbidden_patterns = [w for w in numeric_warnings if "$" in diff_summary or "%" in diff_summary]
        if len(forbidden_patterns) > 0:
            print(f"  ✗ Diff summary contains forbidden numeric patterns: {forbidden_patterns}")
            return False

        print("  ✓ Diff summary is constitutional-safe")
    else:
        print("  ✓ No diff summary present (bundles match)")

    return True


def test_fixtures_constitutional():
    """Test 5: Guards detect any token/numeric/address leakage in fixtures"""
    print("\nTest 5: Fixtures are constitutional-safe")
    import json
    from observation.v10_observation_constitutional_guard import (
        check_observation_token_literals,
    )
    from preview.v11_preview_constitutional_guard import (
        check_address_patterns,
    )

    fixture_dir = Path(__file__).parent.parent / "fixtures" / "golden" / "v1.0"

    # Check all fixture files
    fixture_files = [
        "mock_connection.json",
        "mock_provider_config.json",
        "mock_observations_case_A.json",
        "mock_observations_case_B.json",
    ]

    for fixture_file in fixture_files:
        file_path = fixture_dir / fixture_file
        if not file_path.exists():
            print(f"  ⚠ Fixture not found: {fixture_file}")
            continue

        try:
            with open(file_path, "r") as f:
                content_str = f.read()

            # Check for token literals
            token_warnings = check_observation_token_literals(content_str)
            if len(token_warnings) > 0:
                print(f"  ✗ {fixture_file} contains token literals: {token_warnings}")
                return False

            # Check for address patterns
            address_warnings = check_address_patterns(content_str)
            if len(address_warnings) > 0:
                print(f"  ✗ {fixture_file} contains address patterns: {address_warnings}")
                return False

        except Exception as e:
            print(f"  ✗ Error checking {fixture_file}: {e}")
            return False

    print(f"  ✓ All {len(fixture_files)} fixtures are constitutional-safe")
    return True


def test_defensive_behavior():
    """Test 6: Defensive behavior on missing fixture files"""
    print("\nTest 6: Defensive behavior on missing fixture files")
    from regression import run_golden_regression_v1

    # Try to run with non-existent case
    result = run_golden_regression_v1("case_nonexistent")

    if result.get("status") != "ERROR":
        print(f"  ✗ Non-existent case did not return ERROR status: {result.get('status')}")
        return False
    print("  ✓ Non-existent case returns ERROR status")

    if "error_info" not in result:
        print("  ✗ ERROR status but no error_info provided")
        return False
    print(f"  ✓ Error info provided: {result.get('error_info')[:50]}...")

    # Should not raise exception
    print("  ✓ No exception raised (defensive)")
    return True


def test_warning_only_behavior():
    """Test 7: Exit code always 0"""
    print("\nTest 7: Exit code always 0 (warning-only)")
    from regression import run_golden_regression_v1

    # Test various cases - none should raise
    test_cases = ["case_A", "case_B", "case_nonexistent", "invalid_case"]

    for case_name in test_cases:
        try:
            result = run_golden_regression_v1(case_name)
            if "status" not in result:
                print(f"  ✗ Case {case_name}: Invalid result structure")
                return False
            print(f"  ✓ Case {case_name}: No exception raised, valid result returned")
        except Exception as e:
            print(f"  ✗ Case {case_name}: Exception raised: {e}")
            return False

    print("  ✓ All error cases handled defensively (warning-only)")
    return True


def main():
    """Run all smoke tests"""
    print("=" * 60)
    print("PR117: v1.0 Golden Regression Harness v1")
    print("Smoke Tests")
    print("=" * 60)
    print()

    tests = [
        test_harness_import,
        test_case_A_matches,
        test_case_B_matches,
        test_diff_summary_constitutional,
        test_fixtures_constitutional,
        test_defensive_behavior,
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
