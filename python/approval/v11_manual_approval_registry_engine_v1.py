#!/usr/bin/env python3
"""
PR114: v1.1 Manual Approval Registry Engine v1 (READ-ONLY)

Purpose:
    Apply manual approval events to registry state machine.
    Registry = State Transition Record (not action/instruction).

Constitutional Constraints:
    - READ-ONLY: No execution, no signing, no transaction construction
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - No asset vocabulary: No balance, holdings, portfolio
    - No action vocabulary: No recommend, suggest, optimize
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No should/must vocabulary
    - "APPROVED" is a state label only (not instruction)
    - Defensive: Never raises, returns valid records

Registry Engine Philosophy:
    Engine ≠ Action
    Engine ≠ Instruction
    Engine = State Transition Logic

    Engine applies:
    - Event-driven state transitions
    - Static transition rules (if/elif)
    - Defensive handling (invalid → warnings)

    Engine does NOT:
    - Execute trades
    - Recommend actions
    - Provide instructions
    - Auto-approve
    - Couple APPROVED state to execution

    IMPORTANT: "APPROVED" is a state label only.
    It does NOT mean "execute" or "proceed".

Static Transition Rules (v1 - First Match Wins):

Rule 0 — Defensive Defaults
    - Invalid/missing input → ERROR record with UNREQUESTED state

Rule 1 — If requirement is NOT_REQUIRED
    - Force: state = UNREQUESTED, event = NONE
    - Ignore incoming event
    - Summary: "approval not required. registry remains unrequested."

Rule 2 — REQUEST event
    - Allowed if requirement is REQUIRED or REQUIRED_STRICT
    - Transitions:
      - UNREQUESTED → REQUESTED
      - REQUESTED → REQUESTED (idempotent)
      - APPROVED/REJECTED/EXPIRED → REQUESTED (re-request allowed)

Rule 3 — APPROVE event
    - Only valid if current state is REQUESTED
    - REQUESTED → APPROVED
    - Otherwise: no state change + warning

Rule 4 — REJECT event
    - Only valid if current state is REQUESTED
    - REQUESTED → REJECTED
    - Otherwise: no state change + warning

Rule 5 — EXPIRE event
    - Allowed if current state is REQUESTED
    - REQUESTED → EXPIRED
    - Otherwise: no state change + warning

Rule 6 — NONE event
    - No state change (pure read)
"""

from typing import Any, Dict, Optional, List
from .v11_approval_registry_schema import V11ApprovalRegistrySchema


