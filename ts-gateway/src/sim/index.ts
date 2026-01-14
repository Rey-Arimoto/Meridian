/**
 * PR156: v1.4 Execution Simulation + Slippage Envelope - Exports
 *
 * Purpose:
 *   Central export point for simulation package.
 */

// Main simulation API
export {
  runExecutionSimulationV1,
  createErrorSimulationRecord,
  createPassSimulationRecord,
} from "./sim";

// Types
export type {
  SimStatus,
  SlippageLabel,
  ImpactLabel,
  LiquidityLabel,
  SimReason,
  SimulationInput,
  ExecutionSimulationRecord,
} from "./types";

// Guards (for testing/validation)
export {
  containsForbiddenVocab,
  containsTokenLiteral,
  containsNumericLike,
  containsPrescriptive,
  validateLabelOnlyStrings,
  sanitizeWarnings,
  validateSimulationOutput,
} from "./guards";
