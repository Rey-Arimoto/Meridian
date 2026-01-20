/**
 * PR152: v1.4 TS Rebalance Type Definitions (READ-ONLY)
 *
 * Purpose:
 *   Define types for rebalance template resolution and execution.
 *
 * Token Scope:
 *   - wBTC: Risk asset (target of rebalancing)
 *   - USDC: Stable asset (safe haven)
 *   - SUI: Gas only (not rebalanced, minimum balance reserved)
 */

import { TemplateId } from "./templates";

/**
 * Token symbols supported in Meridian TS Gateway
 */
export type TokenSymbol = "WBTC" | "USDC" | "SUI";

/**
 * Portfolio snapshot (wallet balances + prices + weights)
 *
 * PR155: Oracle-based pricing support added.
 * Prices now come from oracle, and may be unavailable.
 */
export interface PortfolioSnapshot {
  // Token balances (as strings to avoid precision loss)
  balances: {
    WBTC: string;
    USDC: string;
    SUI: string;
  };

  // Token prices in USD (PR155: now optional, from oracle)
  pricesUsd: {
    WBTC?: number; // Optional: may be unavailable if oracle fails
    USDC?: number; // Optional: typically 1.0 (stablecoin)
  };

  // Token values in USD (optional if prices unavailable)
  valuesUsd?: {
    WBTC: number;
    USDC: number;
  };

  // Current weights (optional if prices unavailable)
  weights?: {
    WBTC: number; // wBTC weight (0.0 - 1.0)
    USDC: number; // USDC weight (0.0 - 1.0)
  };

  // Total portfolio value in USD (optional if prices unavailable)
  totalUsd?: number;

  // Oracle status (PR155)
  oracleStatus?: "AVAILABLE" | "STALE" | "ERROR";

  // Timestamp of snapshot
  timestamp: number;
}

/**
 * Rebalance constraints (safety limits and execution parameters)
 */
export interface RebalanceConstraints {
  // Minimum SUI balance to reserve for gas (as string)
  minSuiBalance: string; // e.g., "0.05" SUI

  // Minimum weight delta to trigger action (e.g., 0.05 = 5%)
  minDeltaToAct: number;

  // Maximum notional USD to move in single rebalance
  maxNotionalUsd: number; // e.g., 200 USD

  // Cooldown period between rebalances (seconds)
  cooldownSeconds: number; // e.g., 900 (15 minutes)

  // Slippage tolerance in basis points (e.g., 50 = 0.50%)
  slippageBps: number;

  // Transaction deadline (seconds from now)
  deadlineSeconds: number; // e.g., 120 (2 minutes)
}

/**
 * Rebalance intent (what needs to be done)
 */
export type RebalanceIntent = "INCREASE_WBTC" | "DECREASE_WBTC" | "NOOP";

/**
 * Rebalance plan (target weights + delta + intent)
 */
export interface RebalancePlan {
  // Template ID from Python PR151
  templateId: TemplateId;

  // Target weights from template
  targetWeights: {
    WBTC: number;
    USDC: number;
  };

  // Current weights from portfolio
  currentWeights: {
    WBTC: number;
    USDC: number;
  };

  // Weight deltas (target - current)
  deltaWeights: {
    WBTC: number;
    USDC: number;
  };

  // Rebalance intent
  intent: RebalanceIntent;

  // Notional USD to move (capped by maxNotionalUsd)
  notionalUsd: number;

  // Reason codes (debugging/logging)
  reasonCodes: string[];

  // PR158: Drift evaluation result (optional)
  drift?: {
    status: "AVAILABLE" | "UNKNOWN" | "ERROR";
    driftTooSmall?: boolean;
    reasons: string[];
    warnings: string[];
  };

  // PR158: Cooldown evaluation result (optional)
  cooldown?: {
    status: "AVAILABLE" | "BLOCKED" | "UNKNOWN" | "ERROR";
    blocked?: boolean;
    reasons: string[];
    warnings: string[];
  };
}

/**
 * Transaction draft status (PR153 update)
 */
export type TxDraftStatus =
  | "DRAFT"
  | "EXECUTABLE_DRAFT" // PR153: Gate passed, ready for execution
  | "SIMULATION_ONLY" // PR153: Simulation only, no execution
  | "SKIPPED"
  | "ERROR";

/**
 * Routing protocol
 */
export type RouteProtocol = "CETUS" | "DEEPBOOK" | "UNKNOWN";

/**
 * Swap action
 */
export type SwapAction = "SWAP_USDC_TO_WBTC" | "SWAP_WBTC_TO_USDC" | "NOOP";

/**
 * Transaction draft (ready for simulate/execute)
 *
 * PR157: Enhanced with minOut guard and consistency checks
 */
export interface TxDraft {
  // Draft status
  status: TxDraftStatus;

  // Simulate-only mode (true = do not execute)
  simulateOnly: boolean;

  // Routing protocol
  route: RouteProtocol;

  // Swap action
  action: SwapAction;

  // Amount in (as string)
  amountIn: string;

  // Minimum amount out (PR157: Required for execution safety, string format)
  minOut: string | null;

  // Slippage tolerance in basis points (PR157: Calculated from fixed rules)
  slippageBps: number;

  // Slippage label (PR190: Label-only for telemetry traceability)
  slippageLabel?: string;

  // Transaction deadline (seconds from now)
  deadlineSeconds: number;

  // Safety checks performed (PR157: Label-only, no numbers)
  checks: string[];

  // Notes (debugging/logging)
  notes: string[];

  // Errors (if any)
  errors: string[];

  // Execution reason codes (PR191: Label-only self-explanation)
  executionReasonCodes?: string[];
}

/**
 * Transaction execution result
 */
export interface TxExecutionResult {
  // Success flag
  ok: boolean;

  // Transaction digest (if executed)
  txDigest?: string;

  // Errors (if any)
  errors?: string[];

  // Notes (debugging/logging)
  notes?: string[];
}

/**
 * Simulation result
 */
export interface SimulationResult {
  // Success flag
  ok: boolean;

  // Notes (debugging/logging)
  notes: string[];
}

/**
 * Re-export TemplateId for convenience
 */
export type { TemplateId };

/**
 * PR159: Chunked Execution / TWAP-lite v1
 */

/**
 * Chunk status
 */
export type ChunkStatus =
  | "PLANNED"
  | "SKIPPED"
  | "BLOCKED"
  | "SIMULATED"
  | "EXECUTED"
  | "STOPPED"
  | "ERROR";

/**
 * Run status
 */
export type RunStatus =
  | "PLANNED"
  | "RUNNING"
  | "COMPLETED"
  | "STOPPED"
  | "ERROR";

/**
 * PR196: Execution mode (structural safety for unintended LIVE execution)
 */
export type ExecutionMode =
  | "SIM_ONLY" // Simulation only (never broadcast)
  | "DRY_RUN" // Dry-run (construct tx but never broadcast)
  | "LIVE"; // Live execution (broadcast allowed if unlocked)

/**
 * PR199: LIVE unlock status (handshake for broadcast permission)
 */
export type LiveUnlockStatus =
  | "UNLOCKED" // Both env flag and spec lock OK
  | "LOCKED_ENV" // Env flag MERIDIAN_LIVE_UNLOCK not TRUE
  | "LOCKED_SPEC" // Spec lock not ACTIVE_OK
  | "LOCKED_SPEC_EXPIRED" // Spec lock expired
  | "LOCKED_SPEC_PENDING_ACK" // Spec lock pending ACK
  | "LOCKED_UNKNOWN"; // Unknown / not applicable

/**
 * PR204: Gate Safety Reason Code (Market Safety Explainability)
 */
export type GateReasonCode =
  | "GATE_ORACLE_STALE"
  | "GATE_PRICE_DIVERGENCE"
  | "GATE_IMPACT_TOO_HIGH"
  | "GATE_LIQUIDITY_TOO_THIN"
  | "GATE_DEPTH_UNAVAILABLE"
  | "GATE_QUOTE_UNAVAILABLE"
  | "GATE_UNKNOWN";

/**
 * PR205: Policy Control Reason Code (Constitutional Explainability)
 */
export type PolicyReasonCode =
  | "POLICY_ALLOW"
  | "POLICY_SIM_ONLY"
  | "POLICY_HARDSTOP_ACTIVE"
  | "POLICY_ENV_DISABLED"
  | "POLICY_SPEC_LOCK_PENDING_ACK"
  | "POLICY_SPEC_LOCK_EXPIRED"
  | "POLICY_LIVE_UNLOCK_LOCKED_ENV"
  | "POLICY_LIVE_UNLOCK_LOCKED_SPEC"
  | "POLICY_LIVE_UNLOCK_LOCKED_SPEC_EXPIRED"
  | "POLICY_LIVE_UNLOCK_LOCKED_SPEC_PENDING_ACK"
  | "POLICY_LIVE_UNLOCK_LOCKED_UNKNOWN"
  | "POLICY_UNKNOWN";

/**
 * Chunk plan (single chunk in a run)
 */
export interface ChunkPlan {
  // Chunk identifier
  chunkId: string;

  // Notional USD for this chunk (internal numeric only)
  notionalUsd: number;

  // Intent for this chunk
  intent: "INCREASE_WBTC" | "DECREASE_WBTC" | "NOOP";

  // Template ID (inherited from rebalance plan)
  templateId: string;

  // Venue hint (optional)
  venueHint?: "CETUS" | "DEEPBOOK" | "NONE";
}

/**
 * Chunk result (execution outcome of single chunk)
 */
export interface ChunkResult {
  // Chunk identifier
  chunkId: string;

  // Execution status
  status: ChunkStatus;

