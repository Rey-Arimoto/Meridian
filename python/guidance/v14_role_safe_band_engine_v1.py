#!/usr/bin/env python3
"""
PR144: v1.4 Role Safe Band Engine v1 (READ-ONLY)

Purpose:
    Build role safe band guidance from portfolio snapshot and regime record.
    This is NOT advice, NOT instruction, NOT recommendation.

API:
    build_role_safe_band_guidance_v1(portfolio_snapshot, regime_record) -> dict

Behavior:
    - Extract regime label from regime_record
    - For each role, bucket current ratio and compare to safe band
    - Determine status: BELOW_SAFE / WITHIN_SAFE / ABOVE_SAFE / UNKNOWN
    - Output bucket labels only (no raw numbers)
    - Defensive: invalid input → valid ERROR record

Safe Band Table (Static, Deterministic):
    Maps (regime × role) to safe band bucket.

    CRITICAL regime:
        - VOLATILITY_ROLE → BAND_ZERO (no volatility)
        - Others → higher bands (stability/liquidity/hedge/gas)

    HIGH regime:
        - VOLATILITY_ROLE → BAND_LOW (constrained)
        - Others → mid-high bands

    MEDIUM regime:
        - VOLATILITY_ROLE → BAND_MEDIUM (allowed but bounded)
        - Others → balanced bands

    LOW regime:
        - VOLATILITY_ROLE → BAND_MEDIUM (moderate)
        - Others → moderate bands

Constitutional Constraints:
    - READ-ONLY: No execution, no trading
    - Non-prescriptive: No should/must/recommend
    - No trading verbs: No buy/sell/swap/execute
    - No token literals: No SUI/USDC/BTC/ETH
    - No numeric values in output text: Bucket labels only
    - Defensive: Invalid input → valid ERROR record
    - Warning-only: Never raises exceptions
"""

from typing import Any, Dict, List, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from guidance.v14_role_safe_band_schema import (
    V14RoleSafeBandSchema,
    GUIDANCE_VERSION_V1_4,
    GUIDANCE_STATUS_AVAILABLE,
    GUIDANCE_STATUS_ERROR,
    GUIDANCE_MODE_READ_ONLY,
    BAND_ZERO,
    BAND_MINIMAL,
    BAND_LOW,
    BAND_MEDIUM,
    BAND_HIGH,
    BAND_MAXIMAL,
    BAND_UNKNOWN,
    RATIO_ZERO,
    RATIO_MINIMAL,
    RATIO_LOW,
    RATIO_MEDIUM,
    RATIO_HIGH,
    RATIO_MAXIMAL,
    RATIO_UNKNOWN,
    STATUS_BELOW_SAFE,
    STATUS_WITHIN_SAFE,
    STATUS_ABOVE_SAFE,
    STATUS_UNKNOWN,
    ROLE_VOLATILITY,
    ROLE_LIQUIDITY,
    ROLE_STABILITY,
    ROLE_HEDGE,
    ROLE_GAS,
    REGIME_LOW,
    REGIME_MEDIUM,
    REGIME_HIGH,
    REGIME_CRITICAL,
    REGIME_UNKNOWN,
)


# Internal bucket thresholds (not exposed in output)
# Ratio buckets (0.0 to 1.0)
RATIO_THRESHOLDS = {
    RATIO_ZERO: (0.0, 0.01),      # 0-1%
    RATIO_MINIMAL: (0.01, 0.10),  # 1-10%
    RATIO_LOW: (0.10, 0.25),      # 10-25%
    RATIO_MEDIUM: (0.25, 0.50),   # 25-50%
    RATIO_HIGH: (0.50, 0.75),     # 50-75%
    RATIO_MAXIMAL: (0.75, 1.01),  # 75-100%
}

# Safe band thresholds (0.0 to 1.0)
BAND_THRESHOLDS = {
    BAND_ZERO: (0.0, 0.01),       # 0-1%
    BAND_MINIMAL: (0.01, 0.10),   # 1-10%
    BAND_LOW: (0.10, 0.25),       # 10-25%
    BAND_MEDIUM: (0.25, 0.50),    # 25-50%
    BAND_HIGH: (0.50, 0.75),      # 50-75%
    BAND_MAXIMAL: (0.75, 1.01),   # 75-100%
}

