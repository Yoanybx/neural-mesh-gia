"""Canonical JSON for Minogan digests and byte-identical scorer output (CP-0088).

Rules (docs/schema/minogan/scorer_contract_v1_mapping.md §4, RFC 8785 / JCS-compatible for our data):
- UTF-8, no whitespace, separators ``,`` and ``:``.
- Object keys sorted by UTF-16 code units (same as JS ``Array.prototype.sort`` on strings).
- Numbers formatted like ECMAScript ``Number::toString`` (``1`` not ``1.0``; ``1e-7`` not ``1e-07``).
- NaN / ±Infinity rejected. ``None`` → ``null``. Tuples serialised as arrays.
- Strings escaped like ``JSON.stringify`` (``json.dumps(ensure_ascii=False)`` matches for well-formed text).
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any


class CanonicalError(ValueError):
    """Value cannot be canonicalised (NaN/Inf, non-string key, unsupported type)."""


def _es_number(x: float) -> str:
    """ECMAScript Number::toString for a finite float (shortest round-trip digits)."""
    if x == 0:
        return "0"
    if x < 0:
        return "-" + _es_number(-x)
    r = repr(x)  # shortest round-trip, e.g. '1e-07', '12.5', '1e+16'
    if "e" in r:
        mant, exp_s = r.split("e")
        exp = int(exp_s)
    else:
        mant, exp = r, 0
    if "." in mant:
        int_part, frac = mant.split(".")
    else:
        int_part, frac = mant, ""
    digits = (int_part + frac).lstrip("0")
    # value = 0.int_part frac × 10^(len(int_part)+exp) before stripping leading zeros
    n = len(int_part) + exp
    lead = len(int_part + frac) - len((int_part + frac).lstrip("0"))
    n -= lead
    digits = digits.rstrip("0") or "0"
    k = len(digits)
    if k <= n <= 21:
        return digits + "0" * (n - k)
    if 0 < n <= 21:
        return digits[:n] + "." + digits[n:]
    if -6 < n <= 0:
        return "0." + "0" * (-n) + digits
    e = n - 1
    sign = "+" if e >= 0 else "-"
    head = digits[0] if k == 1 else digits[0] + "." + digits[1:]
    return f"{head}e{sign}{abs(e)}"


def _num(v: float) -> str:
    if isinstance(v, bool):  # pragma: no cover - guarded by caller
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if not math.isfinite(v):
        raise CanonicalError(f"non-finite number not allowed: {v!r}")
    return _es_number(v)


def _utf16_key(s: str) -> bytes:
    return s.encode("utf-16-be", "surrogatepass")


def _enc(v: Any, out: list[str]) -> None:
    if v is None:
        out.append("null")
    elif v is True:
        out.append("true")
    elif v is False:
        out.append("false")
    elif isinstance(v, (int, float)):
        out.append(_num(v))
    elif isinstance(v, str):
        out.append(json.dumps(v, ensure_ascii=False))
    elif isinstance(v, dict):
        for k in v:
            if not isinstance(k, str):
                raise CanonicalError(f"object key must be str, got {type(k).__name__}")
        out.append("{")
        first = True
        for k in sorted(v, key=_utf16_key):
            if not first:
                out.append(",")
            first = False
            out.append(json.dumps(k, ensure_ascii=False))
            out.append(":")
            _enc(v[k], out)
        out.append("}")
    elif isinstance(v, (list, tuple)):
        out.append("[")
        for i, item in enumerate(v):
            if i:
                out.append(",")
            _enc(item, out)
        out.append("]")
    else:
        raise CanonicalError(f"unsupported type for canonical JSON: {type(v).__name__}")


def canonical_json(value: Any) -> bytes:
    """Canonical UTF-8 JSON bytes for ``value``."""
    out: list[str] = []
    _enc(value, out)
    return "".join(out).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def input_digest(value: Any) -> str:
    """``sha256:<hex64>`` over the canonical JSON of a (validated) ScorerInput."""
    return "sha256:" + sha256_hex(canonical_json(value))
