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
- v0.3 Intent Charter: [docs/intent_charter_v0.3.md](docs/intent_charter_v0.3.md)
- v0.4 Confidence Charter: [docs/confidence_charter_v0.4.md](docs/confidence_charter_v0.4.md)
- v0.4 Confidence Logging Charter: [docs/confidence_logging_charter_v0.4.md](docs/confidence_logging_charter_v0.4.md)
- v0.4 Confidence Representation Charter: [docs/confidence_representation_charter_v0.4.md](docs/confidence_representation_charter_v0.4.md)
- v0.4 Confidence Absence Semantics Charter: [docs/confidence_absence_semantics_charter_v0.4.md](docs/confidence_absence_semantics_charter_v0.4.md)
- v0.4 Confidence Source Declaration Charter: [docs/confidence_source_charter_v0.4.md](docs/confidence_source_charter_v0.4.md)
- v0.4 Confidence Reason Structure Charter: [docs/confidence_reason_structure_charter_v0.4.md](docs/confidence_reason_structure_charter_v0.4.md)
- v0.4 Confidence Reason Vocabulary Charter: [docs/confidence_reason_vocabulary_charter_v0.4.md](docs/confidence_reason_vocabulary_charter_v0.4.md)
- v0.4 Confidence Release Declaration: [docs/v0.4_confidence_release_declaration.md](docs/v0.4_confidence_release_declaration.md)
- v0.5 Intelligence Boundary Charter: [docs/v0.5_intelligence_boundary_charter.md](docs/v0.5_intelligence_boundary_charter.md)
- v0.5 Intelligence Input Contract Charter: [docs/v0.5_intelligence_input_contract_charter.md](docs/v0.5_intelligence_input_contract_charter.md)
- v0.5 Intelligence Decision Record Charter: [docs/v0.5_intelligence_decision_record_charter.md](docs/v0.5_intelligence_decision_record_charter.md)

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

## Validation (v0.5)

Meridian v0.5 includes Intelligence Layer compliance validation that verifies:
- Input contract compliance (allowlist enforcement)
- Import ban detection (v0.4 builders/validators)
- Featurization ban detection (confidence_reason operations)
- Read-only consumption validation
- Decision Record immutability (no regeneration or post-hoc rationalization)
- v0.4 Confidence boundary protection (no erosion)
- Decision Engine v1 (mirror base-action, non-numeric, non-evaluative)
- Decision Engine v2 (rule overlay, regime-aware, non-numeric, non-evaluative)
- Decision Record wiring (v5_decision_* fields logged correctly)
- Decision Engine selector (v1/v2 switch, auditable)
- Decision Engine shadow mode (dual record logging for comparison)
- Decision Engine shadow diff logging (machine-readable comparison, non-evaluative)
- Decision diff semantics tagging (non-evaluative classification of divergence types)
- Shadow diff analytics export (daily summary aggregation for comparison analysis)
- Shadow diff report generator (human-readable Markdown/HTML reports, non-evaluative)
- Shadow diff report indexer (archive organization and TOC generation, non-evaluative)
- Daily shadow diff pipeline (orchestrates PR47→PR48A→PR48B in sequence, non-evaluative)
- Daily shadow diff pipeline scheduler (GitHub Actions + launchd templates for automated execution)
- Weekly shadow diff digest (7-day summary, observational only, READ-ONLY)

Run validations:
```bash
cd ~/Meridian
source .venv/bin/activate
python3 python/validation/pr37_intelligence_input_contract_guard_smoke.py
python3 python/validation/pr39_intelligence_decision_record_compliance_smoke.py
python3 python/validation/pr40_intelligence_decision_engine_v1_smoke.py
python3 python/validation/pr41_decision_record_wiring_smoke.py
python3 python/validation/pr41a_decision_record_wiring_consistency_smoke.py
python3 python/validation/pr42_intelligence_decision_engine_v2_smoke.py
python3 python/validation/pr43_decision_engine_selector_wiring_smoke.py
python3 python/validation/pr44_decision_engine_shadow_mode_smoke.py
python3 python/validation/pr45_decision_engine_shadow_diff_smoke.py
python3 python/validation/pr46_decision_diff_semantics_smoke.py
python3 python/validation/pr47_shadow_diff_analytics_export_smoke.py
python3 python/validation/pr48a_shadow_diff_report_generator_smoke.py
python3 python/validation/pr48b_shadow_diff_report_indexer_smoke.py
python3 python/validation/pr49_daily_shadow_diff_pipeline_smoke.py
python3 python/validation/pr50_scheduler_assets_smoke.py
python3 python/validation/pr51_weekly_shadow_diff_digest_smoke.py
```

All scripts exit 0 (warning-only, never fails).

**Analytics Tools:**

Generate human-readable reports from PR47 analytics:
```bash
cd ~/Meridian
source .venv/bin/activate

# Generate Markdown/HTML reports from PR47 outputs
python3 python/analytics/pr48a_shadow_diff_report_generator.py \
  --in_dir analytics_out \
  --out_dir reports

# Format options: md, html, or both (default: both)
python3 python/analytics/pr48a_shadow_diff_report_generator.py \
  --in_dir analytics_out \
  --out_dir reports \
  --format md

# Filter by specific day
python3 python/analytics/pr48a_shadow_diff_report_generator.py \
  --in_dir analytics_out \
  --out_dir reports \
  --day 2026-01-10

# Archive reports and generate index
python3 python/analytics/pr48b_shadow_diff_report_indexer.py \
  --reports_dir reports

# Archive specific day only
python3 python/analytics/pr48b_shadow_diff_report_indexer.py \
  --reports_dir reports \
  --day 2026-01-10

# Complete pipeline (PR47→PR48A→PR48B)
python3 python/analytics/pr49_daily_shadow_diff_pipeline.py \
  --log_path logs/meridian_log.csv \
  --analytics_out_dir analytics_out \
  --reports_dir reports

# Rebuild specific day
python3 python/analytics/pr49_daily_shadow_diff_pipeline.py \
  --log_path logs/meridian_log.csv \
  --day 2026-01-10 \
  --analytics_out_dir analytics_out \
  --reports_dir reports \
  --format both

# Generate weekly digest (auto end_day from latest available report)
python3 python/analytics/pr51_weekly_shadow_diff_digest.py \
  --reports_dir reports \
  --out_dir reports/weekly \
  --format both

# Generate weekly digest ending on specific day
python3 python/analytics/pr51_weekly_shadow_diff_digest.py \
  --reports_dir reports \
  --end_day 2026-01-11 \
  --days 7 \
  --out_dir reports/weekly \
  --format both
```

**Archive Structure:**

After running the indexer, reports are organized as:
```
reports/
  index.md          # Human-readable table of contents
  index.json        # Machine-readable registry
  _archive/
    2026-01-10/
      shadow_diff_report.md
      shadow_diff_report.html
      meta.json
    2026-01-11/
      ...
```

---

## Daily Pipeline Scheduling (PR50)

Meridian v0.5 provides two options for scheduling the daily shadow diff pipeline (PR49):

### Option 1: GitHub Actions (Recommended for CI/CD)

A GitHub Actions workflow is provided for daily automated execution:

**Location:** `.github/workflows/pr50_daily_shadow_diff_pipeline.yml`

**Schedule:** Daily at 00:30 UTC (09:30 JST)

**Features:**
- Scheduled execution via cron
- Manual execution via workflow_dispatch (optional day parameter)
- Artifact upload (analytics_out, reports) with 90-day retention
- Warning-only (never fails workflow)
- Constitutional constraints enforced

**Manual Trigger:**
- Go to Actions tab in GitHub
- Select "PR50 Daily Shadow Diff Pipeline"
- Click "Run workflow"
- Optional: Specify day (YYYY-MM-DD) and log path

### Option 2: Local Scheduling (macOS launchd)

Templates for local scheduling on macOS are provided:

**Location:** `scripts/com.meridian.pr49.daily.plist` (template)

**Installation:**
```bash
cd ~/Meridian

# Option A: Use helper script (recommended)
bash scripts/pr50_launchd_install.sh

# Option B: Manual installation
# 1. Customize the plist template (replace /path/to/meridian with actual path)
# 2. Copy to ~/Library/LaunchAgents/
# 3. Load with launchctl
cp scripts/com.meridian.pr49.daily.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.meridian.pr49.daily.plist
```

**Schedule:** Daily at 00:30 local time

**Management:**
```bash
# Start manually
launchctl start com.meridian.pr49.daily

# Unload
launchctl unload ~/Library/LaunchAgents/com.meridian.pr49.daily.plist

# Remove
rm ~/Library/LaunchAgents/com.meridian.pr49.daily.plist
```

**Logs:**
- stdout: `logs/pr49_daily_stdout.log`
- stderr: `logs/pr49_daily_stderr.log`

**Note:** Customize paths in the plist template before installation. The helper script does this automatically.

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

## v0.2 Log Requirements (PR13B)

**IMPORTANT:** Meridian v0.2 requires all execution logs to include the following columns:

- `regime` — Constitutional regime classification (e.g., `stable_range`, `emerging_trend`, `volatile_noise`, `REGIME_TRANSITION`)
- `base_action` — Base policy decision before overlay (e.g., `HOLD`, `SHIFT`, `PAUSE`)
- `decision_reason` — Human-readable decision explanation

**What happens if these columns are missing:**

1. **At agent startup** — The agent will detect pre-v0.2 logs and refuse to start. You must delete or rename the old log file.
2. **At runtime** — If the agent tries to write a row without these columns (code bug), it will exit immediately with a fatal error.
3. **At pipeline time** — PR8B integrity gate will reject logs missing these columns with a fail-closed error.

These guards ensure that v0.2 constitutional decision logs are **auditable, complete, and pipeline-compatible by design**.

---

## Production Workflow (PR10)

**Standard operating procedure for real log processing:**

1. **Put logs in `logs/`** — Place execution logs in the `logs/` directory
2. **Run canonical command** — Use `pr10_run_pipeline.py` for timestamped isolation
3. **Artifacts are time-stamped** — All outputs go to `artifacts/_<timestamp>/`

```bash
cd ~/Meridian && source .venv/bin/activate && \
python3 python/tools/pr10_run_pipeline.py \
  --log logs/meridian_log_latest.csv \
  --prefix meridian
```

This pipeline:
- Copies the input log to `artifacts/_<timestamp>/input_log.csv` (fixed copy)
- Runs PR8B integrity gate on the fixed copy
- Generates all reports and visualizations
- Creates `index.md` as entry point for all artifacts
- Isolates all outputs in the timestamped directory
- Prevents log mixing, overwrite, and collision

**Reading artifacts:**
- Artifacts include `index.md` (entry point).
- Open `index.md` first for recommended reading order.

---

## Validation (v0.6)

Meridian v0.6 introduces the **Interpretation Layer**: mapping observations to structural meaning types without evaluation or judgment.

