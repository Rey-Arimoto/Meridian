# PR18 — v0.4 Confidence Logging Charter（Confidence の席を定義する）

**Status:** Scope Lock
**Target:** v0.4
**Dependencies:** PR17/PR17A (Confidence Charter)

---

## Goal

This charter defines **where Confidence exists** as a first-class citizen in Meridian's architecture.

It establishes the **seats** for Confidence across Agent, Reporting, and Validation layers.

**This charter does NOT define:**
- How Confidence is defined
- What representation to use
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
- **Purpose:** Primary Confidence assessment
- **Written by:** Agent (Layer A)
- **Read by:** Reporting, Validation
- **v0.4 Status:** In v0.4, this field may be left intentionally undefined

#### `confidence_reason`
- **Purpose:** Human-readable explanation for `confidence_value`
- **Written by:** Agent (Layer A)
- **Read by:** Reporting, Validation
- **v0.4 Status:** In v0.4, this field may be left intentionally undefined

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

**Architectural Role:**
- Agent writes both fields to the log
- When Confidence implementation exists, Agent writes derived values
- When Confidence implementation does not yet exist, Agent may leave fields undefined

**Seat Ownership:**
- Only Agent writes these fields
- Other layers read but never write Confidence values

---

## Reporting Responsibilities

### The Seat: Reporting (Layer B)

Reporting **reads** `confidence_value` and `confidence_reason`.

**Architectural Role:**
- When present, Reporting reads these fields for analysis
- When absent, Reporting continues without Confidence analysis
- When undefined, Reporting treats fields as optional

**Seat Access:**
- Reporting reads but never writes Confidence values
- Reporting never derives or infers Confidence values
- Missing fields should not break report generation

---

## Validation Responsibilities

### The Seat: Validation (Layer C)

Validation **checks** `confidence_value` and `confidence_reason` integrity.

**Architectural Role:**
- When present, Validation checks field integrity
- When absent, Validation continues without Confidence checks
- When undefined, Validation treats fields as optional

**Seat Access:**
- Validation reads but never writes Confidence values
- Validation never derives or infers Confidence values
- Missing fields should not break validation pipeline

---

## v0.4 Transition Strategy

### Phase 1: Reserve the Seat (PR18)
- Add `confidence_value` and `confidence_reason` columns to schema
- Agent may leave fields undefined in v0.4
- Reporting continues without Confidence analysis when fields undefined
- Validation continues without Confidence checks when fields undefined

**Goal:** Establish architectural presence without implementation burden

### Phase 2: Implement Values (PR19+)
- Agent writes derived `confidence_value` from system state
- Agent writes derived `confidence_reason` explaining value
- Reporting analyzes Confidence distribution
- Validation checks Confidence integrity

**Goal:** Fill architectural seats with real Confidence values

---

## Schema Compatibility

### v0.3 Logs (No Confidence Columns)
- Reporting: Skip Confidence analysis
- Validation: Skip Confidence checks
- Pipeline: Continue processing

### v0.4 Logs (Confidence Undefined)
- Reporting: Skip Confidence analysis when fields undefined
- Validation: Skip Confidence checks when fields undefined
- Pipeline: Continue processing

### v0.4+ Logs (Confidence Defined)
- Reporting: Analyze Confidence distribution
- Validation: Check Confidence integrity
- Pipeline: Full Confidence-aware operation

**Backward Compatibility Guarantee:**
v0.4 pipeline processes v0.3 logs without Confidence columns.

---

## Non-Goals (Explicitly Deferred)

**This charter does NOT define:**

- How Confidence values are derived
- What Confidence values represent
- How Confidence values are used
- Any boundaries, rules, or constraints on Confidence values

**Why defer?**

PR18 establishes **architectural seats**, not implementation.

Value derivation, representation, and usage will be defined in future PRs (PR19+).

---

## Constitutional Constraints

### Determinism (Preserved)
- Confidence derivation (when implemented) remains deterministic
- Same system state → same Confidence value
- No randomness, no network calls, no hidden state

### Auditability (Preserved)
- Confidence values accompanied by reasons when present
- Confidence derivation logged when present
- Confidence reproducible from logs when present

### Fail-Closed (Preserved)
- Missing Confidence → continue processing
- Undefined Confidence → continue processing
- Confidence never required for pipeline execution

### Intent Supremacy (New)
- Confidence modulates execution, never overrides Intent
- Intent selection occurs before Confidence assessment
- Confidence cannot change Intent value

---

## Done Criteria

PR18 Confidence Logging Charter is complete when:

1. **Columns Defined:** `confidence_value` and `confidence_reason` specified
2. **Seats Assigned:** Agent writes, Reporting reads, Validation checks
3. **Transition Strategy:** v0.4 undefined behavior documented
4. **Compatibility Strategy:** v0.3/v0.4/v0.4+ compatibility defined
5. **Symmetry with Intent:** Confidence follows Intent architectural pattern
6. **Non-Goals Explicit:** Derivation/usage/representation deferred to future PRs

**This charter does NOT require implementation.**

Implementation will occur in PR19+ following this architectural blueprint.

---

## Why This Charter?

### Without Logging Charter:
- Confidence computation and logging mixed together
- No clear boundary between "where it exists" and "how it is defined"
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
