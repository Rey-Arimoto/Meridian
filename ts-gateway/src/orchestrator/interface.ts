/**
 * PR216: Recovery Orchestration Interface (Scheduler-less Deferred Re-exec) v1
 * PR217: Orchestrator Policy Hooks v1 (Instruction extension)
 *
 * Purpose:
 *   External orchestrator integration for deferred resume re-execution.
 *   Supervisor emits instruction payloads, external orchestrator ACKs and dispatches.
 *   PR217 adds execution timing/condition hints (policy hooks).
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Decision outputs only, no scheduling
 *   - Label-only: All values are strings, no numeric timestamps/durations
 *   - Defensive: Never throws, handles file I/O errors gracefully
 *   - Idempotent: ACK prevents duplicate enqueues
 */

import * as fs from "fs";
import * as path from "path";
import * as os from "os";

/**
 * Orchestration action (label-only)
 */
export type OrchActionV1 = "DEFER" | "MANUAL" | "ABANDON";

/**
 * PR217: Orchestration policy class (label-only)
 */
export type OrchPolicyClassV1 =
  | "NONE"
  | "DELAY_WINDOW"
  | "RETRY_LIMIT"
  | "MARKET_GUARD"
  | "UNKNOWN";

/**
 * PR217: Orchestration "not before" label (label-only, no numeric timestamps)
 */
export type OrchNotBeforeV1 =
  | "NB_0S"
  | "NB_30S"
  | "NB_2M"
  | "NB_5M"
  | "NB_15M"
  | "NB_1H"
  | "UNKNOWN";

/**
 * PR217: Orchestration deadline label (label-only)
 */
export type OrchDeadlineV1 =
  | "DL_1M"
  | "DL_5M"
  | "DL_15M"
  | "DL_1H"
  | "DL_6H"
  | "DL_24H"
  | "NONE"
  | "UNKNOWN";

/**
 * PR217: Orchestration retry limit (label-only)
 */
export type OrchRetryLimitV1 =
  | "RETRY_0"
  | "RETRY_1"
  | "RETRY_3"
  | "RETRY_5"
  | "RETRY_10"
  | "UNKNOWN";

/**
 * PR217: Orchestration market guard (label-only)
 */
export type OrchMarketGuardV1 =
  | "GUARD_NONE"
  | "GUARD_ORACLE_OK"
  | "GUARD_GATE_PASS"
  | "GUARD_LIQUID_OK"
  | "UNKNOWN";

/**
 * PR217: Orchestration policy hooks (label-only)
 */
export interface OrchPolicyHooksV1 {
  orch_policy_class: OrchPolicyClassV1;
  orch_not_before: OrchNotBeforeV1;
  orch_deadline: OrchDeadlineV1;
  orch_retry_limit: OrchRetryLimitV1;
  orch_market_guard: OrchMarketGuardV1;
  orch_hint_codes_status: "PRESENT" | "EMPTY";
  orch_hint_codes: string;
}

/**
 * Orchestration instruction v1 (label-only payload)
 */
export interface OrchestrationInstructionV1 {
  // Schema version
  instruction_version: "ORCH_V1";

  // Correlation keys (from PR208/PR213/PR214/PR215)
  resume_id: string;
  previous_run_id: string;
  stop_reason: string;
  resume_status: string; // RESUMABLE/WAIT/ABANDON

  // Strategy and enforcement context (PR213/PR214)
  resume_strategy?: string;
  enforced_execution_mode?: string;

  // Timing context (PR215)
  delay_class_v1?: string;
  delay_offset_v1?: string;

  // Orchestration action
  orch_action: OrchActionV1;

  // Orchestration hint codes (label-only, pipe-joined, max 8)
  orch_hint_codes_status: "PRESENT" | "EMPTY";
  orch_hint_codes: string;

  // PR217: Policy hooks (optional, backward compatible)
  orch_policy_class?: OrchPolicyClassV1;
  orch_not_before?: OrchNotBeforeV1;
  orch_deadline?: OrchDeadlineV1;
  orch_retry_limit?: OrchRetryLimitV1;
  orch_market_guard?: OrchMarketGuardV1;
}

/**
 * ACK record v1 (label-only)
 */
export interface OrchAckRecordV1 {
  v: "ACK_V1";
  resume_id: string;
  ack_status: "ACKED" | "REJECTED";
}

/**
 * Build orchestration instruction v1
 *
 * @param args - Instruction arguments
 * @returns Orchestration instruction (never throws)
 */