# Safe band table: (regime, role) → safe_band_bucket
# This is static and deterministic
SAFE_BAND_TABLE = {
    # CRITICAL regime: minimize volatility, maximize stability/liquidity
    (REGIME_CRITICAL, ROLE_VOLATILITY): BAND_ZERO,
    (REGIME_CRITICAL, ROLE_LIQUIDITY): BAND_HIGH,
    (REGIME_CRITICAL, ROLE_STABILITY): BAND_HIGH,
    (REGIME_CRITICAL, ROLE_HEDGE): BAND_MEDIUM,
    (REGIME_CRITICAL, ROLE_GAS): BAND_MINIMAL,

    # HIGH regime: constrain volatility
    (REGIME_HIGH, ROLE_VOLATILITY): BAND_LOW,
    (REGIME_HIGH, ROLE_LIQUIDITY): BAND_MEDIUM,
    (REGIME_HIGH, ROLE_STABILITY): BAND_MEDIUM,
    (REGIME_HIGH, ROLE_HEDGE): BAND_MEDIUM,
    (REGIME_HIGH, ROLE_GAS): BAND_MINIMAL,

    # MEDIUM regime: allow volatility but bounded
    (REGIME_MEDIUM, ROLE_VOLATILITY): BAND_MEDIUM,
    (REGIME_MEDIUM, ROLE_LIQUIDITY): BAND_MEDIUM,
    (REGIME_MEDIUM, ROLE_STABILITY): BAND_LOW,
    (REGIME_MEDIUM, ROLE_HEDGE): BAND_LOW,
    (REGIME_MEDIUM, ROLE_GAS): BAND_MINIMAL,

    # LOW regime: moderate volatility
    (REGIME_LOW, ROLE_VOLATILITY): BAND_MEDIUM,
    (REGIME_LOW, ROLE_LIQUIDITY): BAND_LOW,
    (REGIME_LOW, ROLE_STABILITY): BAND_LOW,
    (REGIME_LOW, ROLE_HEDGE): BAND_MINIMAL,
    (REGIME_LOW, ROLE_GAS): BAND_MINIMAL,
}


def _ratio_to_bucket(ratio: float) -> str:
    """
    Convert ratio to bucket label (internal use).

    Args:
        ratio: Ratio value (0.0 to 1.0)

    Returns:
        Bucket label
    """
    if not isinstance(ratio, (int, float)):
        return RATIO_UNKNOWN

    # Clamp ratio to 0.0-1.0 range
    ratio = max(0.0, min(1.0, ratio))

    for bucket, (low, high) in RATIO_THRESHOLDS.items():
        if low <= ratio < high:
            return bucket

    return RATIO_UNKNOWN


def _get_safe_band_bucket(regime_label: str, role: str) -> str:
    """
    Get safe band bucket for (regime, role) pair.

    Args:
        regime_label: Regime label
        role: Role name

    Returns:
        Safe band bucket label
    """
    key = (regime_label, role)
    return SAFE_BAND_TABLE.get(key, BAND_UNKNOWN)


def _determine_status(current_ratio: float, safe_band_bucket: str) -> str:
    """
    Determine status by comparing current ratio to safe band.

    Args:
        current_ratio: Current ratio value
        safe_band_bucket: Safe band bucket label

    Returns:
        Status label: BELOW_SAFE / WITHIN_SAFE / ABOVE_SAFE / UNKNOWN
    """
    if safe_band_bucket == BAND_UNKNOWN:
        return STATUS_UNKNOWN

    if not isinstance(current_ratio, (int, float)):
        return STATUS_UNKNOWN

    # Clamp ratio
    current_ratio = max(0.0, min(1.0, current_ratio))

    # Get band thresholds
    if safe_band_bucket not in BAND_THRESHOLDS:
        return STATUS_UNKNOWN

    low, high = BAND_THRESHOLDS[safe_band_bucket]

    if current_ratio < low:
        return STATUS_BELOW_SAFE
    elif current_ratio < high:
        return STATUS_WITHIN_SAFE
    else:
        return STATUS_ABOVE_SAFE


