"""Mesh scorer v0 for Minogan (CP-0088 P0.3) — deterministic, LLM-free, zero network.

Parity target: pilot ``computeScore`` (``/workspace/minogan-pilot/src/shared/rules.js``, methodology ``score_v0.3``),
within ±1 on ``score``. Same validated input ⇒ byte-identical canonical output (no wall clock, no randomness:
the only time source is ``input.now``). L_judge never participates; ``components.advisory`` stays ``None`` here.

Mesh additions inside ``components``: ``confidence``, ``reasons``, ``model_version``, ``input_digest``, ``uw``.
UW outcome mirrors pilot ``uwOutcome`` (no ``decline`` until AgentMemory recurrence exists — P0.4).
"""

from __future__ import annotations

import math
from typing import Any

from neural_mesh.minogan.canonical import canonical_json, input_digest
from neural_mesh.minogan.contract import (
    MAX_CITED,
    ScorerInput,
    parse_scorer_input,
    validate_scorer_output,
)
from neural_mesh.minogan.memory import DAY_MS, recurrence_from_records

MODEL_VERSION = "mesh.minogan.score/v0"
PARITY_TARGET = "score_v0.3"
METHODOLOGY = f"{MODEL_VERSION}+{PARITY_TARGET}"
SCORER_ID = "mesh"

# Constants copied from the pilot RULES (score_v0.3). Any change ⇒ bump MODEL_VERSION.
SEVERITY_WEIGHT = {"info": 3, "warn": 12, "high": 30}
DECAY_HOURS = 48
CATEGORY_CAP = 40
REPEAT_FACTOR = 0.25
BEHAVIOR_FULL_SCALE = 240
HIGH_FLOOR_BASE = 37
HIGH_FLOOR_STEP = 8
HIGH_FLOOR_CAP = 85
HIGH_FLOOR_HOURS = 48
EXPOSURE_WEIGHT = 0.4
BEHAVIOR_WEIGHT = 0.6

FORMULA = (
    "score = max(round(0.4·exposure + 0.6·behavior), floor); floor = min(85, 37 + 8 × categories with an active high "
    "signal <48h old), 0 if none; exposure = mean(autonomy, toolSurface, dataSensitivity, 100−humanOversight, "
    "changeVelocity, taskDrift); behavior = 100 × Σ category points / 240, category points = min(40, strongest signal "
    "+ 25% of the others), signal points = severity weight (info 3, warn 12, high 30) × e^(−age_h/48), active signals "
    "of the last 7d (false positives and suppressed patterns excluded)"
)


def js_round(x: float) -> int:
    """JavaScript ``Math.round``: halves round toward +∞ (Python ``round`` is banker's)."""
    return math.floor(x + 0.5)


def clamp(x: float) -> int:
    return max(0, min(100, js_round(x)))


def r1(x: float) -> float:
    return js_round(x * 10) / 10


def r3(x: float) -> float:
    return js_round(x * 1000) / 1000


def uw_outcome(score: int) -> str:
    """Pilot ``uwOutcome`` (rules.js). ``decline`` is never produced by v0."""
    return "bind" if score < 40 else "bind-with-terms" if score < 65 else "refer"


def _slug(s: str) -> str:
    out = "".join(c if c.isalnum() or c in "-_." else "_" for c in s.lower())
    return out[:48] or "x"


def _confidence(inp: ScorerInput) -> float:
    f = inp.features
    return r3(0.5 * min(1.0, f.baselineSpans / 200) + 0.3 * min(1.0, f.recentSpans / 50) + 0.2 * (1 if f.hasBaseline else 0))


def _cited(inp: ScorerInput) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for s in inp.signals:
        for t in s.trace_ids:
            if len(out) >= MAX_CITED:
                return out
            if t not in seen:
                seen.add(t)
                out.append(t)
    return out


