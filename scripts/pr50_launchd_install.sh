#!/usr/bin/env bash
#
# PR50: launchd Installation Helper for Daily Shadow Diff Pipeline
#
# Purpose:
#     Help users install com.meridian.pr49.daily.plist to launchd
#
# Usage:
#     cd ~/Meridian
#     bash scripts/pr50_launchd_install.sh
#
# What this script does:
#     1. Detect Meridian directory
#     2. Customize plist template with actual paths
#     3. Copy to ~/Library/LaunchAgents/
#     4. Load the job with launchctl
#
# Constitutional Constraints:
#     - READ-ONLY: Does not modify execution logic
#     - Warning-only: Continues on errors, provides instructions
#

set -e

echo "=========================================="
echo "PR50: launchd Installation Helper"
echo "=========================================="
echo ""

# Detect Meridian directory (assume script is in scripts/)
MERIDIAN_DIR="$(cd "$(dirname "$0")/.." && pwd)"
echo "Detected Meridian directory: $MERIDIAN_DIR"
echo ""

# Paths
TEMPLATE_PLIST="$MERIDIAN_DIR/scripts/com.meridian.pr49.daily.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
INSTALLED_PLIST="$LAUNCH_AGENTS_DIR/com.meridian.pr49.daily.plist"

# Check if template exists
if [ ! -f "$TEMPLATE_PLIST" ]; then
    echo "❌ Template plist not found: $TEMPLATE_PLIST"
    echo "   Make sure you're running this from the Meridian directory."
    exit 1
fi

# Check if virtualenv exists
if [ ! -f "$MERIDIAN_DIR/.venv/bin/python3" ]; then
    echo "⚠️  Warning: Virtualenv not found at $MERIDIAN_DIR/.venv"
    echo "   You may need to create it first with: python3 -m venv .venv"
    echo ""
fi

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$LAUNCH_AGENTS_DIR"

# Customize plist by replacing /path/to/meridian with actual path
echo "Customizing plist template..."
sed "s|/path/to/meridian|$MERIDIAN_DIR|g" "$TEMPLATE_PLIST" > "$INSTALLED_PLIST"
echo "✓ Installed plist to: $INSTALLED_PLIST"
echo ""

# Unload existing job (if any)
if launchctl list | grep -q "com.meridian.pr49.daily"; then
    echo "Unloading existing job..."
    launchctl unload "$INSTALLED_PLIST" 2>/dev/null || true
    echo "✓ Unloaded"
    echo ""
fi

# Load the job
echo "Loading job..."
launchctl load "$INSTALLED_PLIST"
echo "✓ Job loaded"
echo ""

# Verify
echo "=========================================="
echo "Installation Complete"
echo "=========================================="
echo ""
echo "Job details:"
launchctl list | grep "com.meridian.pr49.daily" || echo "  (Job not found - may take a moment to register)"
echo ""
echo "Schedule: Daily at 00:30 local time"
echo ""
echo "Logs:"
echo "  stdout: $MERIDIAN_DIR/logs/pr49_daily_stdout.log"
echo "  stderr: $MERIDIAN_DIR/logs/pr49_daily_stderr.log"
echo ""
echo "Manual commands:"
echo "  Unload:  launchctl unload $INSTALLED_PLIST"
echo "  Load:    launchctl load $INSTALLED_PLIST"
echo "  Remove:  rm $INSTALLED_PLIST"
echo "  Run now: launchctl start com.meridian.pr49.daily"
echo ""
echo "=========================================="
