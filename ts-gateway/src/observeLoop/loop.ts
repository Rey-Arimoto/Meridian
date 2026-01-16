/**
 * PR181: v1.4 Observe 1s Loop + Chunk 10s + Immediate STOP v1 - Loop
 *
 * Purpose:
 *   1-second observation loop for state updates with immediate STOP capability.
 *
 * Constitutional Constraints:
 *   - Fixed rules: No learning, optimization, or prediction
 *   - READ-ONLY: Observation updates state only
 *   - Defensive: Never throws, always returns result
 */

import {
  ObserveStateV1,
  StopTokenV1,
  StopSignal,
  PhaseLabel,
  TrendLabel,
  OracleStatus,
  OBSERVE_INTERVAL_MS,
  ObserveLoopConfig,
} from "./types";
import { sanitizeStringArray, formatTimeLabel } from "./guards";

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
 * Evaluate STOP signal based on observe state (fixed rules)
 *
 * @param observeState - Current observe state
 * @param hardStopActive - HardStop active flag (from PR156)
 * @param specLockPending - Spec lock pending without activeSpec (from PR179)
 * @returns Stop signal
 */
export function evaluateStopSignal(
  observeState: ObserveStateV1,
  hardStopActive: boolean = false,
  specLockPending: boolean = false
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

    // 4. Spec lock pending without activeSpec (PR179)
    if (specLockPending) {
      return "STOP";
    }

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
  getSpecLockPending?: () => Promise<boolean>;
}): Promise<ObserveStateV1> {
  try {
    // Evaluate observe state
    const observeState = await evaluateObserveState({
      getPhaseLabel: deps?.getPhaseLabel,
      getTrendLabel: deps?.getTrendLabel,
      getOracleStatus: deps?.getOracleStatus,
      getLabelsPresence: deps?.getLabelsPresence,
    });

    // Get hardStop and specLock status
    const hardStopActive = deps?.getHardStopActive
      ? await deps.getHardStopActive()
      : false;
    const specLockPending = deps?.getSpecLockPending
      ? await deps.getSpecLockPending()
      : false;

    // Evaluate STOP signal
    const stopSignal = evaluateStopSignal(
      observeState,
      hardStopActive,
      specLockPending
    );

    // Update observe state with STOP signal
    observeState.stopSignal = stopSignal;

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
        await deps.stateStore.patchState({ observeState });
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
