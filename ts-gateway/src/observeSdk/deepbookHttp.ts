/**
 * PR182: v1.4 Real Observation SDK Connectors v1 - DeepBook HTTP
 *
 * Purpose:
 *   HTTP polling fallback for DeepBook orderbook data.
 *   Used when WebSocket is unavailable or stale.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Observation only
 *   - Defensive: Never throws, returns PARTIAL/ERROR on failure
 *   - Rate limit handling: RATE_LIMITED label, backoff
 *   - Safe defaults: Missing data → PARTIAL or ERROR
 */

import {
  NumericBookSnapshot,
  DeepBookHttpResult,
  FetchStatus,
  SdkHealthLabel,
} from "./types";
import { sanitizeStringArray } from "./guards";

/**
 * Rate limit state (simple backoff)
 */
let rateLimitState = {
  lastRequestTs: 0,
  backoffUntilTs: 0,
  consecutiveErrors: 0,
};

/**
 * Check if in backoff period
 *
 * @returns True if in backoff
 */
function isInBackoff(): boolean {
  return Date.now() < rateLimitState.backoffUntilTs;
}

/**
 * Update backoff state
 *
 * @param rateLimited - True if rate limited
 */
function updateBackoff(rateLimited: boolean): void {
  if (rateLimited) {
    rateLimitState.consecutiveErrors++;
    const backoffMs = Math.min(60_000, 1000 * Math.pow(2, rateLimitState.consecutiveErrors));
    rateLimitState.backoffUntilTs = Date.now() + backoffMs;
  } else {
    rateLimitState.consecutiveErrors = 0;
    rateLimitState.backoffUntilTs = 0;
  }
}

/**
 * Fetch orderbook from DeepBook HTTP API
 *
 * NOTE: This is a stub for v1. Real HTTP integration in future PR.
 *
 * @returns HTTP fetch result (defensive)
 */
export async function fetchDeepBookHttp(): Promise<DeepBookHttpResult> {
  const warnings: string[] = [];

  try {
    // Check backoff
    if (isInBackoff()) {
      warnings.push("HTTP_IN_BACKOFF");
      return {
        status: "ERROR",
        healthLabel: "BACKOFF",
        warnings: sanitizeStringArray(warnings),
      };
    }

    // Update last request time
    rateLimitState.lastRequestTs = Date.now();

    // TODO: Real HTTP fetch logic
    // For now, return stub data to simulate unavailable API
    warnings.push("HTTP_SDK_NOT_INTEGRATED");

    // Simulate: API not available yet
    updateBackoff(false);

    return {
      status: "ERROR",
      healthLabel: "UNKNOWN",
      warnings: sanitizeStringArray(warnings),
    };
  } catch (error) {
    // Defensive: Never throw
    warnings.push("HTTP_FETCH_ERROR");
    updateBackoff(true);

    return {
      status: "ERROR",
      healthLabel: "UNKNOWN",
      warnings: sanitizeStringArray(warnings),
    };
  }
}

/**
 * Simulate HTTP success (for testing)
 *
 * @param snapshot - Snapshot to return
 * @returns HTTP result with snapshot
 */
export async function simulateHttpSuccess(
  snapshot: NumericBookSnapshot
): Promise<DeepBookHttpResult> {
  rateLimitState.consecutiveErrors = 0;
  rateLimitState.backoffUntilTs = 0;

  return {
    status: "AVAILABLE",
    snapshot,
    healthLabel: "HTTP_OK",
    warnings: [],
  };
}

/**
 * Simulate HTTP rate limit (for testing)
 *
 * @returns HTTP result with rate limit
 */
export async function simulateHttpRateLimit(): Promise<DeepBookHttpResult> {
  updateBackoff(true);

  return {
    status: "PARTIAL",
    healthLabel: "RATE_LIMITED",
    warnings: ["HTTP_RATE_LIMITED"],
  };
}

/**
 * Reset rate limit state (for testing)
 */
export function resetRateLimitState(): void {
  rateLimitState.lastRequestTs = 0;
  rateLimitState.backoffUntilTs = 0;
  rateLimitState.consecutiveErrors = 0;
}

/**
 * Get current health label
 *
 * @returns Health label based on rate limit state
 */
export function getHttpHealthLabel(): SdkHealthLabel {
  if (isInBackoff()) {
    return "BACKOFF";
  }
  if (rateLimitState.consecutiveErrors > 0) {
    return "RATE_LIMITED";
  }
  return "HTTP_OK";
}
