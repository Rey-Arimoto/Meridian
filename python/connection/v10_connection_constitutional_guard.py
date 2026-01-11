#!/usr/bin/env python3
"""
PR106: v1.0 Connection Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on connection configurations.
    Guards against secrets leakage and execution operations.

Constitutional Constraints:
    - No secrets: No API keys, tokens, credentials, mnemonics
    - No addresses: No wallet/contract addresses in connection records
    - READ-ONLY: No signing, transfer, swap, execute, send operations
    - HTTPS-only: No HTTP URLs (insecure)

Guards:
    1. Secrets guard (API keys, tokens, Bearer, mnemonics, 0x...)
    2. Read-only guard (sign, transfer, swap, execute, send)
    3. HTTPS guard (no HTTP URLs)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List
import re


def check_no_secrets(text: str) -> List[str]:
    """
    Check for secret patterns in text.

    Detects:
        - API key patterns (api_key, apikey, api-key)
        - Token patterns (token, bearer)
        - Credential patterns (password, secret, credential)
        - Mnemonic patterns (mnemonic, seed phrase)
        - Address patterns (0x followed by hex)

    Args:
        text: Text to check

    Returns:
        List of warnings (empty if no secrets detected)
    """
    if not isinstance(text, str):
        return []

    warnings = []
    text_lower = text.lower()

    # API key patterns
    api_key_patterns = [
        r'\bapi[_-]?key\b',
        r'\bapikey\b',
        r'\bapi[_-]?token\b',
    ]
    for pattern in api_key_patterns:
        if re.search(pattern, text_lower):
            warnings.append(f"API key pattern detected: {pattern}")

    # Token/Bearer patterns
    token_patterns = [
        r'\bbearer\b',
        r'\bauth[_-]?token\b',
        r'\baccess[_-]?token\b',
    ]
    for pattern in token_patterns:
        if re.search(pattern, text_lower):
            warnings.append(f"Token pattern detected: {pattern}")

    # Credential patterns
    credential_patterns = [
        r'\bpassword\b',
        r'\bsecret\b',
        r'\bcredential\b',
        r'\bprivate[_-]?key\b',
    ]
    for pattern in credential_patterns:
        if re.search(pattern, text_lower):
            warnings.append(f"Credential pattern detected: {pattern}")

    # Mnemonic patterns
    mnemonic_patterns = [
        r'\bmnemonic\b',
        r'\bseed[_-]?phrase\b',
        r'\brecovery[_-]?phrase\b',
    ]
    for pattern in mnemonic_patterns:
        if re.search(pattern, text_lower):
            warnings.append(f"Mnemonic pattern detected: {pattern}")

    # Address patterns (0x followed by hex)
    # Only flag if it looks like a complete address (0x + 40+ hex chars)
    address_pattern = r'0x[a-fA-F0-9]{40,}'
    if re.search(address_pattern, text):
        warnings.append(f"Address pattern detected: {address_pattern}")

    return warnings


def check_readonly_guard(text: str) -> List[str]:
    """
    Check for execution operation vocabulary.

    Detects:
        - Signing operations (sign, signature)
        - Transfer operations (transfer, send)
        - Swap operations (swap, trade)
        - Execute operations (execute, call)

    Args:
        text: Text to check

    Returns:
        List of warnings (empty if read-only)
    """
    if not isinstance(text, str):
        return []

    warnings = []
    text_lower = text.lower()

    # Signing operations
    signing_patterns = [
        r'\bsign\b',
        r'\bsigning\b',
        r'\bsignature\b',
        r'\bsigned\b',
    ]
    for pattern in signing_patterns:
        if re.search(pattern, text_lower):
            warnings.append(f"Signing operation detected: {pattern}")

    # Transfer operations
    transfer_patterns = [
        r'\btransfer\b',
        r'\btransferring\b',
        r'\bsend\b',
        r'\bsending\b',
    ]
    for pattern in transfer_patterns:
        if re.search(pattern, text_lower):
            warnings.append(f"Transfer operation detected: {pattern}")

    # Swap operations
    swap_patterns = [
        r'\bswap\b',
        r'\bswapping\b',
        r'\btrade\b',
        r'\btrading\b',
    ]
    for pattern in swap_patterns:
        if re.search(pattern, text_lower):
            warnings.append(f"Swap operation detected: {pattern}")

    # Execute operations
    execute_patterns = [
        r'\bexecute\b',
        r'\bexecuting\b',
        r'\bcall\b',
        r'\bcalling\b',
    ]
    for pattern in execute_patterns:
        if re.search(pattern, text_lower):
            warnings.append(f"Execute operation detected: {pattern}")

    return warnings


def check_https_only(url: str) -> List[str]:
    """
    Check that URL uses HTTPS (not HTTP).

    Args:
        url: URL to check

    Returns:
        List of warnings (empty if HTTPS or localhost)
    """
    if not isinstance(url, str):
        return []

    warnings = []

    # Allow localhost/127.0.0.1 with HTTP (for local development)
    if "localhost" in url.lower() or "127.0.0.1" in url:
        return warnings

    # Check for HTTP (non-HTTPS)
    if url.startswith("http://"):
        warnings.append(f"Insecure HTTP URL detected: {url}")

    return warnings


def validate_connection_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate connection record against all constitutional guards.

    Args:
        record: Connection record to validate

    Returns:
        List of warnings (empty if valid)
    """
    warnings = []

    # Check summary for secrets and read-only violations
    if "v10_conn_summary" in record:
        summary = record["v10_conn_summary"]

        # Secrets guard
        secret_warnings = check_no_secrets(summary)
        warnings.extend(secret_warnings)

        # Read-only guard
        readonly_warnings = check_readonly_guard(summary)
        warnings.extend(readonly_warnings)

    # Check provider config
    if "v10_conn_provider_config" in record:
        provider_config = record["v10_conn_provider_config"]
        if isinstance(provider_config, dict):
            # Check endpoints
            if "v10_provider_endpoints" in provider_config:
                endpoints = provider_config["v10_provider_endpoints"]
                if isinstance(endpoints, list):
                    for endpoint in endpoints:
                        if isinstance(endpoint, dict) and "url" in endpoint:
                            url = endpoint["url"]
                            # HTTPS-only guard
                            https_warnings = check_https_only(url)
                            warnings.extend(https_warnings)

                            # Secrets guard on URL
                            url_secret_warnings = check_no_secrets(url)
                            warnings.extend(url_secret_warnings)

    # Check metadata
    if "v10_conn_metadata" in record:
        metadata = record["v10_conn_metadata"]
        if isinstance(metadata, dict):
            # Convert metadata to string for checking
            metadata_str = str(metadata)
            metadata_secret_warnings = check_no_secrets(metadata_str)
            warnings.extend(metadata_secret_warnings)

    return warnings


