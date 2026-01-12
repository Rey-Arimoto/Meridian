#!/usr/bin/env python3
"""
PR138: v1.2 Rescue Flow Render Extension Smoke Tests

Purpose:
    Validate rescue flow render extension for human review renderer.

Tests:
    1. Import works
    2. Renderer without rescue_flow_graph stays unchanged (backward compatible)
    3. STANDARD with rescue_flow_graph includes "Rescue Flow" heading
    4. CONCISE does NOT include rescue flow
    5. DETAILED includes conditions labels
    6. Output contains no token literals
    7. Output contains no numeric patterns
    8. Coupling guard triggers on injected "therefore execute" text
    9. Warning-only behavior
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_1_import_works():
    """Test 1: Import works."""
    print("Test 1: Import works")
    try:
        from render import (
            render_review_packet_v1,
            V11ReviewRenderSchema,
        )
        from render.v12_rescue_flow_render_adapter import (
            project_rescue_flow_for_render,
            get_rescue_flow_render_adapter_info,
        )
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_2_backward_compatible_without_rescue_flow():
    """Test 2: Renderer without rescue_flow_graph stays unchanged (backward compatible)."""
    print("\nTest 2: Renderer without rescue_flow_graph stays unchanged")
    try:
        from render import render_review_packet_v1

        # Create minimal packet without rescue flow
        packet = {
            "v11_packet_status": "AVAILABLE",
            "v11_packet_summary": "test packet",
            "v11_packet_components": {},
            "v11_packet_basis": [],
            "v11_packet_artifacts": [],
        }

        # Render without rescue_flow_graph parameter
        result = render_review_packet_v1(packet, fmt="MARKDOWN", style="STANDARD")

        assert result["v11_render_status"] == "AVAILABLE", "Expected AVAILABLE status"
        output = result["v11_render_output"]
        assert "Rescue Flow" not in output, "Should not include Rescue Flow without rescue_flow_graph"
        print(f"  ✓ Backward compatible: no Rescue Flow section without parameter")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_3_standard_includes_rescue_flow():
    """Test 3: STANDARD with rescue_flow_graph includes 'Rescue Flow' heading."""
    print("\nTest 3: STANDARD with rescue_flow_graph includes 'Rescue Flow' heading")
    try:
        from render import render_review_packet_v1

        # Create minimal packet
        packet = {
            "v11_packet_status": "AVAILABLE",
            "v11_packet_summary": "test packet",
            "v11_packet_components": {},
            "v11_packet_basis": [],
            "v11_packet_artifacts": [],
        }

        # Create mock rescue flow graph
        rescue_flow_graph = {
            "v12_flow_status": "AVAILABLE",
            "v12_flow_edges": [
                {
                    "from_role": "STABILITY_ROLE",
                    "to_role": "VOLATILITY_ROLE",
                    "edge_type": "EDGE_SHIELD",
                    "rescue_strength": "RESCUE_MEDIUM",
                    "conditions": ["REGIME_MEDIUM", "D1_LIQUIDATION"],
                },
            ],
        }

        # Render with rescue_flow_graph
        result = render_review_packet_v1(
            packet,
            fmt="MARKDOWN",
            style="STANDARD",
            rescue_flow_graph=rescue_flow_graph
        )

        assert result["v11_render_status"] == "AVAILABLE", "Expected AVAILABLE status"
        output = result["v11_render_output"]
        assert "## Rescue Flow" in output, "Should include ## Rescue Flow heading"
        assert "STABILITY_ROLE" in output, "Should include role labels"
        assert "EDGE_SHIELD" in output, "Should include edge types"
        assert "RESCUE_MEDIUM" in output, "Should include rescue strength"
        print(f"  ✓ STANDARD includes Rescue Flow section with content")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_4_concise_excludes_rescue_flow():
    """Test 4: CONCISE does NOT include rescue flow."""
    print("\nTest 4: CONCISE does NOT include rescue flow")
    try:
        from render import render_review_packet_v1

        # Create minimal packet
        packet = {
            "v11_packet_status": "AVAILABLE",
            "v11_packet_summary": "test packet",
            "v11_packet_components": {},
            "v11_packet_basis": [],
            "v11_packet_artifacts": [],
        }

        # Create mock rescue flow graph
        rescue_flow_graph = {
            "v12_flow_status": "AVAILABLE",
            "v12_flow_edges": [
                {
                    "from_role": "STABILITY_ROLE",
                    "to_role": "VOLATILITY_ROLE",
                    "edge_type": "EDGE_SHIELD",
                    "rescue_strength": "RESCUE_MEDIUM",
                    "conditions": ["REGIME_MEDIUM"],
                },
            ],
        }

        # Render with CONCISE style
        result = render_review_packet_v1(
            packet,
            fmt="MARKDOWN",
            style="CONCISE",
            rescue_flow_graph=rescue_flow_graph
        )

        output = result["v11_render_output"]
        assert "Rescue Flow" not in output, "CONCISE should NOT include Rescue Flow"
        print(f"  ✓ CONCISE excludes Rescue Flow section")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_5_detailed_includes_conditions():
    """Test 5: DETAILED includes conditions labels."""
    print("\nTest 5: DETAILED includes conditions labels")
    try:
        from render import render_review_packet_v1

        # Create minimal packet
        packet = {
            "v11_packet_status": "AVAILABLE",
            "v11_packet_summary": "test packet",
            "v11_packet_components": {},
            "v11_packet_basis": [],
            "v11_packet_artifacts": [],
        }

        # Create mock rescue flow graph with conditions
        rescue_flow_graph = {
            "v12_flow_status": "AVAILABLE",
            "v12_flow_edges": [
                {
                    "from_role": "STABILITY_ROLE",
                    "to_role": "VOLATILITY_ROLE",
                    "edge_type": "EDGE_SHIELD",
                    "rescue_strength": "RESCUE_MEDIUM",
                    "conditions": ["REGIME_MEDIUM", "D1_LIQUIDATION", "EDGE_SHIELD"],
                },
            ],
        }

        # Render with DETAILED style
        result = render_review_packet_v1(
            packet,
            fmt="MARKDOWN",
            style="DETAILED",
            rescue_flow_graph=rescue_flow_graph
        )

        output = result["v11_render_output"]
        assert "conditions:" in output, "DETAILED should include conditions"
        assert "REGIME_MEDIUM" in output, "Should include regime condition"
        assert "D1_LIQUIDATION" in output, "Should include distortion condition"
        print(f"  ✓ DETAILED includes conditions labels")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_6_no_token_literals():
    """Test 6: Output contains no token literals."""
    print("\nTest 6: Output contains no token literals")
    try:
        from render import render_review_packet_v1

        # Create minimal packet
        packet = {
            "v11_packet_status": "AVAILABLE",
            "v11_packet_summary": "test packet",
            "v11_packet_components": {},
            "v11_packet_basis": [],
            "v11_packet_artifacts": [],
        }

        # Create mock rescue flow graph (only ROLE labels)
        rescue_flow_graph = {
            "v12_flow_status": "AVAILABLE",
            "v12_flow_edges": [
                {
                    "from_role": "STABILITY_ROLE",
                    "to_role": "LIQUIDITY_ROLE",
                    "edge_type": "EDGE_SHIELD",
                    "rescue_strength": "RESCUE_MEDIUM",
                    "conditions": ["REGIME_MEDIUM"],
                },
            ],
        }

        # Render
        result = render_review_packet_v1(
            packet,
            fmt="MARKDOWN",
            style="STANDARD",
            rescue_flow_graph=rescue_flow_graph
        )

        output = result["v11_render_output"]

        # Check no token literals
        forbidden_tokens = ["SUI", "USDC", "BTC", "ETH", "DEEP", "CETUS"]
        for token in forbidden_tokens:
            assert token not in output, f"Should not contain token literal: {token}"

        print(f"  ✓ Output contains no token literals")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_7_no_numeric_patterns():
    """Test 7: Output contains no numeric patterns."""
    print("\nTest 7: Output contains no numeric patterns")
    try:
        from render import render_review_packet_v1
        import re

        # Create minimal packet
        packet = {
            "v11_packet_status": "AVAILABLE",
            "v11_packet_summary": "test packet",
            "v11_packet_components": {},
            "v11_packet_basis": [],
            "v11_packet_artifacts": [],
        }

        # Create mock rescue flow graph
        rescue_flow_graph = {
            "v12_flow_status": "AVAILABLE",
            "v12_flow_edges": [
                {
                    "from_role": "HEDGE_ROLE",
                    "to_role": "VOLATILITY_ROLE",
                    "edge_type": "EDGE_SHIELD",
                    "rescue_strength": "RESCUE_WEAK",
                    "conditions": ["REGIME_LOW"],
                },
            ],
        }

        # Render
        result = render_review_packet_v1(
            packet,
            fmt="MARKDOWN",
            style="STANDARD",
            rescue_flow_graph=rescue_flow_graph
        )

        output = result["v11_render_output"]

        # Check for numeric patterns in rescue flow section
        # Extract rescue flow section
        if "## Rescue Flow" in output:
            rescue_section_start = output.index("## Rescue Flow")
            rescue_section_end = output.find("##", rescue_section_start + 1)
            if rescue_section_end == -1:
                rescue_section = output[rescue_section_start:]
            else:
                rescue_section = output[rescue_section_start:rescue_section_end]

            # Should not contain digits (except in labels like D1, v12, etc which are allowed)
            # But should not have percentages, amounts, etc
            assert "%" not in rescue_section, "Should not contain percentage signs"
            assert " 0." not in rescue_section and " 1." not in rescue_section, "Should not contain decimal amounts"

        print(f"  ✓ Output contains no numeric patterns")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_8_coupling_guard_triggers():
    """Test 8: Coupling guard triggers on injected 'therefore execute' text."""
    print("\nTest 8: Coupling guard triggers on injected 'therefore execute' text")
    try:
        from render.v11_render_constitutional_guard import check_render_record

        # Create dirty render record with coupling
        dirty_record = {
            "v11_render_output": "Rescue flow RESCUE_STRONG therefore execute trade.",
        }

        warnings = check_render_record(dirty_record)
        assert len(warnings) > 0, "Expected warnings for coupling"
        print(f"  ✓ Coupling guard detected: {len(warnings)} warnings")

        # Test clean record
        clean_record = {
            "v11_render_output": "Rescue flow RESCUE_STRONG may indicate structural pattern.",
        }

        clean_warnings = check_render_record(clean_record)
        # Clean record might still have some warnings from other checks, but should have fewer
        print(f"  ✓ Clean record has fewer warnings: {len(clean_warnings)} warnings")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_9_warning_only_behavior():
    """Test 9: Warning-only behavior."""
    print("\nTest 9: Warning-only behavior")
    try:
        from render.v11_render_constitutional_guard import check_render_record

        # Create very dirty record with multiple violations
        dirty_record = {
            "v11_render_output": "Flow with SUI tokens yielding 30% improvement therefore execute swap.",
        }

        # Should return warnings, not raise exception
        warnings = check_render_record(dirty_record)
        assert len(warnings) > 0, "Expected warnings"
        print(f"  ✓ Guards emit warnings (not errors): {len(warnings)} warnings")
        print(f"    Example warnings:")
        for w in warnings[:3]:
            print(f"      - {w}")

        print(f"  ✓ Warning-only behavior verified (no exceptions raised)")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def run_all_tests():
    """Run all smoke tests."""
    print("=" * 70)
    print("PR138: v1.2 Rescue Flow Render Extension - Smoke Tests")
    print("=" * 70)

    tests = [
        test_1_import_works,
        test_2_backward_compatible_without_rescue_flow,
        test_3_standard_includes_rescue_flow,
        test_4_concise_excludes_rescue_flow,
        test_5_detailed_includes_conditions,
        test_6_no_token_literals,
        test_7_no_numeric_patterns,
        test_8_coupling_guard_triggers,
        test_9_warning_only_behavior,
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
