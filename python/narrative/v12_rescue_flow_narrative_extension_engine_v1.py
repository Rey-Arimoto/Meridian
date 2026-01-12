#!/usr/bin/env python3
"""
PR139: v1.2 Rescue Flow Narrative Extension Engine v1 (READ-ONLY)

Purpose:
    Add PR137 Rescue Flow Graph to PR123 Human Narrative Builder output
    as "structural explanation" (not instruction/conclusion).

Engine Philosophy:
    - Defensive: invalid flow graph → SKIPPED (not ERROR)
    - Deterministic: no LLM, no randomness, template-based
    - Label-focused: structural description only
    - Non-prescriptive: no "should", "must", "therefore"

Text Generation Rules:
    CONCISE: 1-2 lines (existence statement only)
    STANDARD: 2-4 paragraphs
        - P1: Existence statement
        - P2: Support direction labels (ROLE-to-ROLE)
        - P3: Rescue strength label distribution
    DETAILED: STANDARD + up to 6 edge lines

Allowed Language:
    - "indicates", "may", "can", "tends to", "is labeled as"

Forbidden Language:
    - "therefore", "so", "means", "should", "must"
    - "execute", "trade", "swap", "buy", "sell"

Constitutional Constraints:
    - READ-ONLY: No execution, no recommendations
    - Non-prescriptive: No instruction language
    - No token literals: No SUI, USDC, BTC, ETH
    - No numeric patterns: No amounts, percentages
    - No causal coupling: No "therefore" → action
"""

from typing import Any, Dict, List, Optional, Tuple

# Handle both relative and absolute imports
try:
    from .v12_narrative_rescue_flow_extension_schema import (
        V12NarrativeRescueFlowExtensionSchema,
        RESCUE_NARRATIVE_MODE_ON,
        RESCUE_NARRATIVE_MODE_OFF,
        RESCUE_NARRATIVE_STATUS_AVAILABLE,
        RESCUE_NARRATIVE_STATUS_SKIPPED,
        RESCUE_NARRATIVE_STYLE_CONCISE,
        RESCUE_NARRATIVE_STYLE_STANDARD,
        RESCUE_NARRATIVE_STYLE_DETAILED,
    )
except ImportError:
    from v12_narrative_rescue_flow_extension_schema import (
        V12NarrativeRescueFlowExtensionSchema,
        RESCUE_NARRATIVE_MODE_ON,
        RESCUE_NARRATIVE_MODE_OFF,
        RESCUE_NARRATIVE_STATUS_AVAILABLE,
        RESCUE_NARRATIVE_STATUS_SKIPPED,
        RESCUE_NARRATIVE_STYLE_CONCISE,
        RESCUE_NARRATIVE_STYLE_STANDARD,
        RESCUE_NARRATIVE_STYLE_DETAILED,
    )


def _safe_get(d: Optional[Dict[str, Any]], key: str, default: Any = None) -> Any:
    """
    Safely get value from dict.

    Args:
        d: Dictionary (may be None)
        key: Key to get
        default: Default value if not found

    Returns:
        Value or default
    """
    if not isinstance(d, dict):
        return default
    return d.get(key, default)


def _get_role_display_name(role: str) -> str:
    """
    Get display name for role (strip _ROLE suffix).

    Args:
        role: Role label (e.g., "STABILITY_ROLE")

    Returns:
        Display name (e.g., "STABILITY")
    """
    if role.endswith("_ROLE"):
        return role[:-5]
    return role


