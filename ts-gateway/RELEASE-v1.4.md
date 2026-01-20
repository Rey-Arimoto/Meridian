# Meridian v1.4 LTS

This is the frozen Long-Term Stability release line for Meridian v1.4.

## Release Status
- **Status**: LTS (Long-Term Stability)
- **Policy**: No new features will be added to v1.4 LTS
- **Maintenance**: Only spec-drift bug fixes may be considered

## Key Features (v1.4 Line)

### Safety & Governance Layers
- **PR229**: Recovery Budgeting (暴走防止)
- **PR230**: Signal Trust & Consensus (Article XI - No Single Source of Market Truth)
- **PR230a**: Regime Gating (NEVER LIVE on weak consensus)
- **PR230b**: Signal Consensus → Execution Hard Cap
- **PR231**: Invariant Checks v1 (Final defensive layer)
- **PR232**: Economic Safety Invariants v1 (LIVE capital safety)
- **PR233**: Economic Risk Constraints Layer v1 (Article XII)
- **PR233a**: Economic Risk Observability Pack v1
- **PR233b**: Economic Execution Shaping v1 (Article XII-b)
- **PR234**: Capital-at-Risk Envelope v1 (Article XIII)
- **PR235**: Adversarial Incident Quarantine v1 (Article XIV)
- **PR236**: Recovery Governance Layer v1 (Article XV)
- **PR237**: Learning Freeze & Drift Firewall v1 (Article XVI)

### Test Coverage
- PR229: 12/12 tests passing ✓
- PR230: 15/15 tests passing ✓
- PR230a: 8/8 tests passing ✓
- PR230b: 6/6 tests passing ✓
- PR231: 8/8 tests passing ✓
- PR232: 9/9 tests passing ✓
- PR233: 10/10 tests passing ✓
- PR233a: 8/8 tests passing ✓
- PR233b: 10/10 tests passing ✓
- PR234: 10/10 tests passing ✓
- PR235: 12/12 tests passing ✓
- PR236: 13/13 tests passing ✓
- PR237: 12/12 tests passing ✓

**Total**: 143 comprehensive unit tests

## Verification
- ✅ TypeScript build passes (npm run build)
- ✅ All unit tests pass
- ✅ Integration tests verified

## Constitutional Principles
All safety layers follow:
- **READ-ONLY**: Never modify execution directly
- **Deterministic**: Same inputs → same outputs
- **Defensive**: Fail-safe behaviors
- **Label-only telemetry**: No raw numeric emissions
- **Backward compatible**: All fields optional

## Migration Notes
- v1.4 LTS is a drop-in replacement for earlier v1.x versions
- All new safety layers are backward compatible
- Telemetry labels added (no breaking changes to existing events)

## Rollback
- Use previous tags if needed
- All safety layers can be disabled via configuration

## Next Steps
- v1.5 development branch will continue with new experimental features
- v1.4 LTS will receive only critical bug fixes
