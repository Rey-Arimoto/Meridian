/**
 * PR181: v1.4 Observe 1s Loop + Chunk 10s + Immediate STOP v1 - Loop
 * PR181a: v1.4 Spec Lock ≠ STOP (Run-on-Old-Spec) v1
 * PR183: v1.4 Observation Load + Cost Control (Fixed Rules) v1
 *
 * Purpose:
 *   1-second observation loop for state updates with immediate STOP capability.
 *   Spec lock status is visible but NOT a STOP reason (execution continues with activeSpec).
 *   Tier-based load control: WS alive → no HTTP fetch. WS dead → tier-based intervals.
 *
 * Constitutional Constraints:
 *   - Fixed rules: No learning, optimization, or prediction
 *   - READ-ONLY: Observation updates state only
 *   - Defensive: Never throws, always returns result
 *   - Separation: Market risk STOP vs spec ACK requirements
 *   - No STOP: Degradation is info only, not a STOP condition
 */

import {
  ObserveStateV1,
  StopTokenV1,
  StopSignal,
  SpecAckStatusLabel,
  PhaseLabel,
  TrendLabel,
  OracleStatus,
  OBSERVE_INTERVAL_MS,
  ObserveLoopConfig,
} from "./types";
import { sanitizeStringArray, formatTimeLabel } from "./guards";
import {
  DegradeStateV1,
  initDegradeState,
  updateDegradeState,
  updateLastFetchTimestamp,
} from "./degrade";

/**
 * Global stop token (in-memory)
 */
let globalStopToken: StopTokenV1 = {
  status: "CLEAR",
  reason: "INIT",
  tsLabel: "T_UNKNOWN",
};

/**
 * Get current stop token
 *
 * @returns Current stop token
 */
export function getStopToken(): StopTokenV1 {
  return { ...globalStopToken };
}

/**
 * Update stop token
 *
 * @param status - Stop token status
 * @param reason - Reason label
 */
export function updateStopToken(status: "STOP" | "CLEAR", reason: string): void {
  globalStopToken = {
    status,
    reason,
    tsLabel: formatTimeLabel(Date.now()),
  };
}

/**
 * Evaluate spec ACK status (PR181a)
 *
 * @param specLockStatus - Spec lock status from PR179
 * @param hasActiveSpec - Whether activeSpec exists
 * @returns Spec ACK status label
 */
export function evaluateSpecAckStatus(
  specLockStatus: string = "UNKNOWN",
  hasActiveSpec: boolean = false
): SpecAckStatusLabel {
  try {
    // SPEC_ACK_OK: activeSpec exists and latest spec is ACKed
    if (specLockStatus === "ACTIVE_OK" && hasActiveSpec) {
      return "SPEC_ACK_OK";
    }

    // SPEC_ACK_PENDING: latest spec not ACKed, but activeSpec exists
    if (specLockStatus === "LOCKED_PENDING_ACK" && hasActiveSpec) {
      return "SPEC_ACK_PENDING";
    }

    // SPEC_ACK_EXPIRED: TTL exceeded, but activeSpec exists
    if (specLockStatus === "LOCKED_EXPIRED" && hasActiveSpec) {
      return "SPEC_ACK_EXPIRED";
    }

    // SPEC_ACK_REQUIRED_BOOTSTRAP: no activeSpec (initial state)
    if (!hasActiveSpec) {
      return "SPEC_ACK_REQUIRED_BOOTSTRAP";
    }

    // Unknown state
    return "SPEC_ACK_UNKNOWN";
  } catch (error) {
    // Defensive: Return unknown on error
    return "SPEC_ACK_UNKNOWN";
  }
}

/**
 * Evaluate STOP signal based on observe state (fixed rules)
 *
 * PR181a: Spec lock is NOT a STOP reason. Market execution continues with activeSpec.
 *
 * @param observeState - Current observe state
 * @param hardStopActive - HardStop active flag (from PR156)
 * @returns Stop signal
 */