def _create_role_interpretation(status: str) -> str:
    """
    Create non-prescriptive interpretation text for status.

    Args:
        status: Status label

    Returns:
        Non-prescriptive interpretation text
    """
    if status == STATUS_WITHIN_SAFE:
        return "allocation appears within the structurally safe band for the current regime label."
    elif status == STATUS_BELOW_SAFE:
        return "allocation appears below the structurally safe band for the current regime label."
    elif status == STATUS_ABOVE_SAFE:
        return "allocation appears above the structurally safe band for the current regime label."
    else:
        return "allocation status could not be determined from available inputs."


def build_role_safe_band_guidance_v1(
    portfolio_snapshot: Optional[Dict[str, Any]],
    regime_record: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build role safe band guidance record (READ-ONLY).

    Args:
        portfolio_snapshot: {ROLE: ratio_float} (expected sum ≈ 1.0)
        regime_record: Existing regime record dict from earlier pipeline

    Returns:
        Dict with:
        - guidance_record: PR144-compliant guidance record
        - warnings: List of warnings
    """
    warnings = []

    # Defensive: Handle invalid portfolio_snapshot
    if portfolio_snapshot is None or not isinstance(portfolio_snapshot, dict):
        warnings.append("invalid portfolio_snapshot (expected dict, got None or non-dict)")
        error_record = V14RoleSafeBandSchema.create_error_record(
            summary="role safe band guidance generation failed: invalid portfolio snapshot."
        )
        return {
            "guidance_record": error_record,
            "warnings": warnings,
        }

    # Defensive: Handle invalid regime_record
    if regime_record is None or not isinstance(regime_record, dict):
        warnings.append("invalid regime_record (expected dict, got None or non-dict)")
        error_record = V14RoleSafeBandSchema.create_error_record(
            summary="role safe band guidance generation failed: invalid regime record."
        )
        return {
            "guidance_record": error_record,
            "warnings": warnings,
        }

    # Extract regime label (defensive)
    regime_label = REGIME_UNKNOWN
    if "v11_regime_level" in regime_record:
        regime_label = regime_record["v11_regime_level"]
    elif "regime_level" in regime_record:
        regime_label = regime_record["regime_level"]

    # Validate regime label
    if regime_label not in V14RoleSafeBandSchema.VALID_REGIME_LABELS:
        warnings.append(f"unrecognized regime_label: {regime_label}, using UNKNOWN")
        regime_label = REGIME_UNKNOWN

    # Process each role
    roles_output = {}
    all_roles = [ROLE_VOLATILITY, ROLE_LIQUIDITY, ROLE_STABILITY, ROLE_HEDGE, ROLE_GAS]

    for role in all_roles:
        # Get current ratio (defensive)
        current_ratio = portfolio_snapshot.get(role)

        if current_ratio is None:
            # Missing role in snapshot
            warnings.append(f"role '{role}' not found in portfolio_snapshot, using UNKNOWN")
            roles_output[role] = {
                "current_ratio_bucket": RATIO_UNKNOWN,
                "safe_band_bucket": BAND_UNKNOWN,
                "status": STATUS_UNKNOWN,
                "interpretation": _create_role_interpretation(STATUS_UNKNOWN),
            }
            continue

        if not isinstance(current_ratio, (int, float)):
            warnings.append(f"role '{role}' has invalid ratio type: {type(current_ratio).__name__}, using UNKNOWN")
            roles_output[role] = {
                "current_ratio_bucket": RATIO_UNKNOWN,
                "safe_band_bucket": BAND_UNKNOWN,
                "status": STATUS_UNKNOWN,
                "interpretation": _create_role_interpretation(STATUS_UNKNOWN),
            }
            continue

        # Clamp ratio and warn if out of bounds
        if current_ratio < 0.0 or current_ratio > 1.0:
            warnings.append(f"role '{role}' ratio out of bounds: {current_ratio}, clamping")
            current_ratio = max(0.0, min(1.0, current_ratio))

        # Convert ratio to bucket
        current_bucket = _ratio_to_bucket(current_ratio)

        # Get safe band bucket
        safe_band_bucket = _get_safe_band_bucket(regime_label, role)

        # Determine status
        status = _determine_status(current_ratio, safe_band_bucket)

        # Create interpretation
        interpretation = _create_role_interpretation(status)

        roles_output[role] = {
            "current_ratio_bucket": current_bucket,
            "safe_band_bucket": safe_band_bucket,
            "status": status,
            "interpretation": interpretation,
        }

    # Create guidance record
    guidance_summary = "role safe band guidance assembled for current regime label."
    guidance_record = V14RoleSafeBandSchema.create_guidance_record(
        version=GUIDANCE_VERSION_V1_4,
        status=GUIDANCE_STATUS_AVAILABLE,
        mode=GUIDANCE_MODE_READ_ONLY,
        summary=guidance_summary,
        regime_label=regime_label,
        roles=roles_output,
        basis=["REGIME_LABEL_USED", "PORTFOLIO_SNAPSHOT_USED"],
        artifacts=["v11_regime_record", "portfolio_snapshot"],
        warnings=warnings,
    )

    # Validate schema
    schema_errors = V14RoleSafeBandSchema.validate_guidance_record(guidance_record)
    if schema_errors:
        warnings.extend([f"schema validation: {e}" for e in schema_errors])

    # Add warnings to guidance record
    guidance_record["v14_guidance_warnings"] = warnings

    return {
        "guidance_record": guidance_record,
        "warnings": warnings,
    }


def get_safe_band_engine_v1_info() -> Dict[str, Any]:
    """
    Get role safe band engine information.

    Returns:
        Dict with engine metadata
    """
    return {
        "engine_version": "v1",
        "engine_type": "role_safe_band_guidance",
        "philosophy": "Guidance ≠ Instruction. Describe shape, not recommend action.",
        "input_formats": [
            "portfolio_snapshot (ROLE: ratio)",
            "regime_record (v11_regime_level)",
        ],
        "output_format": "role_safe_band_guidance (PR144)",
        "safe_band_table": "static, deterministic (regime × role → band)",
        "constitutional_guarantees": [
            "READ-ONLY",
            "non_prescriptive",
            "no_trading_verbs",
            "no_token_literals",
            "bucket_output_only",
            "defensive",
            "warning-only",
        ],
    }


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.4 Role Safe Band Engine - Self Test")
    print("=" * 60)
    print()

    # Test 1: Valid inputs (MEDIUM regime)
    print("Test 1: Valid inputs (MEDIUM regime)")
    test_portfolio = {
        ROLE_VOLATILITY: 0.30,
        ROLE_LIQUIDITY: 0.25,
        ROLE_STABILITY: 0.20,
        ROLE_HEDGE: 0.15,
        ROLE_GAS: 0.10,
    }
    test_regime = {
        "v11_regime_level": REGIME_MEDIUM,
    }

    result1 = build_role_safe_band_guidance_v1(test_portfolio, test_regime)
    print(f"Guidance status: {result1['guidance_record']['v14_guidance_status']}")
    print(f"Regime label: {result1['guidance_record']['v14_guidance_regime_label']}")
    print(f"Warnings: {len(result1['warnings'])}")
    print(f"Roles processed: {len(result1['guidance_record']['v14_guidance_roles'])}")
    print()

    # Test 2: Invalid inputs (defensive)
    print("Test 2: Invalid inputs (defensive)")
    result2 = build_role_safe_band_guidance_v1(None, None)
    print(f"Guidance status: {result2['guidance_record']['v14_guidance_status']}")
    print(f"Warnings: {len(result2['warnings'])}")
    print()

    # Test 3: Missing role in portfolio
    print("Test 3: Missing role in portfolio")
    partial_portfolio = {
        ROLE_VOLATILITY: 0.40,
        ROLE_LIQUIDITY: 0.60,
        # Missing: STABILITY, HEDGE, GAS
    }
    result3 = build_role_safe_band_guidance_v1(partial_portfolio, test_regime)
    print(f"Guidance status: {result3['guidance_record']['v14_guidance_status']}")
    print(f"Warnings: {len(result3['warnings'])}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
