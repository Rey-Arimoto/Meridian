# PR18 — v0.4 Confidence Logging Charter（Confidence の席を定義する）

**Status:** Scope Lock
**Target:** v0.4
**Dependencies:** PR17/PR17A (Confidence Charter)

---

## Goal

This charter defines **where Confidence exists** as a first-class citizen in Meridian's architecture.

It establishes the **seats** for Confidence across Agent, Reporting, and Validation layers.

**This charter does NOT define:**
- How to compute Confidence
- What scale or representation to use
- How to use Confidence values

**This charter ONLY defines:**
- Which log columns exist
- Which layer writes them
- Which layer reads them
- Which layer validates them

---

## Design Principle: Symmetry with Intent

Confidence follows the exact architectural pattern established by Intent in v0.3:

| First-Class Citizen | Primary Column | Reason Column | Writer | Readers |
|---------------------|----------------|---------------|--------|---------|
| **Intent** (v0.3) | `intent_primary` | `intent_reason` | Agent | Reporting, Validation |
| **Confidence** (v0.4) | `confidence_value` | `confidence_reason` | Agent | Reporting, Validation |

This symmetry ensures:
- Architectural consistency
- Parallel auditability
- Uniform evolution path

---

## Log Schema Extension

### New Columns (v0.4)

Meridian v0.4 extends the log schema with **two new columns**:

#### `confidence_value`
- **Type:** Implementation-defined (string, float, int, enum, etc.)
- **Purpose:** Primary Confidence assessment
- **Written by:** Agent (Layer A)
- **Read by:** Reporting, Validation
- **v0.4 Placeholder:** `None`, `"TBD"`, or any valid placeholder
- **Nullability:** Must be present (not null), but value can be placeholder
- **Example (v0.4):** `None`, `"TBD"`, `0.0`, `"PENDING"`

#### `confidence_reason`
- **Type:** `str`
- **Purpose:** Human-readable explanation for `confidence_value`
- **Written by:** Agent (Layer A)
- **Read by:** Reporting, Validation
- **v0.4 Placeholder:** `"Confidence computation deferred to future PR"` or similar
- **Nullability:** Must be present (not null), must be string
- **Example (v0.4):** `"Confidence not yet implemented"`

### Column Placement

```
[Existing v0.3 columns...]
intent_primary      # v0.3
intent_reason       # v0.3
confidence_value    # v0.4 NEW
confidence_reason   # v0.4 NEW
```

Confidence columns appear **after** Intent columns to maintain v0.3 schema compatibility.

---

## Agent Responsibilities

### The Seat: Agent (Layer A)

The Agent **owns** `confidence_value` and `confidence_reason`.

**Constitutional Obligation:**
- Agent **MUST** write both columns on every tick
- Agent **MUST NOT** write null values
- Agent **MAY** write placeholder values in v0.4

**v0.4 Placeholder Behavior (Permitted):**

Until Confidence computation is implemented, the Agent may write:

```python
confidence_value = None  # or "TBD", or 0.0, or other placeholder
confidence_reason = "Confidence computation deferred to future PR"
```

This is **constitutionally valid** in v0.4 because:
- The seat is reserved (columns exist)
- The obligation is fulfilled (columns written)
- The value is honest (explicitly placeholder)

**Future Evolution (v0.4+):**

When Confidence computation is implemented:
1. Agent computes `confidence_value` from system state
2. Agent derives `confidence_reason` explaining the value
3. Agent writes both to log (no placeholders)

**Agent must never:**
- Skip writing these columns
- Write null/NaN
- Write values without reasons
- Compute Confidence outside Agent layer

---

## Reporting Responsibilities

### The Seat: Reporting (Layer B)

Reporting **reads** `confidence_value` and `confidence_reason`.

**Constitutional Obligation:**
- Reporting **MUST** handle missing columns gracefully (v0.3 compatibility)
- Reporting **MUST** handle placeholder values gracefully (v0.4 transition)
- Reporting **MAY** skip Confidence analysis if values are placeholders

**v0.4 Placeholder Behavior (Permitted):**

When Confidence columns contain placeholders:

```python
if confidence_value is None or confidence_value == "TBD":
    # Skip Confidence distribution analysis
    # Or display: "Confidence: Not yet implemented"
    pass
```

**Expected Reporting Outputs (when implemented):**
- Confidence distribution histogram
- Confidence × Intent cross-tabulation
- Confidence × Regime cross-tabulation
- Confidence timeline visualization

**Reporting must never:**
- Fail if Confidence columns missing (v0.3 logs)
- Fail if Confidence values are placeholders
- Compute or infer Confidence values
- Modify Confidence values

---

## Validation Responsibilities

### The Seat: Validation (Layer C)

Validation **checks** `confidence_value` and `confidence_reason` integrity.

