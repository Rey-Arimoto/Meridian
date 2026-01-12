#!/usr/bin/env python3
"""
PR139: v1.2 Rescue Flow Narrative Extension v1 Smoke Tests

Purpose:
    Validate rescue flow narrative extension for human narrative builder.

Tests:
    1. Import works
    2. Mode OFF returns SKIPPED
    3. No flow graph returns SKIPPED
    4. Flow unavailable returns SKIPPED
    5. Empty edges returns SKIPPED
    6. CONCISE style generates 1 paragraph
    7. STANDARD style generates 2-4 paragraphs
    8. DETAILED style includes edge lines
    9. Output contains no prescriptive language
    10. Output contains no action vocabulary
    11. Coupling guard triggers on injected coupling text
    12. Warning-only behavior
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_1_import_works():
    """Test 1: Import works."""
    print("Test 1: Import works")
    try:
        from narrative import (
            V12NarrativeRescueFlowExtensionSchema,
            build_rescue_flow_narrative_extension_v1,
            get_rescue_flow_narrative_extension_info,
            check_rescue_narrative_record,
        )
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_2_mode_off_returns_skipped():
    """Test 2: Mode OFF returns SKIPPED."""
    print("\nTest 2: Mode OFF returns SKIPPED")
    try:
        from narrative import build_rescue_flow_narrative_extension_v1

        result = build_rescue_flow_narrative_extension_v1(None, mode="OFF")

        assert result["v12_rescue_narrative_status"] == "SKIPPED", "Expected SKIPPED status"
        assert result["v12_rescue_narrative_mode"] == "OFF", "Expected OFF mode"
        print(f"  ✓ Mode OFF returns SKIPPED")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_3_no_flow_graph_returns_skipped():
    """Test 3: No flow graph returns SKIPPED."""
    print("\nTest 3: No flow graph returns SKIPPED")
    try:
        from narrative import build_rescue_flow_narrative_extension_v1

        result = build_rescue_flow_narrative_extension_v1(None, mode="ON")

        assert result["v12_rescue_narrative_status"] == "SKIPPED", "Expected SKIPPED status"
        print(f"  ✓ No flow graph returns SKIPPED")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_4_flow_unavailable_returns_skipped():
    """Test 4: Flow unavailable returns SKIPPED."""
    print("\nTest 4: Flow unavailable returns SKIPPED")
    try:
        from narrative import build_rescue_flow_narrative_extension_v1

        # Flow graph with ERROR status
        flow_graph = {
            "v12_flow_status": "ERROR",
            "v12_flow_edges": [],
        }

        result = build_rescue_flow_narrative_extension_v1(flow_graph, mode="ON")

        assert result["v12_rescue_narrative_status"] == "SKIPPED", "Expected SKIPPED status"
        print(f"  ✓ Flow unavailable returns SKIPPED")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_5_empty_edges_returns_skipped():
    """Test 5: Empty edges returns SKIPPED."""
    print("\nTest 5: Empty edges returns SKIPPED")
    try:
        from narrative import build_rescue_flow_narrative_extension_v1

        # Flow graph with no edges
        flow_graph = {
            "v12_flow_status": "AVAILABLE",
            "v12_flow_edges": [],
        }

        result = build_rescue_flow_narrative_extension_v1(flow_graph, mode="ON")

        assert result["v12_rescue_narrative_status"] == "SKIPPED", "Expected SKIPPED status"
        print(f"  ✓ Empty edges returns SKIPPED")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_6_concise_style_one_paragraph():
    """Test 6: CONCISE style generates 1 paragraph."""
    print("\nTest 6: CONCISE style generates 1 paragraph")
    try:
        from narrative import build_rescue_flow_narrative_extension_v1

        # Mock flow graph
        flow_graph = {
            "v12_flow_status": "AVAILABLE",
            "v12_flow_edges": [
                {
                    "from_role": "STABILITY_ROLE",
                    "to_role": "VOLATILITY_ROLE",
                    "edge_type": "EDGE_SHIELD",
                    "rescue_strength": "RESCUE_MEDIUM",
                },
            ],
        }

        result = build_rescue_flow_narrative_extension_v1(flow_graph, style="CONCISE")

        assert result["v12_rescue_narrative_status"] == "AVAILABLE", "Expected AVAILABLE status"
        paragraphs = result["v12_rescue_narrative_paragraphs"]
        assert len(paragraphs) == 1, f"Expected 1 paragraph, got {len(paragraphs)}"
        assert "rescue flow graph" in paragraphs[0].lower(), "Expected existence statement"
        print(f"  ✓ CONCISE style generates 1 paragraph")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_7_standard_style_multiple_paragraphs():
    """Test 7: STANDARD style generates 2-4 paragraphs."""
    print("\nTest 7: STANDARD style generates 2-4 paragraphs")
    try:
        from narrative import build_rescue_flow_narrative_extension_v1

        # Mock flow graph
        flow_graph = {
            "v12_flow_status": "AVAILABLE",
            "v12_flow_edges": [
                {
                    "from_role": "STABILITY_ROLE",
                    "to_role": "VOLATILITY_ROLE",
                    "edge_type": "EDGE_SHIELD",
                    "rescue_strength": "RESCUE_MEDIUM",
                },
                {
                    "from_role": "HEDGE_ROLE",
                    "to_role": "VOLATILITY_ROLE",
                    "edge_type": "EDGE_SHIELD",
                    "rescue_strength": "RESCUE_WEAK",
                },
            ],
        }

        result = build_rescue_flow_narrative_extension_v1(flow_graph, style="STANDARD")

        assert result["v12_rescue_narrative_status"] == "AVAILABLE", "Expected AVAILABLE status"
        paragraphs = result["v12_rescue_narrative_paragraphs"]
        assert 2 <= len(paragraphs) <= 4, f"Expected 2-4 paragraphs, got {len(paragraphs)}"

        # Check P1: existence statement
        assert "rescue flow graph" in paragraphs[0].lower(), "Expected existence statement in P1"

        # Check P2: support direction
        assert "may support" in paragraphs[1].lower(), "Expected support direction in P2"

        # Check P3: rescue strength
        assert "rescue strength" in paragraphs[2].lower(), "Expected rescue strength in P3"

        print(f"  ✓ STANDARD style generates {len(paragraphs)} paragraphs")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_8_detailed_style_includes_edge_lines():
    """Test 8: DETAILED style includes edge lines."""
    print("\nTest 8: DETAILED style includes edge lines")
    try:
        from narrative import build_rescue_flow_narrative_extension_v1

        # Mock flow graph
        flow_graph = {
            "v12_flow_status": "AVAILABLE",
            "v12_flow_edges": [
                {
                    "from_role": "STABILITY_ROLE",
                    "to_role": "VOLATILITY_ROLE",
                    "edge_type": "EDGE_SHIELD",
                    "rescue_strength": "RESCUE_MEDIUM",
                },
                {
                    "from_role": "HEDGE_ROLE",
                    "to_role": "VOLATILITY_ROLE",
                    "edge_type": "EDGE_SHIELD",
                    "rescue_strength": "RESCUE_WEAK",
                },
            ],
        }

        result = build_rescue_flow_narrative_extension_v1(flow_graph, style="DETAILED")

        assert result["v12_rescue_narrative_status"] == "AVAILABLE", "Expected AVAILABLE status"
        paragraphs = result["v12_rescue_narrative_paragraphs"]
        assert len(paragraphs) >= 3, f"Expected at least 3 paragraphs, got {len(paragraphs)}"

        # Check for edge details in last paragraph
        last_paragraph = paragraphs[-1]
        assert "edge details" in last_paragraph.lower() or "may support" in last_paragraph.lower(), \
            "Expected edge details in DETAILED style"

        print(f"  ✓ DETAILED style includes edge lines")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_9_no_prescriptive_language():
    """Test 9: Output contains no prescriptive language."""
    print("\nTest 9: Output contains no prescriptive language")
    try:
        from narrative import build_rescue_flow_narrative_extension_v1

        # Mock flow graph
        flow_graph = {
            "v12_flow_status": "AVAILABLE",
            "v12_flow_edges": [
                {
                    "from_role": "STABILITY_ROLE",
                    "to_role": "VOLATILITY_ROLE",
                    "edge_type": "EDGE_SHIELD",
                    "rescue_strength": "RESCUE_MEDIUM",
                },
            ],
        }

        result = build_rescue_flow_narrative_extension_v1(flow_graph, style="STANDARD")

        # Check all paragraphs for prescriptive language
        forbidden_words = ["should", "must", "need to", "have to", "recommend"]
        full_text = " ".join(result["v12_rescue_narrative_paragraphs"]).lower()

        for word in forbidden_words:
            assert word not in full_text, f"Found forbidden prescriptive word: {word}"

        print(f"  ✓ Output contains no prescriptive language")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_10_no_action_vocabulary():
    """Test 10: Output contains no action vocabulary."""
    print("\nTest 10: Output contains no action vocabulary")
    try:
        from narrative import build_rescue_flow_narrative_extension_v1

        # Mock flow graph
        flow_graph = {
            "v12_flow_status": "AVAILABLE",
            "v12_flow_edges": [
                {
                    "from_role": "STABILITY_ROLE",
                    "to_role": "VOLATILITY_ROLE",
                    "edge_type": "EDGE_SHIELD",
                    "rescue_strength": "RESCUE_MEDIUM",
                },
            ],
        }

        result = build_rescue_flow_narrative_extension_v1(flow_graph, style="STANDARD")

        # Check all paragraphs for action vocabulary
        forbidden_words = ["execute", "trade", "swap", "buy", "sell"]
        full_text = " ".join(result["v12_rescue_narrative_paragraphs"]).lower()

        for word in forbidden_words:
            assert word not in full_text, f"Found forbidden action word: {word}"

        print(f"  ✓ Output contains no action vocabulary")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_11_coupling_guard_triggers():
    """Test 11: Coupling guard triggers on injected coupling text."""
    print("\nTest 11: Coupling guard triggers on injected coupling text")
    try:
        from narrative import check_rescue_narrative_record

        # Create dirty record with coupling
        dirty_record = {
            "v12_rescue_narrative_summary": "rescue flow narrative available.",
            "v12_rescue_narrative_paragraphs": [
                "RESCUE_STRONG therefore execute trade.",
            ],
        }

        warnings = check_rescue_narrative_record(dirty_record)
        assert len(warnings) > 0, "Expected warnings for coupling"
        print(f"  ✓ Coupling guard detected: {len(warnings)} warnings")

        # Test clean record
        clean_record = {
            "v12_rescue_narrative_summary": "rescue flow narrative available.",
            "v12_rescue_narrative_paragraphs": [
                "rescue flow graph indicates STABILITY may support VOLATILITY.",
            ],
        }

        clean_warnings = check_rescue_narrative_record(clean_record)
        print(f"  ✓ Clean record has {len(clean_warnings)} warnings")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_12_warning_only_behavior():
    """Test 12: Warning-only behavior."""
    print("\nTest 12: Warning-only behavior")
    try:
        from narrative import check_rescue_narrative_record

        # Create very dirty record with multiple violations
        dirty_record = {
            "v12_rescue_narrative_summary": "RESCUE_STRONG therefore trade.",
            "v12_rescue_narrative_paragraphs": [
                "System should execute swap operations.",
                "RESCUE_MEDIUM means buy signal.",
            ],
        }

        # Should return warnings, not raise exception
        warnings = check_rescue_narrative_record(dirty_record)
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
    print("PR139: v1.2 Rescue Flow Narrative Extension v1 - Smoke Tests")
    print("=" * 70)

    tests = [
        test_1_import_works,
        test_2_mode_off_returns_skipped,
        test_3_no_flow_graph_returns_skipped,
        test_4_flow_unavailable_returns_skipped,
        test_5_empty_edges_returns_skipped,
        test_6_concise_style_one_paragraph,
        test_7_standard_style_multiple_paragraphs,
        test_8_detailed_style_includes_edge_lines,
        test_9_no_prescriptive_language,
        test_10_no_action_vocabulary,
        test_11_coupling_guard_triggers,
        test_12_warning_only_behavior,
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
