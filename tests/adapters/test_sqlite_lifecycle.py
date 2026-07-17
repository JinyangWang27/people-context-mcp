"""Integration tests for atomic SQLite lifecycle operations."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from people_context.adapters.sqlite import (
    SqliteLifecycleStore,
    SqlitePeopleRepository,
    SqliteRecordStore,
    open_db,
)
from people_context.app import MergePeople, MergePeopleError
from people_context.domain.fact import Fact
from people_context.domain.interaction import Interaction
from people_context.domain.person import Alias, AliasKind, Person
from people_context.domain.relationship import Relationship
from people_context.domain.shared import Provenance

_NOW = datetime(2026, 1, 2, 3, 4, tzinfo=UTC)
_PROVENANCE = Provenance(source="test")


class _Clock:
    def now(self) -> datetime:
        return _NOW


def _person(name: str, *, is_self: bool = False, summary: str | None = None) -> Person:
    return Person(canonical_name=name, is_self=is_self, summary=summary, created_at=_NOW, updated_at=_NOW)


def test_merge_people_reparents_rows_resolves_collisions_and_refreshes_search() -> None:
    conn = open_db(":memory:")
    people = SqlitePeopleRepository(conn)
    records = SqliteRecordStore(conn)
    primary = _person("Alice", summary=None)
    primary.aliases.append(Alias(value="Ally", kind=AliasKind.NICKNAME))
    duplicate = _person("Alice Smith", summary="Engineer")
    duplicate.aliases.extend([Alias(value="ally"), Alias(value="A. Smith")])
    other = _person("Bob")
    for person in (primary, duplicate, other):
        people.save_person(person)

    fact = Fact(person_id=duplicate.id, predicate="location", value="Dubai", provenance=_PROVENANCE)
    records.save_fact(fact)
    surviving = Relationship(
        subject_id=duplicate.id,
        object_id=other.id,
        type="friend_of",
        provenance=_PROVENANCE,
        created_at=_NOW,
    )
    self_loop = Relationship(
        subject_id=duplicate.id,
        object_id=primary.id,
        type="same_team",
        provenance=_PROVENANCE,
        created_at=_NOW,
    )
    records.save_relationship(surviving)
    records.save_relationship(self_loop)
    interaction = Interaction(
        summary="Met",
        occurred_at=_NOW,
        participant_ids=[primary.id, duplicate.id],
        provenance=_PROVENANCE,
    )
    records.save_interaction(interaction)

    result = MergePeople(people, SqliteLifecycleStore(conn), _Clock()).execute(primary.id, duplicate.id)

    assert result.person.summary == "Engineer"
    assert [alias.value for alias in result.person.aliases] == ["Ally", "Alice Smith", "A. Smith"]
    assert result.moved.facts == 1
    assert result.moved.relationships == 1
    assert result.moved.interaction_participations == 1
    assert result.self_loops_removed == 1
    assert records.get_record("fact", fact.id).person_id == primary.id  # type: ignore[union-attr]
    assert records.get_record("relationship", surviving.id).subject_id == primary.id  # type: ignore[union-attr]
    assert records.get_record("relationship", self_loop.id) is None
    assert records.get_record("interaction", interaction.id).participant_ids == [primary.id]  # type: ignore[union-attr]
    assert people.get(duplicate.id).deleted_at == _NOW  # type: ignore[union-attr]
    assert people.search_names("Alice Smith")[0].person.id == primary.id
    audit_rows = conn.execute("SELECT op, entity_id FROM audit_log").fetchall()
    assert [(row["op"], row["entity_id"]) for row in audit_rows] == [("merge", primary.id)]


def test_merge_people_rolls_back_every_change_when_audit_checkpoint_fails() -> None:
    conn = open_db(":memory:")
    people = SqlitePeopleRepository(conn)
    primary = _person("Primary")
    duplicate = _person("Duplicate")
    people.save_person(primary)
    people.save_person(duplicate)

    def fail(_: str) -> None:
        raise RuntimeError("injected")

    with pytest.raises(RuntimeError, match="injected"):
        MergePeople(people, SqliteLifecycleStore(conn, fail), _Clock()).execute(primary.id, duplicate.id)

    assert people.get(duplicate.id).deleted_at is None  # type: ignore[union-attr]
    assert people.get(primary.id).aliases == []  # type: ignore[union-attr]
    assert conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0] == 0


def test_merge_people_validates_same_person_and_self_direction() -> None:
    conn = open_db(":memory:")
    people = SqlitePeopleRepository(conn)
    self_person = _person("Me", is_self=True)
    other = _person("Other")
    people.save_person(self_person)
    people.save_person(other)
    merge = MergePeople(people, SqliteLifecycleStore(conn), _Clock())

    with pytest.raises(MergePeopleError, match="different") as same:
        merge.execute(other.id, other.id)
    assert same.value.code == "same_person"
    with pytest.raises(MergePeopleError, match="primary") as direction:
        merge.execute(other.id, self_person.id)
    assert direction.value.code == "self_merge_direction"