### v0.6 Philosophy: Observation → Interpretation

v0.5 completed observation (what happened).
v0.6 maps observation to meaning type (what structure this represents).
That is not judgment, but structural language.

### Interpretation ≠ Evaluation

- **Interpretation** = Structural Mapping (what structure)
- **Interpretation** ≠ Evaluation (good/bad judgment)
- **Interpretation** ≠ Recommendation (what should be done)

### v0.6 Schema (PR60)

Interpretation records use `v6_` prefix:

- `v6_meaning_mode`: ON | OFF
- `v6_meaning_status`: AVAILABLE | UNAVAILABLE
- `v6_meaning_tag`: Structural meaning type (non-evaluative)
- `v6_meaning_summary`: Non-evaluative explanation
- `v6_meaning_basis`: Array of observation field names used

### v0.6 Interpretation Engine v1 (PR61)

**Interpretation v1 = Static Structural Mapping**

Engine v1 maps observations to meaning types using static rules:

**Meaning Tags (v1 Fixed Set):**
- `OVERLAY_OBSERVED`: Overlay pattern detected
- `ALIGNMENT_STABLE`: Actions aligned with shadow present
- `DIVERGENCE_WITHOUT_CLASS`: Divergence observed but type unclear
- `SHADOW_ABSENT_OR_UNAVAILABLE`: Shadow data not available
- `OBSERVATION_INSUFFICIENT`: Required fields missing
- `UNCLASSIFIED`: Cannot classify with current rules

**Note:** UNKNOWN/UNCLASSIFIED are normal outcomes (not failures).

**Static Mapping Examples:**
- `semantics_tag == DIVERGED_RULE_OVERLAY` → `OVERLAY_OBSERVED`
- `diff_status == ALIGNED` + shadow present → `ALIGNMENT_STABLE`
- `diff_status == DIVERGED` + semantics unclear → `DIVERGENCE_WITHOUT_CLASS`

This is not "getting smarter". This is structural language for what we can understand.

### v0.6 Interpretation Output Wiring (PR62)

**Purpose:** Wire v6 interpretation data into reports and digest (READ-ONLY, display only).

**Changes (PR62):**

1. **PR48A Daily Reports** — Add "Interpretation (v0.6)" section
   - Displays `meaning_status_counts` distribution
   - Displays `meaning_tag_counts` distribution
   - Supports degraded mode when v6 data absent

2. **PR51 Weekly Digest** — Add meaning aggregation
   - Aggregates `meaning_status_counts` across 7 days
   - Aggregates `meaning_tag_counts` across 7 days
   - Supports degraded mode when v6 data absent

**READ-ONLY Guarantee:**
- No execution logic changes
- No decision flow changes
- Display/presentation layer only
- Existing v0.5 sections unchanged

### v0.6 Interpretation Engine v2 (PR63)

**Interpretation v2 = Compositional Structural Mapping**

v1 was a point (single label). v2 is a surface (compositional decomposition).

**v2 Philosophy:**

v2 increases interpretation resolution by decomposing observations into multiple structural elements:

1. **Primary Meaning** — Main structural type (same as v1)
2. **Factors** — Structural elements present (e.g., REGIME_PRESENT, INTENT_PRESENT)
3. **Signals** — Concrete observational signs (e.g., DIFF_STATUS_ALIGNED, SEMANTICS_RULE_OVERLAY)

**Processing Order (v2):**

```
Observation → Signals → Factors → Primary Meaning → Summary
```

First decompose, then compose. This is structural language without loss.

**v2 Extended Output:**

```json
{
  "v6_meaning_tag": "OVERLAY_OBSERVED",
  "v6_meaning_factors": ["REGIME_PRESENT", "INTENT_PRESENT", "SHADOW_PRESENT"],
  "v6_meaning_signals": ["DIFF_STATUS_DIVERGED", "SEMANTICS_RULE_OVERLAY"],
  "v6_meaning_summary": "overlay pattern observed in decision divergence, with regime context.",
  "v6_meaning_basis": ["v5_decision_diff_status", "v5_decision_diff_semantics_tag", "regime"]
}
```

**Factors (Structural Elements):**
- `REGIME_PRESENT` / `REGIME_TRANSITION_PRESENT`
- `INTENT_PRESENT` / `INTENT_ABSENT`
- `SEMANTICS_AVAILABLE` / `SEMANTICS_UNAVAILABLE`
- `SHADOW_PRESENT` / `SHADOW_ABSENT`

**Signals (Observational Signs):**
- `DIFF_STATUS_ALIGNED` / `DIFF_STATUS_DIVERGED` / `DIFF_STATUS_UNAVAILABLE`
- `SEMANTICS_RULE_OVERLAY` / `SEMANTICS_ALIGNED` / `SEMANTICS_UNKNOWN`
- `PAIR_IDENTIFIED` / `PAIR_UNKNOWN`

**Important:**
- v2 does NOT lose information vs v1
- v2 does NOT evaluate or judge
- v2 is decomposition without optimization
- UNKNOWN/UNCLASSIFIED remain normal outcomes

This is not "getting smarter". This is structure without compression.

### v0.6 Interpretation Analytics (PR64)

**Purpose:** Observe meaning as landscape (distribution, transition).

PR61/PR63 create and decompose meaning (point, structure).
PR64 observes meaning distribution and transitions over time.

**Philosophy:**

This is analysis, not optimization.
This is insight, not recommendation.

**Questions PR64 Answers:**
- Which meaning tags exist, how many?
- Which factors/signals appear, in what structure?
- How do meanings transition day-to-day?

**Questions PR64 Does NOT Answer:**
- Is this good or bad?
- Did it improve or degrade?
- What should be done?

**Outputs:**

1. **Meaning Distribution**
   - `meaning_tag_counts`: Distribution across primary meanings
   - `factor_counts`: Structural element distribution
   - `signal_counts`: Observational sign distribution

2. **Meaning Transitions**
   - `daily_distributions`: Per-day meaning distribution
   - `transitions`: Day-to-day meaning changes (observational only)

**Example Usage:**

```bash
python3 python/analytics/pr64_interpretation_analytics.py \
  --in_file interpretation_records.jsonl \
  --out_dir analytics_out \
  --format both
```

**Outputs:**
- `pr64_interpretation_analytics.json` (full analytics)
- `pr64_meaning_tag_distribution.csv` (tag counts)
- `pr64_factor_distribution.csv` (factor counts)
- `pr64_signal_distribution.csv` (signal counts)
- `pr64_daily_meaning_distribution.csv` (daily transitions)

**Important:**
- READ-ONLY: Only reads interpretation records
- Non-evaluative: Only counts and distributions, no judgment
- No action changes: Pure observational visibility

This observes "what structure exists" and "how structure changes".
No evaluation. No recommendation.

### Constitutional Constraints (v0.6)

- **READ-ONLY**: No execution logic or decision changes
- **Non-evaluative**: No good/bad, correct/wrong vocabulary
- **Non-scoric**: No scores, grades, rankings
- **Non-prescriptive**: No "should" or recommendations
- **Observation-bound**: Only uses observation fields as basis
- **v0.4 boundary protection**: No confidence_reason analysis

### Run Validations (v0.6)

```bash
cd ~/Meridian
source .venv/bin/activate
python3 python/validation/pr60_interpretation_schema_smoke.py
python3 python/validation/pr61_interpretation_engine_v1_smoke.py
python3 python/validation/pr62_interpretation_report_integration_smoke.py
python3 python/validation/pr63_interpretation_engine_v2_smoke.py
python3 python/validation/pr64_interpretation_analytics_smoke.py
```

All scripts exit 0 (warning-only, never fails).

---

## v0.7 — Reflection Constitution (READ-ONLY)

### v0.7 Philosophy: Interpretation → Reflection

v0.6 completed interpretation (observation → meaning).
v0.7 observes the interpretation system itself.

Reflection observes:
- What meanings are frequently/rarely observed
- What combinations have never appeared
- What the interpretation engine implicitly assumes

**Reflection ≠ Evaluation**
- **Reflection** = Interpretive System Description
- **Reflection** ≠ Evaluation (good/bad judgment)
- **Reflection** ≠ Recommendation (what should be done)
- **Reflection** ≠ Optimization (improve/fix)

### v0.7 Reflection Schema (PR70)

Reflection records use `v7_` prefix:

- `v7_reflection_mode`: ON | OFF
- `v7_reflection_status`: AVAILABLE | UNAVAILABLE
- `v7_reflection_tag`: Reflection type (non-evaluative)
- `v7_reflection_summary`: Non-evaluative system description
- `v7_reflection_basis`: Array of interpretation field names used
- `v7_reflection_artifacts`: Array of analytics artifacts referenced

**Example Reflection Record:**

```json
{
  "v7_reflection_mode": "ON",
  "v7_reflection_status": "AVAILABLE",
  "v7_reflection_tag": "COVERAGE_GAP_DETECTED",
  "v7_reflection_summary": "certain factor combinations not observed in data.",
  "v7_reflection_basis": ["v6_factors", "pr64_interpretation_analytics"],
  "v7_reflection_artifacts": ["interpretation_distribution.json"]
}
```

**Important:**
- Reflection observes interpretation system characteristics
- No evaluation of whether patterns are good/bad
- No recommendations for what should be changed
- UNKNOWN/UNCLASSIFIED remain normal outcomes

### v0.7 Reflection Engine v1 (PR71)

Engine v1 = **Static Structural Self-Description**

Generates reflection records by observing interpretation analytics from PR64:

**Reflection Tags (v1 Fixed Set):**
- `MEANING_COVERAGE_NARROW`: Limited meaning types observed (≤ 2 types)
- `MEANING_COVERAGE_BROAD`: Diverse meaning types observed (≥ 4 types)
- `MEANING_DISTRIBUTION_SKEWED`: Concentration on limited subset (≥ 80%)
- `FACTOR_DOMINANCE_OBSERVED`: Certain factors almost always present (≥ 90%)
- `UNSEEN_MEANING_COMBINATIONS`: Theoretically possible combinations never observed
- `SIGNAL_NEVER_OBSERVED`: Certain signals not present in data
- `REFLECTION_INSUFFICIENT`: Analytics data insufficient
- `UNCLASSIFIED`: Cannot classify with current rules (normal outcome)

**Detection Logic:**
- **Coverage**: Count distinct meaning types in distribution
- **Skew**: Measure concentration of dominant meaning tag
- **Unseen**: Identify gaps in observed structural patterns
- **No judgment**: All tags are neutral observations

**Usage:**

```python
from reflection.v7_reflection_engine_v1 import reflect_v1, V1ReflectionTags
from analytics.pr64_interpretation_analytics import generate_interpretation_analytics

# Generate analytics from interpretation records
analytics = generate_interpretation_analytics(interpretation_records)

# Generate reflection
reflection = reflect_v1(analytics)

print(reflection["v7_reflection_tag"])
print(reflection["v7_reflection_summary"])
print(reflection["v7_reflection_basis"])
```