export function buildOrchestrationInstructionV1(args: {
  resumeId: string;
  previousRunId: string;
  stopReason: string;
  resumeStatus: string;
  resumeStrategy?: string;
  enforcedExecutionMode?: string;
  delayClassV1?: string;
  delayOffsetV1?: string;
  hintCodes?: string[];
  policyHooks?: OrchPolicyHooksV1; // PR217: Policy hooks (optional)
}): OrchestrationInstructionV1 {
  try {
    // Derive orch_action from delay_class_v1
    let orchAction: OrchActionV1 = "DEFER";
    if (args.delayClassV1 === "MANUAL") {
      orchAction = "MANUAL";
    } else if (args.resumeStatus === "ABANDON") {
      orchAction = "ABANDON";
    } else if (args.delayClassV1 !== "IMMEDIATE") {
      orchAction = "DEFER";
    }

    // Process hint codes: dedup, sort, truncate to 8
    let hintCodesStatus: "PRESENT" | "EMPTY" = "EMPTY";
    let hintCodesJoined = "";

    if (args.hintCodes && args.hintCodes.length > 0) {
      const uniqueCodes = Array.from(new Set(args.hintCodes)).sort();
      const truncated = uniqueCodes.slice(0, 8);
      if (uniqueCodes.length > 8) {
        truncated.push("REASONS_TRUNCATED");
      }
      hintCodesJoined = truncated.join("|");
      hintCodesStatus = "PRESENT";
    }

    const instruction: OrchestrationInstructionV1 = {
      instruction_version: "ORCH_V1",
      resume_id: args.resumeId,
      previous_run_id: args.previousRunId,
      stop_reason: args.stopReason,
      resume_status: args.resumeStatus,
      resume_strategy: args.resumeStrategy,
      enforced_execution_mode: args.enforcedExecutionMode,
      delay_class_v1: args.delayClassV1,
      delay_offset_v1: args.delayOffsetV1,
      orch_action: orchAction,
      orch_hint_codes_status: hintCodesStatus,
      orch_hint_codes: hintCodesJoined,
    };

    // PR217: Add policy hooks if provided (backward compatible)
    if (args.policyHooks) {
      instruction.orch_policy_class = args.policyHooks.orch_policy_class;
      instruction.orch_not_before = args.policyHooks.orch_not_before;
      instruction.orch_deadline = args.policyHooks.orch_deadline;
      instruction.orch_retry_limit = args.policyHooks.orch_retry_limit;
      instruction.orch_market_guard = args.policyHooks.orch_market_guard;
    }

    return instruction;
  } catch (error) {
    // Defensive: Return minimal valid instruction on error
    return {
      instruction_version: "ORCH_V1",
      resume_id: args.resumeId || "UNKNOWN",
      previous_run_id: args.previousRunId || "UNKNOWN",
      stop_reason: args.stopReason || "UNKNOWN",
      resume_status: args.resumeStatus || "UNKNOWN",
      orch_action: "DEFER",
      orch_hint_codes_status: "EMPTY",
      orch_hint_codes: "",
    };
  }
}

/**
 * Append orchestration instruction to queue file
 *
 * @param instruction - Instruction to enqueue
 * @returns Promise (never throws, catches errors internally)
 */
export async function appendOrchQueueV1(
  instruction: OrchestrationInstructionV1
): Promise<void> {
  try {
    const queuePath = path.join(os.homedir(), ".meridian", "orch_queue.jsonl");

    // Ensure .meridian directory exists
    const dir = path.dirname(queuePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    // Append JSONL line
    const line = JSON.stringify(instruction) + "\n";
    fs.appendFileSync(queuePath, line, "utf8");
  } catch (error) {
    // Defensive: Catch and ignore (telemetry will still record ORCH_ENQUEUE)
    // In production, consider logging to stderr or separate error log
  }
}

/**
 * Load ACK set from ACK file
 *
 * @returns Set of resume_id values that have been ACKed (never throws)
 */
export function loadOrchAckSetV1(): Set<string> {
  try {
    const ackPath = path.join(os.homedir(), ".meridian", "orch_ack.jsonl");

    // Return empty set if file doesn't exist
    if (!fs.existsSync(ackPath)) {
      return new Set();
    }

    // Read file and parse each line
    const content = fs.readFileSync(ackPath, "utf8");
    const lines = content.trim().split("\n");
    const ackedSet = new Set<string>();

    for (const line of lines) {
      if (!line.trim()) continue;

      try {
        const record = JSON.parse(line) as OrchAckRecordV1;
        if (record.v === "ACK_V1" && record.ack_status === "ACKED") {
          ackedSet.add(record.resume_id);
        }
      } catch (parseError) {
        // Defensive: Skip malformed lines
        continue;
      }
    }

    return ackedSet;
  } catch (error) {
    // Defensive: Return empty set on any error
    return new Set();
  }
}
