#!/usr/bin/env python3
"""
PR125: v1.1 Review Render Schema v1 (READ-ONLY)

Purpose:
    Define schema for review render records.
    Render = Display Shape (not instruction/conclusion).

Constitutional Constraints:
    - READ-ONLY: No execution, no recommendations
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No "should" language
    - No token literals: No SUI, USDC, BTC, ETH
    - No amounts: No numeric values in output
    - No addresses: No 0x... patterns
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No causal coupling: No "therefore", "so", "hence"

Render Philosophy:
    Render ≠ Instruction
    Render ≠ Conclusion
    Render = Display Shape

    Render provides:
    - Formatted output for human reading
    - Structured presentation of packet contents
    - Non-prescriptive labels and state descriptions
    - Clear section organization

    Render does NOT:
    - Recommend actions
    - Draw conclusions
    - Contain token names, amounts, addresses
    - Prescribe responses
    - Imply next steps

v11_render_ Prefix:
    All render fields use v11_render_ prefix for clear separation
    from other v1.1 fields.

Schema Fields:
    - v11_render_mode: ON | OFF
    - v11_render_status: AVAILABLE | UNAVAILABLE | ERROR
    - v11_render_format: MARKDOWN | TEXT
    - v11_render_style: CONCISE | STANDARD | DETAILED
    - v11_render_summary: Short non-prescriptive summary
    - v11_render_output: Formatted text string (Markdown or plain text)
    - v11_render_basis: Array of field names referenced
    - v11_render_sections_present: (Optional) List of section labels (PR138)
"""

from typing import Any, Dict, List, Optional


class V11ReviewRenderSchema:
    """v1.1 Review Render Schema Definition."""

    # Required fields
    REQUIRED_FIELDS = [
        "v11_render_mode",
        "v11_render_status",
        "v11_render_format",
        "v11_render_style",
        "v11_render_summary",
        "v11_render_output",
        "v11_render_basis",
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v11_render_warnings",
        "v11_render_sections_present",  # PR138: list of section labels
    ]

    # Valid enum values
    VALID_MODES = ["ON", "OFF"]
    VALID_STATUSES = ["AVAILABLE", "UNAVAILABLE", "ERROR"]
    VALID_FORMATS = ["MARKDOWN", "TEXT"]
    VALID_STYLES = ["CONCISE", "STANDARD", "DETAILED"]

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create an empty render record.

        Returns:
            Empty render record
        """
        return {
            "v11_render_mode": "ON",
            "v11_render_status": "UNAVAILABLE",
            "v11_render_format": "MARKDOWN",
            "v11_render_style": "STANDARD",
            "v11_render_summary": "no render available.",
            "v11_render_output": "",
            "v11_render_basis": [],
        }

    @staticmethod
    def create_error_record(error_message: str = "render generation failed.") -> Dict[str, Any]:
        """
        Create an ERROR render record.

        Args:
            error_message: Error description

        Returns:
            ERROR render record
        """
        return {
            "v11_render_mode": "ON",
            "v11_render_status": "ERROR",
            "v11_render_format": "MARKDOWN",
            "v11_render_style": "STANDARD",
            "v11_render_summary": error_message,
            "v11_render_output": f"# Error\n\n{error_message}",
            "v11_render_basis": [],
        }

    @staticmethod
    def create_render_record(
        output: str,
        fmt: str = "MARKDOWN",
        style: str = "STANDARD",
        basis: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a render record.

        Args:
            output: Formatted text output
            fmt: MARKDOWN | TEXT
            style: CONCISE | STANDARD | DETAILED
            basis: Optional array of field names referenced
            warnings: Optional array of warnings

        Returns:
            Render record
        """
        record = {
            "v11_render_mode": "ON",
            "v11_render_status": "AVAILABLE",
            "v11_render_format": fmt,
            "v11_render_style": style,
            "v11_render_summary": f"render complete. packet formatted as {fmt.lower()}.",
            "v11_render_output": output,
            "v11_render_basis": basis or [],
        }

        if warnings:
            record["v11_render_warnings"] = warnings

        return record

    @staticmethod
    def validate_structure(record: Dict[str, Any]) -> List[str]:
        """
        Validate render record structure.

        Args:
            record: Render record to validate

        Returns:
            List of warnings (empty if valid)
        """
        warnings = []

        # Check required fields
        for field in V11ReviewRenderSchema.REQUIRED_FIELDS:
            if field not in record:
                warnings.append(f"Missing required field: {field}")

        # Validate mode
        if "v11_render_mode" in record:
            if record["v11_render_mode"] not in V11ReviewRenderSchema.VALID_MODES:
                warnings.append(f"Invalid render mode: {record['v11_render_mode']}")

        # Validate status
        if "v11_render_status" in record:
            if record["v11_render_status"] not in V11ReviewRenderSchema.VALID_STATUSES:
                warnings.append(f"Invalid render status: {record['v11_render_status']}")

        # Validate format
        if "v11_render_format" in record:
            if record["v11_render_format"] not in V11ReviewRenderSchema.VALID_FORMATS:
                warnings.append(f"Invalid render format: {record['v11_render_format']}")

        # Validate style
        if "v11_render_style" in record:
            if record["v11_render_style"] not in V11ReviewRenderSchema.VALID_STYLES:
                warnings.append(f"Invalid render style: {record['v11_render_style']}")

        # Validate output (must be string)
        if "v11_render_output" in record:
            if not isinstance(record["v11_render_output"], str):
                warnings.append("Render output must be string")

        # Validate basis (must be list of strings)
        if "v11_render_basis" in record:
            if not isinstance(record["v11_render_basis"], list):
                warnings.append("Basis must be a list")
            else:
                for basis_field in record["v11_render_basis"]:
                    if not isinstance(basis_field, str):
                        warnings.append(f"Basis field must be string: {basis_field}")

        return warnings


def get_render_schema_info() -> Dict[str, Any]:
    """
    Get render schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.1",
        "schema_type": "review_render",
        "valid_modes": V11ReviewRenderSchema.VALID_MODES,
        "valid_statuses": V11ReviewRenderSchema.VALID_STATUSES,
        "valid_formats": V11ReviewRenderSchema.VALID_FORMATS,
        "valid_styles": V11ReviewRenderSchema.VALID_STYLES,
        "required_fields": V11ReviewRenderSchema.REQUIRED_FIELDS,
        "optional_fields": V11ReviewRenderSchema.OPTIONAL_FIELDS,
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-evaluative",
            "non-prescriptive",
            "no_token_literals",
            "no_amounts",
            "no_addresses",
            "no_trading_vocabulary",
            "no_causal_coupling",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.1 Review Render Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create empty record
    print("Test 1: Create empty record")
    empty = V11ReviewRenderSchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    print()

    # Test 2: Validate empty record
    print("Test 2: Validate empty record")
    warnings = V11ReviewRenderSchema.validate_structure(empty)
    print(f"Warnings: {warnings}")
    print()

    # Test 3: Create error record
    print("Test 3: Create error record")
    error = V11ReviewRenderSchema.create_error_record("test error")
    print(json.dumps(error, indent=2))
    print()

    # Test 4: Create full render record
    print("Test 4: Create full render record")
    render = V11ReviewRenderSchema.create_render_record(
        output="# Test Output\n\nTest content.",
        fmt="MARKDOWN",
        style="STANDARD",
        basis=["v11_packet_summary"],
    )
    print(json.dumps(render, indent=2))
    print()

    # Test 5: Validate full record
    print("Test 5: Validate full record")
    warnings = V11ReviewRenderSchema.validate_structure(render)
    print(f"Warnings: {warnings}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