  // Reasons (label-only)
  reasons: string[];

  // Transaction draft (if created)
  txDraft?: TxDraft;

  // Venue used (if executed)
  venue?: "CETUS" | "DEEPBOOK" | "NONE";

  // Creation timestamp
  createdAtMs: number;

  // PR161: Phase diagnostics (label-only)
  phaseLabel?: string;

  // PR161: Route selection diagnostics (label-only)
  routeSelected?: "CETUS" | "DEEPBOOK" | "NONE";
  routeChanged?: boolean;

  // PR184: Observe degrade level diagnostics (label-only)
  observeDegradeLevel?: string;
}

/**
 * Run plan (chunked execution plan)
 */
export interface RunPlan {
  // Run identifier
  runId: string;

  // Run status
  status: RunStatus;

  // Creation timestamp
  createdAtMs: number;

  // Template ID
  templateId: string;

  // Total notional USD (internal numeric only)
  totalNotionalUsd: number;

  // Chunk plans
  chunks: ChunkPlan[];

  // Reasons (label-only)
  reasons: string[];

  // PR196: Execution mode (default: SIM_ONLY)
  executionMode?: ExecutionMode;

  // PR208: Resume re-execution link (optional, only for resumed runs)
  resumeId?: string;
  previousRunId?: string;
  resumeStopReason?: StopReason;

  // PR209: Resume origin context (propagated from resumeState for telemetry traceability)
  resumeOriginStopCause?: StopCause;
  resumeOriginRunReasonCodes?: string[];

  // PR213: Resume strategy (autonomous recovery strategy derived from origin context)
  resumeStrategy?: ResumeStrategyV1;
  resumeStrategyCodes?: string[]; // Label-only explainability codes

  // PR214: Resume strategy enforcement (execution mode override)
  resumeStrategyEnforcedExecutionMode?: ExecutionMode;
  resumeStrategyEnforcedCodes?: string[]; // Enforcement reason codes (label-only)

  // PR215: Resume re-execution timing control (delay / backoff)
  resumeDelayClassV1?: ResumeDelayClassV1;
  resumeDelayOffsetLabelV1?: ResumeDelayOffsetLabelV1;
  resumeDelayReasonCodesV1?: string[]; // Timing reason codes (label-only)

  // PR219: Resume strategy escalation (orchestrator feedback → next strategy)
  resumeEscalatedStrategy?: ResumeStrategyV1;
  resumeEscalationCodes?: string[]; // Escalation reason codes (label-only)

  // PR220: Market regime context (regime-aware recovery)
  resumeMarketRegime?: MarketRegimeV1;
  resumeMarketRegimeCodes?: string[]; // Regime derivation codes (label-only)
  resumeMatrixStrategy?: ResumeStrategyV1; // Final strategy after regime overlay
  resumeMatrixCodes?: string[]; // Matrix overlay codes (label-only)

  // PR228: Stability Guard Observability Pack (telemetry-only, label-only)
  // Regime Hysteresis observability (instant vs confirmed)
  resumeRegimeInstant?: MarketRegimeV1; // Instant regime (before hysteresis)
  resumeRegimeConfirmed?: MarketRegimeV1; // Confirmed regime (after hysteresis)
  resumeRegimeHysteresisAction?: string; // H0_NO_CHANGE | H1_CONFIRMED | H2_HOLD | H_UNKNOWN
  resumeRegimeHysteresisCodes?: string[]; // Hysteresis codes (label-only)
  // Consecutive Success Gate observability
  resumeConsecutiveSuccessesClass?: string; // S0 | S1 | S2_PLUS | S_UNKNOWN
  resumeSuccessGate?: string; // GATE_WAIT | GATE_PASS | GATE_NA | G_UNKNOWN
  resumeSuccessGateCodes?: string[]; // Success gate codes (label-only)
  // Oscillation basis observability (window + change levels, label-only)
  resumeOscWindowStatus?: string; // WINDOW_FRESH | WINDOW_RESET | WINDOW_UNKNOWN
  resumeOscChangeLevelStrategy?: string; // CHG_LOW | CHG_MEDIUM | CHG_HIGH | CHG_EXCEEDED | CHG_UNKNOWN
  resumeOscChangeLevelRegime?: string; // CHG_LOW | CHG_MEDIUM | CHG_HIGH | CHG_EXCEEDED | CHG_UNKNOWN
  resumeOscBasisCodes?: string[]; // Oscillation basis codes (label-only)

  // PR229: Recovery Budgeting v1 (暴走防止、label-only telemetry)
  resumeBudgetAttemptStatus?: string; // B0_OK | B1_NEAR_LIMIT | B2_LIMIT_EXCEEDED | B_UNKNOWN
  resumeBudgetImmediateRateStatus?: string; // R0_OK | R1_NEAR_LIMIT | R2_LIMIT_EXCEEDED | R_UNKNOWN
  resumeBudgetFailedMarketRateStatus?: string; // F0_OK | F1_NEAR_LIMIT | F2_LIMIT_EXCEEDED | F_UNKNOWN
  resumeBudgetOscCooldownStatus?: string; // C0_OK | C1_COOLDOWN_ACTIVE | C_UNKNOWN
  resumeBudgetAction?: string; // ALLOW | DEFER | ABANDON | A_UNKNOWN
  resumeBudgetCodes?: string[]; // Budget decision codes (label-only)

  // PR230: Signal Trust & Consensus (Article XI - telemetry parity)
  resumeSignalConsensus?: SignalConsensusV1; // CONSENSUS_STRONG | WEAK | DEGRADED | UNTRUSTED
  resumeSignalConsensusCodesStatus?: string; // PRESENT | EMPTY
  resumeSignalConsensusCodes?: string; // Pipe-separated codes (dedup/sort/truncate)
  resumeSignalOracleTrust?: SignalTrustV1; // TRUSTED | DEGRADED | UNTRUSTED | UNKNOWN
  resumeSignalDexTrust?: SignalTrustV1; // TRUSTED | DEGRADED | UNTRUSTED | UNKNOWN
  resumeSignalRpcTrust?: SignalTrustV1; // TRUSTED | DEGRADED | UNTRUSTED | UNKNOWN
  resumeSignalCrosscheckStatus?: QuoteCrossCheckStatusV1; // XCHK_OK | DIVERGED | INSUFFICIENT | UNKNOWN

  // PR230b: Consensus → Execution Hard Cap (NEVER LIVE) v1
  resumeSignalEnforcedExecutionMode?: ExecutionMode; // SIM_ONLY | DRY_RUN if capped
  resumeSignalEnforcedCodes?: string[]; // Signal cap enforcement codes (label-only)
  resumeSignalExecCapStatus?: SignalExecCapStatusV1; // CAP_NONE | CAP_SIM_ONLY | CAP_DRY_RUN | CAP_ERROR

  // PR231: Invariant Checks v1 (Final defensive layer)
  resumeInvariantStatus?: InvariantStatusV1; // INV_PASS | INV_FAIL | INV_WARN
  resumeInvariantFailedGroup?: InvariantGroupV1; // G0_NONE | G1_EXEC | G2_SIGNAL | G3_REGIME | G4_BUDGET | G9_UNKNOWN
  resumeInvariantCodes?: string[]; // Invariant check codes (label-only, dedup/sort/truncate)

  // PR232: Economic Safety Invariants v1 (LIVE capital safety)
  resumeEconomicInvariantStatus?: EconomicInvariantStatusV1; // EINV_PASS | EINV_FAIL
  resumeEconomicInvariantFailedGroup?: EconomicInvariantGroupV1; // EG0_NONE | EG1_LIQUIDITY | EG2_SLIPPAGE | EG3_CRASH | EG4_EXPOSURE | EG5_INTEGRITY | EG9_UNKNOWN
  resumeEconomicInvariantCodes?: string[]; // Economic invariant codes (label-only, dedup/sort/truncate)
  resumeEconomicActionOverride?: EconomicActionOverrideV1; // NONE | DEFER_BACKOFF_LONG | DEFER_MANUAL | ABORT

  // PR233: Economic Risk Constraints v1 (Article XII - LIVE capital safety)
  resumeEconLiquidityCondition?: LiquidityConditionV1; // LIQ_UNKNOWN | HEALTHY | THIN | VACUUM
  resumeEconSlippageRisk?: SlippageRiskV1; // SLIP_UNKNOWN | LOW | MEDIUM | HIGH | EXTREME
  resumeEconExposureStatus?: ExposureStatusV1; // EXP_UNKNOWN | NONE | SMALL | MEDIUM | LARGE | EXCESSIVE
  resumeEconDrawdownStatus?: DrawdownStatusV1; // DD_UNKNOWN | OK | WARNING | CRITICAL
  resumeEconConstraintClass?: EconConstraintClassV1; // E0_OK | E1_CONSERVATIVE | E2_RISKY | E3_FORBIDDEN | E9_ERROR
  resumeEconConstraintAction?: EconConstraintActionV1; // ECON_ALLOW | DEFER | ABANDON
  resumeEconConstraintCodes?: string[]; // Economic constraint codes (label-only, dedup/sort/truncate)
  resumeEconConstraintCodesStatus?: string; // PRESENT | EMPTY

  // PR233a: Economic Risk Observability Pack v1 (telemetry-only, label passthrough)
  resumeEconRiskSeverity?: string; // SEV_LOW | SEV_MEDIUM | SEV_HIGH | SEV_CRITICAL (derived from econClass)
  resumeEconRiskCooldownStatus?: string; // CD0_OK | CD1_ACTIVE
  resumeEconRiskWindowStatus?: string; // WINDOW_FRESH | WINDOW_RESET | WINDOW_UNKNOWN

