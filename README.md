# Meridian

**Intelligence Against Entropy**

Meridian is an entropy-native intelligence layer for markets.  
It exists to preserve, grow, and protect capital when markets become unexplainable.

---

## What is Meridian?

Meridian is **not a trading bot** and **not a price prediction system**.

It is a system that continuously measures **market entropy** —  
how explainable the current market state is relative to existing rules, assumptions, and strategies —  
and decides **whether action itself is justified**.

When explanation collapses, Meridian does not attempt to trade.
It refuses to act.

This refusal is not passive.
It is enforced intelligence.

---

## Alpha: Intelligence Against Entropy

Meridian does not seek alpha by predicting prices better.

It extracts alpha by **measuring entropy** and **aligning action with market explainability**.

Markets are classified into **Entropy Regimes**:

- **Stable Regime** — low entropy, assumptions hold
- **Unstable Regime** — entropy rising, assumptions weakening
- **Chaotic Regime** — high entropy, behavior unexplainable
- **Reformation Regime** — entropy declining, new order forming

All strategies are subordinated to the current Entropy Regime.

### The NoOp Premium

Meridian’s most distinctive alpha source is **NoOp**.

In Chaotic Regimes:
- signals lose meaning,
- correlations spike,
- forced action destroys capital.

Meridian treats **not acting** as a first-class strategic action, enforced by constitutional rules.

Avoiding catastrophic loss during chaos — and re-entering early during reformation —  
creates a compounding advantage others cannot replicate.

👉 For a detailed explanation, see [docs/alpha.md](docs/alpha.md).

---

## Why Entropy?

Traditional systems assume markets are always interpretable.

Meridian rejects this assumption.

Entropy answers a different question:

> *Is the market still explainable by what we think we know?*

When the answer is no, prediction is meaningless.
Meridian stops.

Entropy in Meridian is a **state variable**, not a signal.

👉 See [docs/entropy_spec.md](docs/entropy_spec.md).

---

## Architecture (v0.1)

Meridian v0.1 is intentionally simple and conservative.

- Composite entropy calculation (volatility + structural dispersion)
- Entropy expressed in **basis points (bp)**
- Constitutional freeze above critical entropy
- Explicit NoOp / Freeze behavior
- Deterministic, explainable decisions
- Full CSV logging (every decision is auditable)

There is no learning, no optimization, and no hidden behavior.

Stability precedes intelligence.

---

## Development Roadmap

**Phase 1 — v0.1: Entropy Constitutional Core**
- Entropy measurement
- Freeze enforcement
- Deterministic paper trading
- Immutable decision logs

**Phase 2 — v0.2: State Objectization (Sui)**
- On-chain MeridianState
- Entropy Regime as persistent state
- Deterministic state transitions

**Phase 3 — v0.5–0.8: Agent Core (Constrained)**
- Plan / Act separation
- Suggestions without execution authority
- Hard constitutional guards remain dominant

**Phase 4 — v1.0: Integrated Intelligence**
- Multi-market, multi-strategy
- Regime-driven strategy selection
- Self-diagnosis and automatic contraction

---

## Design Principles (Constitution)

- **Regime overrides strategy**
- **NoOp is a valid action**
- **High entropy forces non-action**
- **Determinism before learning**
- **Survival before profit**

These rules are non-negotiable.

---

## Documentation

- Alpha model: [docs/alpha.md](docs/alpha.md)
- Entropy specification: [docs/entropy_spec.md](docs/entropy_spec.md)
- Design decisions (ADR): [docs/decisions.md](docs/decisions.md)
- Vision: [docs/vision.md](docs/vision.md)

---

## Why Now

Markets are becoming:
- faster,
- more composable,
- more reflexive,
- more chaotic.

On-chain systems amplify entropy instead of absorbing it.

In such an environment, **entropy-aware intelligence is no longer optional infrastructure**.

---

## Why It Is Hard to Copy

- Entropy is not a price signal
- NoOp must be enforced against incentives
- Regime must dominate strategy
- Constitutional freezes cannot be overridden
- Loss avoidance is culturally undervalued but mathematically dominant

---

## Validation (v0.2)

Meridian v0.2 includes constitutional compliance validation scripts that verify:
- Hysteresis stability (regime transitions don't oscillate)
- Matrix invariants (Act forbidden in volatile/transition regimes)
- Policy decision integrity (regime-first enforcement)
- Log schema compliance (decision audit trail)

Run validations:
```bash
cd ~/Meridian
source .venv/bin/activate
python3 python/validation/pr4a_hysteresis_stability.py
python3 python/validation/pr4a_matrix_invariants.py
python3 python/validation/pr4a_policy_decision_invariants.py
python3 python/validation/pr4a_log_schema_smoke.py
```

All scripts exit 0 on PASS, 1 on FAIL.

---

## Canonical Report Generation (PR8B + PR9A)

The following command is the **canonical and supported way** to generate all Meridian reports from an execution log.

It enforces data integrity gates and produces all reporting artifacts in a single run.

**Execution Command:**

```bash
cd ~/Meridian && source .venv/bin/activate && \
python3 python/tools/pr8b_integrity_gate_runner.py meridian_log.csv \
  --prefix meridian \
  --out-dir artifacts
```

**Generated Artifacts**

If the integrity gate passes, the following files will be generated in the `artifacts` directory:

- `meridian_health.md` — Data health and integrity report (PR8A)
- `meridian_investor_report.md` — Investor-facing summary (PR7A)
- `meridian_performance.md` — Performance and risk summary (PR9A)
- `meridian_dashboard.html` — Interactive dashboard (PR7C)
- `meridian_timeline.png` — Timeline visualization (PR7B)
- `meridian_overlay_hist.png` — Overlay distribution (PR7B)
- `meridian_regime_dist.png` — Regime distribution (PR7B)

**Notes**

- Reports are generated only if all integrity checks pass.
- No assumptions are made about tick frequency, capital scaling, or annualization.
- This command is read-only and does not modify logs or trading logic.

---

## Status

Meridian is under active development.
v0.2 implements constitutional regime-first decision making with full compliance validation.

Meridian optimizes for **survival first**, because only surviving systems get to compound.

---

**Meridian**  
*Intelligence Against Entropy.*
