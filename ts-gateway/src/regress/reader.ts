/**
 * PR175: v1.4 Regression Guard v1 - Reader
 *
 * Purpose:
 *   Read PR174 effects.log and PR173 decisions.log for regression analysis.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No file modification
 *   - Defensive: Handles missing/corrupt files gracefully
 */

import { readRecentEffectReportsV1 } from "../effect/store";
import { readRecentDecisionAcksV1 } from "../decision/store";
import { PatchEffectReportV1 } from "../effect/types";
import { DecisionAckRecordV1 } from "../decision/types";

/**
 * Read recent effects
 *
 * @param options - Read options
 * @returns Effects and status
 */
export function readRecentEffectsV1(options: {
  tail?: number;
  proposalId?: string;
}): {
  status: "OK" | "PARTIAL" | "ERROR";
  reports: PatchEffectReportV1[];
  warnings: string[];
} {
  try {
    const { reports, warnings } = readRecentEffectReportsV1({
      tail: options.tail || 100,
      effectDecision: undefined, // Read all decisions
    });

    // Filter by proposalId if provided
    let filtered = reports;
    if (options.proposalId) {
      filtered = reports.filter(
        (r) => r.decisionAckRef.proposalId === options.proposalId
      );
    }

    if (filtered.length === 0) {
      return {
        status: "PARTIAL",
        reports: [],
        warnings: [...warnings, "WARN_NO_EFFECTS_FOUND"],
      };
    }

    return {
      status: "OK",
      reports: filtered,
      warnings,
    };
  } catch (error) {
    return {
      status: "ERROR",
      reports: [],
      warnings: ["ERROR_READING_EFFECTS"],
    };
  }
}

/**
 * Read recent decisions (optional)
 *
 * @param options - Read options
 * @returns Decisions and status
 */
export function readRecentDecisionsV1(options: {
  tail?: number;
  proposalId?: string;
}): {
  status: "OK" | "PARTIAL" | "ERROR";
  records: DecisionAckRecordV1[];
  warnings: string[];
} {
  try {
    const { status, records, warnings } = readRecentDecisionAcksV1({
      tail: options.tail || 100,
      proposalId: options.proposalId,
    });

    if (status === "ERROR") {
      return {
        status: "PARTIAL", // Decisions are optional
        records: [],
        warnings: [...warnings, "WARN_DECISIONS_UNAVAILABLE"],
      };
    }

    return {
      status: "OK",
      records,
      warnings,
    };
  } catch (error) {
    return {
      status: "PARTIAL", // Decisions are optional
      records: [],
      warnings: ["WARN_DECISIONS_READ_ERROR"],
    };
  }
}

/**
 * Group effects by proposalId, sorted by timestamp
 *
 * @param reports - Effect reports
 * @returns Map of proposalId to sorted effects
 */
export function groupEffectsByProposal(
  reports: PatchEffectReportV1[]
): Map<string, PatchEffectReportV1[]> {
  const grouped = new Map<string, PatchEffectReportV1[]>();

  for (const report of reports) {
    const proposalId = report.decisionAckRef.proposalId;
    if (!proposalId) {
      continue; // Skip reports without proposalId
    }
    if (!grouped.has(proposalId)) {
      grouped.set(proposalId, []);
    }
    grouped.get(proposalId)!.push(report);
  }

  // Sort each group by timestamp
  for (const [proposalId, effects] of grouped.entries()) {
    effects.sort((a, b) => a.ts - b.ts);
  }

  return grouped;
}