  // PR233b: Economic Execution Shaping v1 (Article XII-b, execution control)
  resumeEconExecSizeCap?: EconomicExecSizeCapV1; // SIZE_NONE | SIZE_TINY | SIZE_SMALL | SIZE_ZERO
  resumeEconExecFreqCap?: EconomicExecFreqCapV1; // FREQ_NONE | FREQ_SLOW | FREQ_COOLDOWN
  resumeEconCapitalCap?: EconomicCapitalCapV1; // CAPITAL_NONE | CAPITAL_LOW | CAPITAL_MINIMAL
  resumeEconExecShapeStatus?: EconomicExecShapeStatusV1; // SHAPE_NONE | SHAPE_APPLIED | SHAPE_ERROR
  resumeEconExecShapeCodes?: string[]; // Execution shaping codes (label-only, dedup/sort/truncate)

  // PR234: Capital-at-Risk Envelope v1 (Article XIII, runaway prevention)
  resumeCapitalRiskWindowStatus?: CapitalRiskWindowStatusV1; // WIN_FRESH | WIN_ACTIVE | WIN_EXPIRED
  resumeCapitalRiskUsageLevel?: CapitalRiskUsageLevelV1; // RISK_LOW | RISK_MEDIUM | RISK_HIGH | RISK_EXHAUSTED
  resumeCapitalRiskAction?: CapitalRiskActionV1; // CAR_ALLOW | CAR_DEFER | CAR_ABORT
  resumeCapitalRiskCodes?: string[]; // Capital risk codes (label-only, dedup/sort/truncate)
  resumeCapitalRiskCodesStatus?: "PRESENT" | "EMPTY"; // Parity with supervisor telemetry

  // PR235: Adversarial Incident Quarantine v1 (Article XIV, hostile market isolation)
  resumeQuarantineStatus?: QuarantineStatusV1; // Q0_NONE | Q1_ACTIVE | Q2_EXPIRED | Q9_ERROR
  resumeQuarantineIncidentType?: IncidentTypeV1; // INC_NONE | INC_FLASH_CRASH | INC_ORACLE_MANIPULATION | ...
  resumeQuarantineSeverity?: IncidentSeverityV1; // SEV0_NONE | SEV1_SUSPECT | SEV2_HIGH | SEV3_CRITICAL
  resumeQuarantineExitCondition?: QuarantineExitConditionV1; // EXIT_NONE | EXIT_MANUAL_ONLY | EXIT_CONSENSUS_STRONG_2TICKS | ...
  resumeQuarantineAction?: QuarantineActionV1; // QA_ALLOW | QA_DEFER | QA_ABORT
  resumeQuarantineCodes?: string[]; // Quarantine codes (label-only, dedup/sort/truncate)
  resumeQuarantineCodesStatus?: "PRESENT" | "EMPTY"; // Parity with supervisor telemetry

  // PR236: Recovery Governance Layer v1 (Article XV, recovery permission control)
  resumeRecoveryPermission?: RecoveryPermissionV1; // AUTO_ALLOWED | COOLDOWN_ONLY | MANUAL_ONLY | PERMANENT_HALT
  resumeRecoveryGateAction?: RecoveryGateActionV1; // RG_ALLOW | RG_DEFER | RG_ABORT | RG_ABANDON
  resumeRecoveryGateReason?: RecoveryGateReasonV1; // BY_NONE | BY_QUARANTINE_SEV2 | BY_CAR_EXHAUSTED | ...
  resumeRecoveryGateCooldownClass?: "CD_NONE" | "CD_SHORT" | "CD_LONG" | "CD_ACTIVE"; // Cooldown state (label-only)
  resumeRecoveryGateAgeClass?: "AGE_NONE" | "AGE_FRESH" | "AGE_MODERATE" | "AGE_OLD" | "AGE_EXPIRED"; // Permission age (label-only)
  resumeRecoveryGateCodesStatus?: "PRESENT" | "EMPTY"; // Parity with supervisor telemetry
  resumeRecoveryGateCodes?: string; // Pipe-separated codes (dedup/sort/truncate(8))

  // PR237: Learning Freeze & Drift Firewall v1 (Article XVI, prevent learning from disequilibrium)
  resumeLearningFreezeStatus?: LearningFreezeStatusV1; // FREEZE_OFF | FREEZE_ON | FREEZE_ERROR
  resumeLearningFreezeReason?: LearningFreezeReasonV1; // LFR_NONE | LFR_SIGNAL_NOT_STRONG | LFR_QUARANTINE_ACTIVE | ...
  resumeLearningFreezeExit?: LearningFreezeExitV1; // LFX_NONE | LFX_AUTO_STABLE_2TICK | LFX_COOLDOWN_60MIN | LFX_MANUAL_RELEASE
  resumeLearningFreezeAction?: "FREEZE_APPLY" | "FREEZE_HOLD" | "FREEZE_RELEASE"; // Action taken
  resumeLearningFreezeCodesStatus?: "PRESENT" | "EMPTY"; // Parity with supervisor telemetry
  resumeLearningFreezeCodes?: string; // Pipe-separated codes (dedup/sort/truncate(8))

  // PR240: Market Phase Graph v1 (Article XVII, market phase state machine)
  resumeMarketPhase?: MarketPhaseV1; // PHASE_CALM | PHASE_TENSION | PHASE_STRESS | PHASE_DISLOCATION | PHASE_RECOVERY | PHASE_UNKNOWN_SAFE
  resumeMarketPhaseEdge?: MarketPhaseEdgeV1; // EDGE_STAY | EDGE_ESCALATE | EDGE_DEESCALATE | EDGE_RESET_SAFE | EDGE_ERROR_SAFE
  resumeMarketPhaseConfidence?: MarketPhaseConfidenceV1; // CONF_STRONG | CONF_WEAK | CONF_UNKNOWN
  resumeMarketPhaseCodes?: string[]; // Phase codes (label-only, dedup/sort/truncate(8))
  resumeMarketPhaseEdgeCodes?: string[]; // Edge codes (label-only, dedup/sort/truncate(8))
}

/**
 * Run result (chunked execution outcome)
 */
export interface RunResult {
  // Run identifier
  runId: string;

  // Run status
  status: RunStatus;

  // Reasons (label-only)
  reasons: string[];

  // Chunk results
  chunkResults: ChunkResult[];

  // Start timestamp
  startedAtMs: number;

  // Finish timestamp (if completed/stopped)
  finishedAtMs?: number;

  // PR162: Resume state (if stopped with resume possibility)
  resumeState?: ResumeState;
}

/**
 * PR162: Partial Resume Policy v1
 */

/**
 * Resume status
 */
export type ResumeStatus = "RESUMABLE" | "WAIT" | "ABANDON" | "UNKNOWN";

/**
 * PR207: Resume Reason Code (Resumability Explainability)
 * Structured reason codes for resume evaluation decisions
 */
export type ResumeReasonCode =
  // Decision codes
  | "RESUME_PRESENT"
  | "RESUME_NOT_PRESENT"
  | "RESUME_ALLOWED"
  | "RESUME_BLOCKED"
  | "RESUME_EXPIRED"
  | "RESUME_UNKNOWN"
  // Oracle condition codes
  | "RESUME_ORACLE_AVAILABLE"
  | "RESUME_ORACLE_UNAVAILABLE"
  // Gate condition codes
  | "RESUME_GATE_PASS"
  | "RESUME_GATE_BLOCK"
  // Route condition codes
  | "RESUME_ROUTE_AVAILABLE"
  | "RESUME_ROUTE_UNAVAILABLE"
  // Policy condition codes
  | "RESUME_POLICY_ENV_ENABLED"
  | "RESUME_POLICY_ENV_DISABLED"
  | "RESUME_HARDSTOP_ACTIVE"
  | "RESUME_HARDSTOP_INACTIVE"
  // Phase condition codes
  | "RESUME_PHASE_NORMAL"
  | "RESUME_PHASE_RISK"
  // Timeout condition codes
  | "RESUME_TIMEOUT_EXCEEDED"
  | "RESUME_TIMEOUT_OK";

/**
 * Stop reason (label-only)
 */
export type StopReason =
  | "STOP_PHASE_POLICY"
  | "STOP_NO_ROUTE"
  | "STOP_ORACLE_STALE"
  | "STOP_ORACLE_ERROR"
  | "STOP_QUOTE_STALE"
  | "STOP_QUOTE_INCONSISTENT"
  | "STOP_IMPACT_HIGH"
  | "STOP_SLIPPAGE_HIGH"
  | "STOP_DEPTH_THIN"
  | "STOP_POLICY_DENY"
  | "STOP_HARDSTOP_ACTIVE"
  | "STOP_DURATION_EXCEEDED"
  | "STOP_BLOCKED_STREAK"
  | "STOP_ERROR"
  | "STOP_UNKNOWN";

/**
 * PR209: Stop cause attribution (high-level category)
 */
export type StopCause = "GATE" | "POLICY" | "PHASE" | "TIMEOUT" | "NONE";

/**
 * PR213: Resume Strategy v1 (Autonomous Recovery Strategy)
 *
 * Purpose:
 *   Define how supervisor should handle resume re-execution based on
 *   origin stop cause and context. Ensures safe, explainable recovery.
 *
 * Constitutional:
 *   - READ-ONLY: Fixed strategy taxonomy, no learning/optimization
 *   - Safe defaults: Dangerous scenarios default to SIM_ONLY or WAIT
 *   - Label-only: Strategy is a string label, not numeric score
 *   - Deterministic: Same inputs → same strategy
 *
 * Strategies:
 *   - RETRY_IMMEDIATE: Safe to retry immediately (e.g., timeout)
 *   - RETRY_SAFE_SIM_ONLY: Retry in SIM_ONLY mode for safety (e.g., gate/phase risk)
 *   - WAIT_FOR_RECOVERY: Wait for system recovery (e.g., resume decision WAIT)
 *   - WAIT_FOR_UNLOCK: Wait for policy unlock (e.g., hardstop/env key)
 *   - ABANDON: Do not retry (e.g., resume decision ABANDON)
 */