def validate_provider_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate provider config against all constitutional guards.

    Args:
        config: Provider config to validate

    Returns:
        List of warnings (empty if valid)
    """
    warnings = []

    # Check endpoints
    if "v10_provider_endpoints" in config:
        endpoints = config["v10_provider_endpoints"]
        if isinstance(endpoints, list):
            for i, endpoint in enumerate(endpoints):
                if isinstance(endpoint, dict) and "url" in endpoint:
                    url = endpoint["url"]

                    # HTTPS-only guard
                    https_warnings = check_https_only(url)
                    for w in https_warnings:
                        warnings.append(f"Endpoint {i}: {w}")

                    # Secrets guard
                    secret_warnings = check_no_secrets(url)
                    for w in secret_warnings:
                        warnings.append(f"Endpoint {i}: {w}")

    # Check metadata
    if "v10_provider_metadata" in config:
        metadata = config["v10_provider_metadata"]
        if isinstance(metadata, dict):
            metadata_str = str(metadata)
            metadata_secret_warnings = check_no_secrets(metadata_str)
            warnings.extend(metadata_secret_warnings)

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.0 Connection Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean connection record
    print("Test 1: Clean connection record")
    clean_conn = {
        "v10_conn_summary": "connection established to testnet. rpc read available.",
        "v10_conn_provider_config": {
            "v10_provider_endpoints": [
                {"type": "RPC", "url": "https://testnet.example.com/rpc"}
            ]
        },
    }
    clean_warnings = validate_connection_record(clean_conn)
    print(f"Clean connection warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty connection record (secrets)
    print("Test 2: Dirty connection record (secrets)")
    dirty_conn_secrets = {
        "v10_conn_summary": "connection with api_key authentication established.",
        "v10_conn_provider_config": {
            "v10_provider_endpoints": [
                {"type": "RPC", "url": "https://testnet.example.com/rpc?bearer=secret123"}
            ]
        },
    }
    dirty_warnings = validate_connection_record(dirty_conn_secrets)
    print(f"Dirty connection warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty connection record (read-only violation)
    print("Test 3: Dirty connection record (read-only violation)")
    dirty_conn_readonly = {
        "v10_conn_summary": "connection ready to sign and transfer tokens.",
    }
    dirty_warnings_readonly = validate_connection_record(dirty_conn_readonly)
    print(f"Dirty connection warnings: {len(dirty_warnings_readonly)}")
    if dirty_warnings_readonly:
        print("  Warnings:")
        for w in dirty_warnings_readonly:
            print(f"    - {w}")
    print()

    # Test 4: HTTP URL (HTTPS-only violation)
    print("Test 4: HTTP URL (HTTPS-only violation)")
    http_config = {
        "v10_provider_endpoints": [
            {"type": "RPC", "url": "http://testnet.example.com/rpc"}
        ]
    }
    http_warnings = validate_provider_config(http_config)
    print(f"HTTP config warnings: {len(http_warnings)}")
    if http_warnings:
        print("  Warnings:")
        for w in http_warnings:
            print(f"    - {w}")
    print()

    # Test 5: Localhost HTTP (allowed)
    print("Test 5: Localhost HTTP (allowed)")
    localhost_config = {
        "v10_provider_endpoints": [
            {"type": "RPC", "url": "http://localhost:9000/rpc"}
        ]
    }
    localhost_warnings = validate_provider_config(localhost_config)
    print(f"Localhost config warnings: {len(localhost_warnings)}")
    if localhost_warnings:
        print(f"  Warnings: {localhost_warnings}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
