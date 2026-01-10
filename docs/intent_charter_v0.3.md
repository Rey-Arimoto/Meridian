# PR14 — v0.3 Intent Charter（Intent を第一級市民にする）

**Status:** Scope Lock
**Target:** v0.3
**Dependencies:** v0.2-final (PR0-PR13B)

---

## Goal

Meridian v0.3 introduces **Intent** as a first-class citizen in the decision-making architecture.

Intent represents **what the system wants to achieve** in the current market state, independent of how it will be executed.

This separation enables:
- Clearer reasoning about system behavior
- Explicit priority ordering of competing goals
- Deterministic Intent → Action mapping
- Constitutional constraints enforced at Intent level

---

## Intent Types (Fixed Set)

Meridian v0.3 defines **6 canonical Intents**:

| Intent | Description | When Active |
|--------|-------------|-------------|
| **SEEK** | Actively search for new opportunities | Stable regime, low entropy, no existing exposure |
| **HARVEST** | Extract value from existing positions | Emerging trend, favorable conditions, existing exposure |
| **DEFEND** | Protect existing capital from adverse moves | Volatility rising, trend weakening, exposure at risk |
| **STABILIZE** | Reduce exposure during regime transitions | Regime change detected, entropy crossing thresholds |
| **PAUSE** | Constitutional freeze, no new action permitted | Critical entropy, emergency conditions, overlay suppression |
| **IDLE** | No intent, maintain current state | Default fallback, no clear signal |

**Key Properties:**
- Fixed set (no dynamic Intent creation)
- Mutually exclusive (exactly one Intent active per tick)
- Deterministic selection based on observable state
- Priority-ordered (see below)

---

## Intent Priority Hierarchy (Fixed Order)

When multiple Intents could apply, selection follows strict priority:

```
1. PAUSE       — Constitutional supremacy (overlay, emergency, freeze)
2. STABILIZE   — Regime transition / stabilization required
3. DEFEND      — Capital protection (exposure at risk)
4. HARVEST     — Value extraction (favorable conditions + exposure)
5. SEEK        — Opportunity search (stable + no exposure)
6. IDLE        — Default fallback (no clear signal)
```

**Rationale:**
- Safety (PAUSE/STABILIZE) > Capital Protection (DEFEND) > Value Extraction (HARVEST) > Exploration (SEEK)
- Constitutional constraints dominate all other considerations
- Fail-closed: IDLE when no Intent matches

---

## Intent Primary Architecture

v0.3 implements **Intent-primary decision flow**:

```
Market State → Intent Selection → Action Derivation → Overlay → Final Action
```

**Intent Selection (Layer A):**
- Input: Entropy, Regime, Current Weight, Market State
- Output: Single canonical Intent
- Logic: Deterministic priority-based selection
- Location: `IntentClassifier` (new)

**Action Derivation (Layer B):**
- Input: Intent + Current State
- Output: Base Action (target weight, direction)
- Logic: Intent → Action mapping
- Location: `IntentActionMapper` (new)

**Overlay (Layer C):**
- Input: Base Action
- Output: Final Action (after safety constraints)
- Logic: Existing SafetyOverlay (unchanged)

---

## Migration Path: Computation Location (B→A)

v0.3 development follows a **safe migration path** for moving computation from Layer B to Layer A:

### Phase 1: PR15B / PR16B (Layer B - Action Level)
- Implement Intent selection logic **inside Action derivation**
- Intent computed as intermediate step before Action
- Validates Intent semantics while preserving v0.2 structure
- **Goal:** Prove Intent logic is correct and stable

### Phase 2: PR15A / PR16A (Layer A - Intent Level)
- Move Intent selection **before Action derivation**
- Intent becomes primary decision output
- Action derived from Intent (not Regime)
- **Goal:** Complete Intent-primary architecture

**Why B→A (not A directly)?**
- Risk reduction: Validate Intent logic before restructuring
- Incremental validation: Each PR independently testable
- Rollback safety: B-level implementation can be reverted without breaking v0.2 foundations

---

## Constraints

**Constitutional Constraints (Preserved from v0.2):**
- Regime hysteresis remains unchanged
- Safety overlay fail-closed guarantees remain
- Emergency freeze supremacy remains
- No action in REGIME_TRANSITION (mapped to PAUSE Intent)

**Determinism (Preserved from v0.2):**
- Intent selection is deterministic (same inputs → same Intent)
- No randomness, no learning, no hidden state
- Tick-based execution (no real-time dependencies)
- Auditable: Every Intent logged with reason

**Scope Boundaries (v0.3):**
- READ-ONLY for v0.2 components (no breaking changes to core/overlay)
- Intent logic implemented as new modules (IntentClassifier, IntentActionMapper)
- v0.2 validations continue to pass (PR4A-PR13B)
- No changes to CSV schema (Intent logged as additional column)

---

## Non-Goals (Deferred)

**Not in v0.3:**
- Dynamic Intent creation or modification
- Intent → Intent transitions (Intent history)
- Multi-Intent composition or blending
- Intent-level optimization or learning
- Real-time Intent adaptation

**Rationale:** v0.3 focuses on **architectural foundation**. Advanced Intent mechanics deferred to v0.4+.

---

## Implementation Sequence (Tentative)

1. **PR15B:** Intent Classification Logic (Layer B)
   - Implement `IntentClassifier` (deterministic selection)
   - Call from within Action derivation (v0.2 structure preserved)
   - Log Intent alongside existing decision fields
   - Validate: Intent semantics correct, all tests pass

2. **PR16B:** Intent → Action Mapping (Layer B)
   - Implement `IntentActionMapper` (Intent → target weight/direction)
   - Replace direct Regime → Action logic with Intent → Action
   - Validate: Same Actions produced, Intent mapping correct

3. **PR15A:** Elevate Intent to Primary (Layer A)
   - Move Intent selection before Action derivation
   - Refactor decision flow: State → Intent → Action
   - Validate: Intent-primary flow correct, v0.2 validations pass

4. **PR16A:** Intent-Action Contract (Layer A)
   - Formalize Intent → Action contract (invariants, tests)
   - Intent-based reporting and visualization
   - Validate: Intent auditable, Intent distribution analysis

**Note:** Sequence may adjust based on implementation findings. Core principle: **B→A migration with validation at each step**.

---

## Done Criteria

v0.3 Intent Charter is complete when:

1. **6 Intents Defined:** SEEK / HARVEST / DEFEND / STABILIZE / PAUSE / IDLE
2. **Priority Hierarchy Enforced:** Deterministic Intent selection based on fixed priority
3. **Intent Primary Architecture:** Intent selected before Action derivation (Layer A)
4. **Migration Complete:** Computation moved from Layer B to Layer A safely
5. **Deterministic & Auditable:** Every Intent logged with reason, reproducible
6. **v0.2 Validations Pass:** All PR4A-PR13B validations continue to pass
7. **Intent Logged:** CSV includes Intent column, pipeline processes Intent distribution

---

## Why Intent?

**Intent separates "what" from "how":**
- **What** the system wants to achieve (Intent) is conceptually simpler than **how** to achieve it (Action)
- Intent provides a **human-interpretable** layer above Actions
- Intent enables **constitutional reasoning** at a higher level of abstraction

**Intent as first-class citizen:**
- Regime answers: "What is the market state?"
- Intent answers: "What do we want to do about it?"
- Action answers: "How do we execute that Intent?"

This separation makes the system **more explainable, more auditable, and more constitutional**.

---

**Meridian v0.3: Intelligence through Intent**
