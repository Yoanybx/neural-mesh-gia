#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate
python -m pip install -e '.[distributed,ml,telemetry]'
