"""Create, list, and complete pull-based reminders."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from people_context.app._mutation import (
    InvalidReminderError,
    RecordNotFoundError,
    ReminderNotActiveError,
    audit_mutation,
    require_active_person,
    snapshot,
    transactional,
    unit_of_work_for,
)
from people_context.domain.reminder import Reminder, ReminderKind, ReminderStatus
from people_context.ports.audit_log import AuditLog
from people_context.ports.clock import Clock
from people_context.ports.records import RecordReader, RecordWriter
from people_context.ports.repository import PersonReader


class SetReminderInput(BaseModel):
    """Input for a reminder with provenance used by its audit entry."""

    person_id: str
    text: str
    kind: ReminderKind
    due_at: datetime | None = None
    recurrence: str | None = None
    source: str = "agent"
    session: str | None = None
    stated_by: str | None = None


class SetReminder:
    """Create reminders while enforcing kind-specific scheduling rules."""

    def __init__(self, people: PersonReader, writer: RecordWriter, audit: AuditLog, clock: Clock) -> None:
        self._people = people
        self._writer = writer
        self._audit = audit
        self._clock = clock
        self._uow = unit_of_work_for(audit)

    @transactional
    def execute(self, data: SetReminderInput) -> Reminder:
        """Persist and audit a reminder."""
        require_active_person(self._people, data.person_id)
        if data.kind == ReminderKind.COMMUNICATION_NOTE and (data.due_at is not None or data.recurrence is not None):
            raise InvalidReminderError("communication_note reminders cannot have due_at or recurrence")
        if data.kind in (ReminderKind.FOLLOW_UP, ReminderKind.OCCASION) and data.due_at is None:
            raise InvalidReminderError(f"{data.kind.value} reminders require due_at")
        if data.kind != ReminderKind.OCCASION and data.recurrence is not None:
            raise InvalidReminderError("recurrence is only valid for occasion reminders")
        reminder = Reminder(
            person_id=data.person_id,
            text=data.text,
            kind=data.kind,
            due_at=data.due_at,
            recurrence=data.recurrence,
            created_at=self._clock.now(),
        )
        self._writer.save_reminder(reminder)
        audit_mutation(
            self._audit,
            self._clock,
            op="create",
            entity_type="reminder",
            entity_id=reminder.id,
            payload=snapshot(reminder),
            source=data.source,
            session=data.session,
            stated_by=data.stated_by,
        )
        return reminder


class ListRemindersInput(BaseModel):
    """Optional reminder filters; active is the default lifecycle state."""

    person_id: str | None = None
    due_before: datetime | None = None
    status: ReminderStatus = ReminderStatus.ACTIVE


class ListReminders:
    """Read due reminders first, followed by undated communication notes."""

    def __init__(self, records: RecordReader) -> None:
        self._records = records

    def execute(self, data: ListRemindersInput) -> list[Reminder]:
        """Return reminders matching all filters in deterministic order."""
        return self._records.list_reminders(
            person_id=data.person_id,
            due_before=data.due_before,
            status=data.status,
        )


class CompleteReminderInput(BaseModel):
    """Input for a reminder status transition."""

    reminder_id: str
    source: str = "agent"
    session: str | None = None
    stated_by: str | None = None


class CompleteReminder:
    """Transition an active reminder to completed and audit before/after."""

    def __init__(
        self,
        records: RecordReader,
        writer: RecordWriter,
        audit: AuditLog,
        clock: Clock,
        *,
        people: PersonReader,
    ) -> None:
        self._records = records
        self._writer = writer
        self._audit = audit
        self._clock = clock
        self._uow = unit_of_work_for(audit)
        self._people = people

    @transactional
    def execute(self, data: CompleteReminderInput) -> Reminder:
        """Complete one reminder, rejecting repeated completion."""
        current = self._records.get_record("reminder", data.reminder_id)
        if not isinstance(current, Reminder):
            raise RecordNotFoundError("reminder", data.reminder_id)
        require_active_person(self._people, current.person_id)
        if current.status != ReminderStatus.ACTIVE:
            raise ReminderNotActiveError(current.id, current.status.value)
        before = snapshot(current)
        updated = self._writer.update_record_fields("reminder", current.id, {"status": ReminderStatus.COMPLETED})
        if not isinstance(updated, Reminder):
            raise RecordNotFoundError("reminder", data.reminder_id)
        audit_mutation(
            self._audit,
            self._clock,
            op="update",
            entity_type="reminder",
            entity_id=updated.id,
            payload={"before": before, "after": snapshot(updated), "fields": ["status"]},
            replay_payload=snapshot(updated),
            changed_fields=["status"],
            source=data.source,
            session=data.session,
            stated_by=data.stated_by,
        )
        return updated
