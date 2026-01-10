# Confidence Reason Vocabulary Charter (v0.4)

**Status**: Frozen (PR30)
**Dependency**: PR27 (Reason Structure Charter), PR29B (Reason Vocabulary Sanitization)
**Type**: Design Specification

---

## Purpose

This charter defines the **allowed vocabulary** for `confidence_reason` generation.

PR29B removed numeric expressions from `confidence_reason`.
PR30 **freezes the vocabulary** to prevent future drift.

This ensures:
- **Logs** remain consistent
- **UI** displays human-readable text
- **Translation/summarization** tools have stable input
- **Audit trails** maintain repeatability

---

## Vocabulary Specification

### 1. Structure (PR27)

```
Source:<text>; Stability:<text>; Consistency:<text>; Completeness:<text>
```

Each section has **fixed vocabulary** defined below.

---

### 2. Stability Vocabulary (Fixed)

**Allowed values:**
- `temporal indicators present`
- `temporal indicators absent`

**Meaning:**
- `present`: Observation contains keys starting with `recent_`
- `absent`: No temporal (recent) observations

**Prohibited:**
- Numeric counts
- Evaluative terms (good/bad/sufficient/insufficient)
- Comparative terms (more/less/better/worse)

---

### 3. Consistency Vocabulary (Fixed)

**Allowed values:**
- `all core signals present`
- `some core signals present`
- `no core signals present`

**Meaning:**
- Core signals: `intent_primary`, `regime`, `base_action`, `overlay_rule`
- `all`: All 4 core signals exist in observation
- `some`: 1-3 core signals exist in observation
- `no`: 0 core signals exist in observation

**Prohibited:**
- Numeric fractions (e.g., "3/4")
- Counts (e.g., "3 signals")
- Evaluative terms (complete/incomplete/sufficient/insufficient)
- Comparative terms (more/fewer/better/worse)

---

### 4. Completeness Vocabulary (Fixed)

**Allowed values:**
- `temporal and current observations`
- `current observations only`
- `no observations`

**Meaning:**
- `temporal and current`: Observation contains both recent_* and current keys
- `current only`: Observation contains only current keys (no recent_*)
- `no observations`: Observation is empty

**Prohibited:**
- Numeric field counts (e.g., "7 fields")
- Evaluative terms (complete/incomplete/sufficient/insufficient)
- Comparative terms (more/fewer/better/worse)

---

### 5. Source Vocabulary (Fixed Rule)

**Allowed format:**
- Comma-separated list of observation key names
- Alphabetical order (repeatable)
- Separator: `, ` (comma + space)

**Example:**
```
Source:base_action, entropy_bp, intent_primary, overlay_rule, regime
```

**Rules:**
- List observation keys as-is (no summarization)
- No evaluative terms
- No counts or aggregations
- If observation is empty, return empty string (PR21)

**Prohibited:**
- Key summarization (e.g., "5 observations")
- Evaluative terms (comprehensive/sparse/rich/limited)
- Abbreviations or renaming

---

## Required Properties

`confidence_reason` must satisfy:

1. **Human-readable**: Natural language, not machine codes
2. **Auditable**: Reproducible from observation keys alone
3. **Repeatable**: Same observation → same reason
4. **Non-numeric**: No digits (0-9), fractions, counts, percentages
5. **Non-evaluative**: No good/bad, high/low, strong/weak, sufficient/insufficient
6. **Optional**: Empty string allowed (PR21 absence semantics)

---

## Prohibited Vocabulary (Hard Ban)

The following terms are **prohibited** in `confidence_reason` generation:

### Numeric/Quantitative
- Any ASCII digits: `0-9`
- Fractions: `1/4`, `3/4`, `N/M`
- Counts: `N fields`, `N signals`, `N observations`
- Percentages: `%`, `percent`
- Ranges: `0-1`, `0–1`

### Evaluative/Comparative
- Good/bad: `good`, `bad`, `excellent`, `poor`
- High/low: `high`, `low`, `higher`, `lower`
- Strong/weak: `strong`, `weak`, `stronger`, `weaker`
- Sufficient/insufficient: `sufficient`, `insufficient`, `enough`, `lacking`
- Reliable/unreliable: `reliable`, `unreliable`, `trustworthy`, `questionable`
- Complete/incomplete: `complete`, `incomplete`, `partial` (exception: `partial` not used)
- Rich/sparse: `rich`, `sparse`, `abundant`, `scarce`

