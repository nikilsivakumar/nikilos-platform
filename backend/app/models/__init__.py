"""
Every model must be imported here. Alembic's autogenerate (see alembic/env.py)
inspects Base.metadata to figure out what tables should exist -- a model that
isn't imported anywhere is invisible to it and won't get a migration, even
though the file exists on disk. This file's only job is to prevent that.
"""

from app.models.users import User  # noqa: F401
from app.models.coach_profiles import CoachProfile  # noqa: F401
from app.models.coach_clients import CoachClient, CoachClientStatus  # noqa: F401
from app.models.coach_billing import CoachBilling, BillingTier  # noqa: F401
from app.models.client_intro import ClientIntro, ExperienceLevel  # noqa: F401