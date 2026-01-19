// tools/orch-result.ts
// PR218: Orchestrator result writing tool (simulates external orchestrator)

import {
  OrchestrationResultV1,
  appendOrchResultV1,
  loadOrchResultLinesV1,
} from "../src/orchestrator/interface";
import * as path from "path";
import * as os from "os";

/**
 * Simulate orchestrator writing a result record
 *
 * Usage:
 *   ts-node tools/orch-result.ts <resume_id> <status> [outcome_codes...]
 *
 * Example:
 *   ts-node tools/orch-result.ts RESUME_123 SUCCEEDED
 *   ts-node tools/orch-result.ts RESUME_456 FAILED_NETWORK ORCH_NET_TIMEOUT ORCH_NET_RETRY
 */
async function main() {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.error("Usage: ts-node tools/orch-result.ts <resume_id> <status> [outcome_codes...]");
    console.error("\nValid status values:");
    console.error("  DISPATCHED, SKIPPED_POLICY, SKIPPED_WINDOW");
    console.error("  FAILED_NETWORK, FAILED_MARKET, FAILED_UNKNOWN");
    console.error("  SUCCEEDED, UNKNOWN");
    process.exit(1);
  }

  const [resumeId, status, ...outcomeCodes] = args;

  // Validate status
  const validStatuses = [
    "DISPATCHED",
    "SKIPPED_POLICY",
    "SKIPPED_WINDOW",
    "FAILED_NETWORK",
    "FAILED_MARKET",
    "FAILED_UNKNOWN",
    "SUCCEEDED",
    "UNKNOWN",
  ];
  if (!validStatuses.includes(status)) {
    console.error(`Invalid status: ${status}`);
    console.error(`Valid values: ${validStatuses.join(", ")}`);
    process.exit(1);
  }

  // Generate unique result_id (idempotency key)
  const resultId = `RESULT_${Date.now()}_${Math.floor(Math.random() * 100000)}`;

  // Build result record
  const result: OrchestrationResultV1 = {
    v: "v1",
    resume_id: resumeId,
    result_id: resultId,
    status: status as any,
  };

  if (outcomeCodes.length > 0) {
    result.outcome_codes = outcomeCodes;
  }

  // Write result
  await appendOrchResultV1(result);

  console.log("=== Orchestrator Result Written ===");
  console.log(JSON.stringify(result, null, 2));

  // Show current queue state
  const resultPath = path.join(os.homedir(), ".meridian", "orch_result.jsonl");
  console.log(`\nResult file: ${resultPath}`);

  const allResults = loadOrchResultLinesV1(20);
  console.log(`Total results in file: ${allResults.length}`);

  if (allResults.length > 0) {
    console.log("\nRecent results:");
    for (const r of allResults.slice(-5)) {
      console.log(`  ${r.resume_id} -> ${r.status} (${r.result_id})`);
    }
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
