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

/**
 * PR218: Orchestration result status (label-only)
 */
export type OrchResultStatusV1 =
  | "DISPATCHED"
  | "SKIPPED_POLICY"
  | "SKIPPED_WINDOW"
  | "FAILED_NETWORK"
  | "FAILED_MARKET"
  | "FAILED_UNKNOWN"
  | "SUCCEEDED"
  | "UNKNOWN";

/**
 * PR218: Orchestration result v1 (label-only)
 */
export interface OrchestrationResultV1 {
  v: "v1";
  resume_id: string;
  result_id: string; // Unique per result line (idempotency key)
  status: OrchResultStatusV1;
  outcome_codes?: string[]; // Label-only codes e.g. ["ORCH_NET_TIMEOUT"]
  hint_codes?: string[]; // Echoed from instruction if available
}

/**
 * PR218: Append orchestration result to result file
 *
 * @param result - Result to record
 * @returns Promise (never throws, catches errors internally)
 */
export async function appendOrchResultV1(
  result: OrchestrationResultV1
): Promise<void> {
  try {
    const resultPath = path.join(os.homedir(), ".meridian", "orch_result.jsonl");

    // Ensure .meridian directory exists
    const dir = path.dirname(resultPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    // Append JSONL line
    const line = JSON.stringify(result) + "\n";
    fs.appendFileSync(resultPath, line, "utf8");
  } catch (error) {
    // Defensive: Catch and ignore (telemetry will still record ORCH_RESULT)
  }
}

/**
 * PR218: Load orchestration result lines from result file
 *
 * @param limit - Maximum number of lines to read (default: 200)
 * @returns Array of result records (never throws, skips malformed lines)
 */
export function loadOrchResultLinesV1(limit = 200): OrchestrationResultV1[] {
  try {
    const resultPath = path.join(os.homedir(), ".meridian", "orch_result.jsonl");

    // Return empty array if file doesn't exist
    if (!fs.existsSync(resultPath)) {
      return [];
    }

    // Read file and parse each line
    const content = fs.readFileSync(resultPath, "utf8");
    const lines = content.trim().split("\n");
    const results: OrchestrationResultV1[] = [];

    // Read up to limit lines (from end, newest first)
    const startIdx = Math.max(0, lines.length - limit);
    for (let i = startIdx; i < lines.length; i++) {
      const line = lines[i];
      if (!line.trim()) continue;

      try {
        const result = JSON.parse(line) as OrchestrationResultV1;
        if (result.v === "v1" && result.resume_id && result.result_id) {
          results.push(result);
        }
      } catch (parseError) {
        // Defensive: Skip malformed lines
        continue;
      }
    }

    return results;
  } catch (error) {
    // Defensive: Return empty array on any error
    return [];
  }
}

/**
 * PR218: Load seen result IDs from seen file
 *
 * @returns Set of result_id values that have been seen (never throws)
 */
export function loadOrchResultSeenSetV1(): Set<string> {
  try {
    const seenPath = path.join(os.homedir(), ".meridian", "orch_result_seen.jsonl");

    // Return empty set if file doesn't exist
    if (!fs.existsSync(seenPath)) {
      return new Set();
    }

    // Read file and collect result_ids
    const content = fs.readFileSync(seenPath, "utf8");
    const lines = content.trim().split("\n");
    const seenSet = new Set<string>();

    for (const line of lines) {
      if (!line.trim()) continue;

      try {
        const record = JSON.parse(line) as { result_id: string };
        if (record.result_id) {
          seenSet.add(record.result_id);
        }
      } catch (parseError) {
        // Defensive: Skip malformed lines
        continue;
      }
    }

    return seenSet;
  } catch (error) {
    // Defensive: Return empty set on any error
    return new Set();
  }
}

/**
 * PR218: Mark result as seen (append to seen file)
 *
 * @param resultId - Result ID to mark as seen
 * @returns Promise (never throws, catches errors internally)
 */
export async function markOrchResultSeenV1(resultId: string): Promise<void> {
  try {
    const seenPath = path.join(os.homedir(), ".meridian", "orch_result_seen.jsonl");

    // Ensure .meridian directory exists
    const dir = path.dirname(seenPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    // Append result_id line
    const line = JSON.stringify({ result_id: resultId }) + "\n";
    fs.appendFileSync(seenPath, line, "utf8");
  } catch (error) {
    // Defensive: Catch and ignore
  }
}