export type ResumeStrategyV1 =
  | "RETRY_IMMEDIATE"
  | "RETRY_SAFE_SIM_ONLY"
  | "WAIT_FOR_RECOVERY"
  | "WAIT_FOR_UNLOCK"
  | "ABANDON";

/**
 * PR215: Resume Re-execution Timing Control (Delay / Backoff) v1
 *
 * Purpose:
 *   Define when supervisor should re-execute after STOP, not just how.
 *   Enables explainable timing decisions without numeric timestamps.
 *
 * Constitutional:
 *   - READ-ONLY: Fixed delay class mapping, no learning
 *   - Label-only: No numeric timestamps/milliseconds exposed
 *   - Deterministic: Same strategy → same delay class
 *   - Scheduler-less v1: Decision only, no actual scheduling implementation
 *
 * Delay Classes:
 *   - IMMEDIATE: Execute now (e.g., timeout recovery)
 *   - BACKOFF_SHORT: Brief delay (e.g., gate/phase risk cooling)
 *   - BACKOFF_LONG: Extended delay (e.g., system recovery)
 *   - MANUAL: Operator intervention required (e.g., policy unlock)
 */
export type ResumeDelayClassV1 =
  | "IMMEDIATE"
  | "BACKOFF_SHORT"
  | "BACKOFF_LONG"
  | "MANUAL";

/**
 * PR215: Resume Delay Offset Labels (label-only time representation)
 *
 * Purpose:
 *   Express delay duration as discrete labels, not numeric milliseconds.
 *   Enables audit trail without exposing internal timing values.
 *
 * Constitutional:
 *   - Label-only: No numeric values
 *   - Fixed taxonomy: Enumerated duration labels
 *   - Deterministic: Same delay class → same offset label
 */
export type ResumeDelayOffsetLabelV1 =
  | "DELAY_0S"
  | "DELAY_30S"
  | "DELAY_2M"
  | "DELAY_5M"
  | "DELAY_15M"
  | "DELAY_1H";

/**
 * PR220: Market Regime v1 (label-only market condition taxonomy)
 *
 * Purpose:
 *   Classify market conditions to inform strategy/timing decisions.
 *   Enables regime-aware recovery without numeric calculations.
 *
 * Constitutional:
 *   - READ-ONLY: Derived from existing signals, no learning
 *   - Label-only: No BPS/prices/numeric thresholds
 *   - Deterministic: Same signals → same regime
 *   - Safety-first: Regimes guide conservative overlays
 *
 * Regimes:
 *   - REGIME_NORMAL: Nominal conditions (oracle OK, liquidity OK, network OK)
 *   - REGIME_VOLATILE: High volatility (phase shock, gate block)
 *   - REGIME_ILLIQUID: Thin liquidity (depth thin, quote unavailable)
 *   - REGIME_ORACLE_UNCERTAIN: Oracle issues (stale, unavailable)
 *   - REGIME_NETWORK_UNSTABLE: Network degraded or failing
 *   - REGIME_UNKNOWN: Insufficient signals to classify
 */
export type MarketRegimeV1 =
  | "REGIME_NORMAL"
  | "REGIME_VOLATILE"
  | "REGIME_ILLIQUID"
  | "REGIME_ORACLE_UNCERTAIN"
  | "REGIME_NETWORK_UNSTABLE"
  | "REGIME_UNKNOWN";

/**
 * PR220: Market Regime Signals v1 (label-only inputs for regime derivation)
 *
 * Purpose:
 *   Collect existing telemetry-friendly signals for regime classification.
 *   All fields optional, defensive, label-only.
 */
export interface MarketRegimeSignalsV1 {
  oracle_status?: "ORACLE_OK" | "ORACLE_STALE" | "ORACLE_UNAVAILABLE" | "ORACLE_UNKNOWN";
  gate_status?: "PASS" | "BLOCK" | "UNKNOWN";
  gate_depth_status?: "DEPTH_OK" | "DEPTH_THIN" | "DEPTH_UNAVAILABLE" | "DEPTH_UNKNOWN";
  quote_status?: "QUOTE_OK" | "QUOTE_UNAVAILABLE" | "QUOTE_STALE" | "QUOTE_UNKNOWN";
  network_status?: "NET_OK" | "NET_DEGRADED" | "NET_FAIL" | "NET_UNKNOWN";
  phase_label?: string; // e.g., PHASE_NORMAL, PHASE_DOWN_SHOCK, PHASE_UP_REVERSAL
}

/**
 * PR230: Signal Trust & Consensus Layer v1 (Article XI)
 *
 * Purpose:
 *   Multi-source signal verification to prevent single-source market truth risks.
 *   Converts raw signals (oracle/dex/rpc) into trust status + consensus.
 *
 * Constitutional:
 *   - READ-ONLY: Fixed trust mapping rules, no learning
 *   - Label-only: No numeric prices/timestamps/diffs
 *   - Safety-first: Disagreement/missing → degrade, never upgrade
 *   - Deterministic: Same inputs → same outputs
 *   - Defensive: Never throws, fallback to UNTRUSTED
 */

/**
 * Oracle signal status (label-only)
 */
export type OracleStatusV1 =
  | "ORACLE_OK"
  | "ORACLE_STALE"
  | "ORACLE_MISSING"
  | "ORACLE_ERROR"
  | "ORACLE_UNKNOWN";

/**
 * DEX price signal status (label-only)
 */
export type DexPriceStatusV1 =
  | "DEX_OK"
  | "DEX_STALE"
  | "DEX_MISSING"
  | "DEX_ERROR"
  | "DEX_UNKNOWN";

/**
 * RPC health signal status (label-only)
 */
export type RpcHealthStatusV1 =
  | "RPC_OK"
  | "RPC_DEGRADED"
  | "RPC_DOWN"
  | "RPC_UNKNOWN";

/**
 * Quote cross-check status (oracle vs dex comparison, label-only)
 */
export type QuoteCrossCheckStatusV1 =
  | "XCHK_OK"
  | "XCHK_DIVERGED"
  | "XCHK_INSUFFICIENT"
  | "XCHK_UNKNOWN";

/**
 * Per-source trust status (derived from signal status)
 */
export type SignalTrustV1 =
  | "TRUSTED"
  | "DEGRADED"
  | "UNTRUSTED"
  | "UNKNOWN";

/**
 * Signal consensus status (multi-source truth confidence)
 *
 * Rules (safety-first):
 *   - CONSENSUS_STRONG: All sources trusted + cross-check OK
 *   - CONSENSUS_WEAK: Mixed trusted/degraded, no untrusted
 *   - CONSENSUS_DEGRADED: Any source degraded, none untrusted
 *   - CONSENSUS_UNTRUSTED: Any source untrusted OR both oracle+dex unknown
 */
export type SignalConsensusV1 =
  | "CONSENSUS_STRONG"
  | "CONSENSUS_WEAK"
  | "CONSENSUS_DEGRADED"
  | "CONSENSUS_UNTRUSTED";

/**
 * PR230b: Signal Execution Cap Status (label-only)
 *
 * Purpose:
 *   Track whether signal consensus enforced an execution mode cap.
 *
 * Constitutional:
 *   - Label-only: Categorical status, no numeric values
 *   - Deterministic: Same consensus → same cap status
 *   - Safety-first: Non-STRONG consensus → SIM_ONLY (NEVER LIVE)
 *
 * States:
 *   - CAP_NONE: No cap applied (consensus STRONG)
 *   - CAP_SIM_ONLY: Enforced SIM_ONLY (consensus WEAK/DEGRADED/UNTRUSTED)
 *   - CAP_DRY_RUN: Enforced DRY_RUN (optional extension, unused in v1)
 *   - CAP_ERROR: Defensive fallback (error → SIM_ONLY)
 */
export type SignalExecCapStatusV1 =
  | "CAP_NONE"
  | "CAP_SIM_ONLY"
  | "CAP_DRY_RUN"
  | "CAP_ERROR";

/**
 * PR231: Invariant Check Status (label-only)
 *
 * Purpose:
 *   Track result of invariant validation checks (final defensive layer).
 *
 * Constitutional:
 *   - Label-only: Categorical status, no numeric values
 *   - Deterministic: Same inputs → same status
 *   - Safety-first: Violations → INV_FAIL + ACTION_ABORT
 *
 * States:
 *   - INV_PASS: All invariants satisfied
 *   - INV_FAIL: Critical invariant violated (execution aborted)
 *   - INV_WARN: Non-critical issue detected (execution continues)
 */
export type InvariantStatusV1 =
  | "INV_PASS"
  | "INV_FAIL"
  | "INV_WARN";

/**
 * PR231: Invariant Group (label-only)
 *
 * Purpose:
 *   Categorize which invariant group failed (for debugging/telemetry).
 *
 * Constitutional:
 *   - Label-only: Categorical group, no numeric values
 *   - Deterministic: Same failure → same group
 *
 * Groups:
 *   - G0_NONE: No failure (all checks passed)
 *   - G1_EXEC: Execution mode invariant (NEVER LIVE)
 *   - G2_SIGNAL: Signal consensus enforcement invariant
 *   - G3_REGIME: Regime gating invariant
 *   - G4_BUDGET: Budget decision invariant
 *   - G9_UNKNOWN: Unknown/defensive fallback
 */
