#!/usr/bin/env python3
"""
PR129: v1.2 Distortion Detector Engine v1 (READ-ONLY)

Purpose:
    Classify distortion types D1-D5 from existing pipeline artifacts.
    Static, deterministic, label-based only (no numeric thresholds).

Rules (first-match-wins):
    0. Defensive: Invalid input → ERROR + UNCLASSIFIED
    1. REGIME_CRITICAL → D0_NONE
    2. Event activity present → D4_EVENT_DISTORTION
    3. Correlation drift + DRIFT_MEDIUM+ → D5_CORRELATION_DISTORTION
    4. Low liquidity + decrease → D3_BOOK_HOLLOWING
    5. Decrease + event present → D1_LIQUIDATION
    6. Stable liquidity + no events + low drift → D2_RANGE_STICKINESS
    7. Default → UNCLASSIFIED

Distortion ≠ Signal ≠ Recommendation. Output is a label only.
"""

from typing import Any, Dict, Optional

from .v12_distortion_schema import (
    V12DistortionSchema,
    D0_NONE,
    D1_LIQUIDATION,
    D2_RANGE_STICKINESS,
    D3_BOOK_HOLLOWING,
    D4_EVENT_DISTORTION,
    D5_CORRELATION_DISTORTION,
    DISTORTION_UNCLASSIFIED,
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


def _safe_get_bool(d: Optional[Dict[str, Any]], key: str, default: bool = False) -> bool:
    """
    Safely get boolean value from dict.

    Args:
        d: Dictionary (may be None)
        key: Key to get
        default: Default value

    Returns:
        Boolean value or default
    """
    val = _safe_get(d, key, default)
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.upper() in ["TRUE", "YES", "PRESENT"]
    return default


def detect_distortion_v1(
    regime_record: Optional[Dict[str, Any]] = None,
    analytics_record: Optional[Dict[str, Any]] = None,
    drift_record: Optional[Dict[str, Any]] = None,
    bridge_record: Optional[Dict[str, Any]] = None,
    boundary_record: Optional[Dict[str, Any]] = None,
    monitor_record: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Detect distortion type from pipeline artifacts.

    Args:
        regime_record: PR110 regime record
        analytics_record: PR109 analytics record
        drift_record: PR120 drift record
        bridge_record: PR108 bridge record
        boundary_record: PR91 boundary record (unused, for future)
        monitor_record: PR126 monitor record (unused, for future)

    Returns:
        Distortion record (always valid, ERROR on failure)
    """
    try:
        basis = []
        artifacts = []

        # Extract labels (defensive extraction, no assumptions)
        regime_level = _safe_get(regime_record, "v11_regime_level", "UNCLASSIFIED")
        if regime_record:
            basis.append("v11_regime_level")
            artifacts.append("v110_regime")

        drift_label = _safe_get(drift_record, "v10_drift_label", "UNCLASSIFIED")
        if drift_record:
            basis.append("v10_drift_label")
            artifacts.append("v120_drift")

        # Event activity (from analytics or bridge)
        event_activity_present = _safe_get_bool(analytics_record, "event_activity_present", False)
        if analytics_record and "event_activity_present" in analytics_record:
            basis.append("event_activity_present")
            artifacts.append("v109_analytics")

        # If not in analytics, check bridge
        if not event_activity_present and bridge_record:
            bridge_event = _safe_get(bridge_record, "event_activity", "NONE")
            event_activity_present = bridge_event != "NONE"
            if "event_activity" in bridge_record:
                basis.append("event_activity")
                artifacts.append("v108_bridge")

        # Liquidity regime (from analytics)
        liquidity_regime = _safe_get(analytics_record, "liquidity_regime", "UNCLASSIFIED")
        if analytics_record and "liquidity_regime" in analytics_record:
            basis.append("liquidity_regime")

        # Object dynamics (from analytics)
        object_dynamics = _safe_get(analytics_record, "object_dynamics", "UNCLASSIFIED")
        if analytics_record and "object_dynamics" in analytics_record:
            basis.append("object_dynamics")

        # Vocabulary family presence (from drift)
        vocab_family_presence = _safe_get(drift_record, "v10_vocab_family_presence", {})
        correlation_present = False
        if isinstance(vocab_family_presence, dict):
            correlation_present = _safe_get_bool(vocab_family_presence, "CORRELATION", False)
            if correlation_present:
                basis.append("v10_vocab_family_presence")

        # -----------------------------
        # Rule 0: Defensive (already handled by try/except)
        # -----------------------------

        # -----------------------------
        # Rule 1: REGIME_CRITICAL → D0_NONE
        # -----------------------------
        if regime_level == "REGIME_CRITICAL":
            return V12DistortionSchema.create_distortion_record(
                distortion_type=D0_NONE,
                basis=basis,
                artifacts=artifacts,
            )

        # -----------------------------
        # Rule 2: Event activity present → D4_EVENT_DISTORTION
        # -----------------------------
        if event_activity_present:
            # Check if this is also a liquidation signal (decrease + event)
            # If so, continue to D1 check
            if object_dynamics == "DECREASE":
                # D1 has priority (forced events + decrease)
                # Continue to Rule 5
                pass
            else:
                # Pure event distortion
                return V12DistortionSchema.create_distortion_record(
                    distortion_type=D4_EVENT_DISTORTION,
                    basis=basis,
                    artifacts=artifacts,
                )

        # -----------------------------
        # Rule 3: Correlation drift + DRIFT_MEDIUM+ → D5_CORRELATION_DISTORTION
        # -----------------------------
        if correlation_present and drift_label in ["DRIFT_MEDIUM", "DRIFT_HIGH", "DRIFT_CRITICAL"]:
            return V12DistortionSchema.create_distortion_record(
                distortion_type=D5_CORRELATION_DISTORTION,
                basis=basis,
                artifacts=artifacts,
            )

        # -----------------------------
        # Rule 4: Low liquidity + decrease → D3_BOOK_HOLLOWING
        # -----------------------------
        if liquidity_regime == "LOW" and object_dynamics == "DECREASE":
            # Check if event is also present (then it's D1, not D3)
            if event_activity_present:
                # D1 has priority (forced events)
                # Continue to Rule 5
                pass
            else:
                return V12DistortionSchema.create_distortion_record(
                    distortion_type=D3_BOOK_HOLLOWING,
                    basis=basis,
                    artifacts=artifacts,
                )

        # -----------------------------
        # Rule 5: Decrease + event present → D1_LIQUIDATION
        # -----------------------------
        if object_dynamics == "DECREASE" and event_activity_present:
            return V12DistortionSchema.create_distortion_record(
                distortion_type=D1_LIQUIDATION,
                basis=basis,
                artifacts=artifacts,
            )

        # -----------------------------
        # Rule 6: Stable liquidity + no events + low drift → D2_RANGE_STICKINESS
        # -----------------------------
        if (
            liquidity_regime in ["MEDIUM", "HIGH"]
            and not event_activity_present
            and drift_label in ["DRIFT_NONE", "DRIFT_LOW", "UNCLASSIFIED"]
        ):
            return V12DistortionSchema.create_distortion_record(
                distortion_type=D2_RANGE_STICKINESS,
                basis=basis,
                artifacts=artifacts,
            )

        # -----------------------------
        # Rule 7: Default → UNCLASSIFIED
        # -----------------------------
        return V12DistortionSchema.create_distortion_record(
            distortion_type=DISTORTION_UNCLASSIFIED,
            basis=basis,
            artifacts=artifacts,
        )

    except Exception as e:
        return V12DistortionSchema.create_error_record(f"exception: {type(e).__name__}")


def get_detector_v1_info() -> Dict[str, Any]:
    """
    Get detector v1 information.

    Returns:
        Dict with detector metadata
    """
    return {
        "detector_version": "v1",
        "detector_type": "distortion_classification",
        "input_schema": "regime + analytics + drift + bridge",
        "output_schema": "v12_distortion",
        "classification_rules": [
            "REGIME_CRITICAL → D0_NONE",
            "event_activity_present → D4_EVENT_DISTORTION",
            "correlation_present + drift_medium+ → D5_CORRELATION_DISTORTION",
            "low_liquidity + decrease → D3_BOOK_HOLLOWING",
            "decrease + event_present → D1_LIQUIDATION",
            "stable_liquidity + no_events + low_drift → D2_RANGE_STICKINESS",
            "default → UNCLASSIFIED",
        ],
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-evaluative",
            "non-prescriptive",
            "deterministic",
            "defensive",
            "no_distortion_coupling",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.2 Distortion Detector Engine v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: Invalid input → ERROR
    print("Test 1: Invalid input → ERROR")
    result1 = detect_distortion_v1(None, None, None, None)
    print(f"Status: {result1['v12_distortion_status']}")
    print(f"Type: {result1['v12_distortion_type']}")
    print()

    # Test 2: CRITICAL → D0_NONE
    print("Test 2: CRITICAL → D0_NONE")
    result2 = detect_distortion_v1(
        regime_record={"v11_regime_level": "REGIME_CRITICAL"},
    )
    print(f"Type: {result2['v12_distortion_type']}")
    print(f"Summary: {result2['v12_distortion_summary']}")
    print()

    # Test 3: Event present → D4
    print("Test 3: Event present → D4")
    result3 = detect_distortion_v1(
        analytics_record={"event_activity_present": True},
    )
    print(f"Type: {result3['v12_distortion_type']}")
    print()

    # Test 4: Correlation + drift → D5
    print("Test 4: Correlation + drift → D5")
    result4 = detect_distortion_v1(
        drift_record={
            "v10_drift_label": "DRIFT_MEDIUM",
            "v10_vocab_family_presence": {"CORRELATION": True},
        },
    )
    print(f"Type: {result4['v12_distortion_type']}")
    print()

    # Test 5: Low liquidity + decrease → D3
    print("Test 5: Low liquidity + decrease → D3")
    result5 = detect_distortion_v1(
        analytics_record={
            "liquidity_regime": "LOW",
            "object_dynamics": "DECREASE",
            "event_activity_present": False,
        },
    )
    print(f"Type: {result5['v12_distortion_type']}")
    print()

    # Test 6: Decrease + event → D1
    print("Test 6: Decrease + event → D1")
    result6 = detect_distortion_v1(
        analytics_record={
            "object_dynamics": "DECREASE",
            "event_activity_present": True,
        },
    )
    print(f"Type: {result6['v12_distortion_type']}")
    print()

    # Test 7: Stable + no events + low drift → D2
    print("Test 7: Stable + no events + low drift → D2")
    result7 = detect_distortion_v1(
        analytics_record={
            "liquidity_regime": "MEDIUM",
            "event_activity_present": False,
        },
        drift_record={"v10_drift_label": "DRIFT_LOW"},
    )
    print(f"Type: {result7['v12_distortion_type']}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
