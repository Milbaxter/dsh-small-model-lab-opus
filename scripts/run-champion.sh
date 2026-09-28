#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORKSPACE="$(cd "$1" && pwd)"
PROMPT="$2"
STATE="$(mktemp -d)"
trap 'rm -rf "$STATE"' EXIT
RUN_ID="champion-$(date +%s)-$(python3 -c 'import uuid; print(uuid.uuid4().hex[:8])')-0"
python3 -c 'import json,sys; print(json.dumps({"session":"champion","prompt":sys.argv[1]}))' "$PROMPT" |
  docker run --rm -i --user "$(id -u):$(id -g)" --cpus 1.5 --memory 768m --pids-limit 128 \
    --cap-drop ALL --security-opt no-new-privileges --read-only --tmpfs /tmp:rw,size=128m \
    -v "$WORKSPACE:/workspace" -v "$STATE:/home/lab" -v "$ROOT/champion:/profile:ro" \
    -e HOME=/home/lab -e XDG_CACHE_HOME=/home/lab/.cache -e LAB_ARM=standard -e "LAB_RUN_KEY=$RUN_ID" \
    -e "LAB_GATEWAY=${LAB_GATEWAY:-http://172.17.0.1:18943/v1}" dsh-opus:0.1.5rc1 |
  python3 "$ROOT/scripts/display_result.py"
