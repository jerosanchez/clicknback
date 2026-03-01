#!/usr/bin/env bash
# Parses total coverage from coverage.txt (captured pytest-cov stdout) and
# prints an emoji-graded result. Exits non-zero if coverage is below 70%.
#
# Usage:
#   bash scripts/coverage-grade.sh              # reads coverage.txt
#   bash scripts/coverage-grade.sh <file>       # reads a custom file

set -euo pipefail

COVERAGE_FILE="${1:-coverage.txt}"

if [[ ! -f "$COVERAGE_FILE" ]]; then
    echo "Coverage file '$COVERAGE_FILE' not found. Run 'make coverage' first." >&2
    exit 1
fi

# Extract percentage from the TOTAL line, e.g.:
#   TOTAL    1234   123   90%
PCT=$(grep -E '^TOTAL' "$COVERAGE_FILE" | awk '{print $NF}' | tr -d '%')

if [[ -z "$PCT" ]]; then
    echo "Could not parse coverage percentage from '$COVERAGE_FILE'." >&2
    exit 1
fi

echo ""
echo "Coverage: ${PCT}%"
echo ""

if (( PCT < 50 )); then
    echo "❌  Poor — significant gaps, must improve"
    exit 1
elif (( PCT < 70 )); then
    echo "⚠️  Low — almost there, keep going"
    exit 1
elif (( PCT < 80 )); then
    echo "✅  Approved — minimum bar cleared"
elif (( PCT < 90 )); then
    echo "🌟  High — above expectations"
else
    echo "🚀  Excellent — outstanding coverage"
fi
