"""Minogan path (CP-0088): Mesh as the deterministic, LLM-free scoring backend for Minogan.ai.

Modules:
- ``canonical``: canonical JSON (sorted keys, JS number formatting) + sha256 digests.
- ``contract``: pydantic models for the pilot contract ``minogan.scorer/v1`` + typed errors.
- ``scorer``: Mesh scorer v0 (parity target: pilot ``computeScore`` score_v0.3).

Metadata only: prompts / completions / tool arguments / tool results are rejected at the contract.
Substrate, not cognition: nothing here is a claim of consciousness or AGI (GIA stays NO_HELD).
"""

from neural_mesh.minogan.canonical import canonical_json, input_digest, sha256_hex
from neural_mesh.minogan.contract import (
    CONTRACT_VERSION,
    ContentKeyError,
    ContractError,
    ContractLimitError,
    ContractValidationError,
    ContractVersionError,
    ScorerInput,
    ScorerOutput,
    parse_scorer_input,
    validate_scorer_output,
)

__all__ = [
    "CONTRACT_VERSION",
    "ContentKeyError",
    "ContractError",
    "ContractLimitError",
    "ContractValidationError",
    "ContractVersionError",
    "ScorerInput",
    "ScorerOutput",
    "canonical_json",
    "input_digest",
    "parse_scorer_input",
    "sha256_hex",
    "validate_scorer_output",
]