**Example Output:**

```json
{
  "v7_reflection_mode": "ON",
  "v7_reflection_status": "AVAILABLE",
  "v7_reflection_tag": "MEANING_DISTRIBUTION_SKEWED",
  "v7_reflection_summary": "observed interpretation output concentrates on limited subset. 'OVERLAY_OBSERVED' appears in 85% of records.",
  "v7_reflection_basis": ["meaning_tag_counts", "total_records"],
  "v7_reflection_artifacts": ["pr64_interpretation_analytics"]
}
```

**Rule Priority:**
1. Coverage narrow/broad (primary structural observation)
2. Skew detection (concentration patterns)
3. Factor dominance (v2 compositional patterns)
4. Signal never observed (gap detection)

**Warning-Only Validation:**
- Never raises exceptions
- Handles edge cases gracefully (None, invalid types)
- Always returns valid v7 record
- Exit code always 0

### Constitutional Constraints (v0.7)

- **READ-ONLY**: No execution logic or decision changes
- **Non-evaluative**: No good/bad, correct/wrong vocabulary
- **Non-scoric**: No scores, grades, rankings
- **Non-prescriptive**: No "should" or recommendations
- **Interpretation-bound**: Only uses interpretation fields as basis
- **v0.4 boundary protection**: No confidence_reason analysis
- **Observation boundary protection**: No direct v5 field access

### Run Validations (v0.7)

```bash
cd ~/Meridian
source .venv/bin/activate
python3 python/validation/pr70_reflection_schema_smoke.py
python3 python/validation/pr71_reflection_engine_v1_smoke.py
```

All scripts exit 0 (warning-only, never fails).

---

## v0.8 — Blindspot Constitution (READ-ONLY)

### v0.8 Philosophy: Reflection → Blindspot

v0.6 completed interpretation (observation → meaning).
v0.7 completed reflection (interpretation → system description).
v0.8 observes structural absences — what the system cannot see.

Blindspot observes:
- Signal types never observed
- Factor types never observed
- Meaning types never observed
- Transitions never observed
- Structures the schema cannot express

**Blindspot ≠ Evaluation**
- **Blindspot** = Structural Absence Description
- **Blindspot** ≠ Evaluation (good/bad judgment)
- **Blindspot** ≠ Recommendation (what should be done)
- **Blindspot** ≠ Optimization (improve/fix)

### v0.8 Blindspot Schema (PR80)

Blindspot records use `v8_` prefix:

- `v8_blindspot_mode`: ON | OFF
- `v8_blindspot_status`: AVAILABLE | UNAVAILABLE
- `v8_blindspot_tag`: Structural absence type (non-evaluative)
- `v8_blindspot_summary`: Non-evaluative structural absence description
- `v8_blindspot_basis`: Array of interpretation/reflection field names used
- `v8_blindspot_artifacts`: Array of analytics artifacts referenced

**Example Blindspot Record:**

```json
{
  "v8_blindspot_mode": "ON",
  "v8_blindspot_status": "AVAILABLE",
  "v8_blindspot_tag": "ABSENCE_UNSEEN_SIGNAL_TYPES",
  "v8_blindspot_summary": "certain signal types not observed in data.",
  "v8_blindspot_basis": ["v6_signals", "v7_reflection_tag"],
  "v8_blindspot_artifacts": ["pr64_interpretation_analytics", "pr71_reflection_record"]
}
```

**Important:**
- Blindspot observes structural absences in interpretation/reflection systems
- No evaluation of whether absences are good/bad
- No recommendations for what should be changed
- UNKNOWN/UNCLASSIFIED remain normal outcomes

**Blindspot Tags (v1 Fixed Set):**
- `ABSENCE_INSUFFICIENT_EVIDENCE` - Analytics data insufficient
- `ABSENCE_UNSEEN_SIGNAL_TYPES` - Certain signal types not observed
- `ABSENCE_UNSEEN_FACTOR_TYPES` - Certain factor types not observed
- `ABSENCE_UNOBSERVED_MEANING_TYPES` - Certain meaning types not observed
- `ABSENCE_TRANSITION_NOT_OBSERVED` - Certain transitions not observed
- `ABSENCE_SCHEMA_CANNOT_EXPRESS` - Structure cannot be expressed in current schema
- `UNCLASSIFIED` - Cannot classify with current rules (normal outcome)

### v0.8 Blindspot Detection Engine v1 (PR81)

Engine v1 = **Structural Absence Scan**

Detects structural absences by enumerating differences between possible structures and observed structures.

**Detection Philosophy:**
- Enumerate what exists in definition space but not in observed space
- No judgment about whether absences are problems
- No inference about why absences exist
- Pure set difference operation

**Detection Targets:**
- **Unseen Signal Types**: Signals defined but never observed
- **Unseen Factor Types**: Factors defined but never observed
- **Unobserved Meaning Types**: Meanings defined but never observed
- **Transition Gaps**: Theoretically possible transitions never observed

**Usage:**

```python
from blindspot.v8_blindspot_detection_engine_v1 import detect_blindspot_v1, V1BlindspotTags
from analytics.pr64_interpretation_analytics import generate_interpretation_analytics

# Generate analytics from interpretation records
analytics = generate_interpretation_analytics(interpretation_records)

# Detect blindspot
blindspot = detect_blindspot_v1(analytics)

print(blindspot["v8_blindspot_tag"])
print(blindspot["v8_blindspot_summary"])
print(blindspot["v8_blindspot_basis"])
```

**Example Output:**

```json
{
  "v8_blindspot_mode": "ON",
  "v8_blindspot_status": "AVAILABLE",
  "v8_blindspot_tag": "ABSENCE_UNSEEN_SIGNAL_TYPES",
  "v8_blindspot_summary": "6 signal types not observed in data. certain observational patterns not present.",
  "v8_blindspot_basis": ["meaning_tag_counts", "total_records", "signal_counts"],
  "v8_blindspot_artifacts": ["pr64_interpretation_analytics"]
}
```

**Detection Logic:**
1. Extract observed sets from analytics (signals, factors, meanings, transitions)
2. Compare against known definition space
3. Enumerate differences as structural absences
4. No evaluation, no recommendation

**Warning-Only Validation:**
- Never raises exceptions
- Handles edge cases gracefully (None, invalid types)
- Always returns valid v8 record
- Exit code always 0

### Constitutional Constraints (v0.8)

- **READ-ONLY**: No execution logic or decision changes
- **Non-evaluative**: No good/bad, correct/wrong vocabulary
- **Non-scoric**: No scores, grades, rankings
- **Non-prescriptive**: No "should" or recommendations
- **Interpretation/Reflection-bound**: Only uses v6/v7 fields as basis
- **v0.4 boundary protection**: No confidence_reason analysis
- **Observation boundary protection**: No direct v5 field access

### Run Validations (v0.8)

```bash
cd ~/Meridian
source .venv/bin/activate
python3 python/validation/pr80_blindspot_schema_smoke.py
python3 python/validation/pr81_blindspot_detection_engine_v1_smoke.py
```

All scripts exit 0 (warning-only, never fails).

---

## v0.9 — Boundary Constitution (READ-ONLY)

### v0.9 Philosophy: Blindspot → Boundary

v0.6 completed interpretation (observation → meaning).
v0.7 completed reflection (interpretation → system description).
v0.8 completed blindspot (structural absences enumeration).
v0.9 classifies where observability ends — the boundary itself.

Boundary answers a different question than Blindspot:
- **Blindspot**: What is absent?
- **Boundary**: At which structural boundary does the absence occur?

Boundary treats absences not as failures, but as topological limits of the system.

**Boundary ≠ Evaluation**
- **Boundary** = Structural Limit Description
- **Boundary** ≠ Evaluation (good/bad judgment)
- **Boundary** ≠ Recommendation (what should be done)
- **Boundary** ≠ Optimization (improve/fix)
- **Boundary** ≠ Root-cause analysis

### v0.9 Boundary Schema (PR90)

Boundary records use `v9_` prefix:

- `v9_boundary_mode`: ON | OFF
- `v9_boundary_status`: AVAILABLE | UNAVAILABLE
- `v9_boundary_type`: Structural boundary type (non-evaluative)
- `v9_boundary_description`: Non-evaluative structural limit description
- `v9_boundary_basis`: Array of blindspot/interpretation/reflection field names used
- `v9_boundary_artifacts`: Array of analytics artifacts referenced

**Example Boundary Record:**

```json
{
  "v9_boundary_mode": "ON",
  "v9_boundary_status": "AVAILABLE",
  "v9_boundary_type": "SCHEMA_BOUNDARY",
  "v9_boundary_description": "observability limit at schema layer. structure cannot be expressed with current schema.",
  "v9_boundary_basis": ["v8_blindspot_tag", "v7_reflection_tag"],
  "v9_boundary_artifacts": ["pr81_blindspot_record"]
}
```

**Important:**
- Boundary classifies structural limits of observability
- No evaluation of whether boundaries are good/bad
- No recommendations for what should be changed
- UNKNOWN/UNCLASSIFIED remain normal outcomes

**Boundary Types (v1):**
- `SCHEMA_BOUNDARY` - Structure cannot be expressed with current schema
- `DATA_BOUNDARY` - Required data does not exist or is insufficient
- `ENGINE_BOUNDARY` - Interpretation/reflection rules cannot map structure
- `SAMPLING_BOUNDARY` - Structure exists in definition space but not observed
- `TEMPORAL_BOUNDARY` - Structure exists but cannot be observed in time window
- `UNCLASSIFIED` - Cannot classify with current rules (normal outcome)

### v0.9 Boundary Classification Engine v1 (PR91)

Engine v1 = **Structural Limit Mapping**

Classifies blindspots into structural boundary types using static rules.

**Classification Philosophy:**
- Map blindspot to boundary layer (not evaluation)
- Static rules (if/elif), no learning, no inference
- No judgment about whether boundaries are problems
- No inference about why boundaries exist

**Classification Rules:**
1. **ABSENCE_INSUFFICIENT_EVIDENCE** → `DATA_BOUNDARY`
2. **ABSENCE_SCHEMA_CANNOT_EXPRESS** → `SCHEMA_BOUNDARY`
3. **ABSENCE_TRANSITION_NOT_OBSERVED** →
   - Observation period < 30 days → `TEMPORAL_BOUNDARY`
   - Observation period ≥ 30 days → `SAMPLING_BOUNDARY`
4. **ABSENCE_UNSEEN_SIGNAL/FACTOR/MEANING_TYPES** → `SAMPLING_BOUNDARY`
5. **All others** → `UNCLASSIFIED`

**Usage:**

