// tools/orch-ack.ts
// PR216: Orchestration ACK writer (minimal orchestrator simulator)
//
// Purpose:
//   Simulates an external orchestrator that reads orch_queue.jsonl and writes ACKs.
//   In production, this would be a separate process/service.

import * as fs from "fs";
import * as path from "path";
import * as os from "os";

async function main() {
  const queuePath = path.join(os.homedir(), ".meridian", "orch_queue.jsonl");
  const ackPath = path.join(os.homedir(), ".meridian", "orch_ack.jsonl");

  console.log("=== Orchestration ACK Writer ===");
  console.log(`Queue path: ${queuePath}`);
  console.log(`ACK path: ${ackPath}`);

  // Check if queue file exists
  if (!fs.existsSync(queuePath)) {
    console.log("No queue file found. Nothing to ACK.");
    return;
  }

  // Read queue file
  const queueContent = fs.readFileSync(queuePath, "utf8");
  const queueLines = queueContent.trim().split("\n").filter((l) => l.trim());

  if (queueLines.length === 0) {
    console.log("Queue file is empty. Nothing to ACK.");
    return;
  }

  console.log(`Found ${queueLines.length} instructions in queue`);

  // Read existing ACKs (to avoid duplicates)
  const existingAcks = new Set<string>();
  if (fs.existsSync(ackPath)) {
    const ackContent = fs.readFileSync(ackPath, "utf8");
    const ackLines = ackContent.trim().split("\n").filter((l) => l.trim());
    for (const line of ackLines) {
      try {
        const ack = JSON.parse(line);
        if (ack.v === "ACK_V1" && ack.ack_status === "ACKED") {
          existingAcks.add(ack.resume_id);
        }
      } catch (e) {
        // Skip malformed lines
      }
    }
  }

  console.log(`Existing ACKs: ${existingAcks.size}`);

  // Process each instruction
  let newAckCount = 0;
  for (const line of queueLines) {
    try {
      const instruction = JSON.parse(line);
      const resumeId = instruction.resume_id;

      if (!resumeId) {
        console.log("Skipping instruction without resume_id");
        continue;
      }

      // Skip if already ACKed
      if (existingAcks.has(resumeId)) {
        console.log(`Already ACKed: ${resumeId}`);
        continue;
      }

      // Write ACK
      const ack = {
        v: "ACK_V1",
        resume_id: resumeId,
        ack_status: "ACKED",
      };

      const ackLine = JSON.stringify(ack) + "\n";

      // Ensure directory exists
      const dir = path.dirname(ackPath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }

      // Append ACK
      fs.appendFileSync(ackPath, ackLine, "utf8");
      console.log(`ACKed: ${resumeId}`);
      newAckCount++;
    } catch (e) {
      console.log(`Error processing instruction: ${e}`);
    }
  }

  console.log(`\nTotal new ACKs written: ${newAckCount}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