def _analyze_edges(edges: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze edges for narrative generation.

    Args:
        edges: List of edge objects

    Returns:
        Analysis dict with:
            - from_roles: set of unique from_roles
            - to_roles: set of unique to_roles
            - edge_types: dict of edge_type counts
            - rescue_strengths: dict of rescue_strength counts
            - shield_edges: list of EDGE_SHIELD edges
            - support_pairs: list of (from_role, to_role) tuples for SHIELD edges
    """
    analysis = {
        "from_roles": set(),
        "to_roles": set(),
        "edge_types": {},
        "rescue_strengths": {},
        "shield_edges": [],
        "support_pairs": [],
    }

    for edge in edges:
        from_role = _safe_get(edge, "from_role", "")
        to_role = _safe_get(edge, "to_role", "")
        edge_type = _safe_get(edge, "edge_type", "")
        rescue_strength = _safe_get(edge, "rescue_strength", "")

        if from_role:
            analysis["from_roles"].add(from_role)
        if to_role:
            analysis["to_roles"].add(to_role)

        # Count edge types
        if edge_type:
            analysis["edge_types"][edge_type] = analysis["edge_types"].get(edge_type, 0) + 1

        # Count rescue strengths
        if rescue_strength:
            analysis["rescue_strengths"][rescue_strength] = analysis["rescue_strengths"].get(rescue_strength, 0) + 1

        # Track SHIELD edges (support relationships)
        if edge_type == "EDGE_SHIELD":
            analysis["shield_edges"].append(edge)
            if from_role and to_role:
                analysis["support_pairs"].append((from_role, to_role))

    return analysis


def _generate_existence_statement(analysis: Dict[str, Any]) -> str:
    """
    Generate existence statement (paragraph 1).

    Args:
        analysis: Edge analysis dict

    Returns:
        Existence statement paragraph
    """
    edge_count = sum(analysis["edge_types"].values())

    # Count unique roles
    all_roles = analysis["from_roles"] | analysis["to_roles"]
    role_count = len(all_roles)

    return (
        f"rescue flow graph indicates structural ROLE-to-ROLE rescue relationships. "
        f"graph contains {edge_count} labeled edges across {role_count} role labels."
    )


def _generate_support_direction_text(analysis: Dict[str, Any]) -> str:
    """
    Generate support direction text (paragraph 2).

    Args:
        analysis: Edge analysis dict

    Returns:
        Support direction paragraph
    """
    if not analysis["support_pairs"]:
        return "no EDGE_SHIELD support relationships detected in current flow graph."

    # Group by from_role
    support_map = {}
    for from_role, to_role in analysis["support_pairs"]:
        if from_role not in support_map:
            support_map[from_role] = []
        support_map[from_role].append(to_role)

    # Generate sentences
    sentences = []
    for from_role in sorted(support_map.keys()):
        to_roles = sorted(set(support_map[from_role]))
        from_display = _get_role_display_name(from_role)
        to_displays = [_get_role_display_name(r) for r in to_roles]

        if len(to_displays) == 1:
            sentences.append(f"{from_display} may support {to_displays[0]}.")
        elif len(to_displays) == 2:
            sentences.append(f"{from_display} may support {to_displays[0]} and {to_displays[1]}.")
        else:
            # More than 2
            to_list = ", ".join(to_displays[:-1]) + f", and {to_displays[-1]}"
            sentences.append(f"{from_display} may support {to_list}.")

    return " ".join(sentences)


def _generate_strength_distribution_text(analysis: Dict[str, Any]) -> str:
    """
    Generate rescue strength distribution text (paragraph 3).

    Args:
        analysis: Edge analysis dict

    Returns:
        Strength distribution paragraph
    """
    if not analysis["rescue_strengths"]:
        return "no rescue strength labels detected in current flow graph."

    # Get strength labels in priority order
    strength_order = ["RESCUE_STRONG", "RESCUE_MEDIUM", "RESCUE_WEAK", "RESCUE_NONE"]
    present_strengths = [s for s in strength_order if s in analysis["rescue_strengths"]]

    if not present_strengths:
        return "rescue strength labels indicate baseline or neutral structural relationships."

    if len(present_strengths) == 1:
        return f"rescue strength labels indicate {present_strengths[0]} structural relationships."

    # Multiple strengths
    strength_displays = [s.replace("RESCUE_", "") for s in present_strengths]

    if len(strength_displays) == 2:
        return f"rescue strength labels range from {strength_displays[0]} to {strength_displays[1]}."
    else:
        # 3 or more
        return (
            f"rescue strength labels include {strength_displays[0]}, {strength_displays[1]}, "
            f"and {strength_displays[2]} structural patterns."
        )


def _format_edge_line_for_narrative(edge: Dict[str, Any]) -> str:
    """
    Format a single edge as a narrative line (for DETAILED style).

    Args:
        edge: Edge object

    Returns:
        Formatted line
    """
    from_role = _safe_get(edge, "from_role", "UNKNOWN")
    to_role = _safe_get(edge, "to_role", "UNKNOWN")
    edge_type = _safe_get(edge, "edge_type", "UNKNOWN")
    rescue_strength = _safe_get(edge, "rescue_strength", "UNKNOWN")

    from_display = _get_role_display_name(from_role)
    to_display = _get_role_display_name(to_role)

    # Use non-prescriptive language
    if edge_type == "EDGE_SHIELD":
        verb = "may support"
    elif edge_type == "EDGE_NEUTRAL":
        verb = "is neutral to"
    elif edge_type == "EDGE_AMPLIFY":
        verb = "may amplify"
    elif edge_type == "EDGE_LEAK":
        verb = "may leak to"
    else:
        verb = "relates to"

    return f"{from_display} {verb} {to_display} | {rescue_strength}"


def _generate_paragraphs_concise(analysis: Dict[str, Any]) -> List[str]:
    """
    Generate CONCISE paragraphs (1-2 lines).

    Args:
        analysis: Edge analysis dict

    Returns:
        List of paragraphs
    """
    existence = _generate_existence_statement(analysis)
    return [existence]


def _generate_paragraphs_standard(analysis: Dict[str, Any]) -> List[str]:
    """
    Generate STANDARD paragraphs (2-4 paragraphs).

    Args:
        analysis: Edge analysis dict

    Returns:
        List of paragraphs
    """
    paragraphs = []

    # P1: Existence statement
    existence = _generate_existence_statement(analysis)
    paragraphs.append(existence)

    # P2: Support direction labels
    support = _generate_support_direction_text(analysis)
    paragraphs.append(support)

    # P3: Rescue strength distribution
    strength = _generate_strength_distribution_text(analysis)
    paragraphs.append(strength)

    return paragraphs


def _generate_paragraphs_detailed(
    analysis: Dict[str, Any],
    edges: List[Dict[str, Any]],
) -> List[str]:
    """
    Generate DETAILED paragraphs (STANDARD + up to 6 edge lines).

    Args:
        analysis: Edge analysis dict
        edges: List of edge objects

    Returns:
        List of paragraphs
    """
    # Start with STANDARD paragraphs
    paragraphs = _generate_paragraphs_standard(analysis)

    # Add edge lines (up to 6)
    if edges:
        # Sort edges by rescue_strength priority
        strength_priority = {
            "RESCUE_STRONG": 0,
            "RESCUE_MEDIUM": 1,
            "RESCUE_WEAK": 2,
            "RESCUE_NONE": 3,
        }

        sorted_edges = sorted(
            edges,
            key=lambda e: strength_priority.get(_safe_get(e, "rescue_strength", ""), 99)
        )

        # Take top 6
        selected_edges = sorted_edges[:6]

        # Format as lines
        edge_lines = []
        for edge in selected_edges:
            line = _format_edge_line_for_narrative(edge)
            edge_lines.append(line)

        # Join as single paragraph
        if edge_lines:
            edge_paragraph = "edge details: " + " | ".join(edge_lines)
            paragraphs.append(edge_paragraph)

    return paragraphs


def build_rescue_flow_narrative_extension_v1(
    rescue_flow_graph_record: Optional[Dict[str, Any]] = None,
    style: str = "STANDARD",
    mode: str = "ON",
) -> Dict[str, Any]:
    """
    Build rescue flow narrative extension.

    Args:
        rescue_flow_graph_record: PR137 flow graph record
        style: CONCISE | STANDARD | DETAILED
        mode: ON | OFF

    Returns:
        Rescue narrative record (always valid, SKIPPED on unavailable)
    """
    try:
        # Defensive: validate style
        if style not in V12NarrativeRescueFlowExtensionSchema.VALID_STYLES:
            style = RESCUE_NARRATIVE_STYLE_STANDARD

        # If mode OFF, return skipped
        if mode == RESCUE_NARRATIVE_MODE_OFF:
            return V12NarrativeRescueFlowExtensionSchema.create_skipped_record(
                summary="rescue narrative skipped (mode OFF).",
                style=style,
            )

        # Defensive: validate input
        if not rescue_flow_graph_record or not isinstance(rescue_flow_graph_record, dict):
            return V12NarrativeRescueFlowExtensionSchema.create_skipped_record(
                summary="rescue narrative skipped (no flow graph provided).",
                style=style,
            )

        # Check flow status
        flow_status = _safe_get(rescue_flow_graph_record, "v12_flow_status")
        if flow_status != "AVAILABLE":
            return V12NarrativeRescueFlowExtensionSchema.create_skipped_record(
                summary=f"rescue narrative skipped (flow status: {flow_status}).",
                style=style,
            )

        # Get edges
        edges = _safe_get(rescue_flow_graph_record, "v12_flow_edges", [])
        if not isinstance(edges, list) or len(edges) == 0:
            return V12NarrativeRescueFlowExtensionSchema.create_skipped_record(
                summary="rescue narrative skipped (no edges in flow graph).",
                style=style,
            )

        # Analyze edges
        analysis = _analyze_edges(edges)

        # Generate paragraphs based on style
        if style == RESCUE_NARRATIVE_STYLE_CONCISE:
            paragraphs = _generate_paragraphs_concise(analysis)
        elif style == RESCUE_NARRATIVE_STYLE_DETAILED:
            paragraphs = _generate_paragraphs_detailed(analysis, edges)
        else:  # STANDARD
            paragraphs = _generate_paragraphs_standard(analysis)

        # Generate summary
        edge_count = sum(analysis["edge_types"].values())
        summary = f"rescue flow narrative extension available. {edge_count} edges analyzed."

        # Create record
        return V12NarrativeRescueFlowExtensionSchema.create_rescue_narrative_record(
            mode=RESCUE_NARRATIVE_MODE_ON,
            status=RESCUE_NARRATIVE_STATUS_AVAILABLE,
            style=style,
            summary=summary,
            paragraphs=paragraphs,
            basis=["v12_flow_edges", "v12_flow_status"],
        )

    except Exception:
        # Defensive: never raise, return skipped
        return V12NarrativeRescueFlowExtensionSchema.create_skipped_record(
            summary="rescue narrative skipped (generation error).",
            style=style,
        )


def get_rescue_flow_narrative_extension_info() -> Dict[str, Any]:
    """
    Get rescue flow narrative extension information.

    Returns:
        Dict with extension metadata
    """
    return {
        "extension_version": "v1",
        "extension_type": "rescue_flow_narrative",
        "input_schema": "v12_flow (PR137)",
        "output_schema": "v12_rescue_narrative",
        "styles": {
            "CONCISE": "1-2 lines (existence only)",
            "STANDARD": "2-4 paragraphs (existence, support, strength)",
            "DETAILED": "STANDARD + up to 6 edge lines",
        },
        "allowed_language": [
            "indicates",
            "may",
            "can",
            "tends to",
            "is labeled as",
        ],
        "forbidden_language": [
            "therefore",
            "so",
            "means",
            "should",
            "must",
            "execute",
            "trade",
            "swap",
        ],
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-prescriptive",
            "no_token_literals",
            "no_numeric_patterns",
            "defensive",
        ],
    }


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.2 Rescue Flow Narrative Extension Engine v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: No flow graph (skipped)
    print("Test 1: No flow graph (skipped)")
    result1 = build_rescue_flow_narrative_extension_v1(None)
    print(f"Status: {result1['v12_rescue_narrative_status']}")
    print(f"Summary: {result1['v12_rescue_narrative_summary']}")
    print()

    # Test 2: Mode OFF (skipped)
    print("Test 2: Mode OFF (skipped)")
    result2 = build_rescue_flow_narrative_extension_v1(None, mode="OFF")
    print(f"Status: {result2['v12_rescue_narrative_status']}")
    print(f"Summary: {result2['v12_rescue_narrative_summary']}")
    print()

    # Test 3: Valid flow graph, CONCISE style
    print("Test 3: Valid flow graph, CONCISE style")
    mock_graph = {
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
    result3 = build_rescue_flow_narrative_extension_v1(mock_graph, style="CONCISE")
    print(f"Status: {result3['v12_rescue_narrative_status']}")
    print(f"Paragraphs count: {len(result3['v12_rescue_narrative_paragraphs'])}")
    print("Paragraphs:")
    for i, p in enumerate(result3['v12_rescue_narrative_paragraphs'], 1):
        print(f"  P{i}: {p}")
    print()

    # Test 4: Valid flow graph, STANDARD style
    print("Test 4: Valid flow graph, STANDARD style")
    result4 = build_rescue_flow_narrative_extension_v1(mock_graph, style="STANDARD")
    print(f"Status: {result4['v12_rescue_narrative_status']}")
    print(f"Paragraphs count: {len(result4['v12_rescue_narrative_paragraphs'])}")
    print("Paragraphs:")
    for i, p in enumerate(result4['v12_rescue_narrative_paragraphs'], 1):
        print(f"  P{i}: {p}")
    print()

    # Test 5: Valid flow graph, DETAILED style
    print("Test 5: Valid flow graph, DETAILED style")
    result5 = build_rescue_flow_narrative_extension_v1(mock_graph, style="DETAILED")
    print(f"Status: {result5['v12_rescue_narrative_status']}")
    print(f"Paragraphs count: {len(result5['v12_rescue_narrative_paragraphs'])}")
    print("Paragraphs:")
    for i, p in enumerate(result5['v12_rescue_narrative_paragraphs'], 1):
        print(f"  P{i}: {p}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