```python
from boundary.v9_boundary_classification_engine_v1 import classify_boundary_v1, V1BoundaryTypes
from blindspot.v8_blindspot_detection_engine_v1 import detect_blindspot_v1

# Detect blindspot from analytics
blindspot = detect_blindspot_v1(interpretation_analytics)

# Classify boundary
boundary = classify_boundary_v1(blindspot)

print(boundary["v9_boundary_type"])
print(boundary["v9_boundary_description"])
print(boundary["v9_boundary_basis"])
```

**Example Output:**

```json
{
  "v9_boundary_mode": "ON",
  "v9_boundary_status": "AVAILABLE",
  "v9_boundary_type": "SAMPLING_BOUNDARY",
  "v9_boundary_description": "observability limit at sampling layer. certain structural types exist in definition space but not observed in data.",
  "v9_boundary_basis": ["v8_blindspot_tag"],
  "v9_boundary_artifacts": ["pr81_blindspot_record"]
}
```

**Classification Logic:**
1. Extract blindspot tag from v8 record
2. Apply static mapping rules
3. Classify into boundary type
4. No evaluation, no recommendation

**Warning-Only Validation:**
- Never raises exceptions
- Handles edge cases gracefully (None, invalid types)
- Always returns valid v9 record
- Exit code always 0

### Constitutional Constraints (v0.9)

- **READ-ONLY**: No execution logic or decision changes
- **Non-evaluative**: No good/bad, correct/wrong vocabulary
- **Non-scoric**: No scores, grades, rankings
- **Non-prescriptive**: No "should" or recommendations
- **Blindspot-bound**: Only uses v8/v7/v6 fields as basis
- **v0.4 boundary protection**: No confidence_reason analysis
- **Observation boundary protection**: No direct v5 field access

### Run Validations (v0.9)

```bash
cd ~/Meridian
source .venv/bin/activate
python3 python/validation/pr90_boundary_schema_smoke.py
python3 python/validation/pr91_boundary_classification_engine_v1_smoke.py
```

All scripts exit 0 (warning-only, never fails).

---

## v1.0 — Execution Constitution (READ-ONLY)

### v1.0 Philosophy: Boundary → Execution

v0.6 completed interpretation (observation → meaning).
v0.7 completed reflection (interpretation → system description).
v0.8 completed blindspot (structural absences enumeration).
v0.9 completed boundary (structural limits of observability).
v1.0 describes executability — whether execution is available and what intent exists.

Execution answers a different question than Decision:
- **Execution** = Executability Description
- **Execution** ≠ Trading (no swap/transfer/send/approve/sign)
- **Execution** ≠ Position changes (no fund movement/rebalancing)
- **Execution** ≠ Recommendations (no should/must)

**Execution ≠ Trading**
- **Execution** = Description of execution intent
- **Execution** ≠ Evaluation (good/bad judgment)
- **Execution** ≠ Profit/loss analysis
- **Execution** ≠ Scoring or optimization
- **Execution** ≠ Trading commands

### v1.0 Execution Schema (PR100)

Execution records use `v10_` prefix:

- `v10_execution_mode`: ON | OFF
- `v10_execution_status`: AVAILABLE | UNAVAILABLE
- `v10_execution_intent`: Structural execution intent type (non-evaluative)
- `v10_execution_permission`: Execution permission level
- `v10_execution_summary`: Non-evaluative execution description
- `v10_execution_basis`: Array of boundary/blindspot/reflection/interpretation field names used
- `v10_execution_artifacts`: Array of analytics artifacts referenced (optional)
- `v10_execution_constraints`: Execution constraints (optional)

**Example Execution Record:**

```json
{
  "v10_execution_mode": "ON",
  "v10_execution_status": "AVAILABLE",
  "v10_execution_intent": "REBALANCE_INTENT",
  "v10_execution_permission": "DRY_RUN_ONLY",
  "v10_execution_summary": "rebalance intent observed. execution available in dry-run mode.",
  "v10_execution_basis": ["v9_boundary_type", "v8_blindspot_tag"],
  "v10_execution_artifacts": ["pr91_boundary_record"],
  "v10_execution_constraints": ["dry_run_only", "no_fund_movement"]
}
```

**Important:**
- Execution describes executability, not trading
- No evaluation of whether execution is good/bad
- No recommendations for what should be executed
- NONE/UNKNOWN/HOLD remain normal outcomes

**Execution Intent Types (v1):**
- `NONE` - No execution intent detected
- `MAINTENANCE` - Maintenance execution intent
- `REBALANCE_INTENT` - Rebalance execution intent
- `HEDGE_INTENT` - Hedge execution intent
- `LIQUIDITY_INTENT` - Liquidity execution intent
- `UNCLASSIFIED` - Cannot classify with current rules (normal outcome)

**Execution Permission Types (v1):**
- `UNKNOWN` - Permission status unknown
- `DRY_RUN_ONLY` - Execution permitted in dry-run mode only
- `HOLD` - Execution on hold
- `ALLOW` - Execution allowed

### v1.0 Constitutional Guards (PR100)

PR100 introduces constitutional guards to enforce v1.0 execution principles:

**1. Forbidden Vocabulary Guard**
- Detects evaluative vocabulary (good/bad, correct/wrong)
- Detects scoric vocabulary (score/grade/rank)
- Detects prescriptive vocabulary (should/must/recommend)

**2. Execution Safety Guard (NEW in v1.0)**
- Detects trading action vocabulary (swap/transfer/send/approve/sign)
- Detects position management vocabulary (open/close/liquidate)
- Excludes valid intent type descriptions (e.g., "rebalance intent")

**3. v0.4 Boundary Guard**
- Detects confidence_reason field access
- Execution must not access v0.4 confidence layer

**4. Observation Boundary Guard**
- Detects v5 observation field access
- Execution must only access v6/v7/v8/v9 fields as basis

**Usage:**

```python
from execution.v10_execution_schema import V10ExecutionSchema
from execution.v10_constitutional_guard import validate_execution_record

# Create execution record
record = V10ExecutionSchema.create_empty_record()
record["v10_execution_intent"] = "REBALANCE_INTENT"
record["v10_execution_permission"] = "DRY_RUN_ONLY"

# Validate against constitutional guards
warnings = validate_execution_record(record)

if warnings:
    for warning in warnings:
        print(f"⚠ {warning}")
```

**Example Validation:**

```python
# Clean execution description (no warnings)
record = {
    "v10_execution_intent": "MAINTENANCE",
    "v10_execution_summary": "maintenance intent observed. execution available.",
    "v10_execution_basis": ["v9_boundary_type", "v8_blindspot_tag"]
}
warnings = validate_execution_record(record)  # []

# Forbidden vocabulary (triggers warning)
record = {
    "v10_execution_intent": "REBALANCE_INTENT",
    "v10_execution_summary": "this is a good opportunity that should be taken",
    "v10_execution_basis": ["v9_boundary_type"]
}
warnings = validate_execution_record(record)
# ["Forbidden vocabulary detected: 'good' in text",
#  "Forbidden vocabulary detected: 'should' in text"]

# Trading vocabulary (triggers warning)
record = {
    "v10_execution_intent": "REBALANCE_INTENT",
    "v10_execution_summary": "swap tokens and transfer funds",
    "v10_execution_basis": ["v9_boundary_type"]
}
warnings = validate_execution_record(record)
# ["Execution action vocabulary detected: 'swap' in text",
#  "Execution action vocabulary detected: 'transfer' in text"]
```

**Warning-Only Validation:**
- Never raises exceptions
- Handles edge cases gracefully
- Always returns warnings list
- Exit code always 0

### Constitutional Constraints (v1.0)

- **READ-ONLY**: No execution logic or decision changes
- **Non-evaluative**: No good/bad, correct/wrong vocabulary
- **Non-scoric**: No scores, grades, rankings
- **Non-prescriptive**: No "should" or recommendations
- **Boundary-bound**: Only uses v6/v7/v8/v9 fields as basis
- **v0.4 boundary protection**: No confidence_reason analysis
- **Observation boundary protection**: No direct v5 field access
- **Execution safety**: No trading action vocabulary

### v1.0 Execution Permissioning Engine v1 (PR101)

Engine v1 = **Structural Boundary-to-Permission Mapping**

Classifies execution permission based on boundary type using static rules.

**Permissioning Philosophy:**
- Map boundary to permission level (not evaluation)
- Static rules (if/elif), no learning, no inference
- No judgment about whether permission is good/bad
- No recommendation about what should be executed

**Permission Types (v1):**
- `UNKNOWN` - Insufficient structural clarity
- `HOLD` - Execution structurally disallowed
- `DRY_RUN_ONLY` - Observation-only execution allowed
- `ALLOW` - Execution structurally permitted (rare in v1)

**Classification Rules (v1 - Static):**
1. **SCHEMA_BOUNDARY** → `HOLD`
2. **DATA_BOUNDARY** → `HOLD`
3. **ENGINE_BOUNDARY** → `HOLD`
4. **TEMPORAL_BOUNDARY** → `DRY_RUN_ONLY`
5. **SAMPLING_BOUNDARY** → `DRY_RUN_ONLY`
6. **UNCLASSIFIED** → `UNKNOWN`

**Usage:**

```python
from execution.v10_execution_permissioning_engine_v1 import classify_execution_permission_v1
from boundary.v9_boundary_classification_engine_v1 import classify_boundary_v1
from blindspot.v8_blindspot_detection_engine_v1 import detect_blindspot_v1

# Detect blindspot from analytics
blindspot = detect_blindspot_v1(interpretation_analytics)

# Classify boundary
boundary = classify_boundary_v1(blindspot)

# Classify execution permission
execution = classify_execution_permission_v1(boundary)

print(execution["v10_execution_permission"])
print(execution["v10_execution_summary"])
print(execution["v10_execution_basis"])
```

**Example Output:**

```json
{
  "v10_execution_mode": "ON",
  "v10_execution_status": "AVAILABLE",
  "v10_execution_intent": "NONE",
  "v10_execution_permission": "DRY_RUN_ONLY",
  "v10_execution_summary": "execution permitted only in dry-run mode. sampling boundary detected. structure exists in definition space but not observed.",
  "v10_execution_basis": ["v9_boundary_type"],
  "v10_execution_artifacts": [],
  "v10_execution_constraints": []
}
```

**Classification Logic:**
1. Extract boundary type from v9 record
2. Apply static mapping rules
3. Classify into permission level
4. No evaluation, no recommendation

**Warning-Only Validation:**
- Never raises exceptions
- Handles edge cases gracefully (None, invalid types)
- Always returns valid v10 record
- Exit code always 0

### v1.0 Execution Plan Schema v1 (PR102)

Schema v1 = **Typed Plan Shape (Structural Only)**

Defines execution plan records that describe plan shapes without amounts, token names, or trading actions.

