/**
 * PR183: v1.4 Observation Load + Cost Control (Fixed Rules) v1 - Degrade
 *
 * Purpose:
 *   Fixed tier-based degradation to control observation load and API costs.
 *   WS alive → no HTTP fetch. WS dead → tier-based fetch intervals.
 *
 * Constitutional Constraints:
 *   - Fixed rules: No learning, optimization, or prediction
 *   - READ-ONLY: Observation only
 *   - Label-only: No numerics in logs/CLI
 *   - Defensive: Never throws, always returns result
 *   - No STOP: Degradation is info for downstream, not a STOP condition
 */

/**
 * Observe tier (minimum HTTP fetch interval)
 */
export type ObserveTier = "TIER_1S" | "TIER_2S" | "TIER_5S" | "TIER_10S" | "UNKNOWN";

/**
 * Observe degraded flag
 */
export type ObserveDegraded = "YES" | "NO" | "UNKNOWN";

/**
 * Next fetch allowed flag
 */
export type NextFetchAllowed = "YES" | "NO" | "UNKNOWN";

/**
 * Degrade state v1 (internal, never fully displayed)
 */
export interface DegradeStateV1 {
  tier: ObserveTier;
  lastFetchMs?: number; // Internal numeric (never displayed)
  okStreak?: number; // Internal numeric (never displayed)
}

/**
 * Tier interval mapping (ms)
 */
const TIER_INTERVALS: Record<ObserveTier, number> = {
  TIER_1S: 1000,
  TIER_2S: 2000,
  TIER_5S: 5000,
  TIER_10S: 10000,
  UNKNOWN: 10000, // Safe default
};

/**
 * Tier order (for degradation/improvement)
 */
const TIER_ORDER: ObserveTier[] = ["TIER_1S", "TIER_2S", "TIER_5S", "TIER_10S"];

/**
 * Initialize degrade state
 *
 * @returns Initial degrade state
 */
export function initDegradeState(): DegradeStateV1 {
  return {
    tier: "TIER_1S", // Start optimistic
    lastFetchMs: 0,
    okStreak: 0,
  };
}

/**
 * Get tier index
 *
 * @param tier - Tier to find
 * @returns Index in TIER_ORDER
 */
function getTierIndex(tier: ObserveTier): number {
  const idx = TIER_ORDER.indexOf(tier);
  return idx === -1 ? 0 : idx; // Default to TIER_1S if unknown
}

/**
 * Degrade tier by one level
 *
 * @param current - Current tier
 * @returns Degraded tier
 */
function degradeTier(current: ObserveTier): ObserveTier {
  const idx = getTierIndex(current);
  const nextIdx = Math.min(idx + 1, TIER_ORDER.length - 1);
  return TIER_ORDER[nextIdx];
}

/**
 * Improve tier by one level
 *
 * @param current - Current tier
 * @returns Improved tier
 */
function improveTier(current: ObserveTier): ObserveTier {
  const idx = getTierIndex(current);
  const nextIdx = Math.max(idx - 1, 0);
  return TIER_ORDER[nextIdx];
}

/**
 * Evaluate if next fetch is allowed
 *
 * @param tier - Current tier
 * @param lastFetchMs - Last fetch timestamp (internal)
 * @param nowMs - Current timestamp (internal)
 * @returns True if fetch allowed
 */
function isNextFetchAllowed(
  tier: ObserveTier,
  lastFetchMs: number,
  nowMs: number
): boolean {
  const interval = TIER_INTERVALS[tier];
  const elapsed = nowMs - lastFetchMs;
  return elapsed >= interval;
}

/**
 * Update degrade state based on inputs
 *
 * Fixed rules:
 * 1. WS_ALIVE → no HTTP fetch (nextFetchAllowed=NO, observeDegraded=NO)
 * 2. WS_DEAD → tier-based fetch intervals
 * 3. RATE_LIMITED/BACKOFF → degrade tier by 1 level
 * 4. HTTP_OK × 2 consecutive → improve tier by 1 level
 * 5. observeDegraded=YES when WS_DEAD and tier > 1S
 *
 * @param input - Input state
 * @returns Updated state and flags
 */
