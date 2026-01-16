/**
 * PR178: v1.4 Manual Review Trigger Hook v1 - Types
 *
 * Purpose:
 *   Enable human-initiated review pipeline that runs
 *   snapshot → analyze → propose → preview → review in one command.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No execution/policy changes, no trade stops, no state modification
 *   - Analysis only: Market response (automatic) and strategy improvement (manual) are separate
 *   - Defensive: Never throws, handles errors gracefully
 */

/**
 * Review trigger status
 */
export type ReviewTriggerStatus = "TRIGGERED" | "PARTIAL" | "ERROR";

/**
 * Review trigger result v1
 */
export interface ReviewTriggerResultV1 {
  status: ReviewTriggerStatus;

  // Step execution flags
  ranSnapshot: boolean;
  ranAnalyze: boolean;
  ranPropose: boolean;
  ranPreview: boolean;
  ranReview: boolean;

  // Label-only warnings
  warnings: string[];
}

/**
 * Review trigger options
 */
export interface ReviewTriggerOptions {
  tailSnapshots?: number; // Default 200
  priority?: "P0" | "P1" | "P2" | "ALL"; // Filter proposals by priority
}
