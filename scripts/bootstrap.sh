#!/usr/bin/env bash
set -euo pipefail
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e '.[dev]'
mesh init
pytest -q
mesh checkpoint create --phase 0 --module bootstrap --reason bootstrap --next 'Implement next phase'
mesh resume
