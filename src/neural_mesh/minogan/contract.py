"""Pydantic contract for the Minogan pilot Scorer interface ``minogan.scorer/v1`` (CP-0088 P0.2).

Field names are exactly the pilot's (``/workspace/minogan-pilot/src/shared/scorer.js`` + ``engine.js``).
Mesh additions live inside ``ScorerOutput.components`` (``docs/schema/minogan/scorer_components_mesh_v0.schema.json``).

Validation order (each step raises a typed :class:`ContractError` subclass):
1. body size ≤ 1 MB (when parsing bytes) → :class:`ContractLimitError`
2. ``contract == "minogan.scorer/v1"`` → :class:`ContractVersionError`
3. no prompt/completion/tool-content keys at any depth → :class:`ContentKeyError`
4. list limits (events ≤ 200, signals ≤ 200, trace_ids ≤ 10/signal, allowed_tools ≤ 200) → :class:`ContractLimitError`
5. strict pydantic models, unknown keys forbidden → :class:`ContractValidationError`
"""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    StrictStr,
)
from pydantic import ValidationError as _PydanticValidationError

CONTRACT_VERSION = "minogan.scorer/v1"
MAX_BODY_BYTES = 1_048_576
MAX_EVENTS = 200
MAX_SIGNALS = 200
MAX_TRACE_IDS_PER_SIGNAL = 10
MAX_ALLOWED_TOOLS = 200
MAX_CITED = 50

# Keys that would carry prompt / completion / tool-call content. The pilot drops these at ingest;
# Mesh refuses any input that still carries them (never stored, never scored).
CONTENT_KEYS = frozenset(
    {
        "prompt",
        "prompts",
        "completion",
        "completions",
        "messages",
        "content",
        "input_messages",
        "output_messages",
        "system_prompt",
        "tool_args",
        "tool_arguments",
        "tool_result",
        "arguments",
        "gen_ai.prompt",
        "gen_ai.completion",
        "gen_ai.input.messages",
        "gen_ai.output.messages",
        "gen_ai.system_instructions",
        "gen_ai.tool.call.arguments",
        "gen_ai.tool.call.result",
    }
)


# ----------------------------------------------------------------------------- errors


class ContractError(ValueError):
    """Base typed error for an invalid ScorerInput / ScorerOutput."""

    code = "contract"

    def __init__(self, message: str, *, path: str | None = None, errors: list[dict] | None = None):
        super().__init__(message)
        self.path = path
        self.errors = errors or []

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"code": self.code, "message": str(self)}
        if self.path:
            d["path"] = self.path
        if self.errors:
            d["errors"] = self.errors
        return d


class ContractVersionError(ContractError):
    code = "contract_version"


class ContentKeyError(ContractError):
    code = "content_key"


class ContractLimitError(ContractError):
    code = "limit"


class ContractValidationError(ContractError):
    code = "validation"


# ----------------------------------------------------------------------------- input models

_STRICT = ConfigDict(extra="forbid", strict=True, frozen=True)
Num = StrictInt | StrictFloat


class Window(BaseModel):
    model_config = _STRICT
    from_: StrictInt = Field(alias="from", ge=0)
    to: StrictInt = Field(ge=0)


class Agent(BaseModel):
    model_config = _STRICT
    id: StrictStr = Field(min_length=1, max_length=128)
    name: StrictStr | None = Field(max_length=256)
    function: StrictStr | None = Field(max_length=512)
    framework: StrictStr | None = Field(max_length=128)
    autonomy: StrictInt | None = Field(ge=0, le=100)
    data_sensitivity: StrictInt | None = Field(ge=0, le=100)
    criticality: StrictStr | None = Field(max_length=64)
    allowed_tools: list[StrictStr]


class Features(BaseModel):
    model_config = _STRICT
    distinctTools: StrictInt = Field(ge=0)
    writeTools: StrictInt = Field(ge=0)
    writes: StrictInt = Field(ge=0)
    approvedWrites: StrictInt = Field(ge=0)
    distinctModels: StrictInt = Field(ge=0)
    newTools24h: StrictInt = Field(ge=0)
    toolCalls24h: StrictInt = Field(ge=0)
    newToolCalls24h: StrictInt = Field(ge=0)
    hasBaseline: StrictBool
    recentSpans: StrictInt = Field(ge=0)
    recentErrors: StrictInt = Field(ge=0)
    baselineSpans: StrictInt = Field(ge=0)
    baselineErrors: StrictInt = Field(ge=0)


