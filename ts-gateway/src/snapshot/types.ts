/**
 * PR165: v1.4 Market Regime Snapshot Export v1 - Types
 *
 * Purpose:
 *   Define snapshot schema for exporting "what Meridian saw at that moment"
 *   for strategy verification and post-analysis.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Snapshots are observations, not recommendations
 *   - Label-only: CLI/telemetry display uses labels (no numerics)
 *   - Defensive: Never throws, always returns snapshot (even on error)
 *   - No prediction/optimization: Fixed snapshot logic only
 *
 * NOTE:
 *   - Numerics are allowed in saved files (for analysis)
 *   - Numerics are FORBIDDEN in CLI/telemetry display (use guards)
 */

/**
 * Snapshot status (availability of data)
 */
export type SnapshotStatus = "AVAILABLE" | "PARTIAL" | "ERROR";

/**
 * Snapshot kind (type of snapshot)
 */
export type SnapshotKind =
  | "REGIME_SNAPSHOT" // Full market regime snapshot
  | "RUN_SNAPSHOT" // Run-specific snapshot
  | "TICK_SNAPSHOT"; // Supervisor tick snapshot

/**
 * Snapshot presence flags (which components were available)
 */
export interface SnapshotPresence {
  hasOracle: boolean;
  hasObservationLabels: boolean;
  hasShockPhase: boolean;
  hasStress: boolean;
  hasEscalation: boolean;
  hasActionShape: boolean;
  hasTemplateId: boolean;
  hasRoute: boolean;
  hasGate: boolean;
  hasPolicy: boolean;
  hasHardStop: boolean;
  hasCooldown: boolean;
  hasDrift: boolean;
  hasResume: boolean;
}

/**
 * Snapshot labels (label-only domain)
 */
export interface SnapshotLabels {
  // PR154: Observation labels
  impulse?: "TRUE" | "FALSE" | "UNKNOWN";
  thinning?: "TRUE" | "FALSE" | "UNKNOWN";
  dominance?: "BUY" | "SELL" | "NONE" | "UNKNOWN";
  absorption?: "ASK_PRESENT" | "BID_PRESENT" | "RELEASED" | "NONE" | "UNKNOWN";

  // PR149/150/146/147/151: Higher-level labels
  shockPhase?: string; // e.g., PHASE_UP_SHOCK (label-only)
  stress?: string; // CALM/TENSE/STRESSED/UNKNOWN
  stressEscalated?: string; // Same domain
  actionShape?: string; // FREEZE_STATE / CONSIDER_ONLY / ...
  templateId?: string; // TPL_RISK_90 etc.
  route?: string; // ROUTE_CETUS / ROUTE_DEEPBOOK / NONE
  gateDecision?: "PASS" | "BLOCK" | "ERROR";
  blockReason?: string; // Label-only
  policyDecision?: "ALLOW" | "DENY";
  policyReason?: string; // Label-only
  hardStop?: "ACTIVE" | "INACTIVE" | "UNKNOWN";
  cooldown?: "ACTIVE" | "INACTIVE" | "UNKNOWN";
  drift?: "SMALL" | "OK" | "UNKNOWN";
  resume?: "NONE" | "RESUMABLE" | "WAIT" | "ABANDON" | "UNKNOWN";
}

/**
 * Snapshot numerics (save-only, NEVER display in CLI/telemetry)
 */
export interface SnapshotNumerics {
  // Allowed in saved files for analysis
  notionalUsd?: number;
  targetNotionalUsd?: number;
  oracleAgeMs?: number;
}

/**
 * Build provenance (which tag/commit generated this snapshot)
 */
export interface SnapshotBuild {
  tag?: string;
  commit?: string;
}

/**
 * Market Regime Snapshot v1
 *
 * Purpose:
 *   Capture "what Meridian saw at that moment" for strategy verification.
 *   NOT a recommendation or execution signal.
 *
 * Storage:
 *   - Saved to JSONL file (~/.meridian/snapshots.log by default)
 *   - One snapshot per line
 *   - Append-only (never modified)
 *
 * Display:
 *   - CLI/telemetry: label-only (numerics sanitized)
 *   - File: raw snapshot (numerics included for analysis)
 */
export interface MarketRegimeSnapshotV1 {
  // Schema version
  version: "v1.0";

  // Snapshot kind
  kind: SnapshotKind;

  // Status (availability of data)
  status: SnapshotStatus;

  // Timestamp (epoch ms, internal only, sanitized in display)
  ts: number;

  // Snapshot ID (deterministic-ish, e.g., "snap_<ts>_<rand>")
  id: string;

  // Warnings (label-only, sanitized by guards)
  warnings: string[];

  // Presence flags (which components were available)
  presence: SnapshotPresence;

  // Labels (label-only domain)
  labels: SnapshotLabels;

  // Numerics (save-only, NEVER display)
  numerics?: SnapshotNumerics;

  // Build provenance (optional)
  build?: SnapshotBuild;
}

/**
 * Sanitized snapshot (for CLI/telemetry display)
 *
 * Purpose:
 *   Snapshot with numerics removed/masked for label-only display.
 *   Timestamp converted to label (T_RECENT, T_MIN, T_HOUR, T_OLD).
 */
export interface SanitizedSnapshot {
  version: "v1.0";
  kind: SnapshotKind;
  status: SnapshotStatus;
  timeLabel: string; // T_RECENT / T_MIN / T_HOUR / T_OLD
  idLabel: string; // HAS_ID / NO_ID
  warnings: string[];
  presence: SnapshotPresence;
  labels: SnapshotLabels;
  // numerics field is REMOVED (not displayed)
}
