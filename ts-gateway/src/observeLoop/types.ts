/**
 * PR181: v1.4 Observe 1s Loop + Chunk 10s + Immediate STOP v1 - Types
 *
 * Purpose:
 *   Define observe loop state and stop token types.
 *
 * Constitutional Constraints:
 *   - Fixed rules: No learning, optimization, or prediction
 *   - READ-ONLY: Observation updates state only
 *   - Label-only: No numerics in normal mode
 *   - Defensive: Types support defensive parsing
 */

/**
 * Observe interval (fixed)
 */
export const OBSERVE_INTERVAL_MS = 1000; // 1 second

/**
 * Observe state status
 */
export type ObserveStatus = "AVAILABLE" | "PARTIAL" | "ERROR";

/**
 * Phase labels (from PR149/161)
 */
export type PhaseLabel =
  | "PHASE_NORMAL"
  | "PHASE_PRE_SHOCK"
  | "PHASE_UP_SHOCK"
  | "PHASE_DOWN_SHOCK"
  | "PHASE_UP_REVERSAL"
  | "PHASE_DOWN_REVERSAL"
  | "PHASE_RECOVERY"
  | "PHASE_UNKNOWN"
  | "PHASE_ERROR";

/**
 * Trend labels
 */
export type TrendLabel = "UP_TREND" | "DOWN_TREND" | "RANGE" | "UNKNOWN";

/**
 * Labels presence
 */
export type LabelsPresence = "HAS_LABELS" | "NO_LABELS";

/**
 * Oracle status
 */
export type OracleStatus = "AVAILABLE" | "STALE" | "ERROR" | "UNKNOWN";

/**
 * Stop signal
 */
export type StopSignal = "STOP" | "NO_STOP" | "UNKNOWN";

/**
 * Spec ACK status label (PR181a)
 */
export type SpecAckStatusLabel =
  | "SPEC_ACK_OK" // activeSpec exists, latest spec is ACKed
  | "SPEC_ACK_PENDING" // latest spec not ACKed, continue with activeSpec
  | "SPEC_ACK_EXPIRED" // TTL exceeded, continue with activeSpec
  | "SPEC_ACK_REQUIRED_BOOTSTRAP" // no activeSpec (initial), ACK required
  | "SPEC_ACK_UNKNOWN";

/**
 * Observe state v1 (saved to state)
 */
export interface ObserveStateV1 {
  status: ObserveStatus;
  phaseLabel: PhaseLabel;
  trendLabel: TrendLabel;
  labelsPresence: LabelsPresence;
  oracleStatus: OracleStatus;
  stopSignal: StopSignal;
  specAckStatus?: SpecAckStatusLabel; // PR181a: spec ACK status (not a STOP reason)
  sourceStatus?: string; // PR182: observation source status (AVAILABLE/PARTIAL/ERROR)
  sdkHealth?: string; // PR182: SDK health label (WS_ALIVE/WS_DEAD/HTTP_OK/etc)
  warnings: string[]; // label-only
}

/**
 * Stop token status
 */
export type StopTokenStatus = "STOP" | "CLEAR";

/**
 * Time label (for display)
 */
export type TimeLabel = "T_RECENT" | "T_MIN" | "T_HOUR" | "T_OLD" | "T_UNKNOWN";

/**
 * Stop token v1 (in-memory)
 */
export interface StopTokenV1 {
  status: StopTokenStatus;
  reason: string; // label-only
  tsLabel: TimeLabel; // time label for display
}

/**
 * Observe loop config
 */
export interface ObserveLoopConfig {
  intervalMs: number; // default: OBSERVE_INTERVAL_MS
  enableTelemetry: boolean; // default: true
}
