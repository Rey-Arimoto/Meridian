/**
 * PR169: v1.4 Policy Attribution Graph v1 - Attributor
 *
 * Purpose:
 *   Main attribution engine that aggregates paths and edges from snapshots,
 *   and identifies bottlenecks and weak links.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Analysis only (no execution, no changes)
 *   - Fixed rules: Deterministic thresholds and logic
 *   - Defensive: Never throws, always returns result
 */

import { MarketRegimeSnapshotV1 } from "../snapshot/types";
import {
  AttributionConfig,
  AttributionResultV1,
  AttributionStatus,
  AttrPath,
  AttrEdge,
  AttrNode,
} from "./types";
import {
  extractNodesFromSnapshot,
  buildPresenceFromSnapshots,
  createPathKey,
  createEdgeKey,
} from "./model";

/**
 * Default attribution config
 */
const DEFAULT_CONFIG: AttributionConfig = {
  tail: 200,
  maxPaths: 10,
  maxEdges: 15,
  minCount: 2,
};

/**
 * Attribute snapshots v1
 *
 * Main attribution analysis function.
 *
 * @param snapshots - Snapshots from PR165
 * @param cfg - Optional config (partial)
 * @returns Attribution result (never throws)
 */
export function attributeSnapshotsV1(
  snapshots: MarketRegimeSnapshotV1[],
  cfg?: Partial<AttributionConfig>
): AttributionResultV1 {
  const config: AttributionConfig = {
    ...DEFAULT_CONFIG,
    ...cfg,
  };

  const warnings: string[] = [];

  try {
    // Check if snapshots are available
    if (snapshots.length === 0) {
      warnings.push("WARN_NO_SNAPSHOTS_FOR_ATTRIBUTION");

      return {
        version: "v1.0",
        status: "PARTIAL",
        presence: {
          hasSnapshots: false,
          hasPhase: false,
          hasStress: false,
          hasTemplate: false,
          hasGate: false,
          hasPolicy: false,
          hasResume: false,
          hasRoute: false,
          hasRunStop: false,
        },
        warnings,
        topPaths: [],
        topEdges: [],
        bottlenecks: [],
        weakLinks: [],
        ts: Date.now(),
      };
    }

    // Build presence
    const presence = buildPresenceFromSnapshots(snapshots);

    // Aggregate paths and edges
    const pathMap = new Map<string, AttrPath>();
    const edgeMap = new Map<string, AttrEdge>();

    for (const snapshot of snapshots) {
      try {
        // Extract nodes from snapshot
        const nodes = extractNodesFromSnapshot(snapshot);

        if (nodes.length === 0) {
          continue;
        }

        // Build path
        const pathKey = createPathKey(nodes);
        if (pathMap.has(pathKey)) {
          pathMap.get(pathKey)!.count++;
        } else {
          pathMap.set(pathKey, { nodes, count: 1 });
        }

        // Build edges (adjacent pairs)
        for (let i = 0; i < nodes.length - 1; i++) {
          const from = nodes[i];
          const to = nodes[i + 1];
          const edgeKey = createEdgeKey(from, to);

          if (edgeMap.has(edgeKey)) {
            edgeMap.get(edgeKey)!.count++;
          } else {
            edgeMap.set(edgeKey, { from, to, count: 1 });
          }
        }
      } catch (error) {
        // Defensive: Skip malformed snapshot
        warnings.push("WARN_MALFORMED_SNAPSHOT_SKIPPED");
      }
    }

    // Filter and sort paths
    const topPaths = Array.from(pathMap.values())
      .filter((p) => p.count >= config.minCount)
      .sort((a, b) => b.count - a.count)
      .slice(0, config.maxPaths);

    // Filter and sort edges
    const topEdges = Array.from(edgeMap.values())
      .filter((e) => e.count >= config.minCount)
      .sort((a, b) => b.count - a.count)
      .slice(0, config.maxEdges);

    // Identify bottlenecks
    const bottlenecks = identifyBottlenecks(topEdges, edgeMap);

    // Identify weak links
    const weakLinks = identifyWeakLinks(presence, topEdges, edgeMap);

    // Determine status
    const status: AttributionStatus =
      warnings.length > 0 ? "PARTIAL" : "COMPLETE";

    return {
      version: "v1.0",
      status,
      presence,
      warnings,
      topPaths,
      topEdges,
      bottlenecks,
      weakLinks,
      ts: Date.now(),
    };
  } catch (error) {
    // Defensive: Return minimal result on error
    warnings.push("WARN_ATTRIBUTION_ERROR");

    return {
      version: "v1.0",
      status: "ERROR",
      presence: {
        hasSnapshots: snapshots.length > 0,
        hasPhase: false,
        hasStress: false,
        hasTemplate: false,
        hasGate: false,
        hasPolicy: false,
        hasResume: false,
        hasRoute: false,
        hasRunStop: false,
      },
      warnings,
      topPaths: [],
      topEdges: [],
      bottlenecks: [],
      weakLinks: [],
      ts: Date.now(),
    };
  }
}