**Constitutional Obligation:**
- Validation **MUST** verify columns exist (v0.4+ logs)
- Validation **MUST** verify columns are non-null
- Validation **MUST** verify `confidence_reason` is string
- Validation **MAY** allow placeholder values in v0.4

**v0.4 Placeholder Behavior (Permitted):**

Validation accepts placeholders as valid:

```python
# Valid in v0.4
confidence_value = None  # OK
confidence_value = "TBD"  # OK
confidence_value = 0.0  # OK

# Invalid (always)
confidence_value = <null/NaN>  # FAIL
confidence_reason = None  # FAIL
confidence_reason = 123  # FAIL (not string)
```

**Expected Validation Checks (when implemented):**
- `confidence_value` type check (once type is defined)
- `confidence_value` range check (once range is defined)
- `confidence_reason` non-empty check
- Confidence × Intent consistency check (heuristic warnings)

**Validation must never:**
- Block pipeline on placeholder values (v0.4)
- Fail on missing columns for v0.3 logs
- Compute or infer Confidence values
- Override Agent-written Confidence values

---

## v0.4 Transition Strategy

### Phase 1: Reserve the Seat (PR18)
- Add `confidence_value` and `confidence_reason` columns to schema
- Agent writes placeholders (`None`, `"Not yet implemented"`)
- Reporting skips Confidence analysis
- Validation accepts placeholders

**Goal:** Establish architectural presence without implementation burden

### Phase 2: Implement Computation (PR19+)
- Agent computes real `confidence_value` from system state
- Agent derives real `confidence_reason` explaining computation
- Reporting analyzes Confidence distribution
- Validation checks Confidence integrity

**Goal:** Replace placeholders with real Confidence assessment

---

## Schema Compatibility

### v0.3 Logs (No Confidence Columns)
- Reporting: Skip Confidence analysis
- Validation: Accept missing columns
- Pipeline: Continue processing

### v0.4 Logs (Confidence Placeholders)
- Reporting: Skip Confidence analysis (detect placeholders)
- Validation: Accept placeholder values
- Pipeline: Continue processing

### v0.4+ Logs (Real Confidence Values)
- Reporting: Analyze Confidence distribution
- Validation: Check Confidence integrity
- Pipeline: Full Confidence-aware operation

**Backward Compatibility Guarantee:**
v0.4 pipeline must process v0.3 logs without Confidence columns.

---

## Non-Goals (Explicitly Deferred)

**This charter does NOT define:**

### ❌ Confidence Computation
- Calculation formula
- Input features
- Aggregation logic
- Confidence scale or type

### ❌ Confidence Usage
- How to modulate action size
- How to influence decisions
- How to set boundaries

### ❌ Confidence Thresholds
- High/low Confidence definitions
- Boundary values
- Confidence-based rules

**Why defer?**

PR18 establishes **architectural seats**, not implementation.

Computation, usage, and boundaries will be defined in future PRs (PR19+) after careful design.

---

## Constitutional Constraints

### Determinism (Preserved)
- Confidence computation (when implemented) must be deterministic
- Same system state → same Confidence value
- No randomness, no network calls, no hidden state

### Auditability (Preserved)
- Every Confidence value must have a reason
- Confidence derivation must be logged
- Confidence must be reproducible from logs

### Fail-Closed (Preserved)
- Missing Confidence → safe default (placeholder or skip)
- Invalid Confidence → validation failure (when implemented)
- Confidence never silently ignored

### Intent Supremacy (New)
- Confidence modulates execution, never overrides Intent
- Intent selection occurs before Confidence assessment
- Confidence cannot change Intent value

---

## Done Criteria

PR18 Confidence Logging Charter is complete when:

1. **Columns Defined:** `confidence_value` and `confidence_reason` specified
2. **Seats Assigned:** Agent writes, Reporting reads, Validation checks
3. **Placeholder Strategy:** v0.4 placeholder behavior documented
4. **Compatibility Strategy:** v0.3/v0.4/v0.4+ compatibility defined
5. **Symmetry with Intent:** Confidence follows Intent architectural pattern
6. **Non-Goals Explicit:** Computation/usage/thresholds deferred to future PRs

**This charter does NOT require implementation.**

Implementation will occur in PR19+ following this architectural blueprint.

---

## Why This Charter?

### Without Logging Charter:
- Confidence computation and logging mixed together
- No clear boundary between "where it exists" and "how it's computed"
- Implementation PRs forced to decide architecture + computation simultaneously
- Risk of architectural inconsistency

### With Logging Charter:
- **PR18:** Establish seats (columns, responsibilities, placeholders)
- **PR19+:** Implement computation (fill the seats with real values)
- Clean separation of concerns
- Parallel evolution with Intent architecture
- v0.3 compatibility preserved throughout

**The seat must exist before we decide what sits in it.**

---

**Meridian v0.4: First-Class Citizens Need First-Class Seats**