export type InvariantGroupV1 =
  | "G0_NONE"
  | "G1_EXEC"
  | "G2_SIGNAL"
  | "G3_REGIME"
  | "G4_BUDGET"
  | "G9_UNKNOWN";

/**
 * PR232: Economic Invariant Status (label-only)
 *
 * Purpose:
 *   Economic safety invariants (liquidity, slippage, crash risk, exposure).
 *   Final "last mile" check before execution to prevent capital loss.
 *
 * Constitutional:
 *   - Label-only: No numeric values
 *   - Deterministic: Same inputs → same status
 *   - Safety-first: Violations → EINV_FAIL + action override (ABORT/DEFER)
 *
 * States:
 *   - EINV_PASS: All economic invariants satisfied
 *   - EINV_FAIL: Economic invariant violated (execution prevented)
 */
export type EconomicInvariantStatusV1 =
  | "EINV_PASS"
  | "EINV_FAIL";

/**
 * PR232: Economic Invariant Group (label-only)
 *
 * Purpose:
 *   Categorize which economic invariant group failed.
 *
 * Constitutional:
 *   - Label-only: Categorical group, no numeric values
 *   - Deterministic: Same failure → same group
 *
 * Groups:
 *   - EG0_NONE: No failure (all checks passed)
 *   - EG1_LIQUIDITY: Liquidity adequacy failure
 *   - EG2_SLIPPAGE: Slippage/price impact failure
 *   - EG3_CRASH: Crash risk failure
 *   - EG4_EXPOSURE: Exposure/concentration failure
 *   - EG5_INTEGRITY: Market integrity failure (RPC, crosscheck)
 *   - EG9_UNKNOWN: Unknown/defensive fallback
 */
export type EconomicInvariantGroupV1 =
  | "EG0_NONE"
  | "EG1_LIQUIDITY"
  | "EG2_SLIPPAGE"
  | "EG3_CRASH"
  | "EG4_EXPOSURE"
  | "EG5_INTEGRITY"
  | "EG9_UNKNOWN";

/**
 * PR232: Economic Action Override (label-only)
 *
 * Purpose:
 *   Action override when economic invariant fails.
 *
 * Constitutional:
 *   - Label-only: Categorical action
 *   - Deterministic: Same failure → same override
 *
 * Actions:
 *   - NONE: No override (invariant passed)
 *   - DEFER_BACKOFF_LONG: Defer with long backoff (market conditions may improve)
 *   - DEFER_MANUAL: Defer indefinitely (manual intervention required)
 *   - ABORT: Abort execution immediately (unsafe conditions)
 */
export type EconomicActionOverrideV1 =
  | "NONE"
  | "DEFER_BACKOFF_LONG"
  | "DEFER_MANUAL"
  | "ABORT";

/**
 * PR233: Economic Liquidity Condition (label-only, Article XII)
 *
 * Purpose:
 *   Classify market liquidity depth to prevent execution into thin/vacuum conditions.
 *
 * Constitutional:
 *   - Label-only: No numeric depth/volume values
 *   - Deterministic: Same market state → same classification
 *   - Safety-first: Unknown → conservative treatment
 *
 * States:
 *   - LIQ_UNKNOWN: Insufficient data to classify
 *   - LIQ_HEALTHY: Normal depth, safe for execution
 *   - LIQ_THIN: Reduced depth, requires caution
 *   - LIQ_VACUUM: Critical lack of liquidity (flash crash risk)
 */
export type LiquidityConditionV1 =
  | "LIQ_UNKNOWN"
  | "LIQ_HEALTHY"
  | "LIQ_THIN"
  | "LIQ_VACUUM";

/**
 * PR233: Slippage Risk (label-only, Article XII)
 *
 * Purpose:
 *   Classify expected slippage/price impact risk.
 *
 * Constitutional:
 *   - Label-only: No numeric slippage percentages
 *   - Deterministic: Same conditions → same risk class
 *
 * States:
 *   - SLIP_UNKNOWN: Insufficient data
 *   - SLIP_LOW: Normal conditions
 *   - SLIP_MEDIUM: Elevated but acceptable
 *   - SLIP_HIGH: Significant risk
 *   - SLIP_EXTREME: Unacceptable (likely to cause large losses)
 */
export type SlippageRiskV1 =
  | "SLIP_UNKNOWN"
  | "SLIP_LOW"
  | "SLIP_MEDIUM"
  | "SLIP_HIGH"
  | "SLIP_EXTREME";

/**
 * PR233: Exposure Status (label-only, Article XII)
 *
 * Purpose:
 *   Classify position size relative to risk limits.
 *   No numeric amounts, derived from internal position tracking.
 *
 * Constitutional:
 *   - Label-only: No USD amounts or percentages
 *   - Deterministic: Same position state → same classification
 *
 * States:
 *   - EXP_UNKNOWN: Cannot classify
 *   - EXP_NONE: No position
 *   - EXP_SMALL: Within conservative bounds
 *   - EXP_MEDIUM: Normal operational level
 *   - EXP_LARGE: Approaching limits (requires caution)
 *   - EXP_EXCESSIVE: Over limits (requires reduction/abort)
 */
export type ExposureStatusV1 =
  | "EXP_UNKNOWN"
  | "EXP_NONE"
  | "EXP_SMALL"
  | "EXP_MEDIUM"
  | "EXP_LARGE"
  | "EXP_EXCESSIVE";

/**
 * PR233: Drawdown Status (label-only, Article XII)
 *
 * Purpose:
 *   Classify equity drawdown state for circuit breaker logic.
 *   Optional; requires equity curve tracking.
 *
 * Constitutional:
 *   - Label-only: No numeric drawdown percentages
 *   - Deterministic: Same equity state → same classification
 *
 * States:
 *   - DD_UNKNOWN: No equity tracking available
 *   - DD_OK: Within normal variance
 *   - DD_WARNING: Elevated losses (caution required)
 *   - DD_CRITICAL: Severe drawdown (circuit breaker)
 */
export type DrawdownStatusV1 =
  | "DD_UNKNOWN"
  | "DD_OK"
  | "DD_WARNING"
  | "DD_CRITICAL";

/**
 * PR233: Economic Constraint Action (label-only, Article XII)
 *
 * Purpose:
 *   Final economic constraint decision.
 *
 * Constitutional:
 *   - Label-only: Categorical action
 *   - Deterministic: Same risk envelope → same action
 *
 * Actions:
 *   - ECON_ALLOW: Proceed (risk acceptable)
 *   - ECON_DEFER: Defer execution (conditions too risky)
 *   - ECON_ABANDON: Abandon execution (unrecoverable risk state)
 */
export type EconConstraintActionV1 =
  | "ECON_ALLOW"
  | "ECON_DEFER"
  | "ECON_ABANDON";

/**
 * PR233: Economic Constraint Class (label-only, Article XII)
 *
 * Purpose:
 *   Classify overall economic risk level.
 *
 * Constitutional:
 *   - Label-only: Risk category
 *   - Deterministic: Same inputs → same class
 *
 * Classes:
 *   - E0_OK: All constraints satisfied
 *   - E1_CONSERVATIVE: Marginal conditions (caution)
 *   - E2_RISKY: Elevated risk (defer recommended)
 *   - E3_FORBIDDEN: Hard constraint violation (must defer/abandon)
 *   - E9_ERROR: Error in evaluation (defensive fallback)
 */
export type EconConstraintClassV1 =
  | "E0_OK"
  | "E1_CONSERVATIVE"
  | "E2_RISKY"
  | "E3_FORBIDDEN"
  | "E9_ERROR";

/**
 * PR233b: Economic Execution Size Cap (label-only, Article XII-b)
 *
 * Purpose:
 *   Control execution size based on economic risk state.
 *
 * Constitutional:
 *   - Label-only: No numeric amounts
 *   - Deterministic: Same risk → same cap
 *
 * States:
 *   - SIZE_NONE: No cap (normal execution)
 *   - SIZE_TINY: Very small execution
 *   - SIZE_SMALL: Small execution
 *   - SIZE_ZERO: No execution (effectively blocked)
 */
export type EconomicExecSizeCapV1 =
  | "SIZE_NONE"
  | "SIZE_TINY"
  | "SIZE_SMALL"
  | "SIZE_ZERO";

/**
 * PR233b: Economic Execution Frequency Cap (label-only, Article XII-b)
 *
 * Purpose:
 *   Control execution frequency/cadence based on economic risk state.
 *
 * Constitutional:
 *   - Label-only: No numeric timing values
 *   - Deterministic: Same risk → same cap
 *
 * States:
 *   - FREQ_NONE: No frequency restriction
 *   - FREQ_SLOW: Slower cadence (prefer backoff)
 *   - FREQ_COOLDOWN: Enforce cooldown active
 */
export type EconomicExecFreqCapV1 =
  | "FREQ_NONE"
  | "FREQ_SLOW"
  | "FREQ_COOLDOWN";

/**
 * PR233b: Economic Capital Cap (label-only, Article XII-b)
 *
 * Purpose:
 *   Control capital allocation based on economic risk state.
 *
 * Constitutional:
 *   - Label-only: No numeric USD/USDC amounts
 *   - Deterministic: Same risk → same cap
 *
 * States:
 *   - CAPITAL_NONE: No capital restriction
 *   - CAPITAL_LOW: Low capital allocation
 *   - CAPITAL_MINIMAL: Minimal capital (safety mode)
 */
