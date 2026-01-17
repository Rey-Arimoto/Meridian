/**
 * PR182: v1.4 Real Observation SDK Connectors v1 - Fetcher
 *
 * Purpose:
 *   Main observation snapshot fetcher that orchestrates all sources.
 *   Priority: DeepBook WS → DeepBook HTTP → Cetus Pool
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Observation only
 *   - Defensive: Never throws, always returns result
 *   - Safe defaults: Missing data → PARTIAL with warnings
 *   - Fallback chain: WS → HTTP → Pool
 */

import {
  ObservationSnapshotV1,
  FetcherConfig,
  DEFAULT_FETCHER_CONFIG,
} from "./types";
import {
  createSafeObservationSnapshot,
  evaluatePresence,
  sanitizeStringArray,
} from "./guards";
import { isWsAlive, getCachedSnapshot, getWsStatus } from "./deepbookWs";
import { fetchDeepBookHttp, getHttpHealthLabel } from "./deepbookHttp";
import { fetchCetusPool } from "./cetusPool";

/**
 * Fetch observation snapshot from all available sources
 *
 * Priority order:
 * 1. DeepBook WS (if alive)
 * 2. DeepBook HTTP (fallback)
 * 3. Cetus Pool (fallback)
 *
 * @param config - Fetcher config (optional)
 * @returns Observation snapshot (defensive, never throws)
 */
export async function fetchObservationSnapshotV1(
  config: FetcherConfig = DEFAULT_FETCHER_CONFIG
): Promise<ObservationSnapshotV1> {
  const warnings: string[] = [];

  try {
    // Priority 1: DeepBook WS (if alive and enabled)
    if (config.deepbookWsEnabled) {
      const wsStatus = getWsStatus();

      if (isWsAlive()) {
        const cachedSnapshot = getCachedSnapshot();

        if (cachedSnapshot) {
          warnings.push("SOURCE_DEEPBOOK_WS");

          return {
            status: "AVAILABLE",
            snapshot: cachedSnapshot,
            presence: evaluatePresence(cachedSnapshot),
            sdkHealth: wsStatus.healthLabel,
            warnings: sanitizeStringArray(warnings),
          };
        }
      }

      // WS not alive
      warnings.push(`WS_STATUS_${wsStatus.healthLabel}`);
    }

    // Priority 2: DeepBook HTTP (fallback)
    if (config.deepbookHttpEnabled) {
      const httpResult = await fetchDeepBookHttp();

      if (httpResult.status === "AVAILABLE" && httpResult.snapshot) {
        warnings.push("SOURCE_DEEPBOOK_HTTP");
        warnings.push(...httpResult.warnings);

        return {
          status: "AVAILABLE",
          snapshot: httpResult.snapshot,
          presence: evaluatePresence(httpResult.snapshot),
          sdkHealth: httpResult.healthLabel,
          warnings: sanitizeStringArray(warnings),
        };
      }

      // HTTP failed
      warnings.push(`HTTP_STATUS_${httpResult.healthLabel}`);
      warnings.push(...httpResult.warnings);
    }

    // Priority 3: Cetus Pool (fallback)
    if (config.cetusEnabled) {
      const cetusResult = await fetchCetusPool();

      if (cetusResult.status === "AVAILABLE" && cetusResult.snapshot) {
        warnings.push("SOURCE_CETUS_POOL");
        warnings.push(...cetusResult.warnings);

        return {
          status: "AVAILABLE",
          snapshot: cetusResult.snapshot,
          presence: evaluatePresence(cetusResult.snapshot),
          sdkHealth: cetusResult.healthLabel,
          warnings: sanitizeStringArray(warnings),
        };
      }

      // Cetus failed
      warnings.push("CETUS_UNAVAILABLE");
      warnings.push(...cetusResult.warnings);
    }

    // All sources failed → PARTIAL with warnings
    warnings.push("ALL_SOURCES_UNAVAILABLE");

    return {
      status: "PARTIAL",
      presence: "NO_BOOK_DATA",
      sdkHealth: "UNKNOWN",
      warnings: sanitizeStringArray(warnings),
    };
  } catch (error) {
    // Defensive: Never throw, return ERROR
    warnings.push("FETCH_EXCEPTION");

    return createSafeObservationSnapshot("ERROR", "UNKNOWN", warnings);
  }
}

/**
 * Get current source priority status (for telemetry)
 *
 * @returns Status summary (label-only)
 */
export function getSourcePriorityStatus(): {
  ws: string;
  http: string;
  cetus: string;
} {
  try {
    const wsStatus = getWsStatus();
    const httpHealth = getHttpHealthLabel();

    return {
      ws: wsStatus.healthLabel,
      http: httpHealth,
      cetus: "UNKNOWN", // Cetus doesn't maintain persistent status
    };
  } catch (error) {
    // Defensive
    return {
      ws: "UNKNOWN",
      http: "UNKNOWN",
      cetus: "UNKNOWN",
    };
  }
}
