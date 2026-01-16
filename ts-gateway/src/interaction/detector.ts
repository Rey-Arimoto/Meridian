/**
 * PR176: v1.4 Change Interaction Detector v1 - Detector
 *
 * Purpose:
 *   Detect patch coupling/interaction risks using fixed rules.
 *   Analyzes adoption pairs close in time and their subsequent effects/regressions.
 *
 * Constitutional Constraints:
 *   - Fixed rules: Hardcoded detection logic (no learning)
 *   - READ-ONLY: Observation only
 *   - Defensive: Never throws
 */

import { AdoptionEvent } from "./reader";
import { PatchEffectReportV1 } from "../effect/types";
import { RegressionReportV1 } from "../regress/types";
import {
  InteractionReportV1,
  InteractionKind,
  InteractionStrength,
  InteractionWindowLabel,
  InteractionTimeLabel,
  InteractionEvidence,
  INTERACTION_PARAMS,
} from "./types";

/**
 * Adoption pair (two adoptions close in time)
 */
interface AdoptionPair {
  primary: AdoptionEvent;
  secondary: AdoptionEvent;
  deltaMs: number;
  window: InteractionWindowLabel;
}

/**
 * Detect interactions across all adoption pairs
 *
 * @param adoptions - Sorted adoption events
 * @param effects - Effect reports
 * @param regressions - Regression reports (optional)
 * @returns Interaction reports
 */
export function detectInteractionsV1(
  adoptions: AdoptionEvent[],
  effects: PatchEffectReportV1[],
  regressions: RegressionReportV1[]
): InteractionReportV1[] {
  const reports: InteractionReportV1[] = [];

  // Check minimum data requirement
  if (adoptions.length < INTERACTION_PARAMS.MIN_DECISIONS_FOR_EVAL) {
    return [];
  }

  // Step A: Create adoption pairs
  const pairs = createAdoptionPairs(adoptions);

  // Step B: Analyze each pair
  for (const pair of pairs) {
    const report = analyzePair(pair, effects, regressions);
    if (report) {
      reports.push(report);
    }
  }

  return reports;
}

/**
 * Create adoption pairs from sorted adoption events
 *
 * @param adoptions - Sorted adoption events
 * @returns Adoption pairs
 */
function createAdoptionPairs(adoptions: AdoptionEvent[]): AdoptionPair[] {
  const pairs: AdoptionPair[] = [];

  for (let i = 0; i < adoptions.length - 1; i++) {
    const primary = adoptions[i];
    const secondary = adoptions[i + 1];

    const deltaMs = secondary.ts - primary.ts;

    // Classify window
    const window = classifyWindow(deltaMs);

    // Skip if window is too wide (beyond 24h)
    if (window === "W_UNKNOWN") {
      continue;
    }

    pairs.push({
      primary,
      secondary,
      deltaMs,
      window,
    });
  }

  return pairs;
}

/**
 * Classify time window based on delta
 *
 * @param deltaMs - Time delta in milliseconds
 * @returns Window label
 */
function classifyWindow(deltaMs: number): InteractionWindowLabel {
  const deltaMinutes = deltaMs / (1000 * 60);
  const deltaHours = deltaMs / (1000 * 60 * 60);

  if (deltaMinutes <= INTERACTION_PARAMS.WINDOW_TIGHT_MAX_MINUTES) {
    return "W_TIGHT";
  } else if (deltaHours <= INTERACTION_PARAMS.WINDOW_NORMAL_MAX_HOURS) {
    return "W_NORMAL";
  } else if (deltaHours <= INTERACTION_PARAMS.WINDOW_WIDE_MAX_HOURS) {
    return "W_WIDE";
  } else {
    return "W_UNKNOWN";
  }
}

/**
 * Classify time label (coarse time classification)
 *
 * @param deltaMs - Time delta in milliseconds
 * @returns Time label
 */
function classifyTimeLabel(deltaMs: number): InteractionTimeLabel {
  const deltaMinutes = deltaMs / (1000 * 60);
  const deltaHours = deltaMs / (1000 * 60 * 60);

  if (deltaMinutes <= 5) {
    return "T_RECENT";
  } else if (deltaMinutes <= 60) {
    return "T_MIN";
  } else if (deltaHours <= 24) {
    return "T_HOUR";
  } else {
    return "T_OLD";
  }
}

/**
 * Analyze a single adoption pair for interactions
 *
 * @param pair - Adoption pair
 * @param effects - Effect reports
 * @param regressions - Regression reports
 * @returns Interaction report or null
 */