**Plan Philosophy:**
- Plan = Structural plan shape description
- No amounts, prices, or quantities
- No token literals (SUI, USDC, BTC, etc.)
- No addresses or wallet interactions
- No trading verbs or commands

**Plan Types (v1):**
- `NOOP` - No operation plan
- `MAINTENANCE` - Maintenance plan
- `REBALANCE` - Rebalance plan shape
- `HEDGE` - Hedge plan shape
- `LIQUIDITY` - Liquidity plan shape
- `UNCLASSIFIED` - Cannot classify with current rules

**Schema Fields (v10_plan_ prefix):**
- `v10_plan_mode`: ON | OFF
- `v10_plan_status`: AVAILABLE | UNAVAILABLE
- `v10_plan_type`: Structural plan type
- `v10_plan_description`: Non-evaluative plan shape description
- `v10_plan_constraints`: Structural constraints (time/frequency only)
- `v10_plan_basis`: Array of execution field names referenced
- `v10_plan_artifacts`: Array of artifact names (optional)

**Constraint Types (Structural Only):**
- `time_window` - e.g., "business_hours_only"
- `frequency_limit` - e.g., "once_per_day"
- `dry_run_only` - e.g., "no_live_execution"
- `manual_approval` - e.g., "requires_manual_approval"

**Constitutional Guards:**

**1. Token Literal Guard (NEW in PR102)**
- Detects token names (SUI, USDC, BTC, ETH, etc.)
- Prevents concrete token references in plans
- Maintains abstract plan descriptions

**2. Numeric Pattern Guard (NEW in PR102)**
- Detects amounts (1000, 0.5, etc.)
- Detects prices ($100, €50, etc.)
- Detects addresses (0x...)
- Plans remain purely structural

**3. Forbidden Vocabulary & Execution Safety**
- All PR100 guards apply to plan descriptions
- No evaluative/prescriptive vocabulary
- No trading action verbs

**Usage:**

```python
from execution.v10_execution_plan_schema import V10ExecutionPlanSchema
from execution.v10_plan_constitutional_guard import validate_plan_record

# Create plan record
plan = V10ExecutionPlanSchema.create_empty_record()
plan["v10_plan_mode"] = "ON"
plan["v10_plan_status"] = "AVAILABLE"
plan["v10_plan_type"] = "REBALANCE"
plan["v10_plan_description"] = "rebalance plan available based on boundary analysis."
plan["v10_plan_constraints"] = ["dry_run_only", "time_window_business_hours"]
plan["v10_plan_basis"] = ["v10_execution_permission"]

# Validate against constitutional guards
warnings = validate_plan_record(plan)

if warnings:
    for warning in warnings:
        print(f"⚠ {warning}")
```

**Example Plan Record:**

```json
{
  "v10_plan_mode": "ON",
  "v10_plan_status": "AVAILABLE",
  "v10_plan_type": "REBALANCE",
  "v10_plan_description": "rebalance plan available based on sampling boundary.",
  "v10_plan_constraints": ["dry_run_only", "frequency_limit_once_per_day"],
  "v10_plan_basis": ["v10_execution_permission"],
  "v10_plan_artifacts": ["pr101_execution_record"]
}
```

**Important:**
- Plans describe structure, not specific trades
- No amounts, no token names, no addresses
- Constraints are time/frequency based only
- All trading vocabulary is forbidden

**Warning-Only Validation:**
- Never raises exceptions
- Detects violations via constitutional guards
- Always returns warnings list
- Exit code always 0

### v1.0 Execution Plan Generator v1 (PR103)

Generator v1 = **Static Plan Synthesis**

Generates execution plan records based on permission and boundary analysis using static rules.

**Generator Philosophy:**
- Generate plan shape from permission (not execution)
- Static rules (if/elif), no learning, no inference
- No amounts, no token names, no addresses
- No trading verbs or execution commands

**Generation Rules (v1 - Static):**
1. **HOLD** → `NOOP` + `manual_approval`
   - Execution structurally disallowed
2. **UNKNOWN** → `UNCLASSIFIED` + `manual_approval`
   - Insufficient structural clarity
3. **DRY_RUN_ONLY** → `MAINTENANCE` + `dry_run_only` + `frequency_limit_once_per_day`
   - Observation-only execution
4. **ALLOW** → Intent-based type + `manual_approval`
   - REBALANCE_INTENT → `REBALANCE`
   - HEDGE_INTENT → `HEDGE`
   - LIQUIDITY_INTENT → `LIQUIDITY`
   - MAINTENANCE → `MAINTENANCE`
   - Other → `UNCLASSIFIED`

**Usage:**

```python
from execution.v10_execution_plan_generator_v1 import generate_execution_plan_v1
from execution.v10_execution_permissioning_engine_v1 import classify_execution_permission_v1
from boundary.v9_boundary_classification_engine_v1 import classify_boundary_v1
from blindspot.v8_blindspot_detection_engine_v1 import detect_blindspot_v1

# Full pipeline: Blindspot → Boundary → Permission → Plan
blindspot = detect_blindspot_v1(interpretation_analytics)
boundary = classify_boundary_v1(blindspot)
execution = classify_execution_permission_v1(boundary)
plan = generate_execution_plan_v1(execution, boundary)

print(plan["v10_plan_type"])
print(plan["v10_plan_description"])
print(plan["v10_plan_constraints"])
```

**Example Output (DRY_RUN_ONLY):**

```json
{
  "v10_plan_mode": "ON",
  "v10_plan_status": "AVAILABLE",
  "v10_plan_type": "MAINTENANCE",
  "v10_plan_description": "maintenance plan available in dry-run-only mode due to boundary constraints.",
  "v10_plan_constraints": ["dry_run_only", "frequency_limit_once_per_day"],
  "v10_plan_basis": ["v10_execution_permission", "v9_boundary_type"],
  "v10_plan_artifacts": []
}
```

**Example Output (ALLOW + REBALANCE_INTENT):**

```json
{
  "v10_plan_mode": "ON",
  "v10_plan_status": "AVAILABLE",
  "v10_plan_type": "REBALANCE",
  "v10_plan_description": "rebalance plan shape available under allow permission; manual approval required.",
  "v10_plan_constraints": ["manual_approval"],
  "v10_plan_basis": ["v10_execution_permission", "v10_execution_intent"],
  "v10_plan_artifacts": []
}
```

**Generation Logic:**
1. Extract permission from v10 execution record
2. Apply static mapping rules
3. Generate plan type and constraints
4. No evaluation, no recommendation, no trading

**Constitutional Guarantees:**
- No amounts, prices, or quantities generated
- No token literals (SUI, USDC, etc.) in descriptions
- No addresses or wallet references
- No trading verbs (swap, transfer, sign, etc.)
- All generated plans pass PR102 constitutional guards

**Warning-Only Validation:**
- Never raises exceptions
- Handles edge cases gracefully (None, invalid types)
- Always returns valid v10 plan record
- Exit code always 0

### v1.0 Execution Simulation Engine v1 (PR104)

Engine v1 = **Plan Applicability Scan**

Simulates plan applicability based on constraints without execution, PnL, or evaluation.

**Simulation Philosophy:**
- Simulate = Plan applicability description
- Enumerate constraints as events
- No execution, no wallet, no transactions
- No amounts, no token names, no PnL

**Schema Fields (v10_simulation_ prefix):**
- `v10_simulation_mode`: ON | OFF
- `v10_simulation_status`: AVAILABLE | UNAVAILABLE
- `v10_simulation_type`: PLAN_APPLICABILITY_SCAN | UNCLASSIFIED
- `v10_simulation_summary`: Non-evaluative simulation description
- `v10_simulation_basis`: Array of field names referenced
- `v10_simulation_artifacts`: Array of artifact names (optional)
- `v10_simulation_trace`: Array of simulation events (optional)

**Trace Event Structure:**
- `event_type`: CONSTRAINT_APPLIED | PLAN_APPLICABLE | PLAN_NOT_APPLIED | WINDOW_ADVANCED
- `event_summary`: Non-evaluative event description
- `event_basis`: Array of field names referenced

**Simulation Logic (v1):**
1. Check plan availability
2. Enumerate constraints as CONSTRAINT_APPLIED events
3. Determine applicability based on constraints
4. Generate trace of constraint applications

**Constraint Types Detected:**
- `dry_run_only` - Observation-only mode
- `manual_approval` - Human review required
- `frequency_limit` - Rate limiting active
- `time_window` - Time-based restrictions

**Usage:**

```python
from execution.v10_execution_simulation_engine_v1 import simulate_execution_plan_v1
from execution.v10_execution_plan_generator_v1 import generate_execution_plan_v1
from execution.v10_execution_permissioning_engine_v1 import classify_execution_permission_v1

# Full pipeline: Permission → Plan → Simulation
execution = classify_execution_permission_v1(boundary)
plan = generate_execution_plan_v1(execution, boundary)
simulation = simulate_execution_plan_v1(plan)

print(simulation["v10_simulation_type"])
print(simulation["v10_simulation_summary"])
for event in simulation["v10_simulation_trace"]:
    print(f"  {event['event_type']}: {event['event_summary']}")
```

**Example Output (dry_run_only constraint):**

```json
{
  "v10_simulation_mode": "ON",
  "v10_simulation_status": "AVAILABLE",
  "v10_simulation_type": "PLAN_APPLICABILITY_SCAN",
  "v10_simulation_summary": "plan applicability scan complete. plan type MAINTENANCE applicable under constraint.",
  "v10_simulation_basis": ["v10_plan_mode", "v10_plan_status", "v10_plan_type", "v10_plan_constraints"],
  "v10_simulation_trace": [
    {
      "event_type": "CONSTRAINT_APPLIED",
      "event_summary": "dry-run-only constraint applied. execution limited to observation mode.",
      "event_basis": ["v10_plan_constraints"]
    },
    {
      "event_type": "PLAN_APPLICABLE",
      "event_summary": "plan applicable under constraint. constraints enumerated above.",
      "event_basis": ["v10_plan_constraints"]
    }
  ]
}
```

**Simulation Guarantees:**
- No execution (READ-ONLY)
- No amounts, prices, or quantities
- No token literals (SUI, USDC, etc.)
- No addresses or wallet references
- No trading verbs or commands
- No PnL calculation
- No evaluation (good/bad judgment)

**Warning-Only Validation:**
- Never raises exceptions
- Handles edge cases gracefully (None, invalid types)
- Always returns valid v10 simulation record
- Exit code always 0

### v1.0 Execution Audit Trail v1 (PR105)

Engine v1 = **Causal Chain Trace**

Documents the causal chain from interpretation through simulation without execution, evaluation, or trading.

**Audit Trail Philosophy:**
- Audit Trail = Causal chain documentation
- Link artifacts as explicit chain-of-custody
- No execution, no evaluation, no recommendations
- Fixed layer order (cannot reorder)