/**
 * Identify bottlenecks
 *
 * Bottlenecks are dominant patterns (frequent edges).
 *
 * @param topEdges - Top edges
 * @param edgeMap - All edges map
 * @returns Bottleneck labels
 */
function identifyBottlenecks(
  topEdges: AttrEdge[],
  edgeMap: Map<string, AttrEdge>
): string[] {
  const bottlenecks: string[] = [];

  if (topEdges.length === 0) {
    return bottlenecks;
  }

  // Count edge types
  let gateBlockCount = 0;
  let runStopCount = 0;
  let oracleCount = 0;
  let phaseCount = 0;
  let impactCount = 0;
  let slippageCount = 0;

  for (const edge of topEdges) {
    // GATE_DECISION = BLOCK
    if (edge.from.t === "GATE_DECISION" && edge.from.v === "BLOCK") {
      gateBlockCount += edge.count;
    }

    // RUN_STOP
    if (edge.from.t === "RUN_STOP" || edge.to.t === "RUN_STOP") {
      runStopCount += edge.count;
    }

    // ORACLE block reasons
    if (
      edge.from.t === "GATE_BLOCK_REASON" &&
      edge.from.v.includes("ORACLE")
    ) {
      oracleCount += edge.count;
    }

    // PHASE_POLICY stops
    if (edge.to.t === "RUN_STOP" && edge.to.v === "STOP_BY_PHASE_POLICY") {
      phaseCount += edge.count;
    }

    // IMPACT blocks
    if (
      edge.from.t === "GATE_BLOCK_REASON" &&
      edge.from.v.includes("IMPACT")
    ) {
      impactCount += edge.count;
    }

    // SLIPPAGE blocks
    if (
      edge.from.t === "GATE_BLOCK_REASON" &&
      edge.from.v.includes("SLIPPAGE")
    ) {
      slippageCount += edge.count;
    }
  }

  // Total for ratio calculation
  const totalEdgeCount = topEdges.reduce((sum, e) => sum + e.count, 0);

  // Identify bottlenecks (threshold: >30% of total edge count)
  const threshold = totalEdgeCount * 0.3;

  if (gateBlockCount > threshold) {
    bottlenecks.push("BOTTLENECK_GATE_BLOCK_FREQUENT");
  }

  if (runStopCount > threshold) {
    bottlenecks.push("BOTTLENECK_STOP_FREQUENT");
  }

  if (oracleCount > threshold) {
    bottlenecks.push("BOTTLENECK_ORACLE_DOMINANT");
  }

  if (phaseCount > threshold) {
    bottlenecks.push("BOTTLENECK_PHASE_POLICY_DOMINANT");
  }

  if (impactCount > threshold || slippageCount > threshold) {
    bottlenecks.push("BOTTLENECK_MARKET_IMPACT_DOMINANT");
  }

  return bottlenecks;
}

/**
 * Identify weak links
 *
 * Weak links are rare patterns (infrequent edges).
 *
 * @param presence - Presence flags
 * @param topEdges - Top edges
 * @param edgeMap - All edges map
 * @returns Weak link labels
 */
function identifyWeakLinks(
  presence: any,
  topEdges: AttrEdge[],
  edgeMap: Map<string, AttrEdge>
): string[] {
  const weakLinks: string[] = [];

  // RESUME rare
  if (presence.hasResume) {
    const resumeEdges = topEdges.filter(
      (e) => e.from.t === "RESUME" || e.to.t === "RESUME"
    );
    if (resumeEdges.length === 0) {
      weakLinks.push("WEAKLINK_RESUME_RARE");
    }
  }

  // ROUTE rare
  if (presence.hasRoute) {
    const routeEdges = topEdges.filter(
      (e) => e.from.t === "ROUTE" || e.to.t === "ROUTE"
    );
    if (routeEdges.length === 0) {
      weakLinks.push("WEAKLINK_ROUTE_CHANGE_RARE");
    }
  }

  // PASS rare (gate decision PASS)
  const passEdges = topEdges.filter(
    (e) => e.from.t === "GATE_DECISION" && e.from.v === "PASS"
  );
  if (passEdges.length === 0 && presence.hasGate) {
    weakLinks.push("WEAKLINK_PASS_RARE");
  }

  // RECOVERY phase rare
  const recoveryEdges = topEdges.filter(
    (e) =>
      (e.from.t === "PHASE" && e.from.v.includes("RECOVERY")) ||
      (e.to.t === "PHASE" && e.to.v.includes("RECOVERY"))
  );
  if (recoveryEdges.length === 0 && presence.hasPhase) {
    weakLinks.push("WEAKLINK_NO_RECOVERY_OBSERVED");
  }

  return weakLinks;
}