function analyzePair(
  pair: AdoptionPair,
  effects: PatchEffectReportV1[],
  regressions: RegressionReportV1[]
): InteractionReportV1 | null {
  const warnings: string[] = [];
  const evidence: InteractionEvidence[] = [];

  // Internal scoring (not displayed)
  let score = 0;

  // C1: Window scoring
  if (pair.window === "W_TIGHT") {
    score += 2;
    evidence.push({
      kind: "EVID_DECISION",
      label: "ADOPT_WINDOW_TIGHT",
      strength: "MEDIUM",
    });
  } else if (pair.window === "W_NORMAL") {
    score += 1;
    evidence.push({
      kind: "EVID_DECISION",
      label: "ADOPT_WINDOW_NORMAL",
      strength: "WEAK",
    });
  }

  // C2: Check for regression after pair
  const regressionAfterPair = findRegressionAfterPair(
    pair,
    regressions
  );
  if (regressionAfterPair) {
    score += INTERACTION_PARAMS.STRONG_SCORE;
    evidence.push({
      kind: "EVID_REGRESSION",
      label: "REGRESSION_DETECTED_AFTER_PAIR",
      strength: "STRONG",
    });
  }

  // C3: Check for effect worsening after pair
  const worseningAfterPair = findWorseningAfterPair(pair, effects);
  if (worseningAfterPair) {
    score += INTERACTION_PARAMS.MEDIUM_SCORE;
    evidence.push({
      kind: "EVID_EFFECT",
      label: "EFFECT_WORSENED_AFTER_PAIR",
      strength: "MEDIUM",
    });
  }

  // Determine interaction kind and strength (priority-based)
  let kind: InteractionKind;
  let strength: InteractionStrength;

  if (regressionAfterPair) {
    // Priority 1: Regression after pair
    kind = "INT_PATCH_PAIR_REGRESSION";
    strength = "STRONG";
  } else if (score >= INTERACTION_PARAMS.COUPLING_RISK_SCORE_THRESHOLD) {
    // Priority 2: Coupling risk high
    kind = "INT_COUPLING_RISK_HIGH";
    strength = score >= 5 ? "STRONG" : "MEDIUM";
  } else if (worseningAfterPair) {
    // Priority 3: Worsening after pair
    kind = "INT_PATCH_FOLLOWS_WORSENING";
    strength = "MEDIUM";
  } else if (pair.window === "W_TIGHT") {
    // Priority 4: Multiple adopts same window
    kind = "INT_MULTIPLE_ADOPTS_SAME_WINDOW";
    strength = "MEDIUM";
  } else if (pair.window === "W_NORMAL") {
    kind = "INT_MULTIPLE_ADOPTS_SAME_WINDOW";
    strength = "WEAK";
  } else {
    // No significant interaction
    return null;
  }

  // Sort evidence by strength (STRONG > MEDIUM > WEAK)
  evidence.sort((a, b) => {
    const order: Record<InteractionStrength, number> = {
      STRONG: 3,
      MEDIUM: 2,
      WEAK: 1,
      UNKNOWN: 0,
    };
    return order[b.strength] - order[a.strength];
  });

  // Limit to max evidence
  const limitedEvidence = evidence.slice(0, INTERACTION_PARAMS.MAX_EVIDENCE);

  return {
    kind: "INTERACTION_REPORT_V1",
    status: "AVAILABLE",
    primaryProposalId: pair.primary.proposalId,
    secondaryProposalId: pair.secondary.proposalId,
    primaryDecision: "ADOPT",
    secondaryDecision: "ADOPT",
    interaction: "INTERACTION_DETECTED",
    interactionKind: kind,
    strength,
    window: pair.window,
    timeLabel: classifyTimeLabel(pair.deltaMs),
    evidence: limitedEvidence,
    warnings,
    ts: Date.now(),
  };
}

/**
 * Find regression after pair
 *
 * @param pair - Adoption pair
 * @param regressions - Regression reports
 * @returns True if regression found
 */
function findRegressionAfterPair(
  pair: AdoptionPair,
  regressions: RegressionReportV1[]
): boolean {
  for (const regression of regressions) {
    // Check if regression is for either proposal in the pair
    const matchesPrimary =
      regression.analysis.proposalId === pair.primary.proposalId;
    const matchesSecondary =
      regression.analysis.proposalId === pair.secondary.proposalId;

    if (!matchesPrimary && !matchesSecondary) {
      continue;
    }

    // Check if regression was detected after the pair
    if (regression.ts > pair.secondary.ts) {
      if (regression.analysis.decision === "REGRESSION_DETECTED") {
        return true;
      }
    }
  }

  return false;
}

/**
 * Find effect worsening after pair
 *
 * @param pair - Adoption pair
 * @param effects - Effect reports
 * @returns True if worsening found
 */
function findWorseningAfterPair(
  pair: AdoptionPair,
  effects: PatchEffectReportV1[]
): boolean {
  for (const effect of effects) {
    // Check if effect is for either proposal in the pair
    const matchesPrimary =
      effect.decisionAckRef.proposalId === pair.primary.proposalId;
    const matchesSecondary =
      effect.decisionAckRef.proposalId === pair.secondary.proposalId;

    if (!matchesPrimary && !matchesSecondary) {
      continue;
    }

    // Check if effect was measured after the pair
    if (effect.ts > pair.secondary.ts) {
      if (effect.effectDecision === "EFFECT_WORSENED") {
        return true;
      }
    }
  }

  return false;
}
