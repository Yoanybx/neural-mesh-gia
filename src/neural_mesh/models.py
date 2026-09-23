from enum import Enum
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

class Status(str, Enum):
    PLANNED="PLANNED"; IN_PROGRESS="IN_PROGRESS"; BLOCKED="BLOCKED"
    FAILED="FAILED"; VERIFIED="VERIFIED"; COMPLETED="COMPLETED"
    DEPRECATED="DEPRECATED"; SUPERSEDED="SUPERSEDED"

class Checkpoint(BaseModel):
    checkpoint_id: str
    project: str = "Neural Mesh / GIA-COS"
    project_version: str
    status: Status = Status.IN_PROGRESS
    phase: int
    module: str
    reason: str
    objective: str = ""
    next_action: str = ""
    git_commit: str | None = None
    changed_files: list[str] = Field(default_factory=list)
    tests: dict[str, int] = Field(default_factory=dict)
    known_bugs: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    safety_status: str = "SAFE"
    evidence: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)
    manifest_sha256: str | None = None
    # Phase 2 C-RAM (optional; absent/empty on historical CP-0001..0007)
    cram_root_hash: str | None = None
    cram_objects: list[str] = Field(default_factory=list)

class ProjectState(BaseModel):
    project: str = "Neural Mesh / GIA-COS"
    schema_version: str = "1.0"
    project_version: str = "0.5.4"
    last_checkpoint: str | None = None
    status: Status = Status.IN_PROGRESS
    current_phase: int = 0
    current_module: str = "bootstrap"
    completed_phases: list[int] = Field(default_factory=list)
    active_tasks: list[str] = Field(default_factory=list)
    completed_tasks: list[str] = Field(default_factory=list)
    blocked_tasks: list[str] = Field(default_factory=list)
    next_action: str = ""
    last_successful_test: str | None = None
    last_failed_test: str | None = None
    test_summary: dict[str, int] = Field(default_factory=lambda: {"passed":0,"failed":0,"skipped":0})
    known_bugs: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    decisions_pending: list[str] = Field(default_factory=list)
    safety_status: str = "SAFE"
    human_approval_required: bool = False
    git_commit: str | None = None
    modified_files: list[str] = Field(default_factory=list)
    last_updated: str = Field(default_factory=utc_now)
