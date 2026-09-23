#!/usr/bin/env bash
set -euo pipefail
test -f .project_state/CHECKPOINT.json
test -f .project_state/CURRENT_STATE.md
test -f .project_state/NEXT_ACTION.md
test -d obsidian/Neural-Mesh-Vault
pytest -q
mesh status
mesh checkpoint latest
echo 'AUDIT PASS'
