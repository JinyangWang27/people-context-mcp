"""Semantic search and index maintenance use cases."""

from people_context.app.semantic.reindex import ReindexSemantic, ReindexSemanticResult
from people_context.app.semantic.reindex_people import ReindexPeople, ReindexPeopleResult
from people_context.app.semantic.search import (
    SemanticSearch,
    SemanticSearchHit,
    SemanticSearchModelMismatch,
    SemanticSearchNotAvailable,
    SemanticSearchOk,
    SemanticSearchValidationError,
)

__all__ = [
    "ReindexPeople",
    "ReindexPeopleResult",
    "ReindexSemantic",
    "ReindexSemanticResult",
    "SemanticSearch",
    "SemanticSearchHit",
    "SemanticSearchModelMismatch",
    "SemanticSearchNotAvailable",
    "SemanticSearchOk",
    "SemanticSearchValidationError",
]
