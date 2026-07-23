"""Narrow port for atomic person merges."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from people_context.domain.person import Person
from people_context.ports.audit_log import AuditLog
from people_context.ports.lifecycle import MergeStoreResult


@runtime_checkable
class MergeStore(Protocol):
    """Persist one multi-row person merge atomically."""

    @property
    def audit_log(self) -> AuditLog: ...

    def merge_people(self, primary: Person, duplicate_id: str) -> MergeStoreResult: ...
