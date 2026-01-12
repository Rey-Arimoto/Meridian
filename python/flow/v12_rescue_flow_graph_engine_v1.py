#!/usr/bin/env python3
"""
PR137: v1.2 Rescue Flow Graph Engine v1 (READ-ONLY)

Purpose:
    Build READ-ONLY graph artifact describing ROLE-to-ROLE rescue structure
    using label-only edges from PR135 EdgeType and PR136 RescueStrength.

Flow Graph = Structural mapping (not action, not instruction)

Canonical Rescue Map (v1):
    - STABILITY_ROLE -> LIQUIDITY_ROLE (EDGE_SHIELD)
    - STABILITY_ROLE -> VOLATILITY_ROLE (EDGE_SHIELD)
    - HEDGE_ROLE -> VOLATILITY_ROLE (EDGE_SHIELD)
    - LIQUIDITY_ROLE -> VOLATILITY_ROLE (EDGE_NEUTRAL)
    - GAS_ROLE -> ALL_ROLES (EDGE_NEUTRAL)

Non-rescue constraints:
    - EDGE_AMPLIFY edges must have RESCUE_NONE (amplify ≠ rescue)
    - EDGE_LEAK edges must have RESCUE_NONE (leak ≠ rescue)

Rescue Strength Assignment:
    - Match rescue_strength_records by (role, regime, distortion, edge_type)
    - Conservative defaults if not provided:
      - REGIME_MEDIUM + SHIELD from STABILITY/HEDGE → RESCUE_MEDIUM
      - REGIME_LOW/HIGH → RESCUE_WEAK for SHIELD
      - Default → RESCUE_NONE
"""

from typing import Any, Dict, List, Optional

from .v12_rescue_flow_graph_schema import (
    V12RescueFlowGraphSchema,
    FLOW_MODE_ON,
    FLOW_MODE_OFF,
)


# Role constants (from PR130)
ROLE_GAS = "GAS_ROLE"
ROLE_STABILITY = "STABILITY_ROLE"
ROLE_LIQUIDITY = "LIQUIDITY_ROLE"
ROLE_VOLATILITY = "VOLATILITY_ROLE"
ROLE_HEDGE = "HEDGE_ROLE"

ALL_ROLES = [ROLE_GAS, ROLE_STABILITY, ROLE_LIQUIDITY, ROLE_VOLATILITY, ROLE_HEDGE]

# Edge type constants (from PR135)
EDGE_NONE = "EDGE_NONE"
EDGE_AMPLIFY = "EDGE_AMPLIFY"
EDGE_SHIELD = "EDGE_SHIELD"
EDGE_LEAK = "EDGE_LEAK"
EDGE_NEUTRAL = "EDGE_NEUTRAL"

# Rescue strength constants (from PR136)
RESCUE_NONE = "RESCUE_NONE"
RESCUE_WEAK = "RESCUE_WEAK"
RESCUE_MEDIUM = "RESCUE_MEDIUM"
RESCUE_STRONG = "RESCUE_STRONG"


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


def _get_canonical_rescue_map() -> List[Dict[str, Any]]:
    """
    Get canonical rescue map (v1).

    Returns:
        List of canonical edge definitions
    """
    canonical_map = [
        # STABILITY provides shielding to LIQUIDITY
        {
            "from_role": ROLE_STABILITY,
            "to_role": ROLE_LIQUIDITY,
            "edge_type": EDGE_SHIELD,
            "note": "Stability provides shielding support to liquidity role",
        },
        # STABILITY provides shielding to VOLATILITY
        {
            "from_role": ROLE_STABILITY,
            "to_role": ROLE_VOLATILITY,
            "edge_type": EDGE_SHIELD,
            "note": "Stability provides shielding support to volatility role",
        },
        # HEDGE provides shielding to VOLATILITY
        {
            "from_role": ROLE_HEDGE,
            "to_role": ROLE_VOLATILITY,
            "edge_type": EDGE_SHIELD,
            "note": "Hedge provides defensive buffer to volatility role",
        },
        # LIQUIDITY provides neutral support to VOLATILITY
        {
            "from_role": ROLE_LIQUIDITY,
            "to_role": ROLE_VOLATILITY,
            "edge_type": EDGE_NEUTRAL,
            "note": "Liquidity can stabilize distortions, not always rescue",
        },
    ]

    # GAS provides neutral support to ALL roles
    for to_role in [ROLE_STABILITY, ROLE_LIQUIDITY, ROLE_VOLATILITY, ROLE_HEDGE]:
        canonical_map.append({
            "from_role": ROLE_GAS,
            "to_role": to_role,
            "edge_type": EDGE_NEUTRAL,
            "note": "Gas provides operational enabler support",
        })

    return canonical_map


