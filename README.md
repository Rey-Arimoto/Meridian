# Meridian
Deterministic, entropy-driven stateful intelligence for survivable trading and on-chain auditability.

Meridian is not a “smart trading bot.”  
It is a system designed to **know when action is no longer meaningful**.

---

## Constitution Summary

1. Meridian acts only when the environment is interpretable; high entropy forbids action.
2. Non-action (NoOp) is a deliberate, first-class decision and is always recorded.
3. All state transitions are deterministic and reproducible.
4. Execution is a privilege gated by strict guards, never an entitlement.
5. When meaning collapses, Meridian freezes rather than degrades.

---

## Overview

Meridian is a deterministic, stateful execution system driven by **entropy**, not prediction.

Most automated systems fail by continuing to act after market structure collapses.
Meridian is designed around the opposite principle:

> **Survival and interpretability precede profit.**

The system explicitly models when signals lose semantic meaning and
treats *non-action* as an intelligent outcome.

---

## Core Ideas

### Entropy as the Primary Signal
Meridian does not optimize for returns.
It measures whether **structure exists at all**.

Entropy is used to detect:
- loss of directional meaning
- regime collapse
- environments where decisions become indistinguishable from noise

When entropy exceeds a constitutional threshold, Meridian freezes completely.

### NoOp Is Intelligence
Choosing not to act is not a fallback.
It is a recorded, auditable decision with a reason.

### Determinism First
Given the same inputs:
- prices
- entropy
- deviation
- volatility

Meridian will always produce the same state transition.

This property is non-negotiable.

---

## Architecture (v0.1–v0.2)

### Off-chain (Executor)
- Price observation
- Indicator computation (entropy, deviation, volatility)
- Deterministic state transition (`transition_offchain`)
- Execution gating (NoOp / Freeze / Execute)
- Full decision logging

### On-chain (starting v0.2)
- MeridianState object
  - phase
  - intent
  - last transition
- Entropy anchoring (hash / value)
- Freeze reason verifiability

Execution keys are **never** stored on-chain or in Python.
They live only in the TS Gateway `.env`.

---

## Phases & Intent (Conceptual)

- **Phase (P0–P5)**: What posture the system is in  
  (Stop, Withdraw, Observe, Probe, Strike, Harvest)

- **Intent (I1–I4)**: How aggressively it is allowed to act  
  (Defensive → Emergency → Cautious → Normal)

Execution is allowed only when **both phase and intent permit it**.

---

## Freeze Conditions (Critical)

Meridian will **always stop** when:

- Composite entropy ≥ CRITICAL_ENTROPY
- Sign entropy indicates semantic collapse
- Safety invariants are violated (slippage, loss, execution errors)

Freeze is:
- explicit
- logged
- reproducible
- expected

A system that never stops is considered broken.

---

## Usage (v0.1)

1. Run the executor with price feed enabled
2. Observe:
   - entropy
   - phase
   - intent
   - target weight
3. Verify that:
   - NoOp decisions are logged
   - Freeze conditions are triggered deterministically

Meridian v0.1 is about **observability**, not profit.

---

## Roadmap

- **v0.1**: Observable, deterministic execution (current)
- **v0.2**: Sui Object–based state persistence
- **v0.5**: Agent-style Plan/Act loop (suggestion-only)
- **v1.0**: Multi-market, multi-strategy unified intelligence

At no point will execution authority bypass entropy-based guards.

---

## Philosophy

Meridian does not attempt to be intelligent everywhere.

It attempts to know **where intelligence ends**.

---

## License

MIT License

## Core Documents

- **Vision**  
  Conceptual foundation and philosophy of Meridian  
  → [`docs/vision.md`](docs/vision.md)

- **Entropy Specification**  
  Formal definition of entropy as the system’s highest authority  
  → [`docs/entropy_spec.md`](docs/entropy_spec.md)