**Schema Fields (v10_audit_ prefix):**
- `v10_audit_mode`: ON | OFF
- `v10_audit_status`: AVAILABLE | UNAVAILABLE
- `v10_audit_chain`: Array of chain events (ordered)
- `v10_audit_summary`: Non-evaluative audit description

**Chain Event Structure:**
- `layer`: Layer name (INTERPRETATION_ANALYTICS, BLINDSPOT, etc.)
- `artifact`: Artifact identifier (pr81_blindspot_record, etc.)
- `basis`: Array of field names referenced

**Chain Layers (Fixed Order in v1):**
1. **INTERPRETATION_ANALYTICS** (PR64) - Observation → meaning
2. **BLINDSPOT** (PR81) - Structural absences
3. **BOUNDARY** (PR91) - Observability limits
4. **PERMISSION** (PR101) - Executability permission
5. **PLAN** (PR103) - Plan shape generation
6. **SIMULATION** (PR104) - Plan applicability scan

**Usage:**

```python
from audit.v10_execution_audit_trail_engine_v1 import build_execution_audit_trail_v1

# Full pipeline audit trail
trail = build_execution_audit_trail_v1(
    interpretation_analytics=analytics,
    blindspot_record=blindspot,
    boundary_record=boundary,
    permission_record=execution,
    plan_record=plan,
    simulation_record=simulation
)

print(trail["v10_audit_status"])
print(trail["v10_audit_summary"])
for event in trail["v10_audit_chain"]:
    print(f"  {event['layer']}: {event['artifact']}")
```

**Example Output (full chain):**

```json
{
  "v10_audit_mode": "ON",
  "v10_audit_status": "AVAILABLE",
  "v10_audit_summary": "audit trail built with multiple layers of causal chain. chain links interpretation through simulation.",
  "v10_audit_chain": [
    {
      "layer": "BLINDSPOT",
      "artifact": "pr81_blindspot_record",
      "basis": ["v8_blindspot_tag", "v8_blindspot_basis"]
    },
    {
      "layer": "BOUNDARY",
      "artifact": "pr91_boundary_record",
      "basis": ["v9_boundary_type", "v9_boundary_basis"]
    },
    {
      "layer": "PERMISSION",
      "artifact": "pr101_execution_record",
      "basis": ["v10_execution_permission", "v10_execution_basis"]
    },
    {
      "layer": "PLAN",
      "artifact": "pr103_plan_record",
      "basis": ["v10_plan_type", "v10_plan_constraints", "v10_plan_basis"]
    },
    {
      "layer": "SIMULATION",
      "artifact": "pr104_simulation_record",
      "basis": ["v10_simulation_type", "v10_simulation_basis"]
    }
  ]
}
```

**Audit Trail Guarantees:**
- Fixed layer order (no reordering)
- Defensive (None/invalid → skip layer)
- No execution (READ-ONLY)
- No amounts, prices, or quantities
- No token literals (SUI, USDC, etc.)
- No addresses or wallet references
- No trading verbs or commands
- No evaluation (good/bad judgment)

**Complete Pipeline:**

```
Interpretation Analytics (PR64)
         ↓
    Blindspot (PR81)
         ↓
    Boundary (PR91)
         ↓
    Permission (PR101)
         ↓
    Plan (PR103)
         ↓
    Simulation (PR104)
         ↓
    Audit Trail (PR105) ← Documents entire causal chain
```

**Warning-Only Validation:**
- Never raises exceptions
- Handles edge cases gracefully (None, invalid types)
- Always returns valid v10 audit trail record
- Exit code always 0

### Run Validations (v1.0)

```bash
cd ~/Meridian
source .venv/bin/activate
python3 python/validation/pr100_execution_schema_smoke.py
python3 python/validation/pr101_execution_permissioning_engine_v1_smoke.py
python3 python/validation/pr102_execution_plan_schema_smoke.py
python3 python/validation/pr103_execution_plan_generator_v1_smoke.py
python3 python/validation/pr104_execution_simulation_engine_v1_smoke.py
python3 python/validation/pr105_execution_audit_trail_smoke.py
```

All scripts exit 0 (warning-only, never fails).

---

## v1.1 — Intelligence Native Market (READ-ONLY)

### v1.1 Philosophy: Execution → Market Intelligence

v1.0 completed execution constitution (boundary → executability).
v1.1 integrates onchain market intelligence — regime classification, policy binding, execution preview, and human approval.

**v1.1 Pipeline:**
```
Onchain Connection (PR106)
         ↓
Onchain Observation (PR107)
         ↓
Observation Bridge (PR108)
         ↓
Analytics Extension (PR109)
         ↓
Entropy Regime (PR110)
         ↓
Policy Binding (PR111)
         ↓
Execution Preview (PR112)
         ↓
Human Approval Gate (PR113)
```

### v1.1 Entropy Regime Classification (PR110)

**Purpose:** Classify entropy regime from onchain analytics.

**Regime Philosophy:**
- Regime = State Classification (not action)
- No recommendations, no optimization
- READ-ONLY, non-evaluative, non-prescriptive

**Regime Levels:**
- `REGIME_LOW` - Low variation (stable)
- `REGIME_MEDIUM` - Moderate variation
- `REGIME_HIGH` - High variation (elevated)
- `REGIME_CRITICAL` - Extreme variation or no observations

**Classification Metrics:**
- Market cost regime distribution (entropy)
- Liquidity regime diversity (count)
- Event activity variation (entropy)
- Object dynamics variation (entropy)

**Constitutional Guarantees:**
- No token literals (SUI/USDC prohibited)
- No amounts or addresses
- No asset vocabulary
- No action vocabulary
- Defensive (never raises)
- Warning-only (exit 0)

### v1.1 Regime → Execution Policy Binding (PR111)

**Purpose:** Bind regime classification to execution policy.

**Binding Philosophy:**
- Binding = Constitutional Gate (not action/decision)
- No recommendations, no optimization
- READ-ONLY, non-evaluative, non-prescriptive

**Binding Rules (v1):**
- `REGIME_CRITICAL` → `HOLD` + `["regime_critical_observed"]`
- `REGIME_HIGH` → `DRY_RUN_ONLY` + `["regime_high_observed"]`
- `REGIME_MEDIUM` → `UNKNOWN` + `["regime_medium_observed"]`
- `REGIME_LOW` → `UNKNOWN` + `["regime_low_observed"]`

**Permission Overrides:**
- `HOLD` - Hard stop (critical regime)
- `DRY_RUN_ONLY` - Simulation only (high regime)
- `UNKNOWN` - No override (defer to execution engine)
- `ALLOW` - Explicit permission (reserved)

**Constitutional Guarantees:**
- No amounts (override labels only)
- No token literals, addresses
- No asset/action vocabulary
- Defensive, warning-only

### v1.1 Execution Preview Engine (PR112)

**Purpose:** Describe structural impact shape of potential execution.

**Preview Philosophy:**
- Preview = Impact Shape Description (not simulation/execution)
- No execution, no signing, no transactions
- READ-ONLY, non-evaluative, non-prescriptive

**Preview Fields:**
- `v11_preview_exposure_change`: NONE/INCREASE/DECREASE
- `v11_preview_interaction_type`: NONE/POOL_TOUCH/EVENT_INTERACTION
- `v11_preview_risk_surface`: LOW/MEDIUM/HIGH
- `v11_preview_status`: AVAILABLE/BLOCKED/ERROR

**Static Preview Rules (v1):**

**Exposure Change:**
- NOOP/MAINTENANCE → NONE
- REBALANCE → DECREASE (conservative)
- HEDGE → DECREASE
- LIQUIDITY → INCREASE

**Interaction Type:**
- MAINTENANCE → NONE
- REBALANCE/HEDGE/LIQUIDITY → POOL_TOUCH
- NOOP → NONE

**Risk Surface:**
- REGIME_LOW → LOW
- REGIME_MEDIUM → MEDIUM
- REGIME_HIGH → HIGH
- REGIME_CRITICAL → BLOCKED

**Constitutional Guarantees:**
- No trading vocabulary (swap/buy/sell/execute/sign/transfer)
- No execution operations (transaction/broadcast/submit)
- No token literals, addresses, amounts
- No asset/action vocabulary
- Defensive, warning-only

### v1.1 Human Approval Gate (PR113)

**Purpose:** Determine human approval requirement from upstream records.

**Approval Philosophy:**
- Approval Gate = State Machine (not action/recommendation)
- "APPROVED" is a state label only (not instruction)
- No execution, no recommendations, no evaluation

**Approval Requirement Levels:**
- `NOT_REQUIRED` - No approval needed
- `REQUIRED` - Approval recommended
- `REQUIRED_STRICT` - Approval mandatory (hard gate)

**Approval States:**
- `UNREQUESTED` - No approval requested yet
- `REQUESTED` - Approval requested, pending
- `APPROVED` - Approved (state label only)
- `REJECTED` - Rejected
- `EXPIRED` - Approval expired

**Static Approval Rules (v1 - First Match Wins):**
1. Preview status == `BLOCKED` → `REQUIRED_STRICT`
2. Execution permission == `HOLD` → `REQUIRED_STRICT`
3. Regime level == `REGIME_CRITICAL` → `REQUIRED_STRICT`
4. Execution permission == `DRY_RUN_ONLY` → `REQUIRED`
5. Regime level == `REGIME_HIGH` → `REQUIRED`
6. Default → `NOT_REQUIRED`

**Example Approval Record:**

```json
{
  "v11_approval_mode": "ON",
  "v11_approval_status": "AVAILABLE",
  "v11_approval_requirement": "REQUIRED_STRICT",
  "v11_approval_state": "UNREQUESTED",
  "v11_approval_summary": "approval required under critical regime conditions. no approval requested.",
  "v11_approval_basis": ["v11_regime_level", "v11_preview_risk_surface"],
  "v11_approval_artifacts": ["pr110_regime_record", "pr112_preview_record"]
}
```

**Constitutional Guarantees:**
- No trading vocabulary (swap/buy/sell/execute/sign/transfer)
- No execution operations (transaction/broadcast/submit)
- No token literals, addresses, amounts
- No asset/action vocabulary
- No approval-specific vocabulary (go ahead/proceed/instruction)
- "APPROVED" must not be described as instruction
- Defensive, warning-only

**Usage Pipeline:**

```python
from approval import gate_human_approval_v1

# Gate approval from upstream records
approval = gate_human_approval_v1(
    execution_record=execution,
    plan_record=plan,
    simulation_record=simulation,
    regime_record=regime,
    policy_record=policy,
    preview_record=preview,
)

print(approval["v11_approval_requirement"])  # REQUIRED_STRICT
print(approval["v11_approval_state"])        # UNREQUESTED
print(approval["v11_approval_summary"])
```

### Constitutional Constraints (v1.1)