def _determine_rescue_strength(
    from_role: str,
    to_role: str,
    edge_type: str,
    regime_level: Optional[str],
    distortion_type: Optional[str],
    rescue_strength_records: Optional[List[Dict[str, Any]]],
) -> str:
    """
    Determine rescue strength for an edge.

    Args:
        from_role: Source ROLE
        to_role: Target ROLE
        edge_type: Edge type
        regime_level: Regime level (optional)
        distortion_type: Distortion type (optional)
        rescue_strength_records: PR136 rescue strength records (optional)

    Returns:
        Rescue strength label
    """
    # Rule 1: AMPLIFY/LEAK edges always get RESCUE_NONE
    if edge_type in [EDGE_AMPLIFY, EDGE_LEAK]:
        return RESCUE_NONE

    # Rule 2: Try to match from rescue_strength_records if provided
    if rescue_strength_records:
        # Find matching record by role + regime + edge_type
        for record in rescue_strength_records:
            record_role = _safe_get(record, "v12_rescue_role")
            record_regime = _safe_get(record, "v12_rescue_regime")
            record_edge = _safe_get(record, "v12_rescue_edge_type")
            record_strength = _safe_get(record, "v12_rescue_strength", RESCUE_NONE)

            # Match by from_role (rescue provider) + regime + edge_type
            if (record_role == from_role and
                record_regime == regime_level and
                record_edge == edge_type):
                return record_strength

    # Rule 3: Conservative defaults based on regime + edge_type + role
    if not regime_level:
        return RESCUE_NONE

    # REGIME_MEDIUM + SHIELD from STABILITY/HEDGE → RESCUE_MEDIUM
    if (regime_level == "REGIME_MEDIUM" and
        edge_type == EDGE_SHIELD and
        from_role in [ROLE_STABILITY, ROLE_HEDGE]):
        return RESCUE_MEDIUM

    # REGIME_HIGH/LOW + SHIELD → RESCUE_WEAK
    if regime_level in ["REGIME_HIGH", "REGIME_LOW"] and edge_type == EDGE_SHIELD:
        return RESCUE_WEAK

    # Default
    return RESCUE_NONE


def _get_conditions(
    regime_level: Optional[str],
    distortion_type: Optional[str],
    edge_type: str,
) -> List[str]:
    """
    Get label-only conditions for an edge.

    Args:
        regime_level: Regime level
        distortion_type: Distortion type
        edge_type: Edge type

    Returns:
        List of condition labels
    """
    conditions = []

    if regime_level:
        conditions.append(regime_level)
    if edge_type:
        conditions.append(edge_type)
    if distortion_type:
        conditions.append(distortion_type)

    return conditions if conditions else ["baseline"]


