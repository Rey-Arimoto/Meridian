/**
 * PR176: v1.4 Change Interaction Detector v1 - Reader
 *
 * Purpose:
 *   Read PR173 decisions, PR174 effects, PR175 regressions for interaction analysis.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No file modification
 *   - Defensive: Handles missing/corrupt files gracefully
 */

import { readRecentDecisionAcksV1 } from "../decision/store";
import { readRecentEffectReportsV1 } from "../effect/store";
import { readRecentRegressionReportsV1 } from "../regress/store";
import { DecisionAckRecordV1 } from "../decision/types";
import { PatchEffectReportV1 } from "../effect/types";
import { RegressionReportV1 } from "../regress/types";

/**
 * Read recent decisions (ADOPT events)
 *
 * @param options - Read options
 * @returns Decisions and status
 */
export function readRecentDecisionsForInteraction(options: {
  tail?: number;
}): {
  status: "OK" | "PARTIAL" | "ERROR";
  records: DecisionAckRecordV1[];
  warnings: string[];
} {
  try {
    const { status, records, warnings } = readRecentDecisionAcksV1({
      tail: options.tail || 100,
      decision: "ADOPT", // Only ADOPT events for interaction detection
    });

    if (status === "ERROR") {
      return {
        status: "ERROR",
        records: [],
        warnings: [...warnings, "ERROR_READING_DECISIONS"],
      };
    }

    if (records.length === 0) {
      return {
        status: "PARTIAL",
        records: [],
        warnings: [...warnings, "WARN_NO_ADOPT_DECISIONS_FOUND"],
      };
    }

    return {
      status: "OK",
      records,
      warnings,
    };
  } catch (error) {
    return {
      status: "ERROR",
      records: [],
      warnings: ["ERROR_READING_DECISIONS"],
    };
  }
}

/**
 * Read recent effects for proposals
 *
 * @param options - Read options
 * @returns Effects and status
 */
export function readRecentEffectsForInteraction(options: {
  tail?: number;
  proposalIds?: string[];
}): {
  status: "OK" | "PARTIAL" | "ERROR";
  reports: PatchEffectReportV1[];
  warnings: string[];
} {
  try {
    const { reports, warnings } = readRecentEffectReportsV1({
      tail: options.tail || 200,
    });

    // Filter by proposalIds if provided
    let filtered = reports;
    if (options.proposalIds && options.proposalIds.length > 0) {
      filtered = reports.filter((r) =>
        options.proposalIds!.includes(r.decisionAckRef.proposalId || "")
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
      status: "PARTIAL", // Effects are optional
      reports: [],
      warnings: ["WARN_EFFECTS_READ_ERROR"],
    };
  }
}

/**
 * Read recent regressions for proposals (optional)
 *
 * @param options - Read options
 * @returns Regressions and status
 */
export function readRecentRegressionsForInteraction(options: {
  tail?: number;
  proposalIds?: string[];
}): {
  status: "OK" | "PARTIAL" | "ERROR";
  reports: RegressionReportV1[];
  warnings: string[];
} {
  try {
    const { reports, warnings } = readRecentRegressionReportsV1({
      tail: options.tail || 200,
    });

    // Filter by proposalIds if provided
    let filtered = reports;
    if (options.proposalIds && options.proposalIds.length > 0) {
      filtered = reports.filter((r) =>
        options.proposalIds!.includes(r.analysis.proposalId)
      );
    }

    if (filtered.length === 0) {
      return {
        status: "PARTIAL",
        reports: [],
        warnings: [...warnings, "WARN_NO_REGRESSIONS_FOUND"],
      };
    }

    return {
      status: "OK",
      reports: filtered,
      warnings,
    };
  } catch (error) {
    return {
      status: "PARTIAL", // Regressions are optional
      reports: [],
      warnings: ["WARN_REGRESSIONS_UNAVAILABLE"],
    };
  }
}

/**
 * Adoption event (simplified from DecisionAckRecordV1)
 */
export interface AdoptionEvent {
  proposalId: string;
  ts: number;
  decision: "ADOPT" | "HOLD" | "REJECT" | "UNKNOWN";
  timeLabel?: string;
}

/**
 * Extract adoption events from decision records
 *
 * @param records - Decision ack records
 * @returns Adoption events sorted by timestamp
 */
export function extractAdoptionEvents(
  records: DecisionAckRecordV1[]
): AdoptionEvent[] {
  const events: AdoptionEvent[] = [];

  for (const record of records) {
    if (record.rationale.decision === "ADOPT" && record.refs.proposalId) {
      events.push({
        proposalId: record.refs.proposalId,
        ts: record.ts,
        decision: "ADOPT",
        timeLabel: record.timeLabel,
      });
    }
  }

  // Sort by timestamp
  events.sort((a, b) => a.ts - b.ts);

  return events;
}
