/**
 * PR152: v1.4 Python Signal Bridge (READ-ONLY)
 *
 * Purpose:
 *   Extract template_id from Python PR151 output.
 *   Bridge Python guidance layer to TS execution layer.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No mutations
 *   - Defensive: Handle invalid/missing inputs gracefully
 *   - Conservative: Default to TPL_UNKNOWN if uncertain
 */

import { TemplateId, isValidTemplateId } from "../rebalance/templates";

/**
 * Extract template ID from Python output
 *
 * @param json - Python output (rebalance_record or artifact_bundle)
 * @returns Template ID (defaults to TPL_UNKNOWN if not found)
 *
 * Expected input examples:
 * 1. Direct rebalance record:
 *    { v14_rebalance_template_id: "TPL_RISK_90", ... }
 *
 * 2. Artifact bundle:
 *    { artifacts: { rebalance_record: { v14_rebalance_template_id: "TPL_RISK_90" } } }
 *
 * 3. Nested bundle:
 *    { rebalance_record: { v14_rebalance_template_id: "TPL_RISK_90" } }
 */
export function extractTemplateIdFromPython(json: any): TemplateId {
  // Defensive: handle null/undefined
  if (!json || typeof json !== "object") {
    console.warn(
      "[PYTHON_BRIDGE] Invalid input (not an object), defaulting to TPL_UNKNOWN"
    );
    return "TPL_UNKNOWN";
  }

  // Strategy 1: Direct field v14_rebalance_template_id
  if ("v14_rebalance_template_id" in json) {
    const templateId = json.v14_rebalance_template_id;
    if (typeof templateId === "string" && isValidTemplateId(templateId)) {
      return templateId;
    } else {
      console.warn(
        `[PYTHON_BRIDGE] Invalid template_id: ${templateId}, defaulting to TPL_UNKNOWN`
      );
      return "TPL_UNKNOWN";
    }
  }

  // Strategy 2: Nested in rebalance_record
  if ("rebalance_record" in json && json.rebalance_record) {
    const rebalanceRecord = json.rebalance_record;
    if (
      typeof rebalanceRecord === "object" &&
      "v14_rebalance_template_id" in rebalanceRecord
    ) {
      const templateId = rebalanceRecord.v14_rebalance_template_id;
      if (typeof templateId === "string" && isValidTemplateId(templateId)) {
        return templateId;
      } else {
        console.warn(
          `[PYTHON_BRIDGE] Invalid template_id in rebalance_record: ${templateId}, defaulting to TPL_UNKNOWN`
        );
        return "TPL_UNKNOWN";
      }
    }
  }

  // Strategy 3: Nested in artifacts.rebalance_record
  if ("artifacts" in json && json.artifacts) {
    const artifacts = json.artifacts;
    if (
      typeof artifacts === "object" &&
      "rebalance_record" in artifacts &&
      artifacts.rebalance_record
    ) {
      const rebalanceRecord = artifacts.rebalance_record;
      if (
        typeof rebalanceRecord === "object" &&
        "v14_rebalance_template_id" in rebalanceRecord
      ) {
        const templateId = rebalanceRecord.v14_rebalance_template_id;
        if (typeof templateId === "string" && isValidTemplateId(templateId)) {
          return templateId;
        } else {
          console.warn(
            `[PYTHON_BRIDGE] Invalid template_id in artifacts.rebalance_record: ${templateId}, defaulting to TPL_UNKNOWN`
          );
          return "TPL_UNKNOWN";
        }
      }
    }
  }

  // Fallback: not found
  console.warn(
    "[PYTHON_BRIDGE] template_id not found in any expected location, defaulting to TPL_UNKNOWN"
  );
  return "TPL_UNKNOWN";
}

/**
 * Validate Python rebalance record structure
 *
 * @param json - Python output
 * @returns Validation result with warnings
 */
export function validatePythonRebalanceRecord(json: any): {
  valid: boolean;
  warnings: string[];
} {
  const warnings: string[] = [];

  // Check if object
  if (!json || typeof json !== "object") {
    warnings.push("Input is not an object");
    return { valid: false, warnings };
  }

  // Check required field
  if (!("v14_rebalance_template_id" in json)) {
    warnings.push("Missing v14_rebalance_template_id field");
    return { valid: false, warnings };
  }

  // Check template_id type
  const templateId = json.v14_rebalance_template_id;
  if (typeof templateId !== "string") {
    warnings.push(`template_id is not a string: ${typeof templateId}`);
    return { valid: false, warnings };
  }

  // Check template_id value
  if (!isValidTemplateId(templateId)) {
    warnings.push(`Invalid template_id value: ${templateId}`);
    return { valid: false, warnings };
  }

  // Optional: check other fields (status, rule_id, etc.)
  if ("v14_rebalance_status" in json) {
    const status = json.v14_rebalance_status;
    if (status !== "AVAILABLE" && status !== "ERROR") {
      warnings.push(`Unexpected status: ${status}`);
    }
  }

  return { valid: true, warnings };
}