export type EconomicCapitalCapV1 =
  | "CAPITAL_NONE"
  | "CAPITAL_LOW"
  | "CAPITAL_MINIMAL";

/**
 * PR233b: Economic Execution Shape Status (label-only, Article XII-b)
 *
 * Purpose:
 *   Track whether execution shaping was applied.
 *
 * Constitutional:
 *   - Label-only: Status indicator
 *   - Deterministic: Same inputs → same status
 *
 * States:
 *   - SHAPE_NONE: No shaping applied (risk OK)
 *   - SHAPE_APPLIED: Shaping constraints active
 *   - SHAPE_ERROR: Error in shaping derivation
 */
export type EconomicExecShapeStatusV1 =
  | "SHAPE_NONE"
  | "SHAPE_APPLIED"
  | "SHAPE_ERROR";

/**
 * PR234: Capital-at-Risk Window Status (label-only, Article XIII)
 *
 * Purpose:
 *   Track rolling time window status for cumulative risk envelope.
 *
 * Constitutional:
 *   - Label-only: Window state indicator
 *   - Deterministic: Same timestamp → same status
 *
 * States:
 *   - WIN_FRESH: Window just initialized
 *   - WIN_ACTIVE: Window currently active
 *   - WIN_EXPIRED: Window expired, needs reset
 */
export type CapitalRiskWindowStatusV1 =
  | "WIN_FRESH"
  | "WIN_ACTIVE"
  | "WIN_EXPIRED";

/**
 * PR234: Capital-at-Risk Usage Level (label-only, Article XIII)
 *
 * Purpose:
 *   Classify cumulative risk event usage within window (label-only).
 *
 * Constitutional:
 *   - Label-only: No raw event counts in telemetry
 *   - Deterministic: Same count → same level
 *
 * States:
 *   - RISK_LOW: 0-2 events (safe zone)
 *   - RISK_MEDIUM: 3-5 events (caution)
 *   - RISK_HIGH: 6-8 events (approaching limit)
 *   - RISK_EXHAUSTED: >=9 events (envelope exhausted)
 */
export type CapitalRiskUsageLevelV1 =
  | "RISK_LOW"
  | "RISK_MEDIUM"
  | "RISK_HIGH"
  | "RISK_EXHAUSTED";

/**
 * PR234: Capital-at-Risk Action (label-only, Article XIII)
 *
 * Purpose:
 *   Envelope decision based on usage level.
 *
 * Constitutional:
 *   - Label-only: Action indicator
 *   - Deterministic: Same level → same action
 *
 * States:
 *   - CAR_ALLOW: Envelope OK, allow execution
 *   - CAR_DEFER: Envelope stressed, defer with backoff
 *   - CAR_ABORT: Envelope exhausted, abort execution
 */
export type CapitalRiskActionV1 =
  | "CAR_ALLOW"
  | "CAR_DEFER"
  | "CAR_ABORT";

/**
 * PR235: Adversarial Incident Type (label-only, Article XIV)
 *
 * Purpose:
 *   Classify detected adversarial market conditions (flash crash, oracle manipulation, etc.).
 *
 * Constitutional:
 *   - Label-only: Incident classification
 *   - Deterministic: Same signals → same incident type
 *   - Safety-first: When in doubt, classify as incident
 *
 * States:
 *   - INC_NONE: No adversarial incident detected
 *   - INC_FLASH_CRASH: Flash crash detected (volatile + oscillation/caprisk)
 *   - INC_ORACLE_MANIPULATION: Oracle price divergence detected
 *   - INC_NETWORK_PARTITION: Network/RPC failure detected
 *   - INC_SIGNAL_STARVATION: Signal consensus untrusted
 *   - INC_UNKNOWN: Unknown incident type
 */
export type IncidentTypeV1 =
  | "INC_NONE"
  | "INC_FLASH_CRASH"
  | "INC_ORACLE_MANIPULATION"
  | "INC_NETWORK_PARTITION"
  | "INC_SIGNAL_STARVATION"
  | "INC_UNKNOWN";

/**
 * PR235: Incident Severity (label-only, Article XIV)
 *
 * Purpose:
 *   Classify incident severity for quarantine activation.
 *
 * Constitutional:
 *   - Label-only: Severity classification
 *   - Deterministic: Same incident → same severity
 *   - Safety-first: Critical incidents get strongest quarantine
 *
 * States:
 *   - SEV0_NONE: No incident
 *   - SEV1_SUSPECT: Suspected incident (observe only)
 *   - SEV2_HIGH: High severity (quarantine + defer)
 *   - SEV3_CRITICAL: Critical severity (quarantine + abort)
 */
export type IncidentSeverityV1 =
  | "SEV0_NONE"
  | "SEV1_SUSPECT"
  | "SEV2_HIGH"
  | "SEV3_CRITICAL";

/**
 * PR235: Quarantine Status (label-only, Article XIV)
 *
 * Purpose:
 *   Track quarantine state machine status.
 *
 * Constitutional:
 *   - Label-only: Status indicator
 *   - Deterministic: Same state → same status
 *
 * States:
 *   - Q0_NONE: No quarantine active
 *   - Q1_ACTIVE: Quarantine active (isolating LIVE execution)
 *   - Q2_EXPIRED: Quarantine expired (exit conditions met)
 *   - Q9_ERROR: Error in quarantine derivation
 */
export type QuarantineStatusV1 =
  | "Q0_NONE"
  | "Q1_ACTIVE"
  | "Q2_EXPIRED"
  | "Q9_ERROR";

/**
 * PR235: Quarantine Action (label-only, Article XIV)
 *
 * Purpose:
 *   Quarantine decision based on incident severity.
 *
 * Constitutional:
 *   - Label-only: Action indicator
 *   - Deterministic: Same severity → same action
 *   - Safety-first: Critical → abort, High → defer
 *
 * States:
 *   - QA_ALLOW: No quarantine, allow execution
 *   - QA_DEFER: Quarantine active, defer with long backoff
 *   - QA_ABORT: Quarantine active, abort execution
 */
export type QuarantineActionV1 =
  | "QA_ALLOW"
  | "QA_DEFER"
  | "QA_ABORT";

/**
 * PR235: Quarantine Exit Condition (label-only, Article XIV)
 *
 * Purpose:
 *   Define how quarantine can be automatically released.
 *
 * Constitutional:
 *   - Label-only: Exit condition indicator
 *   - Deterministic: Same severity → same exit condition
 *   - Safety-first: Critical incidents require manual intervention
 *
 * States:
 *   - EXIT_NONE: No exit condition (not quarantined)
 *   - EXIT_MANUAL_ONLY: Manual intervention required (critical incidents)
 *   - EXIT_CONSENSUS_STRONG_2TICKS: Requires 2 consecutive strong consensus ticks
 *   - EXIT_COOLDOWN_EXPIRED: Cooldown period (60min) expired
 */
export type QuarantineExitConditionV1 =
  | "EXIT_NONE"
  | "EXIT_MANUAL_ONLY"
  | "EXIT_CONSENSUS_STRONG_2TICKS"
  | "EXIT_COOLDOWN_EXPIRED";

/**
 * PR236: Recovery Permission v1 (Article XV - Recovery Governance Layer)
 *
 * Purpose:
 *   Define whether automatic recovery (resume re-execution) is permitted after major stops.
 *
 * Constitutional:
 *   - Label-only: Recovery permission state
 *   - Deterministic: Same stop class → same permission
 *   - Safety-first: Major stops require manual intervention or cooldown
 *
 * States:
 *   - AUTO_ALLOWED: Automatic recovery permitted (normal operation)
 *   - COOLDOWN_ONLY: Automatic recovery permitted but requires cooldown delay
 *   - MANUAL_ONLY: Automatic recovery prohibited, manual operator intervention required
 *   - PERMANENT_HALT: Permanent stop, no automatic or manual recovery (audit final state)
 */
export type RecoveryPermissionV1 =
  | "AUTO_ALLOWED"
  | "COOLDOWN_ONLY"
  | "MANUAL_ONLY"
  | "PERMANENT_HALT";

/**
 * PR236: Recovery Gate Action v1 (Article XV - Governance action)
 *
 * Purpose:
 *   Define supervisor action based on recovery permission state.
 *
 * Actions:
 *   - RG_ALLOW: Continue recovery pipeline (call runner)
 *   - RG_DEFER: Defer recovery (delay/backoff, don't call runner yet)
 *   - RG_ABORT: Abort recovery attempt (don't call runner, keep resume state)
 *   - RG_ABANDON: Abandon recovery (don't call runner, clear resume state)
 */
export type RecoveryGateActionV1 =
  | "RG_ALLOW"
  | "RG_DEFER"
  | "RG_ABORT"
  | "RG_ABANDON";

/**
 * PR236: Recovery Gate Reason v1 (Article XV - Trigger/source)
 *
 * Purpose:
 *   Track what triggered the recovery governance decision.
 *
 * Reasons:
 *   - BY_NONE: No special governance (normal operation)
 *   - BY_QUARANTINE_SEV2: Quarantine SEV2_HIGH active
 *   - BY_QUARANTINE_SEV3: Quarantine SEV3_CRITICAL active (fatal)
 *   - BY_CAR_EXHAUSTED: Capital-at-risk envelope exhausted
 *   - BY_ECON_ABANDON: Economic constraints abandoned
 *   - BY_BUDGET_ABANDON: Recovery budget abandoned
 *   - BY_INVARIANT_FAIL: Invariant check failed (fatal)
 *   - BY_OPERATOR_MANUAL_HOLD: Operator manual hold override
 *   - BY_OPERATOR_MANUAL_RELEASE: Operator manual release override
 */