### Mathematical/Statistical
- `compute`, `calculate`, `derive`, `derived`, `derivation`
- `formula`, `equation`, `function`
- `scale`, `normalize`, `standardize`
- `threshold`, `boundary`, `limit`
- `weight`, `weighted`, `weighting`
- `score`, `scoring`, `rating`
- `level`, `tier`, `rank`, `grade`
- `probability`, `likelihood`, `chance`
- `confidence level`, `certainty`, `uncertainty`

### Placeholder/Undefined
- `TBD`, `TODO`, `placeholder`
- `None`, `null`, `N/A` (exception: implementation uses empty string)
- `0.0`, `undefined` (use empty string instead)
- `not yet implemented`

---

## Implementation Mapping

PR29B implementation follows this charter:

| Section | Condition | Vocabulary Output |
|---------|-----------|-------------------|
| **Stability** | Has recent_* keys | `temporal indicators present` |
| | No recent_* keys | `temporal indicators absent` |
| **Consistency** | All 4 core signals | `all core signals present` |
| | 1-3 core signals | `some core signals present` |
| | 0 core signals | `no core signals present` |
| **Completeness** | Has recent_* and current | `temporal and current observations` |
| | Only current (no recent_*) | `current observations only` |
| | Empty observation | `no observations` |
| **Source** | Keys exist | Alphabetical, comma-separated list |
| | Empty observation | Empty string (PR21) |

---

## Examples

### Example 1: Full Observation
```
Observation: {
  intent_primary: "SEEK",
  regime: "emerging_trend",
  base_action: "SHIFT",
  overlay_rule: "ALLOW",
  entropy_bp: 3200,
  recent_intent_primary: "IDLE",
  recent_regime: "stable_range"
}

confidence_reason:
Source:base_action, entropy_bp, intent_primary, overlay_rule, recent_intent_primary, recent_regime, regime; Stability:temporal indicators present; Consistency:all core signals present; Completeness:temporal and current observations
```

### Example 2: Partial Observation
```
Observation: {
  intent_primary: "IDLE",
  regime: "stable_range",
  entropy_bp: 2000
}

confidence_reason:
Source:entropy_bp, intent_primary, regime; Stability:temporal indicators absent; Consistency:some core signals present; Completeness:current observations only
```

### Example 3: Empty Observation (PR21)
```
Observation: {}

confidence_reason: ""
```

---

## Enforcement

### Design Time
- This charter is frozen (PR30)
- Any future changes require new PR with explicit vocabulary migration plan

### Implementation Time
- PR29B implementation already complies
- Future PRs must not introduce prohibited vocabulary
- Test suite verifies no digits in output (PR29B Test 6)

### Review Time
- Code review must verify vocabulary compliance
- Charter violations are blocking issues

---

## Relationship to Other Charters

| Charter | Relationship |
|---------|--------------|
| **PR20: Representation** | confidence_reason is string type (not enum) |
| **PR21: Absence Semantics** | Empty string is valid confidence_reason |
| **PR25: Source Declaration** | Defines which observations may be used |
| **PR27: Reason Structure** | Defines 4-section structure (this charter fixes vocabulary within sections) |

---

## Non-Goals

This charter does NOT define:
- Observation key naming conventions (separate concern)
- confidence_value generation (separate PR)
- Semantic meaning of reasons (future PR)
- Natural language quality or fluency
- Reason length constraints
- Reason usage in control flow

---

## Rationale

### Why freeze vocabulary?

Without vocabulary constraints:
- Future PRs could introduce numeric counts
- Evaluative terms could leak in ("high confidence", "good signals")
- Logs would become inconsistent over time
- Translation/summarization tools would break
- Audit reproducibility would fail

### Why non-numeric?

Numeric expressions imply:
- Quantitative assessment (conflicts with non-evaluative requirement)
- Hidden formulas (breaks auditability)
- False precision (conflicts with qualitative design)

### Why non-evaluative?

Evaluative terms imply:
- Judgment (confidence should describe, not judge)
- Interpretation (prevents objective audit)
- Bias toward action/inaction (conflicts with READ-ONLY requirement)

---

## Future Work

This charter allows:
- **PR31+**: Semantic content improvements (within vocabulary constraints)
- **Future**: Additional vocabulary classes (requires new charter PR)
- **Future**: Localization/translation (vocabulary stability enables this)

This charter prohibits:
- Breaking vocabulary stability
- Introducing numeric/evaluative terms
- Using confidence_reason for control flow

---

**Charter Status**: Frozen (PR30)
**Compliance**: Mandatory for all v0.4+ implementations
**Review**: Required for any confidence_reason changes
