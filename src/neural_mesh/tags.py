"""Floor checkpoint tag schema and invariant validator (CP-0021 / Cycle 17).

Schema
------
Canonical tag form::

    CHECKPOINT@floor:<n>

where ``<n>`` is a non-negative integer floor id.

Invariant
---------
For each declared floor ``n``, exactly one tag ``CHECKPOINT@floor:<n>`` must
be present in the tag set (no missing, no duplicates).

Scope is tags-only — not a broad checkpoint rewrite and not an SLO chase.
"""

from __future__ import annotations

import re
from typing import Iterable, Mapping, Sequence

FLOOR_CHECKPOINT_PREFIX = "CHECKPOINT@floor:"
FLOOR_CHECKPOINT_RE = re.compile(r"^CHECKPOINT@floor:(\d+)$")

__all__ = [
    "FLOOR_CHECKPOINT_PREFIX",
    "FLOOR_CHECKPOINT_RE",
    "FloorCheckpointTagError",
    "TagError",
    "is_floor_checkpoint_tag",
    "make_floor_checkpoint_tag",
    "parse_floor_checkpoint_tag",
    "validate_one_checkpoint_tag_per_floor",
]


class TagError(ValueError):
    """Base error for tag schema / invariant failures."""


class FloorCheckpointTagError(TagError):
    """Raised when the one-checkpoint-tag-per-floor invariant fails."""


def make_floor_checkpoint_tag(floor: int) -> str:
    """Return canonical ``CHECKPOINT@floor:<n>`` for a non-negative floor id."""
    if not isinstance(floor, int) or isinstance(floor, bool):
        raise FloorCheckpointTagError(f"floor must be int, got {type(floor).__name__}")
    if floor < 0:
        raise FloorCheckpointTagError(f"floor must be >= 0, got {floor}")
    return f"{FLOOR_CHECKPOINT_PREFIX}{floor}"


def is_floor_checkpoint_tag(tag: str) -> bool:
    """True iff ``tag`` matches ``CHECKPOINT@floor:<n>`` exactly."""
    return isinstance(tag, str) and FLOOR_CHECKPOINT_RE.fullmatch(tag) is not None


def parse_floor_checkpoint_tag(tag: str) -> int:
    """Parse floor number from a floor-checkpoint tag; raise if invalid."""
    if not isinstance(tag, str):
        raise FloorCheckpointTagError(f"tag must be str, got {type(tag).__name__}")
    m = FLOOR_CHECKPOINT_RE.fullmatch(tag)
    if m is None:
        raise FloorCheckpointTagError(
            f"invalid floor checkpoint tag: {tag!r} "
            f"(expected {FLOOR_CHECKPOINT_PREFIX}<n>)"
        )
    return int(m.group(1))


def validate_one_checkpoint_tag_per_floor(
    tags: Iterable[str],
    floors: Sequence[int] | None = None,
) -> Mapping[str, object]:
    """Require exactly one ``CHECKPOINT@floor:<n>`` tag per declared floor.

    Parameters
    ----------
    tags:
        Tag strings to inspect. Non-floor-checkpoint tags are ignored for the
        count but must be strings.
    floors:
        Required floor ids. If omitted, floors are inferred from matching tags
        present (still enforces uniqueness / well-formedness).

    Returns
    -------
    dict
        ``{"ok": True, "floors": {n: "CHECKPOINT@floor:n", ...}, "schema": ...}``

    Raises
    ------
    FloorCheckpointTagError
        On missing tag, duplicate tag, or malformed floor-checkpoint tag.
    """
    tag_list = list(tags)
    for t in tag_list:
        if not isinstance(t, str):
            raise FloorCheckpointTagError(f"tag must be str, got {type(t).__name__}")

    by_floor: dict[int, list[str]] = {}
    for t in tag_list:
        if not t.startswith(FLOOR_CHECKPOINT_PREFIX) and not is_floor_checkpoint_tag(t):
            # Ignore unrelated tags.
            continue
        # Anything that looks like our prefix must be well-formed.
        n = parse_floor_checkpoint_tag(t)
        by_floor.setdefault(n, []).append(t)

    if floors is None:
        required = sorted(by_floor.keys())
    else:
        required = []
        for f in floors:
            if not isinstance(f, int) or isinstance(f, bool) or f < 0:
                raise FloorCheckpointTagError(f"invalid floor id: {f!r}")
            required.append(f)
        # Stable unique order preserving first occurrence.
        seen: set[int] = set()
        uniq: list[int] = []
        for f in required:
            if f not in seen:
                seen.add(f)
                uniq.append(f)
        required = uniq

    missing: list[int] = []
    duplicates: dict[int, list[str]] = {}
    mapping: dict[int, str] = {}

    for n in required:
        found = by_floor.get(n, [])
        if len(found) == 0:
            missing.append(n)
        elif len(found) > 1:
            duplicates[n] = found
        else:
            mapping[n] = found[0]

    # Also reject duplicate tags for floors not in required when floors was given
    # (extra well-formed tags for other floors are allowed; duplicates of any
    # floor-checkpoint tag are never allowed).
    for n, found in by_floor.items():
        if len(found) > 1 and n not in duplicates:
            duplicates[n] = found

    if missing or duplicates:
        parts: list[str] = []
        if missing:
            parts.append(
                "missing checkpoint tag for floor(s): "
                + ", ".join(str(m) for m in missing)
            )
        if duplicates:
            dup_s = "; ".join(
                f"{n}={found!r}" for n, found in sorted(duplicates.items())
            )
            parts.append(f"duplicate checkpoint tag(s): {dup_s}")
        raise FloorCheckpointTagError("; ".join(parts))

    return {
        "ok": True,
        "floors": mapping,
        "schema": f"{FLOOR_CHECKPOINT_PREFIX}<n>",
        "count": len(mapping),
    }
