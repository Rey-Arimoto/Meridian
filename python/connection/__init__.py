"""
v1.0 Sui Read-Only Connection Layer

This package contains schemas and constitutional guards for Sui read-only connections.

Connection = Observability Extension (not execution).

Connection Definition:
    Connection provides observability extension to blockchain state.

    Read-only connection enables:
    - RPC queries (read blockchain state)
    - Indexer queries (read historical data)
    - Network status observation

    Connection does NOT:
    - Sign transactions
    - Send transactions
    - Execute trades
    - Access private keys

Modules:
    - v10_sui_readonly_connection_schema: Schema for connection records
    - v10_sui_provider_config_schema: Schema for provider configurations
    - v10_connection_constitutional_guard: Constitutional guards for connections
"""

from .v10_sui_readonly_connection_schema import (
    V10SuiReadOnlyConnectionSchema,
    get_readonly_connection_schema_info,
)

from .v10_sui_provider_config_schema import (
    V10SuiProviderConfigSchema,
    get_provider_config_schema_info,
)

from .v10_connection_constitutional_guard import (
    check_no_secrets,
    check_readonly_guard,
    check_https_only,
    validate_connection_record,
    validate_provider_config,
)

__all__ = [
    # Connection Schema
    "V10SuiReadOnlyConnectionSchema",
    "get_readonly_connection_schema_info",
    # Provider Config Schema
    "V10SuiProviderConfigSchema",
    "get_provider_config_schema_info",
    # Constitutional Guards
    "check_no_secrets",
    "check_readonly_guard",
    "check_https_only",
    "validate_connection_record",
    "validate_provider_config",
]
