/**
 * PR176: v1.4 Change Interaction Detector v1 - Store
 *
 * Purpose:
 *   JSONL storage for interaction reports.
 *   Append-only audit trail at ~/.meridian/interactions.log
 *
 * Constitutional Constraints:
 *   - Append-only: Never modify/delete existing records
 *   - Defensive: Handles missing/corrupt files gracefully
 */

import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { InteractionReportV1 } from "./types";

/**
 * Get interaction log path
 *
 * @returns Path to interactions.log
 */
export function getInteractionLogPath(): string {
  const meridianDir = path.join(os.homedir(), ".meridian");

  // Ensure directory exists
  if (!fs.existsSync(meridianDir)) {
    fs.mkdirSync(meridianDir, { recursive: true });
  }

  return path.join(meridianDir, "interactions.log");
}

/**
 * Append interaction report to log
 *
 * @param report - Interaction report
 * @returns Status and warnings
 */
export function appendInteractionReportV1(report: InteractionReportV1): {
  status: "OK" | "ERROR";
  warnings: string[];
} {
  try {
    const logPath = getInteractionLogPath();
    const line = JSON.stringify(report) + "\n";

    fs.appendFileSync(logPath, line, "utf-8");

    return {
      status: "OK",
      warnings: [],
    };
  } catch (error) {
    return {
      status: "ERROR",
      warnings: ["ERROR_APPENDING_INTERACTION_REPORT"],
    };
  }
}

/**
 * Read recent interaction reports
 *
 * @param options - Read options
 * @returns Reports and warnings
 */
export function readRecentInteractionReportsV1(options: {
  tail?: number;
  proposalId?: string;
}): {
  reports: InteractionReportV1[];
  warnings: string[];
} {
  const warnings: string[] = [];

  try {
    const logPath = getInteractionLogPath();

    // Check if file exists
    if (!fs.existsSync(logPath)) {
      return {
        reports: [],
        warnings: ["WARN_INTERACTION_LOG_NOT_FOUND"],
      };
    }

    // Read file
    const content = fs.readFileSync(logPath, "utf-8");
    const lines = content.trim().split("\n").filter(Boolean);

    // Parse JSONL
    const reports: InteractionReportV1[] = [];

    for (let i = 0; i < lines.length; i++) {
      try {
        const report = JSON.parse(lines[i]) as InteractionReportV1;

        // Validate kind
        if (report.kind !== "INTERACTION_REPORT_V1") {
          warnings.push(`WARN_LINE_${i}_INVALID_KIND`);
          continue;
        }

        reports.push(report);
      } catch (error) {
        warnings.push(`WARN_LINE_${i}_PARSE_ERROR`);
      }
    }

    // Filter by proposalId (matches either primary or secondary)
    let filtered = reports;
    if (options.proposalId) {
      filtered = reports.filter(
        (r) =>
          r.primaryProposalId === options.proposalId ||
          r.secondaryProposalId === options.proposalId
      );
    }

    // Sort by timestamp (newest first)
    filtered.sort((a, b) => b.ts - a.ts);

    // Apply tail limit
    const tail = options.tail || 100;
    const result = filtered.slice(0, tail);

    return {
      reports: result,
      warnings,
    };
  } catch (error) {
    return {
      reports: [],
      warnings: ["ERROR_READING_INTERACTION_LOG"],
    };
  }
}