class Signal(BaseModel):
    model_config = _STRICT
    id: StrictStr = Field(min_length=1, max_length=128)
    type: StrictStr = Field(min_length=1, max_length=64)
    rule: StrictStr = Field(min_length=1, max_length=64)
    severity: Literal["info", "warn", "high"]
    title: StrictStr = Field(max_length=512)
    ts: StrictInt = Field(ge=0)
    pattern: StrictStr | None = Field(max_length=512)
    trace_ids: list[StrictStr]


class Event(BaseModel):
    """Normalized event row (metadata only). ``org_id``/``agent_id``/``rn`` are emitted by the pilot's
    events query (``engine.js``) beyond the documented list; accepted, not used for scoring."""

    model_config = _STRICT
    trace_id: StrictStr = Field(min_length=1, max_length=64)
    span_id: StrictStr = Field(min_length=1, max_length=64)
    type: StrictStr = Field(max_length=32)
    name: StrictStr | None = Field(default=None, max_length=256)
    tool: StrictStr | None = Field(default=None, max_length=128)
    model: StrictStr | None = Field(default=None, max_length=128)
    latency_ms: Num | None = Field(default=None, ge=0)
    status: StrictStr = Field(max_length=16)
    is_write: StrictInt | StrictBool
    human_approved: StrictInt | StrictBool
    destination: StrictStr | None = Field(default=None, max_length=256)
    out_bytes: StrictInt | None = Field(default=None, ge=0)
    ts: StrictInt = Field(ge=0)
    org_id: StrictStr | None = Field(default=None, max_length=128)
    agent_id: StrictStr | None = Field(default=None, max_length=128)
    rn: StrictInt | None = None


class ScorerInput(BaseModel):
    model_config = _STRICT
    contract: Literal["minogan.scorer/v1"]
    now: StrictInt = Field(ge=0)
    org_id: StrictStr = Field(min_length=1, max_length=128)
    window: Window
    agent: Agent
    features: Features
    signals: list[Signal]
    baseline_score: StrictInt | None = Field(ge=0, le=100)
    events: list[Event] | None = None

    @property
    def tenant_id(self) -> str:
        return self.org_id

    def trace_id_universe(self) -> set[str]:
        return {t for s in self.signals for t in s.trace_ids}

    def canonical_dict(self) -> dict[str, Any]:
        """Dict for the input digest: validated values, wire names, absent optionals omitted."""
        return self.model_dump(mode="python", by_alias=True, exclude_unset=True)


# ----------------------------------------------------------------------------- output models

_OUT = ConfigDict(extra="forbid", strict=True)
Outcome = Literal["bind", "bind-with-terms", "refer", "decline"]
DriftStatus = Literal["stable", "watch", "elevated", "critical"]


class Reason(BaseModel):
    model_config = _OUT
    code: StrictStr = Field(pattern=r"^[a-z][a-z0-9_.:-]{1,63}$")
    weight: Num
    evidence_trace_ids: list[StrictStr] = Field(max_length=10)


class UwClause(BaseModel):
    model_config = _OUT
    code: StrictStr = Field(pattern=r"^[A-Z][A-Z0-9_]{1,47}$")
    text: StrictStr = Field(min_length=1, max_length=280)
    evidence_trace_ids: list[StrictStr] = Field(default_factory=list, max_length=10)


class UwHint(BaseModel):
    model_config = _OUT
    outcome: Outcome
    conditions: list[UwClause] = Field(max_length=20)


class Advisory(BaseModel):
    model_config = _OUT
    judge: StrictStr
    text: StrictStr = Field(max_length=1000)
    affects_score: Literal[False] = False


class MeshComponents(BaseModel):
    """``ScorerOutput.components``: pilot-compatible free-form keys + required Mesh additions."""

    model_config = ConfigDict(extra="allow", strict=True)
    methodology: StrictStr
    formula: StrictStr
    explain: StrictStr = Field(max_length=500)
    confidence: Num = Field(ge=0, le=1)
    reasons: list[Reason] = Field(max_length=30)
    model_version: StrictStr = Field(pattern=r"^mesh\.minogan\.score/v[0-9]+(\.[0-9]+)*$")
    input_digest: StrictStr = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    uw: UwHint
    advisory: Advisory | None = None


class ScorerOutput(BaseModel):
    model_config = _OUT
    score: StrictInt = Field(ge=0, le=100)
    exposure: StrictInt = Field(ge=0, le=100)
    behavior: StrictInt = Field(ge=0, le=100)
    driftPct: Num
    driftStatus: DriftStatus
    axes: dict[StrictStr, Num]
    components: MeshComponents
    cited_trace_ids: list[StrictStr] = Field(max_length=MAX_CITED)
    methodology: StrictStr
    scorer: StrictStr


