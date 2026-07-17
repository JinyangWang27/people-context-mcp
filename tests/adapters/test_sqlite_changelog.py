"""Replayable changelog capture and lifecycle grouping tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from people_context.adapters.sqlite import (
    SqliteAuditLog,
    SqliteChangelog,
    SqliteLifecycleStore,
    SqliteOrganizationStore,
    SqlitePeopleRepository,
    SqlitePreferencesStore,
    SqliteRecordStore,
    open_db,
)
from people_context.app import (
    AddAlias,
    AddAliasInput,
    CompleteReminder,
    CompleteReminderInput,
    CorrectRecord,
    CorrectRecordInput,
    EditPerson,
    EditPersonInput,
    MergePeople,
    RecordFact,
    RecordFactInput,
    RecordInteraction,
    RecordInteractionInput,
    RecordObservation,
    RecordObservationInput,
    RecordTrait,
    RecordTraitInput,
    RememberPerson,
    RememberPersonInput,
    SetAffiliation,
    SetAffiliationInput,
    SetCommunicationPhilosophy,
    SetCommunicationPhilosophyInput,
    SetRelationship,
    SetRelationshipInput,
    SetReminder,
    SetReminderInput,
)
from people_context.domain.preferences import PREF_COMMUNICATION_PHILOSOPHY
from people_context.domain.reminder import ReminderKind
from people_context.domain.trait import TraitCategory
from people_context.ports.clock import Clock


class _Clock(Clock):
    def now(self) -> datetime:
        return datetime(2026, 7, 17, 12, 0, tzinfo=UTC)


def test_all_ordinary_write_paths_capture_full_replay_payloads() -> None:
    conn = open_db(":memory:")
    people = SqlitePeopleRepository(conn)
    records = SqliteRecordStore(conn)
    organizations = SqliteOrganizationStore(conn)
    preferences = SqlitePreferencesStore(conn)
    audit = SqliteAuditLog(conn)
    clock = _Clock()

    remember = RememberPerson(people, people, audit, clock)
    alice = remember.execute(RememberPersonInput(name="Alice", summary="Initial")).person
    bob = remember.execute(RememberPersonInput(name="Bob")).person
    AddAlias(people, people, audit, clock).execute(AddAliasInput(person_id=alice.id, value="Ally"))
    EditPerson(people, people, audit, clock).execute(EditPersonInput(person_id=alice.id, summary="Updated"))
    relationship = SetRelationship(people, records, audit, clock).execute(
        SetRelationshipInput(subject_id=alice.id, object_id=bob.id, type="colleague")
    )
    affiliation = SetAffiliation(people, organizations, records, audit, clock).execute(
        SetAffiliationInput(person_id=alice.id, org="Acme", role="Engineer")
    )
    fact = RecordFact(people, records, audit, clock).execute(
        RecordFactInput(person_id=alice.id, predicate="timezone", value="Asia/Dubai")
    )
    observation = RecordObservation(people, records, audit, clock).execute(
        RecordObservationInput(person_id=alice.id, text="Prefers concise updates")
    )
    trait = RecordTrait(people, records, audit, clock).execute(
        RecordTraitInput(person_id=alice.id, category=TraitCategory.PREFERENCE, value="Concise")
    )
    interaction = RecordInteraction(people, records, audit, clock).execute(
        RecordInteractionInput(summary="Planning call", participant_ids=[alice.id, bob.id])
    )
    reminder = SetReminder(people, records, audit, clock).execute(
        SetReminderInput(person_id=alice.id, text="Follow up", kind=ReminderKind.COMMUNICATION_NOTE)
    )
    completed = CompleteReminder(records, records, audit, clock, people=people).execute(
        CompleteReminderInput(reminder_id=reminder.id)
    )
    corrected = CorrectRecord(records, records, audit, clock, people=people).execute(
        CorrectRecordInput(entity_type="fact", entity_id=fact.id, fields={"value": "UTC+4"})
    )
    philosophy_text = "Be direct, kind, and concise."
    SetCommunicationPhilosophy(preferences, audit, clock).execute(SetCommunicationPhilosophyInput(text=philosophy_text))

    entries = SqliteChangelog(conn).list_entries(limit=100)
    by_entity = {(entry.entity_type, entry.entity_id, entry.op_kind): entry for entry in entries}
    assert by_entity[("person", alice.id, "create")].payload["canonical_name"] == "Alice"
    assert any(
        entry.entity_type == "person" and entry.entity_id == alice.id and "aliases" in entry.payload
        for entry in entries
    )
    assert by_entity[("relationship", relationship.id, "create")].payload["object_id"] == bob.id
    assert by_entity[("affiliation", affiliation.id, "create")].payload["role"] == "Engineer"
    assert by_entity[("observation", observation.id, "create")].payload["text"] == "Prefers concise updates"
    assert by_entity[("trait", trait.id, "create")].payload["value"] == "Concise"
    assert by_entity[("interaction", interaction.id, "create")].payload["participant_ids"] == [alice.id, bob.id]
    assert by_entity[("reminder", completed.id, "update")].payload["status"] == "completed"
    assert by_entity[("fact", corrected.id, "correct")].payload["value"] == "UTC+4"
    assert by_entity[("fact", corrected.id, "correct")].changed_fields == ["value"]

    preference = by_entity[("preference", PREF_COMMUNICATION_PHILOSOPHY, "prefs")]
    assert preference.payload["value"] == philosophy_text
    audit_entry = next(
        entry
        for entry in audit.list_entries()
        if entry.entity_type == "preference" and entry.entity_id == PREF_COMMUNICATION_PHILOSOPHY
    )
    assert audit_entry.payload == {"before_length": None, "after_length": len(philosophy_text)}
    assert philosophy_text not in str(audit_entry.payload)

    org_entry = next(entry for entry in entries if entry.entity_type == "organization")
    affiliation_entry = by_entity[("affiliation", affiliation.id, "create")]
    assert org_entry.transaction_id == affiliation_entry.transaction_id
    assert all(entry.schema_version == 1 and entry.actor["source"] for entry in entries)


def test_plain_write_rolls_back_primary_audit_hlc_and_changelog_on_capture_failure() -> None:
    conn = open_db(":memory:")
    people = SqlitePeopleRepository(conn)

    def fail(checkpoint: str) -> None:
        assert checkpoint == "before_append"
        raise RuntimeError("injected changelog failure")

    audit = SqliteAuditLog(conn, changelog_failure_hook=fail, wall_clock_ms=lambda: 1000)
    with pytest.raises(RuntimeError, match="injected changelog failure"):
        RememberPerson(people, people, audit, _Clock()).execute(RememberPersonInput(name="Atomic Alice"))

    assert conn.execute("SELECT COUNT(*) FROM persons").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM changelog").fetchone()[0] == 0
    device = conn.execute("SELECT hlc_physical_ms, hlc_logical FROM devices WHERE retired_at IS NULL").fetchone()
    assert tuple(device) == (0, 0)


def test_merge_emits_child_operations_and_parent_manifest_in_one_transaction() -> None:
    conn = open_db(":memory:")
    people = SqlitePeopleRepository(conn)
    records = SqliteRecordStore(conn)
    audit = SqliteAuditLog(conn)
    clock = _Clock()
    remember = RememberPerson(people, people, audit, clock)
    primary = remember.execute(RememberPersonInput(name="Primary")).person
    duplicate = remember.execute(RememberPersonInput(name="Duplicate", summary="Sentinel summary")).person
    fact = RecordFact(people, records, audit, clock).execute(
        RecordFactInput(person_id=duplicate.id, predicate="note", value="Sentinel fact")
    )
    conn.execute("DELETE FROM changelog")
    conn.commit()

    MergePeople(people, SqliteLifecycleStore(conn), clock, audit).execute(primary.id, duplicate.id)

    entries = SqliteChangelog(conn).list_entries(limit=100)
    assert len({entry.transaction_id for entry in entries}) == 1
    parent = next(entry for entry in entries if entry.op_kind == "merge" and entry.entity_type == "person")
    child_fact = next(entry for entry in entries if entry.entity_type == "fact" and entry.entity_id == fact.id)
    duplicate_child = next(
        entry for entry in entries if entry.entity_type == "person" and entry.entity_id == duplicate.id
    )
    assert parent.payload["primary_id"] == primary.id
    assert parent.payload["duplicate_id"] == duplicate.id
    assert child_fact.op_kind == "update"
    assert child_fact.payload["person_id"] == primary.id
    assert child_fact.changed_fields == ["person_id"]
    assert duplicate_child.payload["deleted_at"] is not None


def test_merge_rolls_back_when_child_changelog_capture_fails() -> None:
    conn = open_db(":memory:")
    people = SqlitePeopleRepository(conn)
    records = SqliteRecordStore(conn)
    seed_audit = SqliteAuditLog(conn)
    clock = _Clock()
    remember = RememberPerson(people, people, seed_audit, clock)
    primary = remember.execute(RememberPersonInput(name="Primary")).person
    duplicate = remember.execute(RememberPersonInput(name="Duplicate")).person
    fact = RecordFact(people, records, seed_audit, clock).execute(
        RecordFactInput(person_id=duplicate.id, predicate="city", value="Abu Dhabi")
    )
    audit_count = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    changelog_count = conn.execute("SELECT COUNT(*) FROM changelog").fetchone()[0]

    def fail(_: str) -> None:
        raise RuntimeError("merge changelog failure")

    lifecycle = SqliteLifecycleStore(conn, changelog_failure_hook=fail)
    with pytest.raises(RuntimeError, match="merge changelog failure"):
        MergePeople(people, lifecycle, clock).execute(primary.id, duplicate.id)

    assert people.get(duplicate.id) is not None and people.get(duplicate.id).deleted_at is None
    assert records.get_record("fact", fact.id).person_id == duplicate.id
    assert conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0] == audit_count
    assert conn.execute("SELECT COUNT(*) FROM changelog").fetchone()[0] == changelog_count
