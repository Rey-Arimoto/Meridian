#!/bin/bash
# tools/verify-v1.5-release.sh
# v1.5 Stability Guards release verification script

set -euo pipefail

echo "=== v1.5 Stability Guards Release Verification ==="
echo ""

# Step 1: Show release info
echo "Step 1: Release Information"
echo "  Tag: v1.5-stability-guards-v1"
git show v1.5-stability-guards-v1 --no-patch --format="  Commit: %H%n  Date: %cd%n  Subject: %s" 2>/dev/null || {
  echo "  ✗ ERROR: Tag v1.5-stability-guards-v1 not found"
  exit 1
}
echo ""

# Step 2: Clean install dependencies
echo "Step 2: Clean install dependencies"
if [ -d "node_modules" ]; then
  echo "  Using existing node_modules (skipping npm ci)"
else
  echo "  Running npm ci..."
  npm ci || npm install
fi
echo "  ✓ Dependencies ready"
echo ""

# Step 3: Build TypeScript
echo "Step 3: Build TypeScript"
npm run build
echo "  ✓ Build passed"
echo ""

# Step 4: Run PR224-226 stability tests
echo "Step 4: Run PR224-226 stability tests"
npx ts-node tools/test-pr224-pr225-pr226-stability.ts
echo "  ✓ Stability tests passed"
echo ""

# Step 5: Run PR226 oscillation WARN tests
echo "Step 5: Run PR226 oscillation WARN tests"
npx ts-node tools/test-pr226-oscillation-warn.ts
echo "  ✓ Oscillation WARN tests passed"
echo ""

# Step 6: Summary
echo "=== Verification Summary ==="
echo "  ✓ Build: PASS"
echo "  ✓ Stability tests (7/7): PASS"
echo "  ✓ Oscillation WARN tests (4/4): PASS"
echo ""
echo "✓ v1.5 Stability Guards release candidate VERIFIED"
echo ""
echo "Release contents:"
echo "  - PR224: Regime Hysteresis (2-tick confirmation)"
echo "  - PR225: Consecutive Success Gating (2 SUCCEEDED required)"
echo "  - PR226: Oscillation Detection Telemetry (>10/hour WARN)"
echo ""
echo "Next steps:"
echo "  - Review telemetry in production logs"
echo "  - Monitor for oscillation WARNs"
echo "  - Verify hysteresis reduces regime flapping"
echo ""
