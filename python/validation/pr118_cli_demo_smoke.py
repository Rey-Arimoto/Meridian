#!/usr/bin/env python3
"""
PR118: v1.0 CLI Demo v1 - Smoke Tests

Purpose:
    Validate CLI demo implementation.
    CLI = Display (not instruction/recommendation).

Tests:
    1. CLI import works
    2. Demo case A runs end-to-end (exit 0)
    3. Output digest contains only safe labels (no tokens/numbers/addresses)
    4. Demo case B runs end-to-end
    5. Guard catches forbidden vocab
    6. Defensive behavior on invalid args
    7. Exit code always 0
"""

import sys
import subprocess
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))


def test_cli_import():
    """Test 1: CLI import works"""
    print("Test 1: CLI import works")
    try:
        from cli import (
            render_digest,
            get_digest_renderer_v1_info,
            validate_cli_output,
        )
        print("  ✓ CLI imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_demo_case_A_runs():
    """Test 2: Demo case A runs end-to-end (exit 0)"""
    print("\nTest 2: Demo case A runs end-to-end")
    from cli import render_digest
    from regression import run_golden_regression_v1
    from orchestrator import run_pipeline_v1
    from bundle import build_artifact_bundle_v1
    import json

    try:
        # Load mock observations for case A
        fixture_dir = Path(__file__).parent.parent / "fixtures" / "golden" / "v1.0"
        observations_file = fixture_dir / "mock_observations_case_A.json"

        with open(observations_file, "r") as f:
            mock_observations = json.load(f)

        # Run pipeline
        orchestrator_output = run_pipeline_v1(onchain_analytics=mock_observations)
        bundle = build_artifact_bundle_v1(orchestrator_output)

        # Render digest
        digest = render_digest(bundle, format="text")

        if not digest:
            print("  ✗ Empty digest returned")
            return False

        print("  ✓ Case A pipeline completed")
        print("  ✓ Digest rendered successfully")
        return True

    except Exception as e:
        print(f"  ✗ Case A failed with exception: {e}")
        return False


def test_digest_constitutional():
    """Test 3: Output digest contains only safe labels"""
    print("\nTest 3: Output digest contains only safe labels")
    from cli import render_digest, validate_cli_output
    from regression import run_golden_regression_v1
    from orchestrator import run_pipeline_v1
    from bundle import build_artifact_bundle_v1
    import json

    try:
        # Load mock observations for case A
        fixture_dir = Path(__file__).parent.parent / "fixtures" / "golden" / "v1.0"
        observations_file = fixture_dir / "mock_observations_case_A.json"

        with open(observations_file, "r") as f:
            mock_observations = json.load(f)

        # Run pipeline and render digest
        orchestrator_output = run_pipeline_v1(onchain_analytics=mock_observations)
        bundle = build_artifact_bundle_v1(orchestrator_output)
        digest = render_digest(bundle, format="text")

        # Validate digest
        warnings = validate_cli_output(digest)

        # Filter out acceptable warnings (like layer counts)
        forbidden_warnings = [
            w for w in warnings
            if not any(acceptable in w.lower() for acceptable in [
                "layers present",
                "warnings:",
                "basis:",
            ])
        ]

        if len(forbidden_warnings) > 0:
            print(f"  ✗ Digest contains forbidden content: {len(forbidden_warnings)} warnings")
            for w in forbidden_warnings[:3]:
                print(f"    - {w}")
            return False

        print("  ✓ Digest contains only safe labels")
        return True

    except Exception as e:
        print(f"  ✗ Test failed with exception: {e}")
        return False


def test_demo_case_B_runs():
    """Test 4: Demo case B runs end-to-end"""
    print("\nTest 4: Demo case B runs end-to-end")
    from cli import render_digest
    from regression import run_golden_regression_v1
    from orchestrator import run_pipeline_v1
    from bundle import build_artifact_bundle_v1
    import json

    try:
        # Load mock observations for case B
        fixture_dir = Path(__file__).parent.parent / "fixtures" / "golden" / "v1.0"
        observations_file = fixture_dir / "mock_observations_case_B.json"

        with open(observations_file, "r") as f:
            mock_observations = json.load(f)

        # Run pipeline
        orchestrator_output = run_pipeline_v1(onchain_analytics=mock_observations)
        bundle = build_artifact_bundle_v1(orchestrator_output)

        # Render digest
        digest = render_digest(bundle, format="text")

        if not digest:
            print("  ✗ Empty digest returned")
            return False

        print("  ✓ Case B pipeline completed")
        print("  ✓ Digest rendered successfully")
        return True

    except Exception as e:
        print(f"  ✗ Case B failed with exception: {e}")
        return False


def test_guard_catches_forbidden_vocab():
    """Test 5: Guard catches forbidden vocab"""
    print("\nTest 5: Guard catches forbidden vocab")
    from cli import validate_cli_output

    # Test with trading vocabulary
    dirty_output = """
Bundle Status: AVAILABLE
Regime Level: HIGH

Recommended action: execute swap operations immediately.
Buy tokens now at current price.
"""

    warnings = validate_cli_output(dirty_output)

    if len(warnings) == 0:
        print("  ✗ Guard did not detect forbidden vocabulary")
        return False

    print(f"  ✓ Guard detected forbidden vocabulary: {len(warnings)} warnings")

    # Test with token literals
    dirty_output_token = """
Bundle Status: AVAILABLE
Assets: SUI, USDC, BTC
Balance: 1000 USDC
"""

    token_warnings = validate_cli_output(dirty_output_token)

    if len(token_warnings) == 0:
        print("  ✗ Guard did not detect token literals")
        return False

    print(f"  ✓ Guard detected token literals: {len(token_warnings)} warnings")

    # Test with addresses
    dirty_output_address = """
Bundle Status: AVAILABLE
Wallet: 0x1234567890abcdef
"""

    address_warnings = validate_cli_output(dirty_output_address)

    if len(address_warnings) == 0:
        print("  ✗ Guard did not detect addresses")
        return False

    print(f"  ✓ Guard detected addresses: {len(address_warnings)} warnings")
    return True


def test_defensive_behavior():
    """Test 6: Defensive behavior on invalid args"""
    print("\nTest 6: Defensive behavior on invalid args")
    from cli import render_digest

    # Test with None input
    try:
        digest = render_digest(None)  # type: ignore
        # Should not raise exception
        print("  ✓ None input handled defensively")
    except Exception as e:
        print(f"  ✗ None input raised exception: {e}")
        return False

    # Test with invalid dict
    try:
        digest = render_digest({})
        # Should not raise exception
        print("  ✓ Empty dict handled defensively")
    except Exception as e:
        print(f"  ✗ Empty dict raised exception: {e}")
        return False

    # Test with invalid format
    try:
        mock_bundle = {"v10_bundle_status": "AVAILABLE"}
        digest = render_digest(mock_bundle, format="invalid")
        # Should fallback to text format
        print("  ✓ Invalid format handled defensively")
    except Exception as e:
        print(f"  ✗ Invalid format raised exception: {e}")
        return False

    return True


def test_warning_only_behavior():
    """Test 7: Exit code always 0"""
    print("\nTest 7: Exit code always 0 (warning-only)")
    from cli import render_digest, validate_cli_output

    # Test various error conditions - none should raise
    test_cases = [
        None,
        {},
        {"invalid": "data"},
        {"v10_bundle_status": "ERROR"},
    ]

    for i, test_case in enumerate(test_cases):
        try:
            result = render_digest(test_case, format="text")  # type: ignore
            if result is None:
                print(f"  ✗ Test case {i+1}: None result returned")
                return False
            print(f"  ✓ Test case {i+1}: No exception raised, valid result returned")
        except Exception as e:
            print(f"  ✗ Test case {i+1}: Exception raised: {e}")
            return False

    print("  ✓ All error cases handled defensively (warning-only)")
    return True


def main():
    """Run all smoke tests"""
    print("=" * 60)
    print("PR118: v1.0 CLI Demo v1")
    print("Smoke Tests")
    print("=" * 60)
    print()

    tests = [
        test_cli_import,
        test_demo_case_A_runs,
        test_digest_constitutional,
        test_demo_case_B_runs,
        test_guard_catches_forbidden_vocab,
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
