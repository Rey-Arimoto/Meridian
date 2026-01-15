/**
 * PR169: v1.4 Policy Attribution Graph v1 - Model
 *
 * Purpose:
 *   Node extraction and path building from snapshots.
 *   Fixed order: PHASE → STRESS → ACTION_SHAPE → TEMPLATE → GATE_DECISION →
 *                GATE_BLOCK_REASON → POLICY → RUN_STOP → RESUME → ROUTE
 *
 * Constitutional Constraints:
 *   - Fixed rules: Node extraction follows predetermined order
 *   - Defensive: Handles missing fields gracefully
 *   - Label-only: Node values are labels (no numerics)
 */

import { MarketRegimeSnapshotV1 } from "../snapshot/types";
import { AttrNode, AttrNodeType, AttributionPresence } from "./types";

/**
 * Extract attribution nodes from snapshot
 *
 * Follows fixed order:
 * 1. PHASE
 * 2. STRESS
 * 3. ACTION_SHAPE
 * 4. TEMPLATE
 * 5. GATE_DECISION
 * 6. GATE_BLOCK_REASON (if BLOCK)
 * 7. POLICY
 * 8. RUN_STOP
 * 9. RESUME
 * 10. ROUTE
 *
 * @param snapshot - Snapshot from PR165
 * @returns Array of attribution nodes
 */
export function extractNodesFromSnapshot(
  snapshot: MarketRegimeSnapshotV1
): AttrNode[] {
  const nodes: AttrNode[] = [];

  try {
    // 1. PHASE
    if (snapshot.labels.shockPhase) {
      nodes.push({
        t: "PHASE",
        v: snapshot.labels.shockPhase,
      });
    }

    // 2. STRESS
    if (snapshot.labels.stress) {
      nodes.push({
        t: "STRESS",
        v: snapshot.labels.stress,
      });
    }

    // 3. ACTION_SHAPE (if available)
    if (snapshot.labels.actionShape) {
      nodes.push({
        t: "ACTION_SHAPE",
        v: snapshot.labels.actionShape as string,
      });
    }

    // 4. TEMPLATE
    if (snapshot.labels.templateId) {
      nodes.push({
        t: "TEMPLATE",
        v: snapshot.labels.templateId,
      });
    }

    // 5. GATE_DECISION
    if (snapshot.labels.gateDecision) {
      nodes.push({
        t: "GATE_DECISION",
        v: snapshot.labels.gateDecision,
      });
    }

    // 6. GATE_BLOCK_REASON (if BLOCK)
    if (
      snapshot.labels.gateDecision === "BLOCK" &&
      snapshot.labels.blockReason
    ) {
      nodes.push({
        t: "GATE_BLOCK_REASON",
        v: snapshot.labels.blockReason,
      });
    }

    // 7. POLICY (if available)
    if (snapshot.labels.policyDecision) {
      nodes.push({
        t: "POLICY",
        v: snapshot.labels.policyDecision as string,
      });
    }

    // 8. RUN_STOP (derived from stop reason category)
    if (snapshot.labels.resume && snapshot.labels.resume !== "NONE") {
      // Infer stop reason from block reason or phase
      const stopReason = inferStopReason(snapshot);
      if (stopReason) {
        nodes.push({
          t: "RUN_STOP",
          v: stopReason,
        });
      }
    }

    // 9. RESUME
    if (snapshot.labels.resume) {
      nodes.push({
        t: "RESUME",
        v: snapshot.labels.resume,
      });
    }

    // 10. ROUTE (if available)
    if (snapshot.labels.route) {
      nodes.push({
        t: "ROUTE",
        v: snapshot.labels.route as string,
      });
    }
  } catch (error) {
    // Defensive: Return partial nodes on error
  }

  return nodes;
}

/**
 * Infer stop reason from snapshot
 *
 * @param snapshot - Snapshot
 * @returns Stop reason label or undefined
 */
function inferStopReason(snapshot: MarketRegimeSnapshotV1): string | undefined {
  const blockReason = snapshot.labels.blockReason || "";

  // Phase policy
  if (
    blockReason.includes("PHASE") ||
    blockReason.includes("ESCALAT")
  ) {
    return "STOP_BY_PHASE_POLICY";
  }

  // Gate block
  if (
    blockReason.includes("ORACLE") ||
    blockReason.includes("IMPACT") ||
    blockReason.includes("SLIPPAGE") ||
    blockReason.includes("QUOTE") ||
    blockReason.includes("DRIFT") ||
    blockReason.includes("COOLDOWN")
  ) {
    return "STOP_BY_GATE";
  }

  // HardStop
  if (snapshot.labels.hardStop === "ACTIVE") {
    return "STOP_BY_POLICY_HARDSTOP";
  }

  // Duration
  if (blockReason.includes("DURATION")) {
    return "STOP_BY_DURATION";
  }

  // Block streak
  if (blockReason.includes("STREAK") || blockReason.includes("CONSECUTIVE")) {
    return "STOP_BY_BLOCK_STREAK";
  }

  return "STOP_UNKNOWN";
}

/**
 * Build presence from snapshots
 *
 * @param snapshots - Snapshots
 * @returns Presence flags
 */
export function buildPresenceFromSnapshots(
  snapshots: MarketRegimeSnapshotV1[]
): AttributionPresence {
  const presence: AttributionPresence = {
    hasSnapshots: snapshots.length > 0,
    hasPhase: false,
    hasStress: false,
    hasTemplate: false,
    hasGate: false,
    hasPolicy: false,
    hasResume: false,
    hasRoute: false,
    hasRunStop: false,
  };

  for (const snapshot of snapshots) {
    if (snapshot.labels.shockPhase) {
      presence.hasPhase = true;
    }
    if (snapshot.labels.stress) {
      presence.hasStress = true;
    }
    if (snapshot.labels.templateId) {
      presence.hasTemplate = true;
    }
    if (snapshot.labels.gateDecision) {
      presence.hasGate = true;
    }
    if (snapshot.labels.policyDecision) {
      presence.hasPolicy = true;
    }
    if (snapshot.labels.resume) {
      presence.hasResume = true;
    }
    if (snapshot.labels.route) {
      presence.hasRoute = true;
    }
    if (snapshot.labels.resume && snapshot.labels.resume !== "NONE") {
      presence.hasRunStop = true;
    }
  }

  return presence;
}

/**
 * Create path key from nodes
 *
 * Used for grouping identical paths.
 *
 * @param nodes - Attribution nodes
 * @returns Path key (string)
 */
export function createPathKey(nodes: AttrNode[]): string {
  return nodes.map((n) => `${n.t}:${n.v}`).join("|");
}

/**
 * Create edge key from nodes
 *
 * Used for grouping identical edges.
 *
 * @param from - From node
 * @param to - To node
 * @returns Edge key (string)
 */
export function createEdgeKey(from: AttrNode, to: AttrNode): string {
  return `${from.t}:${from.v}→${to.t}:${to.v}`;
}
