#!/usr/bin/env python3
"""
PR137: v1.2 Rescue Flow Graph Engine v1 Smoke Tests

Purpose:
    Validate rescue flow graph construction and guards.

Tests:
    1. Import works
    2. Empty inputs → AVAILABLE + nodes present + edges present
    3. Edges contain only role labels (no tokens)
    4. No numeric patterns in output
    5. Amplify edges (if any) are labeled RESCUE_NONE
    6. Leak edges (if any) are labeled RESCUE_NONE
    7. REGIME_MEDIUM produces at least one RESCUE_MEDIUM on SHIELD edges
    8. RESCUE_STRONG record matching medium+shield+stability/hedge reflects STRONG
    9. Coupling guard triggers on "therefore execute" text
    10. Warning-only behavior
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_1_import_works():
    """Test 1: Import works."""
    print("Test 1: Import works")
    try:
        from flow import (
            V12RescueFlowGraphSchema,
            get_flow_schema_info,
            build_rescue_flow_graph_v1,
            get_rescue_flow_graph_engine_v1_info,
            check_flow_graph_record,
            check_flow_coupling,
            FLOW_MODE_ON,
            FLOW_MODE_OFF,
            FLOW_STATUS_AVAILABLE,
            FLOW_STATUS_ERROR,
            FLOW_GRAPH_TYPE_RESCUE,
        )
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_2_empty_inputs_available():
    """Test 2: Empty inputs → AVAILABLE + nodes present + edges present."""
    print("\nTest 2: Empty inputs → AVAILABLE + nodes present + edges present")
    try:
        from flow import build_rescue_flow_graph_v1, FLOW_STATUS_AVAILABLE

        # Build with no inputs (defensive)
        result = build_rescue_flow_graph_v1()

        assert result["v12_flow_status"] == FLOW_STATUS_AVAILABLE, "Expected AVAILABLE status"
        assert len(result["v12_flow_nodes"]) > 0, "Expected nodes present"
        assert len(result["v12_flow_edges"]) > 0, "Expected edges present"
        print(f"  ✓ Empty inputs → AVAILABLE with {len(result['v12_flow_nodes'])} nodes and {len(result['v12_flow_edges'])} edges")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_3_edges_contain_only_role_labels():
    """Test 3: Edges contain only role labels (no tokens)."""
    print("\nTest 3: Edges contain only role labels (no tokens)")
    try:
        from flow import build_rescue_flow_graph_v1

        result = build_rescue_flow_graph_v1()

        # Check that edges only contain ROLE labels (not token literals)
        forbidden_tokens = ["SUI", "USDC", "BTC", "ETH", "DEEP", "CETUS"]

        for edge in result["v12_flow_edges"]:
            from_role = edge["from_role"]
            to_role = edge["to_role"]

            # Check from_role and to_role are valid role labels
            assert "_ROLE" in from_role, f"from_role should be a ROLE label: {from_role}"
            assert "_ROLE" in to_role, f"to_role should be a ROLE label: {to_role}"

            # Check no token literals
            for token in forbidden_tokens:
                assert token not in from_role, f"Token literal {token} found in from_role"
                assert token not in to_role, f"Token literal {token} found in to_role"

        print(f"  ✓ All {len(result['v12_flow_edges'])} edges contain only ROLE labels")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_4_no_numeric_patterns():
    """Test 4: No numeric patterns in output."""
    print("\nTest 4: No numeric patterns in output")
    try:
        from flow import build_rescue_flow_graph_v1
        import re

        result = build_rescue_flow_graph_v1(
            regime_record={"v11_regime_level": "REGIME_MEDIUM"},
        )

        # Check summary for numeric patterns
        summary = result["v12_flow_summary"]
        numeric_pattern = re.compile(r'\\d')

        assert not numeric_pattern.search(summary), "Numeric patterns found in summary"
        print(f"  ✓ No numeric patterns in flow graph output")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_5_amplify_edges_rescue_none():
    """Test 5: Amplify edges (if any) are labeled RESCUE_NONE."""
    print("\nTest 5: Amplify edges (if any) are labeled RESCUE_NONE")
    try:
        from flow import build_rescue_flow_graph_v1

        result = build_rescue_flow_graph_v1()

        # Check that any EDGE_AMPLIFY edges have RESCUE_NONE
        amplify_edges = [e for e in result["v12_flow_edges"] if e["edge_type"] == "EDGE_AMPLIFY"]

        if amplify_edges:
            for edge in amplify_edges:
                assert edge["rescue_strength"] == "RESCUE_NONE", "EDGE_AMPLIFY must have RESCUE_NONE"
            print(f"  ✓ All {len(amplify_edges)} AMPLIFY edges have RESCUE_NONE")
        else:
            print(f"  ✓ No AMPLIFY edges in canonical map (expected)")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_6_leak_edges_rescue_none():
    """Test 6: Leak edges (if any) are labeled RESCUE_NONE."""
    print("\nTest 6: Leak edges (if any) are labeled RESCUE_NONE")
    try:
        from flow import build_rescue_flow_graph_v1

        result = build_rescue_flow_graph_v1()

        # Check that any EDGE_LEAK edges have RESCUE_NONE
        leak_edges = [e for e in result["v12_flow_edges"] if e["edge_type"] == "EDGE_LEAK"]

        if leak_edges:
            for edge in leak_edges:
                assert edge["rescue_strength"] == "RESCUE_NONE", "EDGE_LEAK must have RESCUE_NONE"
            print(f"  ✓ All {len(leak_edges)} LEAK edges have RESCUE_NONE")
        else:
            print(f"  ✓ No LEAK edges in canonical map (expected)")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_7_regime_medium_produces_rescue_medium():
    """Test 7: REGIME_MEDIUM produces at least one RESCUE_MEDIUM on SHIELD edges."""
    print("\nTest 7: REGIME_MEDIUM produces at least one RESCUE_MEDIUM on SHIELD edges")
    try:
        from flow import build_rescue_flow_graph_v1

        result = build_rescue_flow_graph_v1(
            regime_record={"v11_regime_level": "REGIME_MEDIUM"},
            distortion_catalog_record={"v12_distortion_type": "D1_LIQUIDATION"},
        )

        # Check for at least one SHIELD edge with RESCUE_MEDIUM
        shield_medium_edges = [e for e in result["v12_flow_edges"]
                                if e["edge_type"] == "EDGE_SHIELD" and e["rescue_strength"] == "RESCUE_MEDIUM"]

        assert len(shield_medium_edges) > 0, "Expected at least one SHIELD edge with RESCUE_MEDIUM"
        print(f"  ✓ REGIME_MEDIUM produces {len(shield_medium_edges)} SHIELD edges with RESCUE_MEDIUM")
        print(f"    Example: {shield_medium_edges[0]['from_role']} -> {shield_medium_edges[0]['to_role']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_8_rescue_strong_from_records():
    """Test 8: RESCUE_STRONG record matching medium+shield+stability/hedge reflects STRONG."""
    print("\nTest 8: RESCUE_STRONG record matching medium+shield+stability/hedge reflects STRONG")
    try:
        from flow import build_rescue_flow_graph_v1

        # Provide a RESCUE_STRONG record for STABILITY_ROLE
        rescue_strength_records = [
            {
                "v12_rescue_strength": "RESCUE_STRONG",
                "v12_rescue_role": "STABILITY_ROLE",
                "v12_rescue_regime": "REGIME_MEDIUM",
                "v12_rescue_edge_type": "EDGE_SHIELD",
            }
        ]

        result = build_rescue_flow_graph_v1(
            regime_record={"v11_regime_level": "REGIME_MEDIUM"},
            rescue_strength_records=rescue_strength_records,
        )

        # Check for SHIELD edges from STABILITY_ROLE with RESCUE_STRONG
        strong_edges = [e for e in result["v12_flow_edges"]
                        if e["from_role"] == "STABILITY_ROLE"
                        and e["edge_type"] == "EDGE_SHIELD"
                        and e["rescue_strength"] == "RESCUE_STRONG"]

        assert len(strong_edges) > 0, "Expected at least one STRONG edge from STABILITY_ROLE"
        print(f"  ✓ RESCUE_STRONG record produces {len(strong_edges)} STRONG edges")
        print(f"    Example: {strong_edges[0]['from_role']} -> {strong_edges[0]['to_role']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_9_coupling_guard_triggers():
    """Test 9: Coupling guard triggers on "therefore execute" text."""
    print("\nTest 9: Coupling guard triggers on 'therefore execute' text")
    try:
        from flow import check_flow_graph_record

        # Test 9a: Flow coupling (edge therefore execute)
        dirty_coupling = {
            "v12_flow_summary": "This edge therefore execute trade.",
        }
        coupling_warnings = check_flow_graph_record(dirty_coupling)
        assert len(coupling_warnings) > 0, "Expected warnings for flow coupling"
        print(f"  ✓ Flow coupling detected: {len(coupling_warnings)} warnings")

        # Test 9b: Strong rescue means proceed
        dirty_means = {
            "v12_flow_summary": "Strong rescue means proceed with swap.",
        }
        means_warnings = check_flow_graph_record(dirty_means)
        assert len(means_warnings) > 0, "Expected warnings for flow coupling"
        print(f"  ✓ Flow coupling (means proceed) detected: {len(means_warnings)} warnings")

        # Test 9c: Clean record (no coupling)
        clean_record = {
            "v12_flow_summary": "Rescue flow graph available. Role nodes and rescue edges assembled as structural mapping.",
        }
        clean_warnings = check_flow_graph_record(clean_record)
        assert len(clean_warnings) == 0, f"Expected no warnings for clean record, got: {clean_warnings}"
        print(f"  ✓ Clean record passes: no warnings")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_10_warning_only_behavior():
    """Test 10: Warning-only behavior."""
    print("\nTest 10: Warning-only behavior")
    try:
        from flow import check_flow_graph_record

        # Guards should warn, not fail
        # Test with multiple violations (token literals, numeric patterns, coupling)
        dirty_record = {
            "v12_flow_summary": "Flow graph with SUI tokens yielding 30% improvement therefore execute trade.",
        }
        warnings = check_flow_graph_record(dirty_record)

        # Should have warnings for:
        # - Token literals (SUI)
        # - Numeric patterns (30%)
        # - Flow coupling (therefore execute trade)
        assert len(warnings) > 0, "Expected warnings for violations"
        print(f"  ✓ Guards emit warnings (not errors): {len(warnings)} warnings")
        print(f"    Example warnings:")
        for w in warnings[:3]:
            print(f"      - {w}")

        # Function should return warnings list, not raise exception
        print(f"  ✓ Warning-only behavior verified (no exceptions raised)")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def run_all_tests():
    """Run all smoke tests."""
    print("=" * 70)
    print("PR137: v1.2 Rescue Flow Graph Engine v1 - Smoke Tests")
    print("=" * 70)

    tests = [
        test_1_import_works,
        test_2_empty_inputs_available,
        test_3_edges_contain_only_role_labels,
        test_4_no_numeric_patterns,
        test_5_amplify_edges_rescue_none,
        test_6_leak_edges_rescue_none,
        test_7_regime_medium_produces_rescue_medium,
        test_8_rescue_strong_from_records,
        test_9_coupling_guard_triggers,
        test_10_warning_only_behavior,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test {test.__name__} crashed: {e}")
            results.append(False)

    print("\n" + "=" * 70)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 70)

    if all(results):
        print("\n✓ ALL TESTS PASSED")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