export function evaluateStopSignal(
  observeState: ObserveStateV1,
  hardStopActive: boolean = false
): StopSignal {
  const warnings: string[] = [];

  try {
    // STOP conditions (fixed table)

    // 1. Phase-based STOP
    const stopPhases: PhaseLabel[] = [
      "PHASE_UNKNOWN",
      "PHASE_ERROR",
      "PHASE_PRE_SHOCK",
      "PHASE_UP_SHOCK",
      "PHASE_DOWN_SHOCK",
      "PHASE_UP_REVERSAL",
      "PHASE_DOWN_REVERSAL",
    ];

    if (stopPhases.includes(observeState.phaseLabel)) {
      return "STOP";
    }

    // 2. Oracle-based STOP
    if (
      observeState.oracleStatus === "STALE" ||
      observeState.oracleStatus === "ERROR"
    ) {
      return "STOP";
    }

    // 3. HardStop active (PR156)
    if (hardStopActive) {
      return "STOP";
    }

    // PR181a: Spec lock is NOT a STOP reason (removed)
    // Execution continues with activeSpec even if latest spec is not ACKed

    // No STOP conditions met
    return "NO_STOP";
  } catch (error) {
    // Defensive: If evaluation fails, default to STOP (safe side)
    return "STOP";
  }
}

/**
 * Evaluate observe state
 *
 * @param deps - Dependencies (for testing)
 * @returns Observe state
 */
export async function evaluateObserveState(deps?: {
  getPhaseLabel?: () => Promise<PhaseLabel>;
  getTrendLabel?: () => Promise<TrendLabel>;
  getOracleStatus?: () => Promise<OracleStatus>;
  getLabelsPresence?: () => Promise<"HAS_LABELS" | "NO_LABELS">;
}): Promise<ObserveStateV1> {
  const warnings: string[] = [];

  try {
    // Step 1: Get phase label (from PR149/161)
    // For v1, use stub or fake phase detection
    const phaseLabel =
      deps?.getPhaseLabel ? await deps.getPhaseLabel() : "PHASE_NORMAL";

    // Step 2: Get trend label (fixed rules for v1)
    const trendLabel =
      deps?.getTrendLabel ? await deps.getTrendLabel() : "UNKNOWN";

    // Step 3: Get oracle status (from PR155)
    const oracleStatus =
      deps?.getOracleStatus ? await deps.getOracleStatus() : "UNKNOWN";

    // Step 4: Get labels presence (from PR154)
    const labelsPresence =
      deps?.getLabelsPresence
        ? await deps.getLabelsPresence()
        : "NO_LABELS";

    // Evaluate STOP signal (will be updated externally with hardStop/specLock)
    const stopSignal: StopSignal = "UNKNOWN";

    return {
      status: "AVAILABLE",
      phaseLabel,
      trendLabel,
      labelsPresence,
      oracleStatus,
      stopSignal,
      warnings: sanitizeStringArray(warnings),
    };
  } catch (error) {
    warnings.push("ERROR_OBSERVE_STATE_EVAL_FAILED");

    return {
      status: "ERROR",
      phaseLabel: "PHASE_ERROR",
      trendLabel: "UNKNOWN",
      labelsPresence: "NO_LABELS",
      oracleStatus: "ERROR",
      stopSignal: "STOP",
      warnings: sanitizeStringArray(warnings),
    };
  }
}

/**
 * Run single observe tick
 *
 * @param deps - Dependencies
 * @returns Observe state
 */