def _uw_conditions(inp: ScorerInput, outcome: str) -> list[dict[str, Any]]:
    if outcome == "bind":
        return []
    f = inp.features

    def traces(sig_type: str) -> list[str]:
        ids: list[str] = []
        for s in inp.signals:
            if s.type == sig_type:
                for t in s.trace_ids:
                    if t not in ids and len(ids) < 10:
                        ids.append(t)
        return ids

    conds: list[dict[str, Any]] = []
    if f.writes > 0 and f.approvedWrites < f.writes:
        conds.append({"code": "HUMAN_APPROVAL_WRITES", "text": "Human approval required for write actions", "evidence_trace_ids": []})
    for code, sig_type, text in (
        ("TOOL_ALLOWLIST_ENFORCED", "policy violation", "Enforce the tool allow-list (calls outside it observed)"),
        ("OUTBOUND_DLP", "data exfil pattern", "Outbound DLP on external/write tools"),
        ("INJECTION_GUARDRAIL", "prompt injection attempt", "Prompt-injection guardrail on inputs and tool results"),
    ):
        ids = traces(sig_type)
        if ids:
            conds.append({"code": code, "text": text, "evidence_trace_ids": ids})
    if f.distinctModels > 1 or f.newTools24h > 0:
        conds.append({"code": "CHANGE_CONTROL_MODELS", "text": "Change control for model / tool changes", "evidence_trace_ids": []})
    return conds