- **READ-ONLY**: No execution logic or decision changes
- **Non-evaluative**: No good/bad, correct/wrong vocabulary
- **Non-scoric**: No scores, grades, rankings
- **Non-prescriptive**: No "should" or recommendations
- **No amounts**: Numeric patterns prohibited
- **No token literals**: SUI, USDC, BTC, ETH prohibited
- **No addresses**: 0x... patterns prohibited
- **No trading vocabulary**: swap, buy, sell, execute, sign, transfer prohibited
- **Defensive**: Never raises exceptions
- **Warning-only**: Exit code always 0

### Run Validations (v1.1)

```bash
cd ~/Meridian
source .venv/bin/activate
python3 python/validation/pr110_entropy_regime_classification_smoke.py
python3 python/validation/pr111_regime_execution_policy_binding_smoke.py
python3 python/validation/pr112_execution_preview_engine_v1_smoke.py
python3 python/validation/pr113_human_approval_gate_v1_smoke.py
```

All scripts exit 0 (warning-only, never fails).

---

## v1.0 Infrastructure — Market Structure Intelligence Pipeline (READ-ONLY)

### v1.0 Philosophy: Intelligence Native Market Architecture

v1.0 Infrastructure builds on the execution constitution (v1.0) and intelligence native market (v1.1) to provide:
- End-to-end pipeline orchestration
- Artifact bundling and chain-of-custody
- Golden regression testing for determinism
- CLI demonstration interface
- Market structure vocabulary abstraction
- Vocabulary drift detection

**Pipeline Flow:**
```
Onchain Observation (PR107)
         ↓
Analytics Extension (PR109)
         ↓
Market Structure Vocabulary (PR119) ← Convert analytics to structural terms
         ↓
Vocabulary Drift Detection (PR120) ← Detect structural language shifts
         ↓
Entropy Regime (PR110)
         ↓
Policy Binding (PR111)
         ↓
Execution Preview (PR112)
         ↓
Human Approval Gate (PR113)
         ↓
Pipeline Orchestrator (PR115) ← Coordinate all layers
         ↓
Artifact Bundle (PR116) ← Chain-of-custody container
         ↓
CLI Demo (PR118) ← Human-readable digest
```

### v1.0 Pipeline Orchestrator v1 (PR115)

**Purpose:** Coordinate observation → vocabulary → drift → regime → policy → preview → approval pipeline.

**Orchestrator Philosophy:**
- Orchestrator = Pipeline Coordinator (not execution)
- Defensive layer-by-layer execution
- No execution, no trading, no recommendations
- READ-ONLY, non-evaluative, non-prescriptive

**Pipeline Stages (Ordered):**
1. **Onchain Observation** - Read pool/object state
2. **Analytics Extension** - Compute market structure metrics
3. **Market Structure Vocabulary** - Convert analytics to structural terms
4. **Vocabulary Drift Detection** - Detect term set changes (NEW in PR120)
5. **Entropy Regime** - Classify regime level
6. **Policy Binding** - Apply regime → permission rules
7. **Execution Preview** - Describe structural impact shape
8. **Human Approval** - Gate approval requirement

**Orchestrator Output:**
```json
{
  "orchestrator_status": "SUCCESS",
  "observation": {...},
  "analytics": {...},
  "vocabulary": {...},
  "drift": {...},
  "regime": {...},
  "policy": {...},
  "preview": {...},
  "approval": {...},
  "warnings": [...]
}
```

**Constitutional Guarantees:**
- Never raises exceptions (defensive)
- Skips failed layers (continues with warnings)
- No trading vocabulary or execution
- Exit code always 0 (warning-only)

### v1.0 Artifact Bundle Schema v1 (PR116)

**Purpose:** Chain-of-custody container for pipeline artifacts.

**Bundle Philosophy:**
- Bundle = Artifact Container (not execution)
- Fixed layer ordering (14 valid layer names)
- Digest-based integrity verification
- READ-ONLY, non-evaluative

**Valid Layer Names (Fixed Set):**
- `connection`, `provider_config`, `observation`
- `analytics`, `vocabulary`, `drift`
- `regime`, `policy`, `preview`, `approval`
- `orchestrator_output`, `bundle_metadata`
- `warnings`, `errors`

**Bundle Guards:**
1. **Overreach Guard** - Detects invalid layer names
2. **Ordering Consistency Guard** - Verifies layer order matches definition

**Example Bundle:**
```json
{
  "bundle_status": "AVAILABLE",
  "bundle_layers": [
    {"layer": "observation", "artifact": {...}},
    {"layer": "analytics", "artifact": {...}},
    {"layer": "vocabulary", "artifact": {...}},
    {"layer": "drift", "artifact": {...}},
    {"layer": "regime", "artifact": {...}}
  ],
  "bundle_digest": "sha256:abcd1234...",
  "bundle_warnings": []
}
```

### v1.0 Golden Fixtures & Regression Harness (PR117)

**Purpose:** Determinism proof using golden test vectors.

**Regression Philosophy:**
- Regression = Output Stability Verification (not optimization)
- Golden fixtures = Canonical test cases
- Deterministic output required (no randomness)
- READ-ONLY, non-evaluative

**Fixtures (v1.0):**
- `mock_connection.json` - Mock onchain connection
- `mock_provider_config.json` - Provider configuration
- `mock_observations_case_A.json` - Stable/low activity case
- `mock_observations_case_B.json` - High variation case
- `expected_bundle_case_A.json` - Expected output A
- `expected_bundle_case_B.json` - Expected output B

**Harness Checks:**
- Output matches expected bundle structure
- All required layers present
- No unexpected layers added
- Digest verification passes

### v1.0 CLI Demo v1 (PR118)

**Purpose:** One-command end-to-end pipeline with human-readable digest.

**CLI Philosophy:**
- CLI = Demo Interface (not production execution)
- Human-readable digest rendering
- No execution, no trading, no recommendations
- READ-ONLY, non-evaluative

**Usage:**
```bash
python3 python/cli/v10_meridian_cli.py \
  --connection mock_connection.json \
  --provider_config mock_provider_config.json
```

**Digest Output:**
```
Bundle Status: AVAILABLE

Observation: 10 observations collected
Analytics: Market cost regime counts available
Vocabulary: 8 structural terms identified
Drift: DRIFT_LOW classification (minor structural changes)
Regime: REGIME_MEDIUM (moderate variation)
Policy: DRY_RUN_ONLY (regime-based constraint)
Preview: Risk surface MEDIUM
Approval: REQUIRED (approval recommended)
```

**Constitutional Guard:**
- Detects instruction vocabulary in CLI output
- No "execute", "run", "approve" commands
- CLI is display-only interface

### v1.0 Market Structure Vocabulary Schema & Builder v1 (PR119)

**Purpose:** Convert analytics to stable structural vocabulary terms.

**Vocabulary Philosophy:**
- Vocabulary = Market Structure Language (not price, not ownership)
- Fixed term set (11 terms in 4 families)
- Presence-only mapping (no counts in output)
- READ-ONLY, non-evaluative

**Vocabulary Term Families:**

**1. Market Cost Regime (3 terms):**
- `COST_LOW_PRESENT` / `COST_MEDIUM_PRESENT` / `COST_HIGH_PRESENT`

**2. Liquidity Regime (3 terms):**
- `LIQUIDITY_LOW_PRESENT` / `LIQUIDITY_MEDIUM_PRESENT` / `LIQUIDITY_HIGH_PRESENT`

**3. Event Activity (2 terms):**
- `EVENT_ACTIVITY_PRESENT` / `EVENT_ACTIVITY_ABSENT`

**4. Object Dynamics (3 terms):**
- `OBJECT_DYNAMICS_DECREASE_PRESENT`
- `OBJECT_DYNAMICS_STABLE_PRESENT`
- `OBJECT_DYNAMICS_INCREASE_PRESENT`

**Mapping Rules:**
- Analytics distribution → Vocabulary term presence
- Count > 0 → `_PRESENT`
- Count == 0 → `_ABSENT`
- No numeric counts in output (constitutional)

**Example Vocabulary Record:**
```json
{
  "v10_vocab_mode": "ON",
  "v10_vocab_status": "AVAILABLE",
  "v10_vocab_terms": [
    "COST_LOW_PRESENT",
    "COST_MEDIUM_PRESENT",
    "LIQUIDITY_LOW_PRESENT",
    "EVENT_ACTIVITY_PRESENT",
    "OBJECT_DYNAMICS_STABLE_PRESENT"
  ],
  "v10_vocab_summary": "market structure vocabulary extracted from analytics. multiple regime types present.",
  "v10_vocab_basis": ["market_cost_regime_counts", "liquidity_regime_presence", "event_activity_frequency"]
}
```

**Constitutional Guards:**
- Token literal guard (SUI, USDC, BTC, ETH prohibited)
- Numeric pattern guard (counts, percentages, scores prohibited)
- Address pattern guard (0x... prohibited)
- Trading vocabulary guard (swap, buy, sell prohibited)
- Vocabulary term validation (only approved terms allowed)

### v1.0 Vocabulary Drift Detection Engine v1 (PR120)

**Purpose:** Detect market structure drift by comparing vocabulary windows.

**Drift Philosophy:**
- Drift = Structural Language Shift (not evaluation, not prediction)
- Qualitative classification only (no numeric output)
- Evidence = Term names only (no counts)
- READ-ONLY, non-evaluative, non-prescriptive

**Detection Approach (v1 - Static, Qualitative):**

1. **Extract term presence sets** from each window:
   - Window A (past): union of all terms across all vocab records
   - Window B (current): union of all terms across all vocab records

2. **Compute structural deltas:**
   - `terms_added`: terms in B but not in A (B \ A)
   - `terms_removed`: terms in A but not in B (A \ B)

3. **Bucket into drift levels** (INTERNAL bucketing - NO numbers in output):
   - `DRIFT_NONE`: no delta
   - `DRIFT_LOW`: small delta (1-2 terms)
   - `DRIFT_MEDIUM`: moderate delta (3-4 terms)
   - `DRIFT_HIGH`: large delta (5-6 terms)
   - `DRIFT_CRITICAL`: very large delta (7+ terms)
   - `UNCLASSIFIED`: insufficient data

4. **Generate evidence list** (term names only, no counts):
   - Format: `"{TERM_NAME}_ADDED"` or `"{TERM_NAME}_REMOVED"`
   - Example: `["COST_HIGH_PRESENT_ADDED", "EVENT_ACTIVITY_ABSENT_REMOVED"]`