export async function runObserveTick(deps?: {
  stateStore?: any;
  telemetryLogger?: any;
  getPhaseLabel?: () => Promise<PhaseLabel>;
  getTrendLabel?: () => Promise<TrendLabel>;
  getOracleStatus?: () => Promise<OracleStatus>;
  getLabelsPresence?: () => Promise<"HAS_LABELS" | "NO_LABELS">;
  getHardStopActive?: () => Promise<boolean>;
  getSpecLockStatus?: () => Promise<string>; // PR181a: spec lock status
  getHasActiveSpec?: () => Promise<boolean>; // PR181a: activeSpec presence
  fetchObservationSnapshotV1?: () => Promise<any>; // PR182: real observation source
  getDegradeState?: () => Promise<DegradeStateV1 | undefined>; // PR183: degrade state
  getWsAlive?: () => Promise<boolean | "UNKNOWN">; // PR183: WS alive status
  getHttpHealth?: () => Promise<string>; // PR183: HTTP health label
}): Promise<ObserveStateV1> {
  try {
    // PR183: Get degrade state and evaluate load control
    const degradeState =
      (await deps?.getDegradeState?.()) || initDegradeState();
    const wsAlive = (await deps?.getWsAlive?.()) ?? "UNKNOWN";
    const httpHealthRaw = (await deps?.getHttpHealth?.()) || "UNKNOWN";
    const httpHealth: "HTTP_OK" | "RATE_LIMITED" | "BACKOFF" | "UNKNOWN" =
      httpHealthRaw === "HTTP_OK" ||
      httpHealthRaw === "RATE_LIMITED" ||
      httpHealthRaw === "BACKOFF"
        ? httpHealthRaw
        : "UNKNOWN";
    const nowMs = Date.now();

    const degradeResult = updateDegradeState({
      prev: degradeState,
      wsAlive,
      httpHealth,
      nowMs,
    });

    // PR183: Only fetch if nextFetchAllowed=YES
    let sourceStatus: string = "UNKNOWN";
    let sdkHealth: string = "UNKNOWN";
    let sourceWarnings: string[] = [];
    let didFetch = false;

    if (
      degradeResult.nextFetchAllowed === "YES" &&
      deps?.fetchObservationSnapshotV1
    ) {
      try {
        const snapshot = await deps.fetchObservationSnapshotV1();
        sourceStatus = snapshot.status || "UNKNOWN";
        sdkHealth = snapshot.sdkHealth || "UNKNOWN";
        sourceWarnings = snapshot.warnings || [];
        didFetch = true;

        // Emit telemetry for source status (defensive)
        if (deps?.telemetryLogger) {
          try {
            await deps.telemetryLogger.log("OBSERVE_SOURCE_STATUS", {
              status: sourceStatus,
              sdkHealth,
            });
          } catch {
            // Non-fatal
          }
        }
      } catch (error) {
        // Defensive: Snapshot fetch failed, continue with UNKNOWN
        sourceStatus = "ERROR";
        sdkHealth = "UNKNOWN";
        sourceWarnings = ["SNAPSHOT_FETCH_FAILED"];
        didFetch = true; // Attempted fetch
      }
    } else if (degradeResult.nextFetchAllowed === "NO") {
      // Fetch skipped due to tier/WS logic
      const skipReason =
        wsAlive === true
          ? "WS_ALIVE"
          : degradeResult.observeTier !== "TIER_1S"
          ? "TIER_WAIT"
          : "UNKNOWN";

      sourceWarnings.push(`FETCH_SKIPPED_${skipReason}`);

      // Emit telemetry for skipped fetch (defensive)
      if (deps?.telemetryLogger) {
        try {
          await deps.telemetryLogger.log("OBSERVE_FETCH_SKIPPED", {
            reason: skipReason,
            tier: degradeResult.observeTier,
          });
        } catch {
          // Non-fatal
        }
      }
    }

    // PR183: Update degrade state if fetch was attempted
    let updatedDegradeState = degradeResult.next;
    if (didFetch) {
      updatedDegradeState = updateLastFetchTimestamp(
        degradeResult.next,
        nowMs
      );
    }

    // PR183: Emit degrade telemetry (defensive)
    if (deps?.telemetryLogger) {
      try {
        await deps.telemetryLogger.log("OBSERVE_DEGRADE_STATUS", {
          tier: degradeResult.observeTier,
          degraded: degradeResult.observeDegraded,
          nextFetchAllowed: degradeResult.nextFetchAllowed,
        });
      } catch {
        // Non-fatal
      }
    }

    // Evaluate observe state
    const observeState = await evaluateObserveState({
      getPhaseLabel: deps?.getPhaseLabel,
      getTrendLabel: deps?.getTrendLabel,
      getOracleStatus: deps?.getOracleStatus,
      getLabelsPresence: deps?.getLabelsPresence,
    });

    // PR182: Add source status to observe state
    observeState.sourceStatus = sourceStatus;
    observeState.sdkHealth = sdkHealth;
    observeState.warnings.push(...sourceWarnings);

    // PR183: Add degrade status to observe state (label-only)
    observeState.observeTier = degradeResult.observeTier;
    observeState.observeDegraded = degradeResult.observeDegraded;
    observeState.nextFetchAllowed = degradeResult.nextFetchAllowed;
    observeState.warnings.push(...degradeResult.warnings);

    // Get hardStop status
    const hardStopActive = deps?.getHardStopActive
      ? await deps.getHardStopActive()
      : false;

    // PR181a: Get spec lock status and activeSpec presence
    const specLockStatus = deps?.getSpecLockStatus
      ? await deps.getSpecLockStatus()
      : "UNKNOWN";
    const hasActiveSpec = deps?.getHasActiveSpec
      ? await deps.getHasActiveSpec()
      : false;

    // PR181a: Evaluate spec ACK status (visible but not a STOP reason)
    const specAckStatus = evaluateSpecAckStatus(specLockStatus, hasActiveSpec);
    observeState.specAckStatus = specAckStatus;

    // Evaluate STOP signal (PR181a: spec lock is NOT a STOP reason)
    const stopSignal = evaluateStopSignal(observeState, hardStopActive);

    // Update observe state with STOP signal
    observeState.stopSignal = stopSignal;

    // PR181a: Emit WARN events for spec ACK status (defensive)
    if (deps?.telemetryLogger) {
      try {
        if (specAckStatus === "SPEC_ACK_PENDING") {
          await deps.telemetryLogger.log("SPEC_ACK_PENDING_WARN", {
            specLockStatus,
            hasActiveSpec: hasActiveSpec ? "YES" : "NO",
          });
        } else if (specAckStatus === "SPEC_ACK_EXPIRED") {
          await deps.telemetryLogger.log("SPEC_ACK_EXPIRED_WARN", {
            specLockStatus,
            hasActiveSpec: hasActiveSpec ? "YES" : "NO",
          });
        } else if (specAckStatus === "SPEC_ACK_REQUIRED_BOOTSTRAP") {
          await deps.telemetryLogger.log("SPEC_ACK_REQUIRED_BOOTSTRAP_WARN", {
            specLockStatus,
            hasActiveSpec: hasActiveSpec ? "YES" : "NO",
          });
        }
      } catch {
        // Non-fatal
      }
    }

    // Update global stop token
    if (stopSignal === "STOP") {
      const reason = `PHASE_${observeState.phaseLabel}_ORACLE_${observeState.oracleStatus}`;
      updateStopToken("STOP", reason);

      // Emit telemetry (defensive)
      if (deps?.telemetryLogger) {
        try {
          await deps.telemetryLogger.log("STOP_SIGNAL_RAISED", {
            reason,
          });
        } catch {
          // Non-fatal
        }
      }
    } else if (globalStopToken.status === "STOP") {
      // Clear STOP token if conditions are now safe
      updateStopToken("CLEAR", "CONDITIONS_CLEARED");

      // Emit telemetry (defensive)
      if (deps?.telemetryLogger) {
        try {
          await deps.telemetryLogger.log("STOP_SIGNAL_CLEARED", {});
        } catch {
          // Non-fatal
        }
      }
    }

    // Save to state store (defensive)
    if (deps?.stateStore) {
      try {
        await deps.stateStore.patchState({
          observeState,
          degradeState: updatedDegradeState, // PR183: Save degrade state
        });
      } catch {
        // Non-fatal
      }
    }

    // Emit telemetry (defensive)
    if (deps?.telemetryLogger) {
      try {
        await deps.telemetryLogger.log("OBSERVE_TICK", {
          status: observeState.status,
          phaseLabel: observeState.phaseLabel,
          stopSignal: observeState.stopSignal,
        });
      } catch {
        // Non-fatal
      }
    }

    return observeState;
  } catch (error) {
    // Defensive: Return ERROR state
    const errorState: ObserveStateV1 = {
      status: "ERROR",
      phaseLabel: "PHASE_ERROR",
      trendLabel: "UNKNOWN",
      labelsPresence: "NO_LABELS",
      oracleStatus: "ERROR",
      stopSignal: "STOP",
      warnings: ["ERROR_OBSERVE_TICK_FAILED"],
    };

    // Emit telemetry (defensive)
    if (deps?.telemetryLogger) {
      try {
        await deps.telemetryLogger.log("OBSERVE_ERROR", {});
      } catch {
        // Non-fatal
      }
    }

    return errorState;
  }
}

/**
 * Sleep with AbortSignal support
 *
 * @param ms - Milliseconds to sleep
 * @param signal - Optional abort signal
 * @returns Promise that resolves after ms or when aborted
 */
export function sleepMs(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve) => {
    const timeout = setTimeout(() => {
      resolve();
    }, ms);

    // If signal is aborted, resolve immediately
    if (signal) {
      signal.addEventListener("abort", () => {
        clearTimeout(timeout);
        resolve();
      });
    }
  });
}