# ----------------------------------------------------------------------------- parsing


def _find_content_key(v: Any, path: str = "$") -> str | None:
    if isinstance(v, dict):
        for k, x in v.items():
            if isinstance(k, str) and k.lower() in CONTENT_KEYS:
                return f"{path}.{k}"
            hit = _find_content_key(x, f"{path}.{k}")
            if hit:
                return hit
    elif isinstance(v, (list, tuple)):
        for i, x in enumerate(v):
            hit = _find_content_key(x, f"{path}[{i}]")
            if hit:
                return hit
    return None


def _check_limits(raw: dict) -> None:
    def _len(x: Any) -> int:
        return len(x) if isinstance(x, (list, tuple)) else 0

    if _len(raw.get("events")) > MAX_EVENTS:
        raise ContractLimitError(f"events: {len(raw['events'])} > {MAX_EVENTS}", path="$.events")
    sigs = raw.get("signals")
    if _len(sigs) > MAX_SIGNALS:
        raise ContractLimitError(f"signals: {len(sigs)} > {MAX_SIGNALS}", path="$.signals")
    for i, s in enumerate(sigs if isinstance(sigs, list) else []):
        if isinstance(s, dict) and _len(s.get("trace_ids")) > MAX_TRACE_IDS_PER_SIGNAL:
            raise ContractLimitError(
                f"signals[{i}].trace_ids: {len(s['trace_ids'])} > {MAX_TRACE_IDS_PER_SIGNAL}",
                path=f"$.signals[{i}].trace_ids",
            )
    agent = raw.get("agent")
    if isinstance(agent, dict) and _len(agent.get("allowed_tools")) > MAX_ALLOWED_TOOLS:
        raise ContractLimitError("agent.allowed_tools too long", path="$.agent.allowed_tools")


def parse_scorer_input(data: bytes | str | dict) -> ScorerInput:
    """Validate a ScorerInput (bytes/str JSON or already-decoded dict). Raises a ContractError subclass."""
    if isinstance(data, (bytes, bytearray, str)):
        raw_bytes = data.encode("utf-8") if isinstance(data, str) else bytes(data)
        if len(raw_bytes) > MAX_BODY_BYTES:
            raise ContractLimitError(f"body {len(raw_bytes)} bytes > {MAX_BODY_BYTES}", path="$")
        try:
            data = json.loads(raw_bytes)
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            raise ContractValidationError(f"invalid JSON: {e}", path="$") from None
    if not isinstance(data, dict):
        raise ContractValidationError("ScorerInput must be a JSON object", path="$")
    if data.get("contract") != CONTRACT_VERSION:
        raise ContractVersionError(
            f"unsupported contract {data.get('contract')!r}; expected {CONTRACT_VERSION!r}", path="$.contract"
        )
    hit = _find_content_key(data)
    if hit:
        raise ContentKeyError(f"content key not allowed (metadata only): {hit}", path=hit)
    _check_limits(data)
    try:
        return ScorerInput.model_validate(data)
    except _PydanticValidationError as e:
        errs = [
            {"loc": ".".join(str(p) for p in err["loc"]), "type": err["type"], "msg": err["msg"]}
            for err in e.errors(include_url=False, include_input=False)
        ]
        first = errs[0]["loc"] if errs else "$"
        raise ContractValidationError(f"invalid ScorerInput ({len(errs)} error(s)); first at {first}", errors=errs, path=first) from None


def validate_scorer_output(out: dict, inp: ScorerInput) -> ScorerOutput:
    """Validate a Mesh ScorerOutput and the pilot guarantee ``cited_trace_ids ⊆ input trace ids``."""
    try:
        model = ScorerOutput.model_validate(out)
    except _PydanticValidationError as e:
        errs = [
            {"loc": ".".join(str(p) for p in err["loc"]), "type": err["type"], "msg": err["msg"]}
            for err in e.errors(include_url=False, include_input=False)
        ]
        raise ContractValidationError("invalid ScorerOutput", errors=errs) from None
    universe = inp.trace_id_universe()
    stray = [t for t in model.cited_trace_ids if t not in universe]
    if stray:
        raise ContractValidationError(f"cited_trace_ids not in input: {stray[:3]}", path="$.cited_trace_ids")
    for r in model.components.reasons:
        if any(t not in universe for t in r.evidence_trace_ids):
            raise ContractValidationError(f"reason {r.code} cites unknown trace", path="$.components.reasons")
    return model
