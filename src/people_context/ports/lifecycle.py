"""Narrow ports for atomic lifecycle operations."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from people_context.domain.person import Person
from people_context.ports.audit_log import AuditEntry


@runtime_checkable
class LifecycleStore(Protocol):
    """Persist multi-row lifecycle mutations atomically."""

    def merge_people(
        self,
        primary: Person,
        duplicate_id: str,
        audit_factory: Callable[[dict[str, int]], AuditEntry],
    ) -> dict[str, int]: ...