def build_rescue_flow_graph_v1(
    regime_record: Optional[Dict[str, Any]] = None,
    role_catalog_record: Optional[Dict[str, Any]] = None,
    distortion_catalog_record: Optional[Dict[str, Any]] = None,
    edge_catalog_record: Optional[Dict[str, Any]] = None,
    rescue_strength_records: Optional[List[Dict[str, Any]]] = None,
    contribution_records: Optional[List[Dict[str, Any]]] = None,
    constraint_binding_record: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build rescue flow graph from canonical map + inputs.

    Args:
        regime_record: PR110 regime record (optional)
        role_catalog_record: Role catalog (optional)
        distortion_catalog_record: Distortion catalog (optional)
        edge_catalog_record: Edge catalog (optional)
        rescue_strength_records: PR136 rescue strength records (optional)
        contribution_records: PR131 contribution records (optional)
        constraint_binding_record: PR132 constraint binding (optional)

    Returns:
        Rescue flow graph record (always AVAILABLE, defensive)
    """
    try:
        basis = []

        # Extract inputs
        regime_level = _safe_get(regime_record, "v11_regime_level")
        if regime_record:
            basis.append("v11_regime_level")

        distortion_type = _safe_get(distortion_catalog_record, "v12_distortion_type")
        if distortion_catalog_record:
            basis.append("v12_distortion_type")

        if rescue_strength_records:
            basis.append("v12_rescue_strength_records")

        # Graph nodes: all 5 roles by default
        nodes = ALL_ROLES.copy()

        # Build edges from canonical map
        canonical_map = _get_canonical_rescue_map()
        edges = []

        for canonical_edge in canonical_map:
            from_role = canonical_edge["from_role"]
            to_role = canonical_edge["to_role"]
            edge_type = canonical_edge["edge_type"]
            note = canonical_edge["note"]

            # Determine rescue strength
            rescue_strength = _determine_rescue_strength(
                from_role=from_role,
                to_role=to_role,
                edge_type=edge_type,
                regime_level=regime_level,
                distortion_type=distortion_type,
                rescue_strength_records=rescue_strength_records,
            )

            # Get conditions
            conditions = _get_conditions(
                regime_level=regime_level,
                distortion_type=distortion_type,
                edge_type=edge_type,
            )

            # Create edge object
            edge = V12RescueFlowGraphSchema.create_edge_object(
                from_role=from_role,
                to_role=to_role,
                edge_type=edge_type,
                rescue_strength=rescue_strength,
                conditions=conditions,
                note=note,
            )
            edges.append(edge)

        # Determine flow mode
        # Flow is ON if we have at least one non-NONE rescue edge
        has_rescue = any(edge["rescue_strength"] != RESCUE_NONE for edge in edges)
        flow_mode = FLOW_MODE_ON if has_rescue else FLOW_MODE_OFF

        # Create flow graph record
        return V12RescueFlowGraphSchema.create_flow_graph_record(
            flow_mode=flow_mode,
            nodes=nodes,
            edges=edges,
            basis=basis,
        )

    except Exception as e:
        # Defensive: never raise, return error record
        return V12RescueFlowGraphSchema.create_error_record(
            f"exception: {type(e).__name__}",
        )


def get_rescue_flow_graph_engine_v1_info() -> Dict[str, Any]:
    """
    Get rescue flow graph engine v1 information.

    Returns:
        Dict with engine metadata
    """
    return {
        "engine_version": "v1",
        "engine_type": "rescue_flow_graph",
        "input_schema": "regime + roles + distortion + edge + rescue_strength (all optional)",
        "output_schema": "v12_flow",
        "graph_structure": {
            "nodes": "5 ROLE labels (GAS/STABILITY/LIQUIDITY/VOLATILITY/HEDGE)",
            "edges": "canonical rescue map + edge_type + rescue_strength labels",
        },
        "canonical_map": [
            "STABILITY -> LIQUIDITY (EDGE_SHIELD)",
            "STABILITY -> VOLATILITY (EDGE_SHIELD)",
            "HEDGE -> VOLATILITY (EDGE_SHIELD)",
            "LIQUIDITY -> VOLATILITY (EDGE_NEUTRAL)",
            "GAS -> ALL_ROLES (EDGE_NEUTRAL)",
        ],
        "constraints": [
            "EDGE_AMPLIFY → RESCUE_NONE (amplify ≠ rescue)",
            "EDGE_LEAK → RESCUE_NONE (leak ≠ rescue)",
        ],
        "rescue_strength_rules": [
            "Match from PR136 rescue_strength_records if provided",
            "REGIME_MEDIUM + SHIELD + STABILITY/HEDGE → RESCUE_MEDIUM (default)",
            "REGIME_HIGH/LOW + SHIELD → RESCUE_WEAK (default)",
            "Default → RESCUE_NONE",
        ],
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-prescriptive",
            "no_numeric_patterns",
            "no_token_literals",
            "no_flow_coupling",
            "deterministic",
            "defensive",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.2 Rescue Flow Graph Engine v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: Build graph with no inputs (defensive)
    print("Test 1: Build graph with no inputs (defensive)")
    result1 = build_rescue_flow_graph_v1()
    print(f"Flow mode: {result1['v12_flow_mode']}")
    print(f"Nodes: {len(result1['v12_flow_nodes'])}")
    print(f"Edges: {len(result1['v12_flow_edges'])}")
    print(f"Summary: {result1['v12_flow_summary']}")
    print()

    # Test 2: Build graph with REGIME_MEDIUM
    print("Test 2: Build graph with REGIME_MEDIUM")
    result2 = build_rescue_flow_graph_v1(
        regime_record={"v11_regime_level": "REGIME_MEDIUM"},
        distortion_catalog_record={"v12_distortion_type": "D1_LIQUIDATION"},
    )
    print(f"Flow mode: {result2['v12_flow_mode']}")
    print(f"Nodes: {len(result2['v12_flow_nodes'])}")
    print(f"Edges: {len(result2['v12_flow_edges'])}")

    # Show shield edges with MEDIUM strength
    shield_edges = [e for e in result2['v12_flow_edges']
                    if e['edge_type'] == 'EDGE_SHIELD' and e['rescue_strength'] == 'RESCUE_MEDIUM']
    print(f"SHIELD edges with RESCUE_MEDIUM: {len(shield_edges)}")
    if shield_edges:
        print(f"  Example: {shield_edges[0]['from_role']} -> {shield_edges[0]['to_role']}")
    print()

    # Test 3: Get engine info
    print("Test 3: Get engine info")
    engine_info = get_rescue_flow_graph_engine_v1_info()
    print(json.dumps(engine_info, indent=2))
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