def score_input(inp: ScorerInput) -> dict[str, Any]:
    """Score one validated ScorerInput. Pure function of ``inp``."""
    f, a = inp.features, inp.agent
    autonomy = 50 if a.autonomy is None else a.autonomy
    sensitivity = 50 if a.data_sensitivity is None else a.data_sensitivity
    axes = {
        "autonomy": clamp(autonomy),
        "toolSurface": clamp(f.distinctTools * 10 + f.writeTools * 15),
        "dataSensitivity": clamp(sensitivity),
        "humanOversight": clamp((f.approvedWrites / f.writes) * 100) if f.writes > 0 else 50,
        "changeVelocity": clamp(max(0, f.distinctModels - 1) * 25 + f.newTools24h * 15),
        "taskDrift": clamp((f.newToolCalls24h / f.toolCalls24h) * 100) if f.hasBaseline and f.toolCalls24h > 0 else 0,
    }
    exposure_raw = (
        axes["autonomy"] + axes["toolSurface"] + axes["dataSensitivity"] + (100 - axes["humanOversight"])
        + axes["changeVelocity"] + axes["taskDrift"]
    ) / 6
    exposure = clamp(exposure_raw)

    contribs: list[dict[str, Any]] = []
    for s in inp.signals:
        age_h = max(0.0, (inp.now - s.ts) / 3600000)
        pts = SEVERITY_WEIGHT[s.severity] * math.exp(-age_h / DECAY_HOURS)
        contribs.append({
            "id": s.id, "type": s.type, "rule": s.rule, "severity": s.severity, "title": s.title,
            "age_h": r1(age_h), "raw_points": r1(pts), "_pts": pts, "trace_ids": list(s.trace_ids[:5]),
            "_all_traces": list(s.trace_ids),
        })
    contribs.sort(key=lambda c: -c["_pts"])  # stable, like V8 Array.prototype.sort

    cats: dict[str, dict[str, Any]] = {}
    for c in contribs:
        k = cats.setdefault(c["type"], {"raw": 0.0, "top": 0.0, "rest": 0.0, "n": 0, "traces": []})
        if k["n"] == 0:
            k["top"] = c["_pts"]
            c["counted"] = 1
        else:
            k["rest"] += c["_pts"]
            c["counted"] = REPEAT_FACTOR
        k["raw"] += c["_pts"]
        k["n"] += 1
        for t in c["_all_traces"]:
            if t not in k["traces"] and len(k["traces"]) < 10:
                k["traces"].append(t)
    by_category: dict[str, Any] = {}
    cat_points: dict[str, float] = {}
    total = 0.0
    for t, k in cats.items():
        uncapped = k["top"] + REPEAT_FACTOR * k["rest"]
        pts = min(CATEGORY_CAP, uncapped)
        total += pts
        cat_points[t] = pts
        by_category[t] = {"points": r1(pts), "signals": k["n"], "raw_points": r1(k["raw"]), "capped": uncapped > CATEGORY_CAP}
    behavior = clamp((total / BEHAVIOR_FULL_SCALE) * 100)
    blended = clamp(EXPOSURE_WEIGHT * exposure + BEHAVIOR_WEIGHT * behavior)
    high_cats: list[str] = []
    for c in contribs:
        if c["severity"] == "high" and c["age_h"] < HIGH_FLOOR_HOURS and c["type"] not in high_cats:
            high_cats.append(c["type"])
    floor_value = min(HIGH_FLOOR_CAP, HIGH_FLOOR_BASE + HIGH_FLOOR_STEP * len(high_cats)) if high_cats else 0
    floor_applied = floor_value > blended
    score = floor_value if floor_applied else blended

    quiet = clamp(EXPOSURE_WEIGHT * exposure)
    base = inp.baseline_score if inp.baseline_score is not None else quiet
    drift_pct = js_round(((score - base) / max(base, 1)) * 1000) / 10
    drift_status = "stable" if drift_pct < 10 else "watch" if drift_pct < 25 else "elevated" if drift_pct < 50 else "critical"

    n_cat = len(by_category)
    if not inp.signals:
        explain = f"{score} = exposure {exposure}×0.4 (no behavior signals in 7d)"
    else:
        head = (
            f"severity floor {floor_value} for {len(high_cats)} high categor{'y' if len(high_cats) == 1 else 'ies'} (blend {blended})"
            if floor_applied
            else f"exposure {exposure}×0.4 + behavior {behavior}×0.6"
        )
        explain = f"{score} = {head} · {n_cat} signal categor{'y' if n_cat == 1 else 'ies'} · top: {contribs[0]['title']}"

    # reasons: signed point attributions; Σ weight ≈ score (before integer rounding)
    reasons: list[dict[str, Any]] = []
    for axis in ("autonomy", "toolSurface", "dataSensitivity", "humanOversight", "changeVelocity", "taskDrift"):
        v = 100 - axes[axis] if axis == "humanOversight" else axes[axis]
        w = r3(EXPOSURE_WEIGHT * v / 6)
        if w:
            reasons.append({"code": f"exposure.{_slug(axis)}", "weight": w, "evidence_trace_ids": []})
    for t, pts in cat_points.items():
        w = r3(BEHAVIOR_WEIGHT * 100 * pts / BEHAVIOR_FULL_SCALE)
        if w:
            reasons.append({"code": f"behavior.{_slug(t)}", "weight": w, "evidence_trace_ids": cats[t]["traces"]})
    if floor_applied:
        fl: list[str] = []
        for t in high_cats:
            for x in cats[t]["traces"]:
                if x not in fl and len(fl) < 10:
                    fl.append(x)
        reasons.append({"code": "floor.high_severity", "weight": r3(floor_value - (EXPOSURE_WEIGHT * exposure + BEHAVIOR_WEIGHT * behavior)), "evidence_trace_ids": fl})

    outcome = uw_outcome(score)
    pub_contribs = [{k: v for k, v in c.items() if not k.startswith("_")} for c in contribs[:15]]
    components = {
        "methodology": METHODOLOGY,
        "parity_target": PARITY_TARGET,
        "formula": FORMULA,
        "exposure": {"value": exposure, "weight": EXPOSURE_WEIGHT, "contribution": r1(exposure * EXPOSURE_WEIGHT), "axes": axes},
        "behavior": {
            "value": behavior, "weight": BEHAVIOR_WEIGHT, "contribution": r1(behavior * BEHAVIOR_WEIGHT),
            "points_total": r1(total), "full_scale": BEHAVIOR_FULL_SCALE,
            "by_signal_type": {t: c["points"] for t, c in by_category.items()}, "by_category": by_category,
            "signals": pub_contribs,
        },
        "floor": {"applied": floor_applied, "value": floor_value, "blended": blended, "high_categories": high_cats,
                  "rule": "min(85, 37 + 8 × high categories <48h)"},
        "drift": {
            "baseline_score": base,
            "baseline_source": "quiet score (no 24h+ history yet)" if inp.baseline_score is None else "mean of score snapshots 24h–7d old",
            "drift_pct": drift_pct, "status": drift_status,
        },
        "explain": explain[:500],
        "confidence": _confidence(inp),
        "reasons": reasons[:30],
        "model_version": MODEL_VERSION,
        "input_digest": input_digest(inp.canonical_dict()),
        "uw": {"outcome": outcome, "conditions": _uw_conditions(inp, outcome)},
        "advisory": None,
    }
    return {
        "score": score, "exposure": exposure, "behavior": behavior, "driftPct": drift_pct, "driftStatus": drift_status,
        "axes": axes, "components": components, "cited_trace_ids": _cited(inp),
        "methodology": METHODOLOGY, "scorer": SCORER_ID,
    }


LONG_HORIZON_DAYS = 90
RECURRENCE_DAYS = 30
DECLINE_TYPES = ("data exfil pattern", "prompt injection attempt")
DECLINE_MIN_SCORE = 85  # tier T4
DECLINE_MIN_CONFIDENCE = 0.6
DECLINE_MIN_DAYS = 2


