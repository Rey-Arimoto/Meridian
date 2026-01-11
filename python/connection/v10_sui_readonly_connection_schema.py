#!/usr/bin/env python3
"""
PR106: v1.0 Sui Read-Only Connection Schema (READ-ONLY)

Purpose:
    Schema for Sui read-only connection records.
    Connection = Observability Extension (not execution).

Constitutional Constraints:
    - READ-ONLY: No signing, no transactions, no wallet operations
    - No secrets: No API keys, tokens, credentials, mnemonics
    - No addresses: No wallet addresses in connection config
    - Observation only: RPC read operations only

Connection Philosophy:
    Connection != Execution
    Connection = Observation Extension

    Read-only connection provides:
    - RPC query capability (read blockchain state)
    - Indexer query capability (read historical data)
    - Network status observation

    Connection does NOT:
    - Sign transactions
    - Send transactions
    - Access private keys
    - Execute trades

Schema Design:
    - v10_conn_ prefix for connection fields
    - Provider configuration (RPC/Indexer URLs)
    - Network selection (mainnet/testnet/devnet)
    - Connection status tracking
"""

from typing import Any, Dict, List, Optional


class V10SuiReadOnlyConnectionSchema:
    """
    Schema for v1.0 Sui read-only connection records.

    Connection = Observability Extension (not execution).
    """

    # Required fields for connection record
    REQUIRED_FIELDS = [
        "v10_conn_mode",           # Connection mode (ON/OFF)
        "v10_conn_status",         # Connection status (CONNECTED/DISCONNECTED/ERROR)
        "v10_conn_network",        # Network (mainnet/testnet/devnet/localnet)
        "v10_conn_capabilities",   # List of capabilities (RPC_READ/INDEXER_READ)
        "v10_conn_summary",        # Summary of connection state
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v10_conn_provider_config",  # Provider configuration (URLs, timeouts)
        "v10_conn_error_info",       # Error information if status is ERROR
        "v10_conn_metadata",         # Additional metadata
    ]

    # Valid connection modes
    VALID_MODES = ["ON", "OFF"]

    # Valid connection statuses
    VALID_STATUSES = ["CONNECTED", "DISCONNECTED", "ERROR"]

    # Valid networks
    VALID_NETWORKS = ["mainnet", "testnet", "devnet", "localnet"]

    # Valid capabilities
    VALID_CAPABILITIES = ["RPC_READ", "INDEXER_READ"]

    @staticmethod
    def validate_structure(record: Dict[str, Any]) -> List[str]:
        """
        Validate connection record structure.

        Args:
            record: Connection record to validate

        Returns:
            List of warnings (empty if valid)
        """
        warnings = []

        # Check required fields
        for field in V10SuiReadOnlyConnectionSchema.REQUIRED_FIELDS:
            if field not in record:
                warnings.append(f"Missing required field: {field}")

        # Validate mode
        if "v10_conn_mode" in record:
            mode = record["v10_conn_mode"]
            if mode not in V10SuiReadOnlyConnectionSchema.VALID_MODES:
                warnings.append(
                    f"Invalid v10_conn_mode: {mode}. "
                    f"Must be one of {V10SuiReadOnlyConnectionSchema.VALID_MODES}"
                )

        # Validate status
        if "v10_conn_status" in record:
            status = record["v10_conn_status"]
            if status not in V10SuiReadOnlyConnectionSchema.VALID_STATUSES:
                warnings.append(
                    f"Invalid v10_conn_status: {status}. "
                    f"Must be one of {V10SuiReadOnlyConnectionSchema.VALID_STATUSES}"
                )

        # Validate network
        if "v10_conn_network" in record:
            network = record["v10_conn_network"]
            if network not in V10SuiReadOnlyConnectionSchema.VALID_NETWORKS:
                warnings.append(
                    f"Invalid v10_conn_network: {network}. "
                    f"Must be one of {V10SuiReadOnlyConnectionSchema.VALID_NETWORKS}"
                )

        # Validate capabilities
        if "v10_conn_capabilities" in record:
            capabilities = record["v10_conn_capabilities"]
            if not isinstance(capabilities, list):
                warnings.append("v10_conn_capabilities must be a list")
            else:
                for cap in capabilities:
                    if cap not in V10SuiReadOnlyConnectionSchema.VALID_CAPABILITIES:
                        warnings.append(
                            f"Invalid capability: {cap}. "
                            f"Must be one of {V10SuiReadOnlyConnectionSchema.VALID_CAPABILITIES}"
                        )

        # Validate summary
        if "v10_conn_summary" in record:
            summary = record["v10_conn_summary"]
            if not isinstance(summary, str):
                warnings.append("v10_conn_summary must be a string")
            elif len(summary) == 0:
                warnings.append("v10_conn_summary must not be empty")

        return warnings

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create empty connection record with safe defaults.

        Returns:
            Empty connection record (disconnected state)
        """
        return {
            "v10_conn_mode": "OFF",
            "v10_conn_status": "DISCONNECTED",
            "v10_conn_network": "localnet",
            "v10_conn_capabilities": [],
            "v10_conn_summary": "connection not initialized. no provider configured.",
        }

    @staticmethod
    def create_connected_record(
        network: str,
        capabilities: List[str],
        provider_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create connected connection record.

        Args:
            network: Network name (mainnet/testnet/devnet/localnet)
            capabilities: List of capabilities (RPC_READ/INDEXER_READ)
            provider_config: Optional provider configuration

        Returns:
            Connected connection record
        """
        record = {
            "v10_conn_mode": "ON",
            "v10_conn_status": "CONNECTED",
            "v10_conn_network": network,
            "v10_conn_capabilities": capabilities,
            "v10_conn_summary": f"connection established to {network}. capabilities available.",
        }

        if provider_config:
            record["v10_conn_provider_config"] = provider_config

        return record

    @staticmethod
    def create_error_record(
        network: str,
        error_info: str,
    ) -> Dict[str, Any]:
        """
        Create error connection record.

        Args:
            network: Network name (mainnet/testnet/devnet/localnet)
            error_info: Error information

        Returns:
            Error connection record
        """
        return {
            "v10_conn_mode": "ON",
            "v10_conn_status": "ERROR",
            "v10_conn_network": network,
            "v10_conn_capabilities": [],
            "v10_conn_error_info": error_info,
            "v10_conn_summary": f"connection error on {network}. check error info for details.",
        }


