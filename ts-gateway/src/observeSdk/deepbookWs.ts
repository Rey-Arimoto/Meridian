/**
 * PR182: v1.4 Real Observation SDK Connectors v1 - DeepBook WebSocket
 *
 * Purpose:
 *   WebSocket connection management for DeepBook orderbook streaming.
 *   Maintains internal TopK cache updated from WS events.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Observation only
 *   - Defensive: Never throws, returns PARTIAL/ERROR on failure
 *   - Safe defaults: WS dead → WS_DEAD label
 *   - Optional dependency: Works without SDK (returns ERROR + warnings)
 */

import {
  NumericBookSnapshot,
  DeepBookWsStatus,
  SdkHealthLabel,
} from "./types";
import { formatTimeLabel } from "./guards";

/**
 * WS connection state (singleton-ish)
 */
let wsConnection: {
  connected: boolean;
  lastEventTs: number;
  cachedSnapshot: NumericBookSnapshot | null;
} = {
  connected: false,
  lastEventTs: 0,
  cachedSnapshot: null,
};

/**
 * Get WS connection status
 *
 * @returns WS status with health label
 */
export function getWsStatus(): DeepBookWsStatus {
  const lastEventLabel = formatTimeLabel(wsConnection.lastEventTs);

  // Determine health
  let healthLabel: SdkHealthLabel = "UNKNOWN";
  if (wsConnection.connected) {
    const age = Date.now() - wsConnection.lastEventTs;
    if (age < 30_000) {
      // Recent event (< 30s)
      healthLabel = "WS_ALIVE";
    } else {
      // Connected but stale
      healthLabel = "WS_DEAD";
    }
  } else {
    healthLabel = "WS_DEAD";
  }

  return {
    connected: wsConnection.connected,
    lastEventTs: wsConnection.lastEventTs,
    lastEventLabel,
    healthLabel,
  };
}

/**
 * Connect to DeepBook WS
 *
 * NOTE: This is a stub for v1. Real SDK integration in future PR.
 *
 * @returns Success/failure (defensive)
 */
export function connectWs(): boolean {
  try {
    // TODO: Real WS connection logic
    // For now, mark as not connected (SDK not integrated)
    wsConnection.connected = false;
    wsConnection.lastEventTs = 0;
    wsConnection.cachedSnapshot = null;

    return false; // SDK not integrated yet
  } catch (error) {
    // Defensive: Never throw
    wsConnection.connected = false;
    return false;
  }
}

/**
 * Disconnect from DeepBook WS
 */
export function disconnectWs(): void {
  try {
    // TODO: Real WS disconnect logic
    wsConnection.connected = false;
    wsConnection.lastEventTs = 0;
    wsConnection.cachedSnapshot = null;
  } catch (error) {
    // Defensive: Suppress error
  }
}

/**
 * Check if WS is alive (recent data)
 *
 * @returns True if WS is alive
 */
export function isWsAlive(): boolean {
  const status = getWsStatus();
  return status.healthLabel === "WS_ALIVE";
}

/**
 * Get cached snapshot from WS
 *
 * @returns Cached snapshot or null
 */
export function getCachedSnapshot(): NumericBookSnapshot | null {
  try {
    if (!isWsAlive()) {
      return null;
    }

    return wsConnection.cachedSnapshot;
  } catch (error) {
    // Defensive: Return null on error
    return null;
  }
}

/**
 * Update cached snapshot (called by WS event handler)
 *
 * NOTE: This would be called when WS events arrive.
 *
 * @param snapshot - New snapshot from WS
 */
export function updateCachedSnapshot(snapshot: NumericBookSnapshot): void {
  try {
    wsConnection.cachedSnapshot = snapshot;
    wsConnection.lastEventTs = Date.now();
  } catch (error) {
    // Defensive: Suppress error
  }
}

/**
 * Simulate WS event (for testing)
 *
 * @param snapshot - Snapshot to inject
 */
export function simulateWsEvent(snapshot: NumericBookSnapshot): void {
  wsConnection.connected = true;
  wsConnection.lastEventTs = Date.now();
  wsConnection.cachedSnapshot = snapshot;
}

/**
 * Reset WS state (for testing)
 */
export function resetWsState(): void {
  wsConnection.connected = false;
  wsConnection.lastEventTs = 0;
  wsConnection.cachedSnapshot = null;
}
