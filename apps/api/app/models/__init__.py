"""
Import all ORM models so that SQLAlchemy's mapper registry is fully populated
before Alembic autogenerate or any table-creation call is made.
"""

from app.models.user import User
from app.models.workspace import Workspace
from app.models.role import Role
from app.models.candidate import Candidate
from app.models.candidate_document import CandidateDocument
from app.models.candidate_score import CandidateScore
from app.models.subscription import Subscription
from app.models.usage_event import UsageEvent

__all__ = [
    "User",
    "Workspace",
    "Role",
    "Candidate",
    "CandidateDocument",
    "CandidateScore",
    "Subscription",
    "UsageEvent",
]
