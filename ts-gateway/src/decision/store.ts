/**
 * PR173: v1.4 Decision Acknowledgement + Reviewer Trace v1 - Store
 *
 * Purpose:
 *   JSONL append-only storage for decision acknowledgement records.
 *   Follows the same pattern as PR165/171 stores.
 *
 * Constitutional Constraints:
 *   - Append-only: No deletion, no modification
 *   - Defensive: Corrupt lines skipped with warnings (never throws)
 *   - File-based: ~/.meridian/decisions.log
 */

import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { DecisionAckRecordV1 } from "./types";

/**
 * Decision Store Config
 */
export interface DecisionStoreConfig {
  /**
   * Custom log path (overrides default)
   */
  path?: string;

  /**
   * Maximum lines to read (for tail)
   */
  maxLines?: number;
}

/**
 * Decision Filter
 */
export interface DecisionFilter {
  /**
   * Tail N most recent records
   */
  tail?: number;

  /**
   * Filter by proposal ID
   */
  proposalId?: string;

  /**
   * Filter by decision (ADOPT/HOLD/REJECT)
   */
  decision?: string;

  /**
   * Filter by reviewer kind
   */
  reviewer?: string;
}

/**
 * Get decision log path
 *
 * @returns Decision log path (~/.meridian/decisions.log)
 */
export function getDecisionLogPath(): string {
  const meridianDir = process.env.MERIDIAN_DECISION_PATH
    ? path.dirname(process.env.MERIDIAN_DECISION_PATH)
    : path.join(os.homedir(), ".meridian");

  const fileName = process.env.MERIDIAN_DECISION_PATH
    ? path.basename(process.env.MERIDIAN_DECISION_PATH)
    : "decisions.log";

  return path.join(meridianDir, fileName);
}

/**
 * Ensure decision log directory exists
 */
function ensureDecisionLogDir(): void {
  const logPath = getDecisionLogPath();
  const dir = path.dirname(logPath);

  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

/**
 * Append decision ack record to log
 *
 * Defensive: Never throws, returns status.
 *
 * @param rec - Decision ack record
 * @param cfg - Store config
 * @returns Append result
 */
export function appendDecisionAckV1(
  rec: DecisionAckRecordV1,
  cfg?: DecisionStoreConfig
): { status: "OK" | "ERROR"; warnings: string[] } {
  const warnings: string[] = [];

  try {
    ensureDecisionLogDir();

    const logPath = cfg?.path || getDecisionLogPath();
    const line = JSON.stringify(rec) + "\n";

    fs.appendFileSync(logPath, line, "utf-8");

    return { status: "OK", warnings };
  } catch (error) {
    // Defensive: Return error status but don't throw
    warnings.push("WARN_DECISION_APPEND_FAILED");
    console.error("ERROR: Failed to append decision ack:", error);

    return { status: "ERROR", warnings };
  }
}

/**
 * Read recent decision ack records
 *
 * Defensive: Corrupt lines skipped with warnings.
 *
 * @param cfg - Store config with optional filter
 * @returns Decision ack records and warnings
 */
export function readRecentDecisionAcksV1(
  cfg: DecisionStoreConfig & DecisionFilter = {}
): { status: "OK" | "ERROR"; records: DecisionAckRecordV1[]; warnings: string[] } {
  const warnings: string[] = [];
  const records: DecisionAckRecordV1[] = [];

  try {
    const logPath = cfg?.path || getDecisionLogPath();

    if (!fs.existsSync(logPath)) {
      warnings.push("WARN_DECISION_LOG_NOT_FOUND");
      return { status: "OK", records: [], warnings };
    }

    const content = fs.readFileSync(logPath, "utf-8");
    const lines = content.split("\n").filter((line) => line.trim().length > 0);

    // Parse all lines
    for (const line of lines) {
      try {
        const rec = JSON.parse(line) as DecisionAckRecordV1;

        // Validate kind
        if (rec.kind !== "DECISION_ACK_V1") {
          warnings.push("WARN_INVALID_RECORD_KIND");
          continue;
        }

        // Apply filters
        if (cfg.proposalId && rec.refs.proposalId !== cfg.proposalId) {
          continue;
        }

        if (cfg.decision && rec.rationale.decision !== cfg.decision) {
          continue;
        }

        if (cfg.reviewer && rec.reviewer !== cfg.reviewer) {
          continue;
        }

        records.push(rec);
      } catch (error) {
        // Corrupt line: Skip and warn
        warnings.push("WARN_CORRUPT_DECISION_LINE");
      }
    }

    // Sort by timestamp (newest first)
    records.sort((a, b) => b.ts - a.ts);

    // Apply tail limit
    const tail = cfg.tail || 20;
    const result = records.slice(0, tail);

    return { status: "OK", records: result, warnings };
  } catch (error) {
    warnings.push("WARN_DECISION_READ_FAILED");
    return { status: "ERROR", records: [], warnings };
  }
}
