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

## Status

Meridian is under active development.
v0.2 implements constitutional regime-first decision making with full compliance validation.

Meridian optimizes for **survival first**, because only surviving systems get to compound.

---

**Meridian**  
*Intelligence Against Entropy.*
