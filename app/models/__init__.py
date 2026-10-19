from app.db.session import Base
from app.models.user import User
from app.models.persona import Persona
from app.models.challenge import Challenge, Zone
from app.models.solution import (
    Solution,
    Innovation,
    solution_relevant_challenges,
    solution_personas,
    innovation_relevant_zones,
    innovation_personas
)
from app.models.relevance import SolutionPersonaRelevance, InnovationPersonaRelevance
from app.models.suggestion import (
    ResearchSuggestion,
    suggestion_personas,
    suggestion_challenges
)
from app.models.interaction import ModuleInteractionLog

__all__ = [
    "Base",
    "User",
    "Persona",
    "Challenge",
    "Zone",
    "Solution",
    "Innovation",
    "solution_relevant_challenges",
    "solution_personas",
    "innovation_relevant_zones",
    "innovation_personas",
    "SolutionPersonaRelevance",
    "InnovationPersonaRelevance",
    "ResearchSuggestion",
    "suggestion_personas",
    "suggestion_challenges",
    "ModuleInteractionLog",
]