def get_readonly_connection_schema_info() -> Dict[str, Any]:
    """
    Get read-only connection schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.0",
        "schema_type": "sui_readonly_connection",
        "required_fields": V10SuiReadOnlyConnectionSchema.REQUIRED_FIELDS,
        "optional_fields": V10SuiReadOnlyConnectionSchema.OPTIONAL_FIELDS,
        "valid_modes": V10SuiReadOnlyConnectionSchema.VALID_MODES,
        "valid_statuses": V10SuiReadOnlyConnectionSchema.VALID_STATUSES,
        "valid_networks": V10SuiReadOnlyConnectionSchema.VALID_NETWORKS,
        "valid_capabilities": V10SuiReadOnlyConnectionSchema.VALID_CAPABILITIES,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.0 Sui Read-Only Connection Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Empty record
    print("Test 1: Empty record")
    empty = V10SuiReadOnlyConnectionSchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    warnings = V10SuiReadOnlyConnectionSchema.validate_structure(empty)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 2: Connected record
    print("Test 2: Connected record")
    connected = V10SuiReadOnlyConnectionSchema.create_connected_record(
        network="testnet",
        capabilities=["RPC_READ", "INDEXER_READ"],
        provider_config={
            "rpc_url": "https://testnet.example.com/rpc",
            "indexer_url": "https://testnet.example.com/indexer",
        },
    )
    print(json.dumps(connected, indent=2))
    warnings = V10SuiReadOnlyConnectionSchema.validate_structure(connected)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 3: Error record
    print("Test 3: Error record")
    error = V10SuiReadOnlyConnectionSchema.create_error_record(
        network="mainnet",
        error_info="connection timeout after multiple retries",
    )
    print(json.dumps(error, indent=2))
    warnings = V10SuiReadOnlyConnectionSchema.validate_structure(error)
    print(f"Validation warnings: {len(warnings)}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
