# Consejo Ciclo 17 — CP-0021 floor checkpoint tag invariant (DeepSeek M2M)

TITLE: Add floor checkpoint tag invariant
VER: 0.14.3 | CP-0021

P0 Define tag schema CHECKPOINT@floor:<n> in docs/debt/CHECKPOINT_EVERY_FLOOR.md
P1 Validator requiring one checkpoint tag per floor
P2 Wire into tag test suite (tests/test_tags.py -k checkpoint_every_floor; create if missing)
P3 Close/update debt status only after validator passes
ACCEPT: schema documented; floor fixture validates; debt status updated; pytest_min green
NO: SLO chase; refactor outside tags; broad checkpoint system; Raft/N>2/ML; new deps; network
