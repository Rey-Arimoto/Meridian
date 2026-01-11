#!/usr/bin/env python3
"""
PR106: v1.0 Sui Provider Config Schema (READ-ONLY)

Purpose:
    Schema for Sui provider configuration (RPC/Indexer URLs).
    Provider Config = Connection Parameters (not credentials).

Constitutional Constraints:
    - READ-ONLY: No signing, no transactions, no wallet operations
    - No secrets: No API keys, tokens, credentials in schema
    - URL validation: Only HTTPS URLs allowed (no HTTP)
    - Defensive: Handles None/invalid gracefully

Provider Config Philosophy:
    Provider Config != Credentials
    Provider Config = Connection Parameters

    Provider config contains:
    - RPC endpoint URL (read operations)
    - Indexer endpoint URL (historical queries)
    - Connection timeouts
    - Retry configuration

    Provider config does NOT contain:
    - API keys (handled separately with secrets manager)
    - Private keys
    - Mnemonics
    - Bearer tokens

Schema Design:
    - v10_provider_ prefix for provider fields
    - HTTPS-only URLs (no HTTP)
    - Safe timeout defaults
    - Retry configuration
"""

from typing import Any, Dict, List, Optional


class V10SuiProviderConfigSchema:
    """
    Schema for v1.0 Sui provider configuration records.

    Provider Config = Connection Parameters (not credentials).
    """

    # Required fields for provider config
    REQUIRED_FIELDS = [
        "v10_provider_type",        # Provider type (RPC/INDEXER/COMBINED)
        "v10_provider_network",     # Network (mainnet/testnet/devnet/localnet)
        "v10_provider_endpoints",   # List of endpoint configurations
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v10_provider_timeout_ms",      # Request timeout in milliseconds
        "v10_provider_retry_count",     # Max retry attempts
        "v10_provider_retry_delay_ms",  # Delay between retries in milliseconds
        "v10_provider_metadata",        # Additional metadata
    ]

    # Valid provider types
    VALID_TYPES = ["RPC", "INDEXER", "COMBINED"]

    # Valid networks
    VALID_NETWORKS = ["mainnet", "testnet", "devnet", "localnet"]

    # Default timeouts and retry settings
    DEFAULT_TIMEOUT_MS = 30000      # 30 seconds
    DEFAULT_RETRY_COUNT = 3
    DEFAULT_RETRY_DELAY_MS = 1000   # 1 second

    @staticmethod
    def validate_structure(config: Dict[str, Any]) -> List[str]:
        """
        Validate provider config structure.

        Args:
            config: Provider config to validate

        Returns:
            List of warnings (empty if valid)
        """
        warnings = []

        # Check required fields
        for field in V10SuiProviderConfigSchema.REQUIRED_FIELDS:
            if field not in config:
                warnings.append(f"Missing required field: {field}")

        # Validate provider type
        if "v10_provider_type" in config:
            ptype = config["v10_provider_type"]
            if ptype not in V10SuiProviderConfigSchema.VALID_TYPES:
                warnings.append(
                    f"Invalid v10_provider_type: {ptype}. "
                    f"Must be one of {V10SuiProviderConfigSchema.VALID_TYPES}"
                )

        # Validate network
        if "v10_provider_network" in config:
            network = config["v10_provider_network"]
            if network not in V10SuiProviderConfigSchema.VALID_NETWORKS:
                warnings.append(
                    f"Invalid v10_provider_network: {network}. "
                    f"Must be one of {V10SuiProviderConfigSchema.VALID_NETWORKS}"
                )

        # Validate endpoints
        if "v10_provider_endpoints" in config:
            endpoints = config["v10_provider_endpoints"]
            if not isinstance(endpoints, list):
                warnings.append("v10_provider_endpoints must be a list")
            elif len(endpoints) == 0:
                warnings.append("v10_provider_endpoints must not be empty")
            else:
                for i, endpoint in enumerate(endpoints):
                    if not isinstance(endpoint, dict):
                        warnings.append(f"Endpoint {i} must be a dict")
                        continue

                    # Check endpoint type
                    if "type" not in endpoint:
                        warnings.append(f"Endpoint {i} missing 'type' field")
                    elif endpoint["type"] not in ["RPC", "INDEXER"]:
                        warnings.append(
                            f"Endpoint {i} has invalid type: {endpoint['type']}. "
                            f"Must be RPC or INDEXER"
                        )

                    # Check endpoint URL
                    if "url" not in endpoint:
                        warnings.append(f"Endpoint {i} missing 'url' field")
                    elif not isinstance(endpoint["url"], str):
                        warnings.append(f"Endpoint {i} url must be a string")
                    elif not endpoint["url"].startswith("https://"):
                        warnings.append(
                            f"Endpoint {i} url must start with https:// (got: {endpoint['url']})"
                        )

        # Validate timeout
        if "v10_provider_timeout_ms" in config:
            timeout = config["v10_provider_timeout_ms"]
            if not isinstance(timeout, int):
                warnings.append("v10_provider_timeout_ms must be an integer")
            elif timeout <= 0:
                warnings.append("v10_provider_timeout_ms must be positive")

        # Validate retry count
        if "v10_provider_retry_count" in config:
            retry_count = config["v10_provider_retry_count"]
            if not isinstance(retry_count, int):
                warnings.append("v10_provider_retry_count must be an integer")
            elif retry_count < 0:
                warnings.append("v10_provider_retry_count must be non-negative")

        # Validate retry delay
        if "v10_provider_retry_delay_ms" in config:
            retry_delay = config["v10_provider_retry_delay_ms"]
            if not isinstance(retry_delay, int):
                warnings.append("v10_provider_retry_delay_ms must be an integer")
            elif retry_delay < 0:
                warnings.append("v10_provider_retry_delay_ms must be non-negative")

        return warnings

    @staticmethod
    def create_rpc_config(
        network: str,
        rpc_url: str,
        timeout_ms: Optional[int] = None,
        retry_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create RPC provider configuration.

        Args:
            network: Network name (mainnet/testnet/devnet/localnet)
            rpc_url: RPC endpoint URL (must be HTTPS)
            timeout_ms: Optional request timeout in milliseconds
            retry_count: Optional max retry attempts

        Returns:
            RPC provider config
        """
        config = {
            "v10_provider_type": "RPC",
            "v10_provider_network": network,
            "v10_provider_endpoints": [
                {
                    "type": "RPC",
                    "url": rpc_url,
                }
            ],
        }

        if timeout_ms is not None:
            config["v10_provider_timeout_ms"] = timeout_ms
        else:
            config["v10_provider_timeout_ms"] = V10SuiProviderConfigSchema.DEFAULT_TIMEOUT_MS

        if retry_count is not None:
            config["v10_provider_retry_count"] = retry_count
        else:
            config["v10_provider_retry_count"] = V10SuiProviderConfigSchema.DEFAULT_RETRY_COUNT

        config["v10_provider_retry_delay_ms"] = V10SuiProviderConfigSchema.DEFAULT_RETRY_DELAY_MS

        return config

    @staticmethod
    def create_indexer_config(
        network: str,
        indexer_url: str,
        timeout_ms: Optional[int] = None,
        retry_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create Indexer provider configuration.

        Args:
            network: Network name (mainnet/testnet/devnet/localnet)
            indexer_url: Indexer endpoint URL (must be HTTPS)
            timeout_ms: Optional request timeout in milliseconds
            retry_count: Optional max retry attempts

        Returns:
            Indexer provider config
        """
        config = {
            "v10_provider_type": "INDEXER",
            "v10_provider_network": network,
            "v10_provider_endpoints": [
                {
                    "type": "INDEXER",
                    "url": indexer_url,
                }
            ],
        }

        if timeout_ms is not None:
            config["v10_provider_timeout_ms"] = timeout_ms
        else:
            config["v10_provider_timeout_ms"] = V10SuiProviderConfigSchema.DEFAULT_TIMEOUT_MS

        if retry_count is not None:
            config["v10_provider_retry_count"] = retry_count
        else:
            config["v10_provider_retry_count"] = V10SuiProviderConfigSchema.DEFAULT_RETRY_COUNT

        config["v10_provider_retry_delay_ms"] = V10SuiProviderConfigSchema.DEFAULT_RETRY_DELAY_MS

        return config

    @staticmethod
    def create_combined_config(
        network: str,
        rpc_url: str,
        indexer_url: str,
        timeout_ms: Optional[int] = None,
        retry_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create combined RPC+Indexer provider configuration.

        Args:
            network: Network name (mainnet/testnet/devnet/localnet)
            rpc_url: RPC endpoint URL (must be HTTPS)
            indexer_url: Indexer endpoint URL (must be HTTPS)
            timeout_ms: Optional request timeout in milliseconds
            retry_count: Optional max retry attempts

        Returns:
            Combined provider config
        """
        config = {
            "v10_provider_type": "COMBINED",
            "v10_provider_network": network,
            "v10_provider_endpoints": [
                {
                    "type": "RPC",
                    "url": rpc_url,
                },
                {
                    "type": "INDEXER",
                    "url": indexer_url,
                }
            ],
        }

        if timeout_ms is not None:
            config["v10_provider_timeout_ms"] = timeout_ms
        else:
            config["v10_provider_timeout_ms"] = V10SuiProviderConfigSchema.DEFAULT_TIMEOUT_MS

        if retry_count is not None:
            config["v10_provider_retry_count"] = retry_count
        else:
            config["v10_provider_retry_count"] = V10SuiProviderConfigSchema.DEFAULT_RETRY_COUNT

        config["v10_provider_retry_delay_ms"] = V10SuiProviderConfigSchema.DEFAULT_RETRY_DELAY_MS

        return config


def get_provider_config_schema_info() -> Dict[str, Any]:
    """
    Get provider config schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.0",
        "schema_type": "sui_provider_config",
        "required_fields": V10SuiProviderConfigSchema.REQUIRED_FIELDS,
        "optional_fields": V10SuiProviderConfigSchema.OPTIONAL_FIELDS,
        "valid_types": V10SuiProviderConfigSchema.VALID_TYPES,
        "valid_networks": V10SuiProviderConfigSchema.VALID_NETWORKS,
        "default_timeout_ms": V10SuiProviderConfigSchema.DEFAULT_TIMEOUT_MS,
        "default_retry_count": V10SuiProviderConfigSchema.DEFAULT_RETRY_COUNT,
        "default_retry_delay_ms": V10SuiProviderConfigSchema.DEFAULT_RETRY_DELAY_MS,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.0 Sui Provider Config Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: RPC config
    print("Test 1: RPC config")
    rpc_config = V10SuiProviderConfigSchema.create_rpc_config(
        network="testnet",
        rpc_url="https://testnet.example.com/rpc",
    )
    print(json.dumps(rpc_config, indent=2))
    warnings = V10SuiProviderConfigSchema.validate_structure(rpc_config)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 2: Indexer config
    print("Test 2: Indexer config")
    indexer_config = V10SuiProviderConfigSchema.create_indexer_config(
        network="mainnet",
        indexer_url="https://mainnet.example.com/indexer",
    )
    print(json.dumps(indexer_config, indent=2))
    warnings = V10SuiProviderConfigSchema.validate_structure(indexer_config)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 3: Combined config
    print("Test 3: Combined config")
    combined_config = V10SuiProviderConfigSchema.create_combined_config(
        network="devnet",
        rpc_url="https://devnet.example.com/rpc",
        indexer_url="https://devnet.example.com/indexer",
        timeout_ms=60000,
        retry_count=5,
    )
    print(json.dumps(combined_config, indent=2))
    warnings = V10SuiProviderConfigSchema.validate_structure(combined_config)
    print(f"Validation warnings: {len(warnings)}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
