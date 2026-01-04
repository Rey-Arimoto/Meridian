# Architectural Decision Records (ADR)
**Meridian Project**

This document records the **key design decisions** made in Meridian,
including *why they were made*, *what alternatives were rejected*,
and *what consequences they impose*.

This file serves as:
- a long-term memory for the project,
- a guard against accidental design drift,
- and an audit trail for future contributors and investors.

---

## ADR-001: Entropy as a State Variable, Not a Signal

**Status**: Accepted  
**Context**: Early design (v0.1)

### Decision

Entropy in Meridian is defined as a **state variable representing explanation failure**,  
not as a predictive signal or trading indicator.

### Rationale

- Predictive signals invite overfitting and regime collapse.
- State variables define *boundaries*, not *opportunities*.
- Intelligence begins by knowing when **not** to act.

Entropy answers:
> *Should action be allowed at all?*

### Alternatives Considered

- Volatility-based indicators (rejected: directional misuse)
- Probabilistic regime classifiers (rejected: opacity)
- ML-based anomaly detection (rejected: non-determinism)

### Consequences

- Entropy must be computed **before** any strategy logic.
- High entropy forbids action entirely.
- Strategy quality is irrelevant under entropy violation.

---

## ADR-002: Composite Entropy via Max(EA, ES)

**Status**: Accepted  
**Context**: v0.1 entropy definition

### Decision

Composite entropy is defined as:
Entropy = max(EA_norm, ES_norm)
Where:
- EA = Entropy of Amplitude
- ES = Entropy of Structure

### Rationale

- Explanation fails if **either** magnitude or structure collapses.
- Averaging would mask single-dimension failure.
- Max preserves worst-case explanatory breakdown.

### Alternatives Considered

- Arithmetic mean (rejected: hides collapse)
- Weighted sum (rejected: introduces subjective tuning)
- Multiplicative form (rejected: unstable scaling)

### Consequences

- Entropy is conservative by construction.
- One failure dimension is sufficient to freeze action.

---

## ADR-003: Normalization to [0.0, 1.0] and Basis Points

**Status**: Accepted  
**Context**: Logging and determinism

### Decision

All entropy values are normalized to:
[0.0, 1.0] → [0, 10000 bp]
### Rationale

- Enables deterministic thresholds.
- Simplifies audit logs.
- Avoids floating-point ambiguity in governance rules.

### Alternatives Considered

- Raw statistical values (rejected: non-comparable)
- Percent only (rejected: insufficient precision)

### Consequences

- `Entropy_bp` is the canonical decision value.
- All freeze logic depends on basis points.

---

## ADR-004: Constitutional Freeze (Entropy-Based)

**Status**: Accepted  
**Context**: Core safety mechanism

### Decision

Meridian enforces an unconditional freeze rule:
If Entropy_bp ≥ CRITICAL_ENTROPY_BP:
Action = FREEZE (NoOp enforced)
### Rationale

- Strategy competence is meaningless under explanation failure.
- Survival precedes optimization.
- Intelligence must have inviolable boundaries.

### Alternatives Considered

- Soft position reduction (rejected: still acting)
- Strategy-specific overrides (rejected: unsafe)
- Manual intervention (rejected: non-deterministic)

### Consequences

- Freeze cannot be overridden by signals or agents.
- Freeze events are logged with explicit reason.
- No capital deployment during chaos.

---

## ADR-005: NoOp as a First-Class Action

**Status**: Accepted  
**Context**: Action semantics

### Decision

NoOp is treated as a **deliberate, logged action**, not as absence of action.

### Rationale

- In chaotic regimes, restraint is the optimal action.
- Silence without intent is ambiguous.
- Intelligence must *choose* not to act.

### Alternatives Considered

- Implicit inactivity (rejected: unauditable)
- Pause states (rejected: unclear semantics)

### Consequences

- NoOp appears explicitly in logs.
- Freeze = enforced NoOp with reason.
- Future agents must justify non-action.

---

## ADR-006: Determinism as a Hard Requirement (v0.x)

**Status**: Accepted  
**Context**: Pre-agent phase

### Decision

Meridian v0.x forbids:
- learning,
- parameter adaptation,
- stochastic decision logic.

### Rationale

- Determinism enables trust.
- Determinism enables audit.
- Non-determinism before governance is unsafe.

### Alternatives Considered

- Online learning (rejected: unbounded behavior)
- LLM-driven decisioning (rejected: non-reproducible)

### Consequences

- Same input → same output.
- Future agentization must sit *above* this layer.
- Determinism is a prerequisite for on-chain state.

---

## ADR-007: Separation of Entropy and Alpha

**Status**: Accepted  
**Context**: Strategic architecture

### Decision

Entropy **never generates alpha**.  
Alpha operates **only within entropy-permitted regimes**.

### Rationale

- Mixing safety and profit corrupts both.
- Alpha must be earned, not assumed.
- Entropy defines *where* intelligence is allowed.

### Alternatives Considered

- Entropy-weighted strategies (rejected: conflation)
- Entropy-driven entries (rejected: misuse)

### Consequences

- Alpha is regime-conditional.
- Reformation Regime becomes the primary alpha zone.
- Safety logic remains strategy-agnostic.

---

## ADR-008: Evolutionary Path (v0.1 → v1.0)

**Status**: Accepted  
**Context**: Roadmap alignment

### Decision

Meridian evolves in strictly ordered layers:

1. Entropy (boundary)
2. Policy (constraint)
3. Alpha (strategy)
4. Agent (planning)
5. On-chain state (governance)

### Rationale

- Premature agency is dangerous.
- Boundaries must precede autonomy.
- Governance must precede learning.

### Consequences

- v0.1 is intentionally weak but safe.
- v0.2 introduces persistence, not intelligence.
- v1.0 integrates agents under constitutional control.

---

## Summary

Meridian’s design decisions are unified by one principle:

> **Intelligence is defined by what it refuses to do under uncertainty.**

These ADRs are binding unless explicitly superseded
by a new, recorded decision.

---
