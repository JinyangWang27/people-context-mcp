"""Application layer: use cases orchestrating domain entities over the ports."""

from __future__ import annotations

from people_context.app.get_person_context import (
    GetPersonContext,
    PersonAffiliationContext,
    PersonContextResult,
    PersonIdentity,
    PersonRelationshipContext,
)
from people_context.app.record import (
    AliasInput,
    AmbiguousPersonError,
    RememberPerson,
    RememberPersonInput,
    RememberPersonResult,
    SelfAlreadyExistsError,
)
from people_context.app.resolve_person import ResolutionCandidate, ResolutionHints, ResolutionResult, ResolvePerson
from people_context.app.search_people import SearchPeople

__all__ = [
    "AliasInput",
    "AmbiguousPersonError",
    "GetPersonContext",
    "PersonAffiliationContext",
    "PersonContextResult",
    "PersonIdentity",
    "PersonRelationshipContext",
    "RememberPerson",
    "RememberPersonInput",
    "RememberPersonResult",
    "ResolutionCandidate",
    "ResolutionHints",
    "ResolutionResult",
    "ResolvePerson",
    "SearchPeople",
    "SelfAlreadyExistsError",
]
