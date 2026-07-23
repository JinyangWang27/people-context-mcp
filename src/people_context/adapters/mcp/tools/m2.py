"""Real MCP tools for M2 writes, reminders, and communication guidance."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from mcp.types import ToolAnnotations
from pydantic import BaseModel, ValidationError

from people_context.app.context import SetCommunicationPhilosophyInput
from people_context.app.people import AddAliasInput
from people_context.app.records import (
    CompleteReminderInput,
    CorrectRecordInput,
    InvalidCorrectionError,
    InvalidReminderError,
    ListRemindersInput,
    OrganizationNotFoundError,
    PersonNotFoundError,
    RecordFactInput,
    RecordInteractionInput,
    RecordNotFoundError,
    RecordObservationInput,
    RecordTraitInput,
    ReminderNotActiveError,
    SetAffiliationInput,
    SetReminderInput,
)
from people_context.app.relationships import SetRelationshipInput
from people_context.domain.person import AliasKind
from people_context.domain.reminder import ReminderStatus
from people_context.domain.shared import Sensitivity

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from people_context.adapters.mcp.server import ToolDeps

_READ_ONLY = ToolAnnotations(readOnlyHint=True)
_WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False)


def _call(action: Callable[[], BaseModel]) -> dict[str, Any]:
    try:
        return action().model_dump(mode="json")
    except PersonNotFoundError as exc:
        return {"error": "person_not_found", "message": str(exc), "person_id": exc.person_id}
    except OrganizationNotFoundError as exc:
        return {"error": "organization_not_found", "message": str(exc), "org_id": exc.org_id}
    except RecordNotFoundError as exc:
        return {
            "error": "record_not_found",
            "message": str(exc),
            "entity_type": exc.entity_type,
            "entity_id": exc.entity_id,
        }
    except InvalidCorrectionError as exc:
        return {
            "error": "invalid_correction",
            "message": str(exc),
            "entity_type": exc.entity_type,
            "fields": exc.fields,
            "allowed_fields": exc.allowed_fields,
        }
    except ReminderNotActiveError as exc:
        return {
            "error": "reminder_not_active",
            "message": str(exc),
            "reminder_id": exc.reminder_id,
            "status": exc.status,
        }
    except InvalidReminderError as exc:
        return {"error": "invalid_reminder", "message": str(exc)}
    except ValidationError as exc:
        return {"error": "validation_error", "message": str(exc), "details": exc.errors(include_url=False)}


def register(mcp: FastMCP, deps: ToolDeps) -> None:
    """Register all M2 tools with their locked signatures and annotations."""

    @mcp.tool(annotations=_READ_ONLY)
    def get_communication_guidance(person_id: str, situation: str | None = None) -> dict[str, Any]:
        """Return sensitivity-gated signal for client-composed communication advice."""
        return deps.get_communication_guidance.execute(person_id, situation=situation).model_dump(mode="json")

    @mcp.tool(annotations=_READ_ONLY)
    def list_reminders(
        person_id: str | None = None,
        due_before: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        """List pull-based reminders, due-dated first and communication notes last."""
        try:
            data = ListRemindersInput(
                person_id=person_id,
                due_before=due_before,
                status=status if status is not None else ReminderStatus.ACTIVE,
            )
        except ValidationError as exc:
            return {"error": "validation_error", "message": str(exc), "details": exc.errors(include_url=False)}
        return {"reminders": [item.model_dump(mode="json") for item in deps.list_reminders.execute(data)]}

    @mcp.tool(annotations=_WRITE)
    def add_alias(
        person_id: str,
        value: str,
        kind: str | None = None,
        lang: str | None = None,
        script: str | None = None,
    ) -> dict[str, Any]:
        """Add a normalized-deduplicated alias to an existing person."""
        return _call(
            lambda: deps.add_alias.execute(
                AddAliasInput(
                    person_id=person_id,
                    value=value,
                    kind=kind if kind is not None else AliasKind.OTHER,
                    lang=lang,
                    script=script,
                )
            )
        )

    @mcp.tool(annotations=_WRITE)
    def set_relationship(
        subject_id: str,
        object_id: str,
        type: str,
        label: str | None = None,
        valid_from: str | None = None,
        valid_to: str | None = None,
        confidence: float | None = None,
    ) -> dict[str, Any]:
        """Create a directed relationship between two existing people."""
        return _call(
            lambda: deps.set_relationship.execute(
                SetRelationshipInput(
                    subject_id=subject_id,
                    object_id=object_id,
                    type=type,
                    label=label,
                    valid_from=valid_from,
                    valid_to=valid_to,
                    confidence=confidence,
                )
            )
        )

    @mcp.tool(annotations=_WRITE)
    def set_affiliation(
        person_id: str,
        org: str,
        role: str,
        valid_from: str | None = None,
        valid_to: str | None = None,
        confidence: float | None = None,
    ) -> dict[str, Any]:
        """Create an affiliation, resolving an org id or get/creating by name."""
        return _call(
            lambda: deps.set_affiliation.execute(
                SetAffiliationInput(
                    person_id=person_id,
                    org=org,
                    role=role,
                    valid_from=valid_from,
                    valid_to=valid_to,
                    confidence=confidence,
                )
            )
        )

    @mcp.tool(annotations=_WRITE)
    def record_fact(
        person_id: str,
        predicate: str,
        value: str,
        valid_from: str | None = None,
        valid_to: str | None = None,
        confidence: float | None = None,
        sensitivity: str | None = None,
    ) -> dict[str, Any]:
        """Record a time-aware fact about an existing person."""
        return _call(
            lambda: deps.record_fact.execute(
                RecordFactInput(
                    person_id=person_id,
                    predicate=predicate,
                    value=value,
                    valid_from=valid_from,
                    valid_to=valid_to,
                    confidence=confidence,
                    sensitivity=sensitivity if sensitivity is not None else Sensitivity.PERSONAL,
                )
            )
        )

    @mcp.tool(annotations=_WRITE)
    def record_observation(
        person_id: str,
        text: str,
        observed_at: str | None = None,
        sensitivity: str | None = None,
    ) -> dict[str, Any]:
        """Record a subjective observation, separate from disclosed context."""
        return _call(
            lambda: deps.record_observation.execute(
                RecordObservationInput(
                    person_id=person_id,
                    text=text,
                    observed_at=observed_at,
                    sensitivity=sensitivity if sensitivity is not None else Sensitivity.PERSONAL,
                )
            )
        )

    @mcp.tool(annotations=_WRITE)
    def record_trait(
        person_id: str,
        category: str,
        value: str,
        evidence_note: str | None = None,
        confidence: float | None = None,
        sensitivity: str | None = None,
    ) -> dict[str, Any]:
        """Record a derived trait with validated category and provenance."""
        return _call(
            lambda: deps.record_trait.execute(
                RecordTraitInput(
                    person_id=person_id,
                    category=category,
                    value=value,
                    evidence_note=evidence_note,
                    confidence=confidence,
                    sensitivity=sensitivity if sensitivity is not None else Sensitivity.PERSONAL,
                )
            )
        )

    @mcp.tool(annotations=_WRITE)
    def record_interaction(
        summary: str,
        participant_ids: list[str],
        occurred_at: str | None = None,
        channel: str | None = None,
        sensitivity: str | None = None,
    ) -> dict[str, Any]:
        """Record a concise interaction summary after validating all participants."""
        return _call(
            lambda: deps.record_interaction.execute(
                RecordInteractionInput(
                    summary=summary,
                    participant_ids=participant_ids,
                    occurred_at=occurred_at,
                    channel=channel,
                    sensitivity=sensitivity if sensitivity is not None else Sensitivity.PERSONAL,
                )
            )
        )

    @mcp.tool(annotations=_WRITE)
    def correct_record(entity_type: str, entity_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        """Correct whitelisted assertion fields in place with before/after audit."""
        return _call(
            lambda: deps.correct_record.execute(
                CorrectRecordInput(entity_type=entity_type, entity_id=entity_id, fields=fields)
            )
        )

    @mcp.tool(annotations=_WRITE)
    def set_reminder(
        person_id: str,
        text: str,
        kind: str,
        due_at: str | None = None,
        recurrence: str | None = None,
    ) -> dict[str, Any]:
        """Create a kind-validated reminder for an existing person."""
        return _call(
            lambda: deps.set_reminder.execute(
                SetReminderInput(
                    person_id=person_id,
                    text=text,
                    kind=kind,
                    due_at=due_at,
                    recurrence=recurrence,
                )
            )
        )

    @mcp.tool(annotations=_WRITE)
    def complete_reminder(reminder_id: str) -> dict[str, Any]:
        """Transition one active reminder to completed."""
        return _call(lambda: deps.complete_reminder.execute(CompleteReminderInput(reminder_id=reminder_id)))

    @mcp.tool(annotations=_WRITE)
    def set_communication_philosophy(text: str) -> dict[str, Any]:
        """Store communication philosophy verbatim while auditing lengths only."""
        return _call(
            lambda: deps.set_communication_philosophy.execute(SetCommunicationPhilosophyInput(text=text))
        )