**Example Drift Record:**
```json
{
  "v10_drift_mode": "ON",
  "v10_drift_status": "AVAILABLE",
  "v10_drift_level": "DRIFT_MEDIUM",
  "v10_drift_summary": "market structure drift classified as drift_medium. moderate structural changes detected. terms added and removed.",
  "v10_drift_basis": ["vocab_window_A", "vocab_window_B"],
  "v10_drift_evidence": [
    "COST_HIGH_PRESENT_ADDED",
    "LIQUIDITY_MEDIUM_PRESENT_ADDED",
    "EVENT_ACTIVITY_ABSENT_REMOVED",
    "OBJECT_DYNAMICS_DECREASE_PRESENT_REMOVED"
  ],
  "v10_drift_warnings": []
}
```

**Constitutional Guards (STRENGTHENED for PR120):**

**1. Numeric Pattern Guard (STRENGTHENED):**
- Detects explicit counts: "3 terms", "5 changes", "10 deltas"
- Detects percentages: "50%", "10 percent"
- Detects numeric assignments: "delta=3", "count=5", "score=0.8"
- Detects decimal numbers (excluding version numbers like "v1.0")
- Detects currency symbols ($, ¥, €)

**2. Drift Level Validation (NEW):**
- Validates drift level is from approved set
- Only `DRIFT_NONE`, `DRIFT_LOW`, `DRIFT_MEDIUM`, `DRIFT_HIGH`, `DRIFT_CRITICAL`, `UNCLASSIFIED` allowed

**3. Inherited Guards:**
- Token literal guard (from PR119)
- Trading vocabulary guard (from PR112)
- Execution operation guard (from PR100)
- Address pattern guard (from PR102)
- Asset vocabulary guard (from PR108)
- Action vocabulary guard (from PR111)
- Forbidden vocabulary guard (from PR100)

**Important Constraints:**
- **NO numeric patterns in output** - Summary must use qualitative language only
  - ❌ "5 terms added and 3 terms removed"
  - ✅ "terms added and removed"
  - ✅ "moderate structural changes detected"
- **Evidence format** - Term names only, no counts
  - ❌ "COST_HIGH_PRESENT_ADDED (count=5)"
  - ✅ "COST_HIGH_PRESENT_ADDED"
- **Drift level** - Decided internally, never exposed as numbers
  - Internal: `total_delta = len(terms_added) + len(terms_removed)`
  - External: `"DRIFT_MEDIUM"` (label only)

**Usage:**
```python
from drift import detect_market_structure_drift_v1, validate_drift_record

# Detect drift between two vocabulary windows
vocab_window_A = [vocab_record_1, vocab_record_2]  # Past window
vocab_window_B = [vocab_record_3, vocab_record_4]  # Current window

drift = detect_market_structure_drift_v1(vocab_window_A, vocab_window_B)

# Validate against constitutional guards
warnings = validate_drift_record(drift)

if warnings:
    print(f"Constitutional violations detected: {len(warnings)} warnings")
    for warning in warnings:
        print(f"  - {warning}")
```

**Defensive Behavior:**
- None/empty windows → `UNCLASSIFIED` or `ERROR`
- Invalid inputs → `ERROR` record (never raises)
- Warning-only (exit code always 0)

### v1.0 Drift → Reflection/Boundary/Execution Binding v1 (PR121)

**Purpose:** Bind drift classification into downstream constitutional layers as structure, not action.

**Binding Philosophy:**
- Drift does not mean "trade" or "stop"
- Drift means: structure is moving
- Binding = Constitutional Gate (not action/recommendation)

PR121 integrates drift detection (PR120) into the explainability chain:

**1. Drift Reflection Attachment v1**

Attaches drift classification to reflection records as structural addenda.

**File:** `python/bridge/v10_drift_to_reflection_attachment_v1.py`

**Behavior:**
- Adds `pr120_drift_record` to reflection artifacts
- Adds `v10_drift_level` to reflection basis
- Appends drift context to reflection summary (non-prescriptive)
- Never modifies reflection tag
- Defensive (None → return original or empty)

**Example:**
```python
from bridge.v10_drift_to_reflection_attachment_v1 import attach_drift_to_reflection_v1

# Attach drift to reflection
enhanced = attach_drift_to_reflection_v1(reflection_record, drift_record)

# Result includes drift artifacts and basis
print(enhanced["v7_reflection_artifacts"])  # ["pr120_drift_record"]
print(enhanced["v7_reflection_basis"])      # [..., "v10_drift_level"]
```

**2. Drift Boundary Hinting v1**

Enhances boundary records with drift-based observability stability hints.

**File:** `python/boundary/v10_drift_boundary_hint_engine_v1.py`

**Behavior:**
- Adds drift hint to boundary description (non-prescriptive)
- Maps drift levels to observability stability:
  - `DRIFT_CRITICAL` → "observability unstable under critical drift"
  - `DRIFT_HIGH` → "observability unstable under high drift"
  - `DRIFT_MEDIUM` → "observability moderate under drift"
  - `DRIFT_LOW` → "observability stable under low drift"
  - `DRIFT_NONE` → "observability stable with no drift"
- Never modifies boundary type
- Defensive (None → return original or empty)

**Example:**
```python
from boundary.v10_drift_boundary_hint_engine_v1 import hint_boundary_with_drift_v1

# Hint boundary with drift
enhanced = hint_boundary_with_drift_v1(boundary_record, drift_record)

# Result includes drift-based observability hint
print(enhanced["v9_boundary_description"])
# "sampling boundary detected. observability unstable under critical drift."
```

**3. Drift Execution Policy Binding v1 (Conservative)**

Binds drift classification to execution permission with conservative rules.

**File:** `python/policy/v10_drift_execution_policy_binding_v1.py`

**Static Binding Rules (v1 - Conservative):**

| Drift Level | Permission Override | Constraint Label |
|-------------|---------------------|------------------|
| `DRIFT_CRITICAL` | `HOLD` | `drift_critical_observed` |
| `DRIFT_HIGH` | `DRY_RUN_ONLY` | `drift_high_observed` |
| `DRIFT_MEDIUM` | No override | `drift_medium_observed` |
| `DRIFT_LOW` | No override | `drift_low_observed` |
| `DRIFT_NONE` | No override | `drift_none_observed` |
| `UNCLASSIFIED` | No override | `drift_unclassified` |

**Permission Override Logic:**
- **HOLD**: Hard stop (critical drift - structure highly unstable)
- **DRY_RUN_ONLY**: Simulation only (high drift - structure unstable)
- **No override**: Defer to upstream execution engine (low/medium/none drift)

**Restrictiveness Order:** `HOLD` > `DRY_RUN_ONLY` > `ALLOW` > `UNKNOWN`
- Always selects more restrictive permission between current and override

**Example:**
```python
from policy.v10_drift_execution_policy_binding_v1 import bind_drift_to_execution_policy_v1

# Bind drift to execution policy
enhanced = bind_drift_to_execution_policy_v1(execution_record, drift_record)

# DRIFT_CRITICAL overrides permission to HOLD
print(enhanced["v10_execution_permission"])  # "HOLD"
print(enhanced["v10_execution_constraints"]) # ["drift_critical_observed"]
```

**4. Drift Policy Constitutional Guard**

Enforces constitutional constraints on drift policy binding outputs.

**File:** `python/policy/v10_drift_policy_constitutional_guard.py`

**Guards (STRENGTHENED):**
1. **Numeric Pattern Guard** - No counts, percentages, scores
2. **Token Literal Guard** - No SUI, USDC, BTC, ETH
3. **Address Pattern Guard** - No 0x... patterns
4. **Trading Vocabulary Guard** - No swap, buy, sell, execute
5. **Execution Operation Guard** - No transaction, broadcast, submit
6. **Forbidden Vocabulary Guard** - No good/bad, correct/wrong
7. **Prescriptive Language Guard (NEW)** - No should/must, proceed/stop/pause

**Example:**
```python
from policy.v10_drift_policy_constitutional_guard import validate_drift_policy_binding

# Validate binding output
warnings = validate_drift_policy_binding(enhanced_execution)

# Detects violations
if warnings:
    for warning in warnings:
        print(f"⚠ {warning}")
```

**Integration into Pipeline:**

```
Vocabulary (PR119)
         ↓
Drift Detection (PR120) ← Detect structural language shifts
         ↓
Drift Reflection Attachment (PR121) ← Add to explainability chain
         ↓
Drift Boundary Hinting (PR121) ← Enhance observability description
         ↓
Drift Execution Binding (PR121) ← Conservative permission gating
         ↓
Regime Classification (PR110)
         ↓
Policy Binding (PR111)
         ↓
Execution Preview (PR112)
```

**Important:**
- Drift binding is **classification only** (not action)
- HOLD/DRY_RUN_ONLY are **permission labels** (not commands)
- All outputs remain **non-prescriptive** (no "should", "must", "pause")
- Constraint labels are **structural context only** (not instructions)

### Constitutional Constraints (v1.0 Infrastructure)

All v1.0 infrastructure components enforce:

- **READ-ONLY**: No execution, no signing, no transaction construction
- **Non-evaluative**: No good/bad, correct/wrong vocabulary
- **Non-scoric**: No scores, grades, rankings
- **Non-prescriptive**: No "should" or recommendations
- **No amounts**: Numeric patterns prohibited in output
- **No token literals**: SUI, USDC, BTC, ETH prohibited
- **No addresses**: 0x... patterns prohibited
- **No trading vocabulary**: swap, buy, sell, execute, sign, transfer prohibited
- **Defensive**: Never raises exceptions (returns ERROR records)
- **Warning-only**: Exit code always 0

### Run Validations (v1.0 Infrastructure)

```bash
cd ~/Meridian
source .venv/bin/activate
python3 python/validation/pr115_pipeline_orchestrator_v1_smoke.py
python3 python/validation/pr116_artifact_bundle_schema_smoke.py
python3 python/validation/pr117_golden_regression_harness_smoke.py
python3 python/validation/pr118_cli_demo_smoke.py
python3 python/validation/pr119_market_structure_vocabulary_smoke.py
python3 python/validation/pr120_market_structure_drift_smoke.py
python3 python/validation/pr121_drift_binding_smoke.py
```

All scripts exit 0 (warning-only, never fails).

---

## Status

Meridian is under active development.
v0.2 implements constitutional regime-first decision making with full compliance validation.
v0.5 completes observation infrastructure (shadow diff, analytics, reporting).
v0.6 introduces interpretation (structural meaning without judgment).
v0.7 introduces reflection (observing interpretation system characteristics).
v0.8 introduces blindspot (observing structural absences in interpretation/reflection systems).
v0.9 introduces boundary (classifying structural limits of observability).
v1.0 introduces execution constitution (boundary → executability without trading).
v1.1 introduces intelligence native market (onchain regime classification, policy binding, execution preview, human approval).
v1.0 infrastructure completes end-to-end pipeline (orchestrator, artifact bundling, regression testing, CLI demo, market structure vocabulary, vocabulary drift detection, drift binding into explainability chain).

Meridian optimizes for **survival first**, because only surviving systems get to compound.

---

**Meridian**  
*Intelligence Against Entropy.*
