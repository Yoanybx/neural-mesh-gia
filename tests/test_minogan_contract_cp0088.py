"""CP-0088 P0.2 — minogan.scorer/v1 contract (pydantic) + canonical JSON / input_digest.

Fixtures: tests/fixtures/minogan/*.json, frozen by scripts/minogan/gen_fixtures.mjs from the REAL pilot pipeline
(synthetic.mjs -> ingest -> scoreAgents in a throw-away /tmp copy; seeded PRNG + fake clock). Metadata only.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from neural_mesh.minogan import (
    CONTRACT_VERSION,
    ContentKeyError,
    ContractError,
    ContractLimitError,
    ContractValidationError,
    ContractVersionError,
    canonical_json,
    input_digest,
    parse_scorer_input,
)
from neural_mesh.minogan.canonical import CanonicalError

pytestmark = pytest.mark.minogan_cp0088

FX_DIR = Path(__file__).parent / "fixtures" / "minogan"
FIXTURES = json.loads((FX_DIR / "scorer_v1_fixtures.json").read_text(encoding="utf-8"))
INVALID = json.loads((FX_DIR / "scorer_v1_invalid.json").read_text(encoding="utf-8"))
ERR_BY_CODE = {
    "contract_version": ContractVersionError,
    "validation": ContractValidationError,
    "content_key": ContentKeyError,
    "limit": ContractLimitError,
}


def test_fixture_meta_and_volume():
    meta = FIXTURES["meta"]
    assert meta["contract"] == CONTRACT_VERSION
    assert meta["pilot_methodology"] == "score_v0.3"
    assert meta["pilot_version"]  # git sha or 'pilot unversioned at capture time'
    assert len(FIXTURES["fixtures"]) == meta["count"] >= 50
    assert meta["pipeline_captures"] >= 50  # ≥50 straight from the pilot pipeline (not variants)
    assert any("events" in f["input"] for f in FIXTURES["fixtures"])


def test_all_fixtures_validate():
    for f in FIXTURES["fixtures"]:
        m = parse_scorer_input(f["input"])
        assert m.contract == CONTRACT_VERSION
        assert m.tenant_id == f["input"]["org_id"]


def test_input_digest_matches_js_canonical_sha256():
    # generator hashed the same canonical form in JS; cross-language equality pins the canonicalisation
    for f in FIXTURES["fixtures"]:
        m = parse_scorer_input(f["input"])
        assert input_digest(m.canonical_dict()) == "sha256:" + f["input_sha256"], f["id"]


def test_parse_from_bytes_and_str_equivalent():
    f = FIXTURES["fixtures"][0]["input"]
    raw = json.dumps(f).encode()
    a, b, c = parse_scorer_input(raw), parse_scorer_input(raw.decode()), parse_scorer_input(f)
    assert a == b == c


@pytest.mark.parametrize("case", INVALID["cases"], ids=lambda c: c["code"])
def test_invalid_fixtures_raise_typed_errors(case):
    with pytest.raises(ERR_BY_CODE[case["code"]]) as ei:
        parse_scorer_input(case["input"])
    assert isinstance(ei.value, ContractError)
    assert ei.value.code == case["code"]
    assert ei.value.to_dict()["code"] == case["code"]


def test_invalid_case_coverage():
    assert {c["code"] for c in INVALID["cases"]} == set(ERR_BY_CODE)


def test_body_over_1mb_is_limit_error():
    with pytest.raises(ContractLimitError):
        parse_scorer_input(b" " * (1_048_576 + 1))


def test_bad_json_and_non_object_are_validation_errors():
    with pytest.raises(ContractValidationError):
        parse_scorer_input(b"{not json")
    with pytest.raises(ContractValidationError):
        parse_scorer_input([1, 2])  # type: ignore[arg-type]


def test_strict_types_no_coercion():
    i = copy.deepcopy(FIXTURES["fixtures"][0]["input"])
    i["features"]["hasBaseline"] = 1  # int is not bool
    with pytest.raises(ContractValidationError):
        parse_scorer_input(i)
    i = copy.deepcopy(FIXTURES["fixtures"][0]["input"])
    i["now"] = 1.5
    with pytest.raises(ContractValidationError):
        parse_scorer_input(i)


def test_content_key_case_insensitive_any_depth():
    i = copy.deepcopy(FIXTURES["fixtures"][0]["input"])
    i["agent"]["Prompt"] = "x"
    with pytest.raises(ContentKeyError) as ei:
        parse_scorer_input(i)
    assert ei.value.path == "$.agent.Prompt"


def test_absent_events_differs_from_empty_events():
    i = copy.deepcopy(next(f for f in FIXTURES["fixtures"] if "events" not in f["input"])["input"])
    d0 = input_digest(parse_scorer_input(i).canonical_dict())
    i["events"] = []
    assert input_digest(parse_scorer_input(i).canonical_dict()) != d0


def test_fixtures_carry_no_content():
    blob = (FX_DIR / "scorer_v1_fixtures.json").read_text(encoding="utf-8")
    for bad in ("SYNTHETIC prompt", "IGNORE ALL", "jane.doe", "4111 1111", "123-45-6789", "gen_ai.input.messages"):
        assert bad not in blob


# ---------------------------------------------------------------- canonical JSON

JS_NUMBERS = [  # value -> JSON.stringify(value) in Node v20
    (0.0, "0"), (-0.0, "0"), (1.0, "1"), (1.5, "1.5"), (-2.25, "-2.25"), (0.1, "0.1"), (0.000001, "0.000001"),
    (1e-7, "1e-7"), (123456789012345680000.0, "123456789012345680000"), (1e21, "1e+21"), (1.5e22, "1.5e+22"),
    (33.3, "33.3"), (0.30000000000000004, "0.30000000000000004"), (5e-324, "5e-324"),
    (1.7976931348623157e308, "1.7976931348623157e+308"), (1e16, "10000000000000000"), (-1e-10, "-1e-10"), (48.8, "48.8"),
]


@pytest.mark.parametrize("value,js", JS_NUMBERS)
def test_numbers_match_js(value, js):
    assert canonical_json(value) == js.encode()


def test_canonical_sorted_compact_utf8():
    assert canonical_json({"b": 1, "a": [True, None, "·"], "A": {}}) == '{"A":{},"a":[true,null,"·"],"b":1}'.encode()


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), {1: "x"}, {"a": {1, 2}}])
def test_canonical_rejects(bad):
    with pytest.raises(CanonicalError):
        canonical_json(bad)
