#!/usr/bin/env bash
set -euo pipefail
# Run on the prepared UpCloud host; argument 1 is another side's profile directory.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROFILE="$(cd "$1" && pwd)"
BANK="${TASK_BANK:-/opt/dsh-tasks-opus/bank.json}"
exec python3 "$ROOT/scripts/background.py" --bank "$BANK" --sweep "${SWEEP_NAME:-cross-eval}" --split held-out --arms standard external --external-profile "$PROFILE" --k 5 --workers 2
