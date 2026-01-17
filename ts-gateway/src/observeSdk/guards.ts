/**
 * PR182: v1.4 Real Observation SDK Connectors v1 - Guards
 *
 * Purpose:
 *   Label-only validation and sanitization for observation SDK.
 *
 * Constitutional Constraints:
 *   - Label-only: No numerics/addresses/token names in output
 *   - Defensive: Never throws, always returns safe default
 */

import {
  FetchStatus,
  SdkHealthLabel,
  PresenceLabel,
  ObservationSnapshotV1,
} from "./types";

/**
 * Validate fetch status
 *
 * @param value - Value to validate
 * @returns Valid fetch status or safe default
 */
export function validateFetchStatus(value: unknown): FetchStatus {
  if (
    value === "AVAILABLE" ||
    value === "PARTIAL" ||
    value === "ERROR"
  ) {
    return value;
  }
  return "ERROR"; // Safe default
}

/**
 * Validate SDK health label
 *
 * @param value - Value to validate
 * @returns Valid health label or UNKNOWN
 */
export function validateSdkHealthLabel(value: unknown): SdkHealthLabel {
  if (
    value === "WS_ALIVE" ||
    value === "WS_DEAD" ||
    value === "HTTP_OK" ||
    value === "RATE_LIMITED" ||
    value === "BACKOFF" ||
    value === "UNKNOWN"
  ) {
    return value;
  }
  return "UNKNOWN"; // Safe default
}

/**
 * Validate presence label
 *
 * @param value - Value to validate
 * @returns Valid presence label or NO_BOOK_DATA
 */
export function validatePresenceLabel(value: unknown): PresenceLabel {
  if (
    value === "HAS_BIDS_ASKS" ||
    value === "HAS_BIDS_ONLY" ||
    value === "HAS_ASKS_ONLY" ||
    value === "NO_BOOK_DATA"
  ) {
    return value;
  }
  return "NO_BOOK_DATA"; // Safe default
}

/**
 * Sanitize string array (label-only)
 *
 * Removes:
 * - Numerics (3+ digits, hex addresses, floats)
 * - Token identifiers
 * - Addresses
 *
 * @param arr - String array to sanitize
 * @returns Sanitized array
 */
export function sanitizeStringArray(arr: string[]): string[] {
  return arr.map((str) => {
    // Remove long numbers (3+ digits)
    let sanitized = str.replace(/\d{3,}/g, "***");

    // Remove hex addresses (0x + 40 hex chars)
    sanitized = sanitized.replace(/0x[a-fA-F0-9]{40}/g, "0x***");

    // Remove floats with many decimals
    sanitized = sanitized.replace(/\d+\.\d{4,}/g, "***.***");

    // Remove common token identifiers
    sanitized = sanitized.replace(/\b(SUI|USDC|DEEP|CETUS)\b/g, "TOKEN");

    return sanitized;
  });
}

/**
 * Format time label from timestamp
 *
 * @param ts - Timestamp (ms)
 * @returns Time label (label-only)
 */
export function formatTimeLabel(
  ts: number
): "T_RECENT" | "T_MIN" | "T_HOUR" | "T_OLD" | "T_NEVER" {
  const now = Date.now();
  const age = now - ts;

  if (age < 0 || ts === 0) return "T_NEVER";
  if (age < 10_000) return "T_RECENT"; // < 10s
  if (age < 60_000) return "T_MIN"; // < 1min
  if (age < 3600_000) return "T_HOUR"; // < 1hr
  return "T_OLD";
}

/**
 * Evaluate presence from snapshot
 *
 * @param snapshot - Numeric book snapshot (internal)
 * @returns Presence label
 */
export function evaluatePresence(snapshot?: {
  bids: any[];
  asks: any[];
}): PresenceLabel {
  if (!snapshot) return "NO_BOOK_DATA";

  const hasBids = snapshot.bids && snapshot.bids.length > 0;
  const hasAsks = snapshot.asks && snapshot.asks.length > 0;

  if (hasBids && hasAsks) return "HAS_BIDS_ASKS";
  if (hasBids) return "HAS_BIDS_ONLY";
  if (hasAsks) return "HAS_ASKS_ONLY";
  return "NO_BOOK_DATA";
}

/**
 * Create safe observation snapshot (defensive)
 *
 * @param status - Fetch status
 * @param sdkHealth - SDK health label
 * @param warnings - Warning messages
 * @returns Safe observation snapshot
 */
export function createSafeObservationSnapshot(
  status: FetchStatus = "ERROR",
  sdkHealth: SdkHealthLabel = "UNKNOWN",
  warnings: string[] = []
): ObservationSnapshotV1 {
  return {
    status: validateFetchStatus(status),
    presence: "NO_BOOK_DATA",
    sdkHealth: validateSdkHealthLabel(sdkHealth),
    warnings: sanitizeStringArray(warnings),
  };
}
