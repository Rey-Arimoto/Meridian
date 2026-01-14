/**
 * PR153: v1.4 Execution Router (READ-ONLY)
 *
 * Purpose:
 *   Compare quotes from multiple venues and select best route.
 *   Fixed rule-based selection (no learning, no optimization).
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No execution, just route selection
 *   - Fixed rules: First-match-wins priority
 *   - Deterministic: Same inputs → same output
 *
 * Router Priority (fixed):
 *   1. Both unavailable/error → NONE
 *   2. Only one available → that venue
 *   3. Both available → compare by:
 *      a. Impact (LOW < MED < HIGH < UNKNOWN)
 *      b. Depth (OK > THIN > UNKNOWN)
 *      c. Fee (LOW < MED < HIGH)
 *      d. Tie-break: CETUS (fixed preference)
 */

import {
  QuoteResult,
  QuoteVenue,
  ImpactLabel,
  DepthLabel,
  FeeLabel,
} from "./quotes";

/**
 * Route plan (selected venue + reasoning)
 */
export interface RoutePlan {
  // Selected venue (NONE if no quotes available)
  venue: "CETUS" | "DEEPBOOK" | "NONE";

  // Reason labels (for debugging/logging)
  reasonLabels: string[];

  // Chosen quote (if any)
  chosenQuote?: QuoteResult;
}

/**
 * Impact priority (lower is better)
 */
const IMPACT_PRIORITY: Record<ImpactLabel, number> = {
  IMPACT_LOW: 1,
  IMPACT_MED: 2,
  IMPACT_HIGH: 3,
  IMPACT_UNKNOWN: 4,
};

/**
 * Depth priority (lower is better)
 */
const DEPTH_PRIORITY: Record<DepthLabel, number> = {
  DEPTH_OK: 1,
  DEPTH_THIN: 2,
  DEPTH_UNKNOWN: 3,
};

/**
 * Fee priority (lower is better)
 */
const FEE_PRIORITY: Record<FeeLabel, number> = {
  FEE_LOW: 1,
  FEE_MED: 2,
  FEE_HIGH: 3,
  FEE_UNKNOWN: 4,
};

/**
 * Select route from quotes
 *
 * @param quotes - Array of quotes from different venues
 * @returns Route plan
 *
 * Fixed router logic:
 *   1. Both unavailable/error → NONE
 *   2. Only one available → that venue
 *   3. Both available → compare impact → depth → fee → tie-break CETUS
 */
export function selectRoute(quotes: QuoteResult[]): RoutePlan {
  const reasonLabels: string[] = [];

  // Defensive: Handle empty quotes
  if (!quotes || quotes.length === 0) {
    reasonLabels.push("ROUTE_NO_QUOTES");
    return { venue: "NONE", reasonLabels };
  }

  // Filter available quotes
  const availableQuotes = quotes.filter((q) => q.status === "AVAILABLE");

  // Rule 1: No available quotes → NONE
  if (availableQuotes.length === 0) {
    reasonLabels.push("ROUTE_NO_AVAILABLE_QUOTES");
    return { venue: "NONE", reasonLabels };
  }

  // Rule 2: Only one available → use it
  if (availableQuotes.length === 1) {
    const chosen = availableQuotes[0];
    reasonLabels.push("ROUTE_ONLY_ONE_AVAILABLE");
    reasonLabels.push(`ROUTE_VENUE_${chosen.venue}`);

    return {
      venue: chosen.venue,
      reasonLabels,
      chosenQuote: chosen,
    };
  }

  // Rule 3: Multiple available → compare
  // Sort by impact → depth → fee → venue (CETUS preferred)
  const sortedQuotes = [...availableQuotes].sort((a, b) => {
    // Compare impact (lower is better)
    const impactDiff = IMPACT_PRIORITY[a.impact] - IMPACT_PRIORITY[b.impact];
    if (impactDiff !== 0) return impactDiff;

    // Compare depth (lower is better)
    const depthDiff = DEPTH_PRIORITY[a.depth] - DEPTH_PRIORITY[b.depth];
    if (depthDiff !== 0) return depthDiff;

    // Compare fee (lower is better)
    const feeDiff = FEE_PRIORITY[a.fee] - FEE_PRIORITY[b.fee];
    if (feeDiff !== 0) return feeDiff;

    // Tie-break: CETUS preferred (a=CETUS → -1, b=CETUS → 1, else 0)
    if (a.venue === "CETUS" && b.venue !== "CETUS") return -1;
    if (a.venue !== "CETUS" && b.venue === "CETUS") return 1;

    return 0;
  });

  // Select best quote
  const chosen = sortedQuotes[0];

  reasonLabels.push("ROUTE_BEST_QUOTE");
  reasonLabels.push(`ROUTE_VENUE_${chosen.venue}`);
  reasonLabels.push(`ROUTE_IMPACT_${chosen.impact}`);
  reasonLabels.push(`ROUTE_DEPTH_${chosen.depth}`);
  reasonLabels.push(`ROUTE_FEE_${chosen.fee}`);

  return {
    venue: chosen.venue,
    reasonLabels,
    chosenQuote: chosen,
  };
}

/**
 * Check if route plan is executable
 *
 * @param plan - Route plan
 * @returns True if route is executable (venue !== NONE)
 */
export function isRouteExecutable(plan: RoutePlan): boolean {
  return plan.venue !== "NONE";
}
