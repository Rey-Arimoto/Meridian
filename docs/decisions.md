# Architecture Decision Records (ADR)

This document records the **irreversible design decisions** of Meridian.

Each ADR exists to answer one question:
> *“Why is the system this way, and what failure does it avoid?”*

These decisions are treated as **constitutional** unless explicitly superseded
by a new ADR.

---

## ADR-001: Determinism Over Adaptivity

**Status:** Accepted  
**Decision:**  
Meridian prioritizes deterministic state transitions over adaptive or learned behavior.

**Rationale:**  
A system that changes its decision logic in response to outcomes
cannot be reliably audited or replayed.
Determinism ensures that identical inputs always produce identical outputs.

**Consequences:**  
- Pros: auditability, reproducibility, resistance to hindsight bias  
- Cons: slower adaptation, no automatic optimization  

This trade-off is intentional.

---

## ADR-002: Entropy as the Primary Authority

**Status:** Accepted  
**Decision:**  
Entropy is the highest-order signal governing whether action is allowed.

**Rationale:**  
Most failures occur not because systems choose the wrong action,
but because they continue acting after meaning collapses.
Entropy measures the loss of interpretability itself.

**Consequences:**  
- All other signals are subordinate to entropy  
- High entropy invalidates action entirely  

---

## ADR-003: Hard CRITICAL_ENTROPY Threshold

**Status:** Accepted  
**Decision:**  
Meridian enforces a hard, non-adaptive CRITICAL_ENTROPY threshold.

**Rationale:**  
Soft degradation encourages rationalization.
A hard threshold produces a binary, inspectable freeze event.

**Consequences:**  
- Missed opportunities are acceptable  
- Late freezes are not  

Changing this threshold requires a new ADR.

---

## ADR-004: NoOp as First-Class Decision

**Status:** Accepted  
**Decision:**  
Non-action (NoOp) is treated as an explicit, logged decision.

**Rationale:**  
In high-uncertainty environments, restraint is intelligence.
Failing to record NoOp obscures system intent.

**Consequences:**  
- Every tick produces a decision  
- “Doing nothing” always has a reason  

---

## ADR-005: Separation of State and Execution

**Status:** Accepted  
**Decision:**  
Meridian separates state representation from execution authority.

**Rationale:**  
Combining state and execution creates opaque coupling and hidden mutation.
Separating them enables verification without granting power.

**Consequences:**  
- On-chain state is declarative  
- Off-chain execution is revocable  

---

## ADR-006: Phases as Posture, Not Strategy

**Status:** Accepted  
**Decision:**  
Meridian models behavior through phases (posture) rather than strategies.

**Rationale:**  
Strategies imply beliefs about outcomes.
Phases describe allowed behavior under uncertainty.

**Consequences:**  
- Phases constrain execution, not prediction  
- Strategy can change without redefining phase  

---

## ADR-007: Guardrails Above Intelligence

**Status:** Accepted  
**Decision:**  
Risk and safety guardrails cannot be overridden by intelligence components.

**Rationale:**  
Any intelligence that violates its own survival constraints is invalid.

**Consequences:**  
- Guards are constitutional  
- Optimization never weakens constraints  

---

## ADR-008: Freeze as a Normal State

**Status:** Accepted  
**Decision:**  
System freeze is treated as a valid, expected operational state.

**Rationale:**  
A system that never stops is brittle.
Freeze preserves capital, coherence, and future optionality.

**Consequences:**  
- Freeze events are logged and analyzed  
- Recovery requires explicit conditions  

---

## ADR-009: No Learning at the Core (v0.x)

**Status:** Accepted  
**Decision:**  
Learning or LLM components are excluded from core state transition logic in v0.x.

**Rationale:**  
Learning obscures causality and breaks determinism.
Meridian must first be fully inspectable.

**Consequences:**  
- Learning may suggest, but not decide  
- Core transitions remain rule-based  

---

## ADR-010: Basis-Point Comparison Only

**Status:** Accepted  
**Decision:**  
All thresholds are compared using integer basis points, not floats.

**Rationale:**  
Floating-point comparison introduces ambiguity near boundaries.
Integer comparison guarantees deterministic behavior.

**Consequences:**  
- Threshold behavior is explicit  
- Boundary conditions are reproducible  

---

## Amendment Process

Any change to these decisions requires:
1. A new ADR
2. Explicit statement of what failure is now accepted
3. Acceptance that previous guarantees may no longer hold

Silently changing behavior is considered a system failure.

---

## Closing Note

Meridian’s decisions are not optimized for profit.

They are optimized for **coherence, survival, and explainability**.

Anything that compromises these values is considered out of scope.
