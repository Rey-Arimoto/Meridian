#!/usr/bin/env python3
"""
PR138: v1.2 Rescue Flow Render Adapter (READ-ONLY)

Purpose:
    Project rescue flow graph for human review renderer.
    Adapter produces label-only formatted lines (not instruction).

Constitutional Constraints:
    - READ-ONLY: No execution, no recommendations
    - Non-prescriptive: No "should", "must", "therefore"
    - No token literals: No SUI, USDC, BTC, ETH
    - No numeric patterns: No amounts, percentages
    - No trading vocabulary: No swap, buy, sell, execute

Render = Display shape (not instruction)
"""

from typing import Any, Dict, List, Optional


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


def _get_role_order_priority(role: str) -> int:
    """
    Get priority for role ordering (lower = higher priority).

    Args:
        role: ROLE label

    Returns:
        Priority value
    """
    order = {
        "STABILITY_ROLE": 0,
        "HEDGE_ROLE": 1,
        "LIQUIDITY_ROLE": 2,
        "VOLATILITY_ROLE": 3,
        "GAS_ROLE": 4,
    }
    return order.get(role, 99)


def _get_rescue_strength_priority(strength: str) -> int:
    """
    Get priority for rescue strength ordering (lower = higher priority).

    Args:
        strength: Rescue strength label

    Returns:
        Priority value
    """
    order = {
        "RESCUE_STRONG": 0,
        "RESCUE_MEDIUM": 1,
        "RESCUE_WEAK": 2,
        "RESCUE_NONE": 3,
    }
    return order.get(strength, 99)


def _get_edge_type_priority(edge_type: str) -> int:
    """
    Get priority for edge type ordering (lower = higher priority).

    Args:
        edge_type: Edge type label

    Returns:
        Priority value
    """
    order = {
        "EDGE_SHIELD": 0,
        "EDGE_NEUTRAL": 1,
        "EDGE_AMPLIFY": 2,
        "EDGE_LEAK": 3,
        "EDGE_NONE": 4,
    }
    return order.get(edge_type, 99)


def _format_edge_line(
    edge: Dict[str, Any],
    include_conditions: bool = False,
) -> str:
    """
    Format a single edge as a label-only line.

    Args:
        edge: Edge object
        include_conditions: Include conditions in output

    Returns:
        Formatted line
    """
    from_role = _safe_get(edge, "from_role", "UNKNOWN")
    to_role = _safe_get(edge, "to_role", "UNKNOWN")
    edge_type = _safe_get(edge, "edge_type", "UNKNOWN")
    rescue_strength = _safe_get(edge, "rescue_strength", "UNKNOWN")
    conditions = _safe_get(edge, "conditions", [])

    # Basic format: from → to | edge_type | rescue_strength
    line = f"{from_role} → {to_role} | {edge_type} | {rescue_strength}"

    # Add conditions if requested
    if include_conditions and conditions:
        conditions_str = ", ".join(conditions)
        line += f" | conditions: {conditions_str}"

    return line


