"""Person context and communication preference use cases."""

from people_context.app.context.guidance import CommunicationGuidanceResult, GetCommunicationGuidance
from people_context.app.context.models import PersonAffiliationContext, PersonRelationshipContext
from people_context.app.context.preferences import SetCommunicationPhilosophy, SetCommunicationPhilosophyInput
from people_context.app.context.query import GetPersonContext, PersonContextResult, PersonIdentity

__all__ = [
    "CommunicationGuidanceResult",
    "GetCommunicationGuidance",
    "GetPersonContext",
    "PersonAffiliationContext",
    "PersonContextResult",
    "PersonIdentity",
    "PersonRelationshipContext",
    "SetCommunicationPhilosophy",
    "SetCommunicationPhilosophyInput",
]