def apply_approval_event_v1(
    approval_gate_record: Optional[Dict[str, Any]] = None,
    registry_record: Optional[Dict[str, Any]] = None,
    event: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Apply manual approval event to registry state machine.

    Args:
        approval_gate_record: Approval gate record (from PR113)
        registry_record: Optional existing registry record
        event: Event to apply (NONE/REQUEST/APPROVE/REJECT/EXPIRE)

    Returns:
        Updated registry record (always valid)

    Design:
        - Static transition rules (if/elif)
        - Defensive (None/invalid → error record)
        - Warning-only (never raises)
        - Always returns valid records
        - First match wins
    """
    warnings: List[str] = []

    # Rule 0: Defensive - validate approval gate record
    if not isinstance(approval_gate_record, dict):
        return V11ApprovalRegistrySchema.create_error_record(
            error_info="invalid approval gate record type",
            warnings=["Approval gate record must be dict"],
        )

    # Extract requirement from approval gate record
    requirement = approval_gate_record.get("v11_approval_requirement", "REQUIRED_STRICT")

    # Extract current state from registry record (or default to UNREQUESTED)
    current_state = "UNREQUESTED"
    if registry_record is not None and isinstance(registry_record, dict):
        current_state = registry_record.get("v11_registry_state", "UNREQUESTED")

    # Normalize event (None → "NONE")
    if event is None or not isinstance(event, str):
        event = "NONE"

    # Validate event
    if event not in V11ApprovalRegistrySchema.VALID_EVENTS:
        warnings.append(f"Invalid event: {event}. Defaulting to NONE.")
        event = "NONE"

    # Build basis and artifacts
    basis = ["v11_requirement"]
    if registry_record is not None:
        basis.append("v11_registry_state")
    if event != "NONE":
        basis.append("event")

    artifacts = ["pr113_approval_record"]

    # Apply transition rules
    new_state, new_event, summary, trans_warnings = _apply_transition_rules(
        requirement=requirement,
        current_state=current_state,
        event=event,
    )

    warnings.extend(trans_warnings)

    # Create registry record
    return V11ApprovalRegistrySchema.create_registry_record(
        requirement=requirement,
        state=new_state,
        event=new_event,
        summary=summary,
        basis=basis,
        artifacts=artifacts,
        warnings=warnings if warnings else None,
    )


def _apply_transition_rules(
    requirement: str,
    current_state: str,
    event: str,
) -> tuple[str, str, str, List[str]]:
    """
    Apply static transition rules.

    Args:
        requirement: Approval requirement
        current_state: Current approval state
        event: Event to apply

    Returns:
        Tuple of (new_state, new_event, summary, warnings)
    """
    warnings: List[str] = []

    # Rule 1: If requirement is NOT_REQUIRED
    if requirement == "NOT_REQUIRED":
        return (
            "UNREQUESTED",
            "NONE",
            "approval not required. registry remains unrequested.",
            [],
        )

    # Rule 2: REQUEST event
    if event == "REQUEST":
        if requirement in ["REQUIRED", "REQUIRED_STRICT"]:
            # Valid transitions: any state → REQUESTED
            if current_state == "REQUESTED":
                # Idempotent
                return (
                    "REQUESTED",
                    "REQUEST",
                    "approval request recorded. registry state already requested (idempotent).",
                    [],
                )
            else:
                # Transition to REQUESTED
                return (
                    "REQUESTED",
                    "REQUEST",
                    "approval request recorded. registry state set to requested.",
                    [],
                )
        else:
            warnings.append(f"REQUEST event not valid for requirement: {requirement}")
            return (
                current_state,
                "NONE",
                f"approval request ignored. requirement is {requirement}.",
                warnings,
            )

    # Rule 3: APPROVE event
    if event == "APPROVE":
        if current_state == "REQUESTED":
            # Valid transition: REQUESTED → APPROVED
            return (
                "APPROVED",
                "APPROVE",
                "approval state recorded as approved. this is a state label only.",
                [],
            )
        else:
            warnings.append(f"APPROVE event only valid from REQUESTED state. Current: {current_state}")
            return (
                current_state,
                "NONE",
                f"approval event not applied. state is {current_state} (not requested).",
                warnings,
            )

    # Rule 4: REJECT event
    if event == "REJECT":
        if current_state == "REQUESTED":
            # Valid transition: REQUESTED → REJECTED
            return (
                "REJECTED",
                "REJECT",
                "approval request rejected. registry state set to rejected.",
                [],
            )
        else:
            warnings.append(f"REJECT event only valid from REQUESTED state. Current: {current_state}")
            return (
                current_state,
                "NONE",
                f"rejection event not applied. state is {current_state} (not requested).",
                warnings,
            )

    # Rule 5: EXPIRE event
    if event == "EXPIRE":
        if current_state == "REQUESTED":
            # Valid transition: REQUESTED → EXPIRED
            return (
                "EXPIRED",
                "EXPIRE",
                "approval request expired. registry state set to expired.",
                [],
            )
        else:
            warnings.append(f"EXPIRE event only valid from REQUESTED state. Current: {current_state}")
            return (
                current_state,
                "NONE",
                f"expiration event not applied. state is {current_state} (not requested).",
                warnings,
            )

    # Rule 6: NONE event (or unknown event)
    return (
        current_state,
        "NONE",
        f"registry state unchanged. current state: {current_state}.",
        [],
    )


def get_manual_approval_registry_engine_v1_info() -> Dict[str, Any]:
    """
    Get manual approval registry engine v1 information.

    Returns:
        Dict with engine metadata
    """
    return {
        "engine_version": "v1",
        "engine_type": "manual_approval_registry",
        "transition_rules": {
            "rule_0": "Defensive: invalid input → ERROR record",
            "rule_1": "NOT_REQUIRED → force UNREQUESTED + NONE",
            "rule_2": "REQUEST → UNREQUESTED/REQUESTED/APPROVED/REJECTED/EXPIRED → REQUESTED",
            "rule_3": "APPROVE → REQUESTED → APPROVED (only)",
            "rule_4": "REJECT → REQUESTED → REJECTED (only)",
            "rule_5": "EXPIRE → REQUESTED → EXPIRED (only)",
            "rule_6": "NONE → no state change",
        },
        "defensive": True,
        "warning_only": True,
        "no_auto_approve": True,
        "no_time_based_transitions": True,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.1 Manual Approval Registry Engine v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: REQUEST event (UNREQUESTED → REQUESTED)
    print("Test 1: REQUEST event (UNREQUESTED → REQUESTED)")
    approval_gate = {
        "v11_approval_requirement": "REQUIRED",
        "v11_approval_state": "UNREQUESTED",
    }
    registry = apply_approval_event_v1(
        approval_gate_record=approval_gate,
        registry_record=None,
        event="REQUEST",
    )
    print(json.dumps(registry, indent=2))
    print()

    # Test 2: APPROVE event (REQUESTED → APPROVED)
    print("Test 2: APPROVE event (REQUESTED → APPROVED)")
    existing_registry = {
        "v11_registry_state": "REQUESTED",
    }
    registry = apply_approval_event_v1(
        approval_gate_record=approval_gate,
        registry_record=existing_registry,
        event="APPROVE",
    )
    print(json.dumps(registry, indent=2))
    print()

    # Test 3: APPROVE event from wrong state (warning)
    print("Test 3: APPROVE event from wrong state (warning)")
    wrong_state_registry = {
        "v11_registry_state": "UNREQUESTED",
    }
    registry = apply_approval_event_v1(
        approval_gate_record=approval_gate,
        registry_record=wrong_state_registry,
        event="APPROVE",
    )
    print(json.dumps(registry, indent=2))
    print()

    # Test 4: NOT_REQUIRED ignores events
    print("Test 4: NOT_REQUIRED ignores events")
    not_required_gate = {
        "v11_approval_requirement": "NOT_REQUIRED",
    }
    registry = apply_approval_event_v1(
        approval_gate_record=not_required_gate,
        registry_record=None,
        event="REQUEST",
    )
    print(json.dumps(registry, indent=2))
    print()

    # Test 5: REJECT event (REQUESTED → REJECTED)
    print("Test 5: REJECT event (REQUESTED → REJECTED)")
    registry = apply_approval_event_v1(
        approval_gate_record=approval_gate,
        registry_record=existing_registry,
        event="REJECT",
    )
    print(json.dumps(registry, indent=2))
    print()

    # Test 6: EXPIRE event (REQUESTED → EXPIRED)
    print("Test 6: EXPIRE event (REQUESTED → EXPIRED)")
    registry = apply_approval_event_v1(
        approval_gate_record=approval_gate,
        registry_record=existing_registry,
        event="EXPIRE",
    )
    print(json.dumps(registry, indent=2))
    print()

    # Test 7: Idempotent REQUEST
    print("Test 7: Idempotent REQUEST (REQUESTED → REQUESTED)")
    registry = apply_approval_event_v1(
        approval_gate_record=approval_gate,
        registry_record=existing_registry,
        event="REQUEST",
    )
    print(json.dumps(registry, indent=2))
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