def project_rescue_flow_for_render(
    flow_graph_record: Optional[Dict[str, Any]],
    style: str = "STANDARD",
) -> List[str]:
    """
    Project rescue flow graph for human review renderer.

    Args:
        flow_graph_record: PR137 flow graph record
        style: Render style (CONCISE/STANDARD/DETAILED)

    Returns:
        List of formatted lines (label-only)
    """
    try:
        # Defensive: invalid input → empty list
        if not isinstance(flow_graph_record, dict):
            return []

        # Check flow status
        flow_status = _safe_get(flow_graph_record, "v12_flow_status")
        if flow_status != "AVAILABLE":
            return []

        # Get edges
        edges = _safe_get(flow_graph_record, "v12_flow_edges", [])
        if not isinstance(edges, list) or len(edges) == 0:
            return []

        # CONCISE: do not include rescue flow
        if style == "CONCISE":
            return []

        # Sort edges by:
        # 1. rescue_strength (STRONG > MEDIUM > WEAK > NONE)
        # 2. edge_type (SHIELD first)
        # 3. from_role stable order (STABILITY, HEDGE, LIQUIDITY, VOLATILITY, GAS)
        sorted_edges = sorted(
            edges,
            key=lambda e: (
                _get_rescue_strength_priority(_safe_get(e, "rescue_strength", "")),
                _get_edge_type_priority(_safe_get(e, "edge_type", "")),
                _get_role_order_priority(_safe_get(e, "from_role", "")),
            )
        )

        # STANDARD: include up to 8 edges, no conditions
        if style == "STANDARD":
            include_conditions = False
            max_edges = 8
            selected_edges = sorted_edges[:max_edges]
        # DETAILED: include all edges + conditions
        else:  # DETAILED
            include_conditions = True
            selected_edges = sorted_edges

        # Format lines
        lines = []
        for edge in selected_edges:
            line = _format_edge_line(edge, include_conditions=include_conditions)
            lines.append(line)

        return lines

    except Exception:
        # Defensive: never raise, return empty list
        return []


def get_rescue_flow_render_adapter_info() -> Dict[str, Any]:
    """
    Get rescue flow render adapter information.

    Returns:
        Dict with adapter metadata
    """
    return {
        "adapter_version": "v1",
        "adapter_type": "rescue_flow_render",
        "input_schema": "v12_flow (PR137)",
        "output_format": "label-only formatted lines",
        "styles": {
            "CONCISE": "no rescue flow",
            "STANDARD": "up to 8 edges, no conditions",
            "DETAILED": "all edges + conditions",
        },
        "sorting_priority": [
            "rescue_strength (STRONG > MEDIUM > WEAK > NONE)",
            "edge_type (SHIELD first)",
            "from_role (STABILITY > HEDGE > LIQUIDITY > VOLATILITY > GAS)",
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
    import json

    print("=" * 60)
    print("v1.2 Rescue Flow Render Adapter - Self Test")
    print("=" * 60)
    print()

    # Test 1: Project STANDARD style
    print("Test 1: Project STANDARD style")
    mock_graph = {
        "v12_flow_status": "AVAILABLE",
        "v12_flow_edges": [
            {
                "from_role": "STABILITY_ROLE",
                "to_role": "VOLATILITY_ROLE",
                "edge_type": "EDGE_SHIELD",
                "rescue_strength": "RESCUE_MEDIUM",
                "conditions": ["REGIME_MEDIUM", "D1_LIQUIDATION"],
            },
            {
                "from_role": "HEDGE_ROLE",
                "to_role": "VOLATILITY_ROLE",
                "edge_type": "EDGE_SHIELD",
                "rescue_strength": "RESCUE_WEAK",
                "conditions": ["REGIME_MEDIUM"],
            },
            {
                "from_role": "GAS_ROLE",
                "to_role": "STABILITY_ROLE",
                "edge_type": "EDGE_NEUTRAL",
                "rescue_strength": "RESCUE_NONE",
                "conditions": ["baseline"],
            },
        ],
    }

    lines_standard = project_rescue_flow_for_render(mock_graph, style="STANDARD")
    print(f"STANDARD style: {len(lines_standard)} lines")
    for line in lines_standard:
        print(f"  {line}")
    print()

    # Test 2: Project DETAILED style
    print("Test 2: Project DETAILED style")
    lines_detailed = project_rescue_flow_for_render(mock_graph, style="DETAILED")
    print(f"DETAILED style: {len(lines_detailed)} lines")
    for line in lines_detailed:
        print(f"  {line}")
    print()

    # Test 3: Project CONCISE style (empty)
    print("Test 3: Project CONCISE style (empty)")
    lines_concise = project_rescue_flow_for_render(mock_graph, style="CONCISE")
    print(f"CONCISE style: {len(lines_concise)} lines")
    print()

    # Test 4: Get adapter info
    print("Test 4: Get adapter info")
    adapter_info = get_rescue_flow_render_adapter_info()
    print(json.dumps(adapter_info, indent=2))
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
