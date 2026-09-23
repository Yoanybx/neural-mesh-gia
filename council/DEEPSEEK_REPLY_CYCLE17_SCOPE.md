M2M_v1
DIR: ACK
CYCLE: 17
CP: CP-0021
TITLE: Add floor checkpoint tag invariant
SCOPE: tags
P0: Define tag schema CHECKPOINT@floor:<n> in docs/debt/CHECKPOINT_EVERY_FLOOR.md
P1: Add validator requiring one checkpoint tag per floor
P2: Wire validator into existing tag test suite
P3: Close debt only after validator passes
PYTEST_MIN: pytest -q tests/test_tags.py -k checkpoint_every_floor
VER_NEXT: 0.14.3
BOUNDS: DeepSeek-only; Search=OFF; inline-only; no new deps; no network; no Raft/N>2/ML
ACCEPT: schema documented; floor fixture validates; debt status updated; pytest_min green
NO: no SLO chase; no refactor outside tags; no broad checkpoint system
CYCLE_NEXT: 18
CP_NEXT: CP-0022