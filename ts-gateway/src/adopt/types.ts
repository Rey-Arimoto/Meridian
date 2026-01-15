/**
 * PR168: v1.4 Policy-First Adoption Loop - Types
 *
 * Purpose:
 *   Convert improvement proposals into patch plans and compare before/after
 *   via snapshot replay to close the improvement cycle.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No automatic application (proposals and comparison only)
 *   - Policy-First: Changes that reduce safety are PATCH_NOT_ALLOWED
 *   - Label-only: Normal output uses labels (numeric counts only in debug mode)
 *   - Defensive: Never throws, always returns result
 *   - Deterministic: Fixed rules only (no learning, no optimization)
 */

/**
 * Adopt Status
 *
 * - COMPLETE: Adoption decision made successfully
 * - PARTIAL: Some operations could not be completed
 * - ERROR: Fatal error
 */
export type AdoptStatus = "COMPLETE" | "PARTIAL" | "ERROR";

/**
 * Adopt Priority
 *
 * Same as proposal priority (P0 > P1 > P2)
 */
export type AdoptPriority = "P0" | "P1" | "P2";

/**
 * Adopt Decision
 *
 * - ADOPT: Patch plan is safe and improves metrics (can be adopted)
 * - HOLD: Patch plan needs review or has no clear improvement
 * - REJECT: Patch plan reduces safety or worsens metrics
 */
export type AdoptDecision = "ADOPT" | "HOLD" | "REJECT";

/**
 * Patch Kind
 *
 * Types of patches that can be applied to the system.
 * PATCH_NOT_ALLOWED is used for changes that reduce safety.
 */
export type PatchKind =
  | "PATCH_PHASE_POLICY"         // Phase escalation/resume policy changes
  | "PATCH_GATE_ORDER"           // Gate evaluation order changes
  | "PATCH_SLIPPAGE_RULES"       // Slippage calculation rule changes
  | "PATCH_ORACLE_FRESHNESS"     // Oracle freshness policy changes
  | "PATCH_COOLDOWN_RULES"       // Cooldown duration/behavior changes
  | "PATCH_DRIFT_RULES"          // Drift threshold changes
  | "PATCH_ROUTER_TIEBREAK"      // Router tie-break logic changes
  | "PATCH_NOT_ALLOWED";         // Changes that reduce safety (rejected)

/**
 * Patch Target
 *
 * Component targeted by the patch.
 */
export type PatchTarget =
  | "PHASE_POLICY"
  | "GATE"
  | "SLIPPAGE"
  | "ORACLE"
  | "COOLDOWN"
  | "DRIFT"
  | "ROUTER"
  | "UNKNOWN";

/**
 * Patch Operation
 *
 * A single operation in a patch plan.
 */
export interface PatchOp {
  /**
   * Patch kind
   */
  kind: PatchKind;

  /**
   * Patch target component
   */
  target: PatchTarget;

  /**
   * Operation ID (fixed identifier)
   *
   * Example: "OP_PHASE_RECOVERY_RESUME_V1"
   */
  opId: string;

  /**
   * Change description (label-only)
   *
   * Example: "REMAP_PHASE_POLICY_STOP_TO_WAIT"
   */
  change: string;

  /**
   * Safety guarantees (label-only)
   *
   * Example: ["KEEP_DOUBLE_KEY", "KEEP_LABEL_ONLY", "KEEP_BLOCK_ON_UNCERTAIN"]
   */
  safety: string[];

  /**
   * Reason for NOT_ALLOWED (if applicable)
   *
   * Example: "WOULD_REDUCE_EXECUTION_SAFETY"
   */
  notAllowedReason?: string;
}

/**
 * Patch Plan
 *
 * A plan of operations to implement an improvement proposal.
 */
export interface PatchPlan {
  /**
   * Status
   */
  status: AdoptStatus;

  /**
   * Source proposal ID
   */
  proposalId?: string;

  /**
   * Proposal priority
   */
  priority?: AdoptPriority;

  /**
   * Patch operations (1-3 ops, keep it small)
   */
  ops: PatchOp[];

  /**
   * Warnings
   */
  warnings: string[];
}

/**
 * Compare Signal
 *
 * Signals indicating improvement or worsening after patch application.
 */
export type CompareSignal =
  // Improvements
  | "IMPROVED_BLOCK_DOMINANCE"      // Gate BLOCK ratio decreased
  | "IMPROVED_STOP_BY_PHASE_POLICY" // Phase policy stops decreased
  | "IMPROVED_ORACLE_STALE_RATE"    // Oracle stale blocks decreased
  | "IMPROVED_IMPACT_BLOCK_RATE"    // Impact blocks decreased
  | "IMPROVED_SLIPPAGE_BLOCK_RATE"  // Slippage blocks decreased
  | "IMPROVED_COOLDOWN_BLOCK_RATE"  // Cooldown blocks decreased
  | "IMPROVED_DRIFT_NOOP_RATE"      // Drift no-op rate decreased
  // Worsenings
  | "WORSENED_BLOCK_DOMINANCE"      // Gate BLOCK ratio increased
  | "WORSENED_STOP_UNKNOWN"         // Unknown stops increased
  // No change
  | "NO_CHANGE"
  // Compare unavailable
  | "COMPARE_UNAVAILABLE";

/**
 * Replay Compare
 *
 * Comparison of before/after metrics via snapshot replay.
 */
export interface ReplayCompare {
  /**
   * Status
   */
  status: AdoptStatus;

  /**
   * Snapshot window (label-only)
   *
   * Example: "TAIL_200"
   */
  window: string;

  /**
   * Before summary (label-only)
   *
   * Example: ["GATE_BLOCK_DOMINATES", "PHASE_POLICY_STOPS_FREQUENT"]
   */
  before: string[];

  /**
   * After summary (label-only)
   *
   * Example: ["GATE_PASS_INCREASED", "PHASE_POLICY_STOPS_REDUCED"]
   */
  after: string[];

  /**
   * Comparison signals (improvement/worsening indicators)
   */
  signals: CompareSignal[];

  /**
   * Warnings
   */
  warnings: string[];
}

/**
 * Adopt Result v1
 *
 * Result of policy-first adoption evaluation.
 */
export interface AdoptResultV1 {
  /**
   * Version (always "v1.0")
   */
  version: "v1.0";

  /**
   * Status
   */
  status: AdoptStatus;

  /**
   * Adoption decision (ADOPT / HOLD / REJECT)
   */
  decision: AdoptDecision;

  /**
   * Proposal priority
   */
  priority?: AdoptPriority;

  /**
   * Source proposal ID
   */
  proposalId?: string;

  /**
   * Patch plan
   */
  patchPlan: PatchPlan;

  /**
   * Replay comparison
   */
  compare: ReplayCompare;

  /**
   * Decision reasons (label-only)
   *
   * Example: ["IMPROVED_WITHOUT_WORSENING", "P0_PRIORITY_ADOPT"]
   */
  reasons: string[];

  /**
   * Warnings
   */
  warnings: string[];

  /**
   * Timestamp
   */
  ts: number;
}
