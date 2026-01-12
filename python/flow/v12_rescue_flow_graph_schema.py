#!/usr/bin/env python3
"""
PR137: v1.2 Rescue Flow Graph Schema (READ-ONLY)

Purpose:
    Define rescue flow graph schema for ROLE-to-ROLE structural mapping.
    Flow graph = structural mapping, NOT action, NOT instruction.

Constitutional Constraints:
    - READ-ONLY: No execution, no recommendations
    - Non-prescriptive: Use observational language
    - No numeric patterns: No digits, %
    - No token literals: No SUI, USDC, BTC, ETH
    - No flow coupling: No "this edge means execute"

Graph Structure:
    - Nodes: ROLE labels only (GAS/STABILITY/LIQUIDITY/VOLATILITY/HEDGE)
    - Edges: Label-only connections with edge_type + rescue_strength
    - Edges are structural annotations, not instructions

Flow Graph ≠ Action
Flow Graph = Structural mapping
"""

from typing import Any, Dict, List, Optional


# Flow mode constants
FLOW_MODE_ON = "ON"
FLOW_MODE_OFF = "OFF"

# Flow status constants
FLOW_STATUS_AVAILABLE = "AVAILABLE"
FLOW_STATUS_ERROR = "ERROR"

# Graph type constant
FLOW_GRAPH_TYPE_RESCUE = "RESCUE_FLOW_GRAPH"


class V12RescueFlowGraphSchema:
    """
    v1.2 Rescue Flow Graph schema class.

    Defines structural ROLE-to-ROLE rescue flow graph.
    """

    @staticmethod
    def create_flow_graph_record(
        flow_mode: str,
        nodes: List[str],
        edges: List[Dict[str, Any]],
        basis: List[str],
        warnings: Optional[List[str]] = None,
        artifacts: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a rescue flow graph record.

        Args:
            flow_mode: Flow mode (ON/OFF)
            nodes: List of ROLE labels (nodes in graph)
            edges: List of edge objects with from_role, to_role, edge_type, rescue_strength
            basis: List of basis field names
            warnings: Optional list of warnings
            artifacts: Optional list of artifact labels

        Returns:
            Rescue flow graph record
        """
        # Generate non-prescriptive summary
        num_nodes = len(nodes)
        num_edges = len(edges)

        summary = f"Rescue flow graph available. {num_nodes} role nodes and {num_edges} rescue edges assembled as structural mapping."

        record = {
            "v12_flow_mode": flow_mode,
            "v12_flow_status": FLOW_STATUS_AVAILABLE,
            "v12_flow_graph_type": FLOW_GRAPH_TYPE_RESCUE,
            "v12_flow_summary": summary,
            "v12_flow_nodes": nodes,
            "v12_flow_edges": edges,
            "v12_flow_basis": basis,
        }

        # Add optional fields
        if warnings:
            record["v12_flow_warnings"] = warnings
        if artifacts:
            record["v12_flow_artifacts"] = artifacts

        return record

    @staticmethod
    def create_edge_object(
        from_role: str,
        to_role: str,
        edge_type: str,
        rescue_strength: str,
        conditions: List[str],
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Create an edge object for the flow graph.

        Args:
            from_role: Source ROLE label
            to_role: Target ROLE label
            edge_type: PR135 edge type label (EDGE_SHIELD/AMPLIFY/NEUTRAL/LEAK)
            rescue_strength: PR136 rescue strength label (RESCUE_NONE/WEAK/MEDIUM/STRONG)
            conditions: Label-only conditions (e.g., ["REGIME_MEDIUM", "D1_LIQUIDATION"])
            note: Short non-prescriptive description

        Returns:
            Edge object
        """
        return {
            "from_role": from_role,
            "to_role": to_role,
            "edge_type": edge_type,
            "rescue_strength": rescue_strength,
            "conditions": conditions,
            "note": note,
        }

    @staticmethod
    def create_error_record(
        error_message: str,
    ) -> Dict[str, Any]:
        """
        Create an error record (defensive: returns empty graph, not ERROR).

        Args:
            error_message: Error message

        Returns:
            Error record with empty graph
        """
        return {
            "v12_flow_mode": FLOW_MODE_OFF,
            "v12_flow_status": FLOW_STATUS_AVAILABLE,
            "v12_flow_graph_type": FLOW_GRAPH_TYPE_RESCUE,
            "v12_flow_summary": f"Rescue flow graph unavailable (defensive: {error_message}).",
            "v12_flow_nodes": [],
            "v12_flow_edges": [],
            "v12_flow_basis": [],
            "v12_flow_warnings": [error_message],
        }


def get_flow_schema_info() -> Dict[str, Any]:
    """
    Get rescue flow graph schema metadata.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.2",
        "schema_type": "rescue_flow_graph",
        "prefix": "v12_flow_",
        "graph_type": FLOW_GRAPH_TYPE_RESCUE,
        "flow_modes": [FLOW_MODE_ON, FLOW_MODE_OFF],
        "flow_statuses": [FLOW_STATUS_AVAILABLE, FLOW_STATUS_ERROR],
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-prescriptive",
            "no_numeric_patterns",
            "no_token_literals",
            "no_flow_coupling",
            "defensive",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.2 Rescue Flow Graph Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create flow graph record
    print("Test 1: Create flow graph record")

    # Create sample edges
    edge1 = V12RescueFlowGraphSchema.create_edge_object(
        from_role="STABILITY_ROLE",
        to_role="VOLATILITY_ROLE",
        edge_type="EDGE_SHIELD",
        rescue_strength="RESCUE_MEDIUM",
        conditions=["REGIME_MEDIUM", "D1_LIQUIDATION"],
        note="Stability provides shielding support to volatility role",
    )

    edge2 = V12RescueFlowGraphSchema.create_edge_object(
        from_role="HEDGE_ROLE",
        to_role="VOLATILITY_ROLE",
        edge_type="EDGE_SHIELD",
        rescue_strength="RESCUE_WEAK",
        conditions=["REGIME_MEDIUM"],
        note="Hedge provides defensive buffer",
    )

    nodes = ["STABILITY_ROLE", "HEDGE_ROLE", "VOLATILITY_ROLE", "LIQUIDITY_ROLE", "GAS_ROLE"]
    edges = [edge1, edge2]

    record = V12RescueFlowGraphSchema.create_flow_graph_record(
        flow_mode=FLOW_MODE_ON,
        nodes=nodes,
        edges=edges,
        basis=["v11_regime_level", "v12_role_carrier_role_type", "v12_distortion_type"],
    )
    print(json.dumps(record, indent=2))
    print()

    # Test 2: Create error record
    print("Test 2: Create error record")
    error_record = V12RescueFlowGraphSchema.create_error_record(
        error_message="invalid inputs: regime_level must be classified.",
    )
    print(json.dumps(error_record, indent=2))
    print()

    # Test 3: Get schema info
    print("Test 3: Get schema info")
    schema_info = get_flow_schema_info()
    print(json.dumps(schema_info, indent=2))
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