export function updateDegradeState(input: {
  prev: DegradeStateV1;
  wsAlive: boolean | "UNKNOWN";
  httpHealth: "HTTP_OK" | "RATE_LIMITED" | "BACKOFF" | "UNKNOWN";
  nowMs: number;
}): {
  next: DegradeStateV1;
  nextFetchAllowed: NextFetchAllowed;
  observeTier: ObserveTier;
  observeDegraded: ObserveDegraded;
  warnings: string[];
} {
  const warnings: string[] = [];

  try {
    let tier = input.prev.tier;
    let lastFetchMs = input.prev.lastFetchMs || 0;
    let okStreak = input.prev.okStreak || 0;

    // Rule 1: WS_ALIVE → no HTTP fetch
    if (input.wsAlive === true) {
      return {
        next: {
          tier,
          lastFetchMs,
          okStreak,
        },
        nextFetchAllowed: "NO",
        observeTier: tier,
        observeDegraded: "NO", // WS alive is not degraded
        warnings: [],
      };
    }

    // Rule 2: WS_DEAD or UNKNOWN → tier-based logic
    const fetchAllowed = isNextFetchAllowed(tier, lastFetchMs, input.nowMs);

    // Rule 3: Degrade tier on RATE_LIMITED/BACKOFF
    if (input.httpHealth === "RATE_LIMITED" || input.httpHealth === "BACKOFF") {
      const oldTier = tier;
      tier = degradeTier(tier);
      okStreak = 0; // Reset streak

      if (oldTier !== tier) {
        warnings.push(`TIER_DEGRADED_${oldTier}_TO_${tier}`);
      }
    }

    // Rule 4: Improve tier on HTTP_OK × 2 consecutive
    else if (input.httpHealth === "HTTP_OK") {
      okStreak++;

      if (okStreak >= 2) {
        const oldTier = tier;
        tier = improveTier(tier);
        okStreak = 0; // Reset streak after improvement

        if (oldTier !== tier) {
          warnings.push(`TIER_IMPROVED_${oldTier}_TO_${tier}`);
        }
      }
    }

    // UNKNOWN health → no tier change, preserve streak
    else if (input.httpHealth === "UNKNOWN") {
      // No tier change, no streak reset
    }

    // Rule 5: observeDegraded=YES when WS_DEAD and tier > 1S
    const observeDegraded: ObserveDegraded =
      input.wsAlive === "UNKNOWN"
        ? "UNKNOWN"
        : tier !== "TIER_1S"
        ? "YES"
        : "NO";

    return {
      next: {
        tier,
        lastFetchMs,
        okStreak,
      },
      nextFetchAllowed: fetchAllowed ? "YES" : "NO",
      observeTier: tier,
      observeDegraded,
      warnings,
    };
  } catch (error) {
    // Defensive: Return safe defaults on error
    warnings.push("DEGRADE_UPDATE_ERROR");

    return {
      next: input.prev, // Preserve previous state
      nextFetchAllowed: "NO",
      observeTier: input.prev.tier || "TIER_10S", // Safe default
      observeDegraded: "UNKNOWN",
      warnings,
    };
  }
}

/**
 * Update last fetch timestamp
 *
 * Call this after successfully fetching.
 *
 * @param prev - Previous state
 * @param nowMs - Current timestamp
 * @returns Updated state
 */
export function updateLastFetchTimestamp(
  prev: DegradeStateV1,
  nowMs: number
): DegradeStateV1 {
  return {
    ...prev,
    lastFetchMs: nowMs,
  };
}

/**
 * Get tier label (for display)
 *
 * @param tier - Tier
 * @returns Label-only tier name
 */
export function getTierLabel(tier: ObserveTier): string {
  return tier; // Already label-only
}

/**
 * Get tier interval (internal use only, never display)
 *
 * @param tier - Tier
 * @returns Interval in ms (internal numeric)
 */
export function getTierInterval(tier: ObserveTier): number {
  return TIER_INTERVALS[tier];
}