export type RecoveryGateReasonV1 =
  | "BY_NONE"
  | "BY_QUARANTINE_SEV2"
  | "BY_QUARANTINE_SEV3"
  | "BY_CAR_EXHAUSTED"
  | "BY_ECON_ABANDON"
  | "BY_BUDGET_ABANDON"
  | "BY_INVARIANT_FAIL"
  | "BY_OPERATOR_MANUAL_HOLD"
  | "BY_OPERATOR_MANUAL_RELEASE";

/**
 * PR237: Learning Freeze Status v1 (Article XVI - Learning Freeze & Drift Firewall)
 *
 * Purpose:
 *   Control whether adaptive/learning components can update during abnormal states.
 *   Prevents "learning from disequilibrium" - contaminated signals from hostile periods.
 *
 * Constitutional:
 *   - Label-only: Freeze state (no numeric thresholds)
 *   - Deterministic: Same inputs → same freeze decision
 *   - Fail-closed: On error → FREEZE_ON (defensive)
 *
 * States:
 *   - FREEZE_OFF: Normal operation, adaptive components may update
 *   - FREEZE_ON: Freeze active, adaptive components must use conservative defaults
 *   - FREEZE_ERROR: Defensive error state (treated as FREEZE_ON)
 */
export type LearningFreezeStatusV1 = "FREEZE_OFF" | "FREEZE_ON" | "FREEZE_ERROR";

/**
 * PR237: Learning Freeze Reason v1 (Article XVI - Trigger/source)
 *
 * Purpose:
 *   Track what triggered the learning freeze activation.
 *
 * Priority order (most severe wins):
 *   INV_FAIL > QUAR_ACTIVE > RISK_EXHAUSTED > GOV_NOT_AUTO > SIGNAL_NOT_STRONG > ECON_SEV_HIGH > RISK_HIGH > OSC_WARN
 *
 * Reasons:
 *   - LFR_NONE: No freeze trigger (normal operation)
 *   - LFR_SIGNAL_NOT_STRONG: Signal consensus not STRONG (degraded/weak)
 *   - LFR_QUARANTINE_ACTIVE: Adversarial quarantine active
 *   - LFR_GOV_NOT_AUTO: Governance permission not AUTO_ALLOWED
 *   - LFR_ECON_SEV_HIGH: Economic severity HIGH or CRITICAL
 *   - LFR_CAPITAL_RISK_HIGH: Capital-at-risk level HIGH or EXHAUSTED
 *   - LFR_OSC_WARN: Oscillation warning active
 *   - LFR_INVARIANT_FAIL: Invariant check failed (highest priority)
 *   - LFR_DEFENSIVE_ERROR: Defensive error fallback
 */
export type LearningFreezeReasonV1 =
  | "LFR_NONE"
  | "LFR_SIGNAL_NOT_STRONG"
  | "LFR_QUARANTINE_ACTIVE"
  | "LFR_GOV_NOT_AUTO"
  | "LFR_ECON_SEV_HIGH"
  | "LFR_CAPITAL_RISK_HIGH"
  | "LFR_OSC_WARN"
  | "LFR_INVARIANT_FAIL"
  | "LFR_DEFENSIVE_ERROR";

/**
 * PR237: Learning Freeze Exit v1 (Article XVI - Exit protocol)
 *
 * Purpose:
 *   Track how freeze will be/was exited.
 *
 * Exit conditions:
 *   - LFX_NONE: No exit (freeze active or never activated)
 *   - LFX_AUTO_STABLE_2TICK: Automatic exit after 2 stable ticks (no triggers)
 *   - LFX_COOLDOWN_60MIN: Exit after 60min cooldown (v1.1, future)
 *   - LFX_MANUAL_RELEASE: Manual operator release override
 */
export type LearningFreezeExitV1 =
  | "LFX_NONE"
  | "LFX_AUTO_STABLE_2TICK"
  | "LFX_COOLDOWN_60MIN"
  | "LFX_MANUAL_RELEASE";

/**
 * PR240: Market Phase Graph v1 (Article XVII - Market Phase State Machine)
 *
 * Purpose:
 *   Introduce "Market Phase" as a higher-order state machine above Regime.
 *   - Regime = instantaneous market condition label
 *   - Phase = structural stage of market evolution (state + transition graph)
 *   Provides deterministic, READ-ONLY, label-only phase derivation and phase transition rules.
 *
 * Use Cases:
 *   (A) Clamp which regimes/strategies are eligible
 *   (B) Adjust recovery timing
 *   (C) Improve safety explainability
 *
 * Constitutional:
 *   - READ-ONLY: Fixed rules, no learning, no numeric telemetry
 *   - Label-only outputs: phases, edges, reasons, confidence buckets
 *   - Deterministic: Same inputs → same phase/transition
 *   - Defensive: Never throws; on error → safety-first phase
 *
 * Phases (ordered by severity: CALM < TENSION < STRESS < DISLOCATION):
 *   - PHASE_CALM: Stable signals + low stress
 *   - PHASE_TENSION: Early stress / weak consensus / mild risk shaping
 *   - PHASE_STRESS: Degraded signals / repeated tightening / conservative execution
 *   - PHASE_DISLOCATION: Incident/quarantine/capital-risk high; only sim/manual pathways
 *   - PHASE_RECOVERY: Post-incident normalization under cooldown governance
 *   - PHASE_UNKNOWN_SAFE: Defensive fallback (safety-first)
 */
export type MarketPhaseV1 =
  | "PHASE_CALM"
  | "PHASE_TENSION"
  | "PHASE_STRESS"
  | "PHASE_DISLOCATION"
  | "PHASE_RECOVERY"
  | "PHASE_UNKNOWN_SAFE";

/**
 * PR240: Market Phase Edge v1 (Phase Transition Labels)
 *
 * Purpose:
 *   Track how phase transitions occur (for observability and safety audit).
 *
 * Edges:
 *   - EDGE_STAY: No phase change (stable)
 *   - EDGE_ESCALATE: Phase worsened (CALM→TENSION→STRESS→DISLOCATION)
 *   - EDGE_DEESCALATE: Phase improved (DISLOCATION→RECOVERY→TENSION→CALM)
 *   - EDGE_RESET_SAFE: Initial safe posture (no prior phase)
 *   - EDGE_ERROR_SAFE: Defensive error fallback
 */
export type MarketPhaseEdgeV1 =
  | "EDGE_STAY"
  | "EDGE_ESCALATE"
  | "EDGE_DEESCALATE"
  | "EDGE_RESET_SAFE"
  | "EDGE_ERROR_SAFE";

/**
 * PR240: Market Phase Confidence v1 (Label-only confidence buckets)
 *
 * Purpose:
 *   Indicate confidence level in phase derivation based on input signal quality.
 *
 * Confidence Levels:
 *   - CONF_STRONG: All required signals present & trusted
 *   - CONF_WEAK: Some degraded but sufficient
 *   - CONF_UNKNOWN: Missing/unknown inputs → safe fallback
 */
export type MarketPhaseConfidenceV1 =
  | "CONF_STRONG"
  | "CONF_WEAK"
  | "CONF_UNKNOWN";

/**
 * PR240: Market Phase Truth v1 (Phase derivation output)
 *
 * Purpose:
 *   Deterministic output of phase derivation function.
 *   Contains phase, edge, confidence, and explainability codes.
 *
 * Fields:
 *   - phase: Current market phase
 *   - edge: Phase transition edge
 *   - confidence: Confidence level in phase derivation
 *   - phase_codes: Explainability codes for phase (dedup/sort/truncate 8)
 *   - phase_edge_codes: Explainability codes for edge (dedup/sort/truncate 8)
 */
export interface MarketPhaseTruthV1 {
  phase: MarketPhaseV1;
  edge: MarketPhaseEdgeV1;
  confidence: MarketPhaseConfidenceV1;
  phase_codes: string[];
  phase_edge_codes: string[];
}

/**
 * Normalized signal truth output (for downstream regime derivation)
 */
export interface SignalTruthV1 {
  // Per-source trust status
  oracle_trust: SignalTrustV1;
  dex_trust: SignalTrustV1;
  rpc_trust: SignalTrustV1;

  // Cross-check status
  crosscheck_status: QuoteCrossCheckStatusV1;

  // Consensus (overall truth confidence)
  consensus: SignalConsensusV1;

  // Explainability codes (dedup/sort/truncate to 8)
  truth_codes: string[];
}

/**
 * PR211: Phase transition reason taxonomy (PHASE explainability v1)
 *
 * Purpose:
 *   Track WHY phase transitions occurred (not just that they did).
 *   Label-only, defensive, deterministic.
 *
 * Transition types (what changed):
 *   - PHASE_TXN_*: Describes the state machine transition
 *
 * Trigger categories (why it changed):
 *   - PHASE_TRIG_*: Root cause of the transition
 */
export type PhaseTransitionReasonCode =
  // Transition types (state machine edges)
  | "PHASE_TXN_NORMAL_TO_RANGE"
  | "PHASE_TXN_RANGE_TO_DOWN_SHOCK"
  | "PHASE_TXN_RANGE_TO_UP_REVERSAL"
  | "PHASE_TXN_DOWN_SHOCK_TO_RANGE"
  | "PHASE_TXN_UP_REVERSAL_TO_RANGE"
  | "PHASE_TXN_UNKNOWN"
  // Trigger categories (root causes)
  | "PHASE_TRIG_GATE_BLOCK"
  | "PHASE_TRIG_POLICY_HARDSTOP"
  | "PHASE_TRIG_QUOTE_IMPACT_ELEVATED"
  | "PHASE_TRIG_SLIPPAGE_ELEVATED"
  | "PHASE_TRIG_MINOUT_ZERO"
  | "PHASE_TRIG_MINOUT_UNAVAILABLE"
  | "PHASE_TRIG_EXEC_ERROR"
  | "PHASE_TRIG_EXEC_DISABLED"
  | "PHASE_TRIG_TIMEOUT_PRESSURE"
  | "PHASE_TRIG_UNKNOWN";