def _drift_status(p: float) -> str:
    return "stable" if p < 10 else "watch" if p < 25 else "elevated" if p < 50 else "critical"


def apply_memory(inp: ScorerInput, out: dict[str, Any], memory: Any) -> dict[str, Any]:
    """Long-horizon drift + recurrence from AgentMemory (read-only, records with ts ≤ input.now only).

    Never changes ``score``/``driftPct``/``driftStatus``. May turn ``uw.outcome`` into ``decline`` per uw_v0 §3 rule 4.
    """
    now, tenant, agent = inp.now, inp.org_id, inp.agent.id
    recs = memory.history(tenant, agent, now - LONG_HORIZON_DAYS * DAY_MS, now)
    c = out["components"]
    # long-horizon baseline: scores older than the pilot's 7-day window, up to 90 days back
    older = [r for r in recs if r.get("kind") == "score" and r["ts"] < inp.window.from_]
    if older:
        mean = sum(r["score"] for r in older) / len(older)
        dp = js_round(((out["score"] - mean) / max(mean, 1)) * 1000) / 10
        c["drift_long"] = {"window_days": LONG_HORIZON_DAYS, "excludes": "pilot 7d window", "n": len(older),
                           "baseline_mean": r1(mean), "drift_pct": dp, "status": _drift_status(dp),
                           "memory_from": older[0]["ts"]}
    else:
        c["drift_long"] = {"window_days": LONG_HORIZON_DAYS, "excludes": "pilot 7d window", "n": 0,
                           "baseline_mean": None, "drift_pct": None, "status": None, "memory_from": None}
    cur = [{"id": s.id, "rule": s.rule, "severity": s.severity, "ts": s.ts} for s in inp.signals]
    rules = sorted({(s.rule, s.type) for s in inp.signals})
    rec_list = []
    for rule, typ in rules:
        rr = recurrence_from_records(recs, rule, RECURRENCE_DAYS, now, extra_signals=cur)
        rh = recurrence_from_records(recs, rule, RECURRENCE_DAYS, now, severity="high", extra_signals=cur)
        rec_list.append({"rule": rule, "type": typ, "days": RECURRENCE_DAYS, "occurrences": rr["occurrences"],
                         "distinct_days": rr["distinct_days"], "high_distinct_days": rh["distinct_days"]})
    c["recurrence"] = rec_list
    basis = [r for r in rec_list if r["type"] in DECLINE_TYPES and r["high_distinct_days"] >= DECLINE_MIN_DAYS]
    if out["score"] >= DECLINE_MIN_SCORE and c["confidence"] >= DECLINE_MIN_CONFIDENCE and basis:
        c["uw"] = {"outcome": "decline", "conditions": _uw_conditions(inp, "decline")}
        c["decline_basis"] = {"rule": "uw_v0 §3.4", "recurrence": basis, "min_score": DECLINE_MIN_SCORE,
                              "min_confidence": DECLINE_MIN_CONFIDENCE}
    return out


def score(data: Any, memory: Any = None) -> dict[str, Any]:
    """Validate (typed ContractError on bad input), score, and self-check the output contract.

    ``memory`` (an AgentMemory) is optional; without it the output is the parity path, byte-for-byte.
    """
    inp = data if isinstance(data, ScorerInput) else parse_scorer_input(data)
    out = score_input(inp)
    if memory is not None:
        apply_memory(inp, out, memory)
    validate_scorer_output(out, inp)
    return out


def score_bytes(data: Any, memory: Any = None) -> bytes:
    """Canonical JSON bytes of the ScorerOutput (byte-identical for identical input and memory state)."""
    return canonical_json(score(data, memory))


class MeshScorer:
    """Mirror of the pilot Scorer interface (``id``, ``methodology``, ``needs``, ``score``)."""

    id = SCORER_ID
    methodology = METHODOLOGY
    needs: tuple[str, ...] = ()

    def __init__(self, memory: Any = None, ledger: Any = None):
        self.memory = memory
        self.ledger = ledger  # optional ScoreLedger (P0.6): every scoring recorded + replayable

    def score(self, data: Any) -> dict[str, Any]:
        if self.ledger is None:
            return score(data, self.memory)
        from neural_mesh.minogan.ledger import (
            record_scoring,  # local: ledger imports this module
        )

        inp = data if isinstance(data, ScorerInput) else parse_scorer_input(data)
        return record_scoring(inp, self.memory, self.ledger)[0]
