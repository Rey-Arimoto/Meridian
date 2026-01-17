/**
 * PR182: v1.4 Real Observation SDK Connectors v1 - Types
 *
 * Purpose:
 *   Define types for real observation data fetching from DeepBook WS/HTTP and Cetus Pool.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Observation only, no trading execution
 *   - Defensive: Never throws, always returns result
 *   - Safe defaults: Missing data → UNKNOWN / PARTIAL
 *   - Label-only: No numerics/addresses in logs/CLI/state
 */

/**
 * Fetch status for observation sources
 */
export type FetchStatus = "AVAILABLE" | "PARTIAL" | "ERROR";

/**
 * SDK health label (connection status)
 */
export type SdkHealthLabel =
  | "WS_ALIVE" // WebSocket connected and receiving data
  | "WS_DEAD" // WebSocket disconnected or stale
  | "HTTP_OK" // HTTP polling successful
  | "RATE_LIMITED" // HTTP rate limited
  | "BACKOFF" // Backing off from requests
  | "UNKNOWN"; // Status unknown

/**
 * Presence flags (label-only)
 */
export type PresenceLabel =
  | "HAS_BIDS_ASKS" // Both bids and asks present
  | "HAS_BIDS_ONLY" // Only bids present
  | "HAS_ASKS_ONLY" // Only asks present
  | "NO_BOOK_DATA"; // No order book data

/**
 * Numeric book snapshot (internal use only, never displayed)
 */
export interface NumericBookSnapshot {
  // Bids (buy orders, price descending)
  bids: Array<{
    price: number; // Internal numeric
    quantity: number; // Internal numeric
  }>;

  // Asks (sell orders, price ascending)
  asks: Array<{
    price: number; // Internal numeric
    quantity: number; // Internal numeric
  }>;

  // Metadata (internal)
  timestamp: number; // Internal numeric
  source: "DEEPBOOK_WS" | "DEEPBOOK_HTTP" | "CETUS_POOL" | "UNKNOWN";
}

/**
 * Observation snapshot result
 */
export interface ObservationSnapshotV1 {
  // Fetch status
  status: FetchStatus;

  // Book snapshot (numeric, internal only)
  snapshot?: NumericBookSnapshot;

  // Presence (label-only)
  presence: PresenceLabel;

  // SDK health (label-only)
  sdkHealth: SdkHealthLabel;

  // Warnings (label-only, no numerics)
  warnings: string[];
}

/**
 * DeepBook WS connection status
 */
export interface DeepBookWsStatus {
  connected: boolean;
  lastEventTs?: number; // Internal numeric
  lastEventLabel: "T_RECENT" | "T_MIN" | "T_HOUR" | "T_OLD" | "T_NEVER";
  healthLabel: SdkHealthLabel;
}

/**
 * DeepBook HTTP fetch result
 */
export interface DeepBookHttpResult {
  status: FetchStatus;
  snapshot?: NumericBookSnapshot;
  healthLabel: SdkHealthLabel;
  warnings: string[];
}

/**
 * Cetus pool fetch result
 */
export interface CetusPoolResult {
  status: FetchStatus;
  snapshot?: NumericBookSnapshot;
  healthLabel: SdkHealthLabel;
  warnings: string[];
}

/**
 * Fetcher config
 */
export interface FetcherConfig {
  // DeepBook config
  deepbookWsEnabled: boolean;
  deepbookHttpEnabled: boolean;

  // Cetus config
  cetusEnabled: boolean;

  // Timeouts (ms)
  wsTimeout: number;
  httpTimeout: number;
}

/**
 * Default fetcher config
 */
export const DEFAULT_FETCHER_CONFIG: FetcherConfig = {
  deepbookWsEnabled: true,
  deepbookHttpEnabled: true,
  cetusEnabled: true,
  wsTimeout: 5000,
  httpTimeout: 3000,
};