/**
 * Resume state (stopped run state for resume evaluation)
 */
export interface ResumeState {
  // Status (constant "STOPPED")
  status: "STOPPED";

  // Stop reason (label-only)
  stopReason: StopReason;

  // Stop timestamp (internal numeric only)
  stopAtTs: number;

  // Resume after timestamp (internal numeric only, optional)
  resumeAfterTs?: number;

  // Last phase label (label-only, for observability)
  lastPhaseLabel?: string;

  // Last route (label-only, for observability)
  lastRoute?: string;

  // Last template ID (label-only, for observability)
  lastTemplateId?: string;

  // Last intent (label-only, for observability)
  lastIntent?: string;

  // Warnings (label-only)
  warnings: string[];

  // PR209: Resume origin context (persisted from original STOP for telemetry traceability)
  originStopCause?: StopCause;
  originRunReasonCodes?: string[];

  // PR218: Orchestrator feedback (last known result, optional)
  orchLastStatus?: string; // OrchResultStatusV1 from orchestrator/interface
  orchLastOutcomeCodes?: string[];
  orchLastResultId?: string;

  // PR220: Market regime context (last known regime, optional)
  marketRegime?: MarketRegimeV1;
  marketRegimeCodes?: string[];

  // PR221: Orchestrator feedback staleness tracking (hotfix v1.4.1)
  orchLastStatusTs?: number; // Timestamp when orchLastStatus was set (internal only, not emitted in labels)

  // PR222: Deferral guard tracking (hotfix v1.4.1)
  deferralCount?: number; // Count of consecutive deferrals for this resume
  firstDeferredAtTs?: number; // Timestamp when first deferred (internal only, not emitted in labels)

  // PR224: Regime hysteresis (v1.5 stability guards)
  priorRegime?: MarketRegimeV1; // Last confirmed regime (after hysteresis)
  regimeHistory?: MarketRegimeV1[]; // Last N instant regimes (circular buffer, N=3)

  // PR225: Consecutive success gating (v1.5 stability guards)
  consecutiveSuccesses?: number; // Counter for consecutive SUCCEEDED statuses (internal only, not emitted as raw number)
  lastOrchEffectiveStatus?: string; // Last effective orch status (for deterministic resets)

  // PR226: Oscillation detection (v1.5 stability guards)
  strategyChangeCount?: number; // Changes within 1h window (internal only)
  lastStrategyChangeTs?: number; // Timestamp of last strategy change (internal only)
  regimeChangeCount?: number; // Changes within 1h window (internal only)
  lastRegimeChangeTs?: number; // Timestamp of last regime change (internal only)
  lastObservedStrategy?: ResumeStrategyV1; // Last observed strategy
  lastObservedRegime?: MarketRegimeV1; // Last observed regime

  // PR229: Recovery Budgeting (暴走防止、内部数値保持OK、telemetryはclassのみ)
  recoveryAttemptCount?: number; // Attempt counter (internal only, not emitted as raw number)
  recoveryWindowAnchorTs?: number; // Window anchor timestamp (internal only)
  recoveryImmediateCountInWindow?: number; // IMMEDIATE count within window (internal only)
  recoveryFailedMarketCountInWindow?: number; // FAILED_MARKET count within window (internal only)
  recoveryWindowLastResetTs?: number; // Last window reset timestamp (internal only, optional)

  // PR230: Signal Trust & Consensus (Article XI - No Single Source of Market Truth)
  lastSignalConsensus?: SignalConsensusV1; // Last consensus status (for audit continuity)
  lastSignalConsensusCodes?: string[]; // Last consensus codes
  lastSignalTrustOracle?: SignalTrustV1; // Last oracle trust
  lastSignalTrustDex?: SignalTrustV1; // Last dex trust
  lastSignalTrustRpc?: SignalTrustV1; // Last rpc trust

  // PR233: Economic Risk Constraints (Article XII - LIVE Capital Safety)
  lastLiquidityCondition?: LiquidityConditionV1; // Last liquidity classification
  lastSlippageRisk?: SlippageRiskV1; // Last slippage risk classification
  lastExposureStatus?: ExposureStatusV1; // Last exposure classification
  lastDrawdownStatus?: DrawdownStatusV1; // Last drawdown state
  econConstraintLastAction?: EconConstraintActionV1; // Last constraint action
  econConstraintCooldownUntilTs?: number; // Cooldown expiry timestamp (internal only, not emitted)
  econConstraintActionCountInWindow?: number; // DEFER/ABANDON count within window (internal only)
  econConstraintWindowAnchorTs?: number; // Window anchor timestamp (internal only)

  // PR234: Capital-at-Risk Envelope (Article XIII - Runaway Prevention)
  capitalRiskWindowAnchorTs?: number; // Rolling window anchor timestamp (internal only, not emitted)
  capitalRiskEventsInWindow?: number; // Risk event counter within window (internal only, NOT emitted as raw number)
  capitalRiskLevelLast?: CapitalRiskUsageLevelV1; // Last usage level (for audit continuity)

  // PR235: Adversarial Incident Quarantine (Article XIV - Adversarial Market Isolation)
  quarantineActiveSinceTs?: number; // Quarantine activation timestamp (internal only, not emitted as raw)
  quarantineIncidentType?: IncidentTypeV1; // Detected incident type
  quarantineSeverity?: IncidentSeverityV1; // Incident severity
  quarantineExitCondition?: QuarantineExitConditionV1; // Exit condition for this quarantine
  quarantineConsecutiveStrongConsensus?: number; // Counter for 2-tick exit (internal only, NOT emitted as raw number)
  quarantineLastWindowResetTs?: number; // Last window reset timestamp (internal only)

  // PR236: Recovery Governance Layer (Article XV - Recovery Permission Control)
  recoveryPermission?: RecoveryPermissionV1; // Current recovery permission state
  recoveryPermissionReason?: RecoveryGateReasonV1; // Reason for current permission state
  recoveryPermissionSinceTs?: number; // Permission state activation timestamp (internal only, for age tracking)
  recoveryCooldownUntilTs?: number; // Cooldown expiry timestamp (internal only, not emitted as raw)
  recoveryManualHoldUntilTs?: number; // Manual hold expiry timestamp (internal only, optional)
  recoveryGateLastAction?: RecoveryGateActionV1; // Last gate action taken
  recoveryGateCodes?: string[]; // Gate decision codes (internal, telemetry is summary)
  lastMajorStopClass?: "STOP_NONE" | "STOP_SOFT" | "STOP_MAJOR" | "STOP_FATAL"; // Last major stop classification (optional)

  // PR237: Learning Freeze & Drift Firewall (Article XVI - Prevent learning from disequilibrium)
  learningFreezeStatus?: LearningFreezeStatusV1; // Current freeze state (FREEZE_OFF/ON/ERROR)
  learningFreezeReason?: LearningFreezeReasonV1; // Reason for freeze activation
  learningFreezeSinceTs?: number; // Freeze activation timestamp (internal only, not emitted as raw)
  learningFreezeCooldownAnchorTs?: number; // Cooldown window anchor timestamp (internal only, v1.1)
  learningFreezeStableTickCount?: number; // Consecutive stable ticks counter (internal only, 0/1/2 for exit)
  learningFreezeLastDecisionCodes?: string[]; // Last decision codes (internal audit trail)

  // PR240: Market Phase Graph v1 (Article XVII - Market Phase State Machine)
  lastMarketPhase?: MarketPhaseV1; // Last market phase (for edge derivation)
  lastMarketPhaseTs?: number; // Phase activation timestamp (internal only, NOT emitted)
  lastMarketPhaseCodes?: string[]; // Last phase decision codes (optional)
}

/**
 * PR212: Phase Policy Evaluator v1 (separation of concerns)
 *
 * Purpose:
 *   Separate phase transition decision logic from execution loop.
 *   READ-ONLY policy evaluator for phase updates and STOP conditions.
 */

/**
 * Phase policy inputs (v1)
 * PR212a: Updated to label-only (no numeric inputs)
 */
export interface PhasePolicyInputsV1 {
  // Previous phase label (PHASE_UNKNOWN if first chunk)
  prevPhase: string;

  // Current phase label (from observation)
  currentPhase: string;

  // Stop cause category (from runner context)
  stopCause: StopCause;

  // Gate status (from gate evaluation)
  gateStatus: "PASS" | "BLOCK" | "ERROR";

  // Policy status (from policy evaluation)
  policyStatus: "ALLOW" | "SIM_ONLY" | "BLOCKED" | "ERROR";

  // Blocked streak status (label-only)
  blockedStreakStatus: "STREAK_OK" | "STREAK_EXCEEDED";

  // Timeout status (label-only)
  timeoutStatus: "TIMEOUT_OK" | "TIMEOUT_EXCEEDED";
}

/**
 * Phase policy decision (v1)
 */
export interface PhasePolicyDecisionV1 {
  // Next phase label (may be same as current)
  nextPhase: string;

  // Phase changed? (true if prevPhase !== nextPhase)
  changed: boolean;

  // Transition codes (label-only: PHASE_TXN_* and PHASE_TRIG_*)
  transitionCodes: string[];

  // Should stop the run?
  shouldStop: boolean;

  // Stop cause (if shouldStop=true)
  stopCause?: StopCause;
}
