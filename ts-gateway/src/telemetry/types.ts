/**
 * PR164: v1.4 Telemetry Types (READ-ONLY)
 *
 * Purpose:
 *   Define event types for append-only audit log.
 *   Events record "what happened" (facts), not predictions or instructions.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Record facts only, no learning, no optimization, no prediction
 *   - Label-only: All labels/warnings are strings, no numerics in display
 *   - Numeric timestamps: Internal only (ts field), never in labels/warnings
 *   - Defensive: Never throws, handles malformed events gracefully
 */

/**
 * Telemetry event types (label-only)
 */
export type TelemetryEventType =
  | "SUPERVISOR_TICK" // Supervisor tick started
  | "RESUME_EVAL" // Resume condition evaluation
  | "RESUME_DECISION" // Resume decision outcome (PR207)
  | "RESUME_REEXEC_ATTEMPT" // Resume re-execution attempt (PR208)
  | "RESUME_REEXEC_RESULT" // Resume re-execution result (PR208)
  | "RESUME_REEXEC_DEFERRED" // Resume re-execution deferred (PR215)
  | "RESUME_REEXEC_ABANDONED" // Resume re-execution abandoned (PR222 hotfix)
  | "RESUME_REEXEC_ABORTED" // Resume re-execution aborted (PR231 invariant violation)
  | "RUN_START" // TWAP run started
  | "RUN_STOP" // TWAP run stopped
  | "CHUNK_START" // Chunk execution started
  | "CHUNK_RESULT" // Chunk execution completed
  | "PHASE_CHANGE" // Phase transition detected (PR211)
  | "PHASE_POLICY_EVAL" // Phase policy evaluation (PR212a)
  | "EXECUTE_ATTEMPT" // Execute attempt (PR195)
  | "EXECUTE_RESULT" // Execute outcome (PR194)
  | "POLICY_BLOCK" // Policy blocked execution
  | "GATE_BLOCK" // Gate blocked execution
  | "ROUTE_SELECTED" // Route selected for chunk
  | "ORACLE_STATUS" // Oracle status check
  | "SNAPSHOT_SAVED" // Snapshot saved (PR165)
  | "SNAPSHOT_ERROR" // Snapshot save error (PR165)
  | "SPEC_LOCK_STATUS" // Spec lock status (PR179)
  | "SPEC_LOCK_EXPIRED" // Spec lock expired (PR179)
  | "SPEC_LOCK_ERROR" // Spec lock error (PR179)
  | "SPEC_ACK_WRITTEN" // Spec ACK written (PR179)
  | "SPEC_RECORD_WRITTEN" // Spec record written (PR179)
  | "OBSERVE_TICK" // Observe loop tick (PR181)
  | "OBSERVE_STATE" // Observe state updated (PR181)
  | "OBSERVE_ERROR" // Observe error (PR181)
  | "STOP_SIGNAL_RAISED" // STOP signal raised (PR181)
  | "STOP_SIGNAL_CLEARED" // STOP signal cleared (PR181)
  | "SPEC_ACK_PENDING_WARN" // Spec ACK pending (PR181a)
  | "SPEC_ACK_EXPIRED_WARN" // Spec ACK expired (PR181a)
  | "SPEC_ACK_REQUIRED_BOOTSTRAP_WARN" // Spec ACK required bootstrap (PR181a)
  | "OBSERVE_SOURCE_STATUS" // Observation source status (PR182)
  | "OBSERVE_WS_STATUS" // DeepBook WS status (PR182)
  | "OBSERVE_HTTP_STATUS" // DeepBook HTTP status (PR182)
  | "OBSERVE_CETUS_STATUS" // Cetus pool status (PR182)
  | "OBSERVE_DEGRADE_STATUS" // Observation degrade status (PR183)
  | "OBSERVE_TIER_CHANGED" // Observation tier changed (PR183)
  | "OBSERVE_FETCH_SKIPPED" // Observation fetch skipped (PR183)
  | "OBSERVE_DEGRADED_LEVEL" // Observe degrade level (PR184)
  | "OBSERVE_DEGRADED_TIGHTENING_APPLIED" // Degrade tightening applied (PR184)
  | "QUOTE_NORMALIZED" // Quote normalized (PR187)
  | "ORCH_ENQUEUE" // Orchestration instruction enqueued (PR216)
  | "ORCH_ACK" // Orchestration ACK received (PR216)
  | "ORCH_DISPATCH" // Orchestration dispatch initiated (PR216)
  | "ORCH_RESULT" // Orchestration dispatch result (PR216)
  | "ERROR"; // Error occurred

/**
 * Telemetry event level
 */
export type TelemetryLevel = "INFO" | "WARN" | "ERROR";

/**
 * Meridian event v1 (single audit record)
 */
export interface MeridianEventV1 {
  // Schema version
  v: "v1";

  // Timestamp (internal numeric only, never displayed as number)
  ts: number;

  // Event level
  level: TelemetryLevel;

  // Event type
  type: TelemetryEventType;

  // Labels (label-only, key-value pairs)
  labels: Record<string, string | undefined>;

  // Warnings (label-only array)
  warnings: string[];
}

/**
 * Common label keys (recommended but not enforced)
 */
export type CommonLabelKey =
  | "phase" // Phase label (PHASE_NORMAL, etc)
  | "stress" // Stress label (STRESS_CALM, etc)
  | "template_id" // Template ID (TPL_RISK_50, etc)
  | "action_shape" // Action shape label
  | "route" // Route label (CETUS, DEEPBOOK, etc)
  | "route_changed" // Route changed (YES/NO)
  | "stop_reason" // Stop reason (STOP_ORACLE_STALE, etc)
  | "gate_reason" // Gate block reason
  | "policy_reason" // Policy block reason
  | "run_status" // Run status (COMPLETED, STOPPED, etc)
  | "chunk_status" // Chunk status (PASS, BLOCK, SKIP, ERROR)
  | "oracle_status"; // Oracle status (AVAILABLE, STALE, ERROR)

/**
 * Create empty event (helper)
 */
export function createEventV1(
  type: TelemetryEventType,
  level: TelemetryLevel = "INFO",
  labels: Record<string, string | undefined> = {},
  warnings: string[] = []
): MeridianEventV1 {
  return {
    v: "v1",
    ts: Date.now(),
    level,
    type,
    labels,
    warnings,
  };
}
