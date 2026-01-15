/**
 * PR169: v1.4 Policy Attribution Graph v1 - Types
 *
 * Purpose:
 *   Analyze snapshot logs to identify causal chains (attribution paths)
 *   that lead to outcomes like BLOCK, STOP, etc.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Analysis only (no proposals, no execution, no changes)
 *   - Fixed rules: No learning, no optimization, no estimation
 *   - Defensive: Never throws, always returns result
 *   - Label-only: Normal output uses labels (numeric counts only in debug mode)
 */

/**
 * Attribution Status
 *
 * - COMPLETE: Attribution analysis completed successfully
 * - PARTIAL: Some operations could not be completed
 * - ERROR: Fatal error
 */
export type AttributionStatus = "COMPLETE" | "PARTIAL" | "ERROR";

/**
 * Attribution Node Type
 *
 * Types of nodes that can appear in attribution paths.
 */
export type AttrNodeType =
  | "PHASE"               // Shock phase (PHASE_NORMAL, PHASE_PRE_SHOCK, etc.)
  | "STRESS"              // Market stress (STRESS_CALM, STRESS_TENSE, etc.)
  | "ACTION_SHAPE"        // Action shape (if available)
  | "TEMPLATE"            // Risk template (TPL_RISK_50, etc.)
  | "GATE_DECISION"       // Gate decision (PASS, BLOCK, ERROR, UNKNOWN)
  | "GATE_BLOCK_REASON"   // Block reason (BLOCK_ORACLE_STALE, etc.)
  | "POLICY"              // Policy decision (ALLOW, DENY, UNKNOWN)
  | "RESUME"              // Resume state (RESUMABLE, WAIT, ABANDON, UNKNOWN)
  | "ROUTE"               // Venue route (CETUS, DEEPBOOK, NONE, UNKNOWN)
  | "RUN_STOP";           // Run stop reason category (STOP_BY_PHASE_POLICY, etc.)

/**
 * Attribution Node
 *
 * A single node in an attribution path.
 */
export interface AttrNode {
  /**
   * Node type
   */
  t: AttrNodeType;

  /**
   * Node value (label-only)
   *
   * Example: "PHASE_PRE_SHOCK", "BLOCK_ORACLE_STALE"
   */
  v: string;
}

/**
 * Attribution Edge
 *
 * A directed edge between two nodes (from → to).
 */
export interface AttrEdge {
  /**
   * Source node
   */
  from: AttrNode;

  /**
   * Target node
   */
  to: AttrNode;

  /**
   * Edge count (internal numeric, not displayed in normal mode)
   */
  count: number;
}

/**
 * Attribution Path
 *
 * An ordered sequence of nodes representing a causal chain.
 */
export interface AttrPath {
  /**
   * Ordered nodes
   */
  nodes: AttrNode[];

  /**
   * Path count (internal numeric, not displayed in normal mode)
   */
  count: number;
}

/**
 * Attribution Focus
 *
 * Focus mode for CLI display.
 */
export type AttrFocus =
  | "TOP_PATHS"      // Show top attribution paths
  | "TOP_EDGES"      // Show top edges
  | "BOTTLENECKS"    // Show bottlenecks (dominant patterns)
  | "WEAK_LINKS";    // Show weak links (rare patterns)

/**
 * Attribution Config
 *
 * Configuration for attribution analysis.
 */
export interface AttributionConfig {
  /**
   * Number of snapshots to analyze (tail)
   */
  tail: number;

  /**
   * Maximum number of top paths to return
   */
  maxPaths: number;

  /**
   * Maximum number of top edges to return
   */
  maxEdges: number;

  /**
   * Minimum count threshold (internal, not displayed)
   */
  minCount: number;

  /**
   * Focus mode (optional)
   */
  focus?: AttrFocus;
}

/**
 * Attribution Presence
 *
 * Indicates which components are present in the snapshot data.
 */
export interface AttributionPresence {
  hasSnapshots: boolean;
  hasPhase: boolean;
  hasStress: boolean;
  hasTemplate: boolean;
  hasGate: boolean;
  hasPolicy: boolean;
  hasResume: boolean;
  hasRoute: boolean;
  hasRunStop: boolean;
}

/**
 * Attribution Result v1
 *
 * Result of attribution analysis.
 */
export interface AttributionResultV1 {
  /**
   * Version (always "v1.0")
   */
  version: "v1.0";

  /**
   * Status
   */
  status: AttributionStatus;

  /**
   * Presence flags
   */
  presence: AttributionPresence;

  /**
   * Warnings (label-only)
   */
  warnings: string[];

  /**
   * Top attribution paths (sorted by count desc)
   */
  topPaths: AttrPath[];

  /**
   * Top edges (sorted by count desc)
   */
  topEdges: AttrEdge[];

  /**
   * Bottlenecks (label-only summaries)
   *
   * Example: ["BOTTLENECK_ORACLE_DOMINANT", "BOTTLENECK_STOP_FREQUENT"]
   */
  bottlenecks: string[];

  /**
   * Weak links (label-only summaries)
   *
   * Example: ["WEAKLINK_RESUME_RARE", "WEAKLINK_PASS_RARE"]
   */
  weakLinks: string[];

  /**
   * Timestamp
   */
  ts: number;
}
