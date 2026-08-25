"""
Tests for app/core/permissions.py — the single piece of logic that keeps
one coach's clients invisible to every other coach and to each other.

Uses an in-memory SQLite database, not real Postgres. This is deliberate:
these tests check pure access-control LOGIC (does the right row produce
the right AccessLevel), not database-specific behavior — SQLite is faster
and needs no setup, so this can run constantly while iterating. Anything
Postgres-specific (like the coach_client_status enum type) still gets
exercised for real when you run `alembic upgrade head` against nikilos_dev.

Run with (from backend/, venv active):
    pytest tests/test_permissions.py -v
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.models.users import User
from app.models.coach_clients import CoachClient, CoachClientStatus
from app.core.permissions import get_access_level, require_access, AccessLevel

from fastapi import HTTPException


@pytest.fixture
def db():
    """Fresh in-memory SQLite database, one per test — no state leaks between tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def make_user(db, email):
    user = User(email=email, name=email.split("@")[0])
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_user_always_has_own_access(db):
    """A user must always have full access to their own data — no relationship needed."""
    alice = make_user(db, "alice@example.com")
    assert get_access_level(db, alice.id, alice.id) == AccessLevel.OWN


def test_stranger_has_no_access(db):
    """Two users with no coach_clients row between them see nothing of each other."""
    alice = make_user(db, "alice@example.com")
    bob = make_user(db, "bob@example.com")
    assert get_access_level(db, alice.id, bob.id) == AccessLevel.NONE
    assert get_access_level(db, bob.id, alice.id) == AccessLevel.NONE


def test_active_coach_client_grants_full_access(db):
    """An ACTIVE relationship gives the coach full access to that specific client."""
    coach = make_user(db, "coach@example.com")
    client = make_user(db, "client@example.com")
    db.add(CoachClient(coach_id=coach.id, client_id=client.id, status=CoachClientStatus.active))
    db.commit()

    assert get_access_level(db, coach.id, client.id) == AccessLevel.COACH_FULL


def test_pending_coach_client_grants_intro_only(db):
    """A PENDING relationship (not yet accepted) grants intro-only, not full access."""
    coach = make_user(db, "coach@example.com")
    client = make_user(db, "client@example.com")
    db.add(CoachClient(coach_id=coach.id, client_id=client.id, status=CoachClientStatus.pending))
    db.commit()

    assert get_access_level(db, coach.id, client.id) == AccessLevel.COACH_INTRO_ONLY


def test_inactive_coach_client_grants_no_access(db):
    """An INACTIVE relationship (e.g. client left) reverts the coach to no access."""
    coach = make_user(db, "coach@example.com")
    client = make_user(db, "client@example.com")
    db.add(CoachClient(coach_id=coach.id, client_id=client.id, status=CoachClientStatus.inactive))
    db.commit()

    assert get_access_level(db, coach.id, client.id) == AccessLevel.NONE


def test_client_has_no_reverse_access_to_coach(db):
    """
    A client being coached does NOT give them elevated access back to the
    coach's own data — the relationship is one-directional.
    """
    coach = make_user(db, "coach@example.com")
    client = make_user(db, "client@example.com")
    db.add(CoachClient(coach_id=coach.id, client_id=client.id, status=CoachClientStatus.active))
    db.commit()

    assert get_access_level(db, client.id, coach.id) == AccessLevel.NONE


def test_coach_cannot_see_another_coachs_client(db):
    """
    THE critical negative test. Two separate coaches, each with their own
    active client. Coach A must have zero access to Coach B's client, even
    though both relationships exist in the same coach_clients table.
    This is the exact scenario the whole permission model exists to prevent.
    """
    coach_a = make_user(db, "coach_a@example.com")
    coach_b = make_user(db, "coach_b@example.com")
    client_of_a = make_user(db, "client_a@example.com")
    client_of_b = make_user(db, "client_b@example.com")

    db.add(CoachClient(coach_id=coach_a.id, client_id=client_of_a.id, status=CoachClientStatus.active))
    db.add(CoachClient(coach_id=coach_b.id, client_id=client_of_b.id, status=CoachClientStatus.active))
    db.commit()

    # Coach A can see their own client...
    assert get_access_level(db, coach_a.id, client_of_a.id) == AccessLevel.COACH_FULL
    # ...but NOT coach B's client.
    assert get_access_level(db, coach_a.id, client_of_b.id) == AccessLevel.NONE
    # And the reverse holds too.
    assert get_access_level(db, coach_b.id, client_of_a.id) == AccessLevel.NONE


def test_two_clients_of_same_coach_cannot_see_each_other(db):
    """
    THE other critical negative test. Clients must not be visible to each
    other, even when they share the same coach.
    """
    coach = make_user(db, "coach@example.com")
    client_1 = make_user(db, "client_1@example.com")
    client_2 = make_user(db, "client_2@example.com")

    db.add(CoachClient(coach_id=coach.id, client_id=client_1.id, status=CoachClientStatus.active))
    db.add(CoachClient(coach_id=coach.id, client_id=client_2.id, status=CoachClientStatus.active))
    db.commit()

    assert get_access_level(db, client_1.id, client_2.id) == AccessLevel.NONE
    assert get_access_level(db, client_2.id, client_1.id) == AccessLevel.NONE


def test_require_access_allows_when_level_is_permitted(db):
    """require_access should return the level quietly when it's in the allowed set."""
    alice = make_user(db, "alice@example.com")
    level = require_access(db, alice.id, alice.id, allowed={AccessLevel.OWN, AccessLevel.COACH_FULL})
    assert level == AccessLevel.OWN


def test_require_access_raises_403_when_level_not_permitted(db):
    """
    require_access must raise 403, not silently return NONE — a route that
    forgets to check a return value would otherwise leak data.
    """
    alice = make_user(db, "alice@example.com")
    bob = make_user(db, "bob@example.com")

    with pytest.raises(HTTPException) as exc_info:
        require_access(db, alice.id, bob.id, allowed={AccessLevel.OWN, AccessLevel.COACH_FULL})

    assert exc_info.value.status_code == 403


def test_require_access_excludes_intro_only_from_full_data_routes(db):
    """
    A pending coach must NOT be able to reach a full-data route just because
    SOME access level was achieved — the allowed set has to be exact, and
    require_access must respect it rather than treating any non-NONE level
    as good enough.
    """
    coach = make_user(db, "coach@example.com")
    client = make_user(db, "client@example.com")
    db.add(CoachClient(coach_id=coach.id, client_id=client.id, status=CoachClientStatus.pending))
    db.commit()

    # Pending coach CAN reach an intro-only route...
    level = require_access(db, coach.id, client.id, allowed={AccessLevel.COACH_INTRO_ONLY})
    assert level == AccessLevel.COACH_INTRO_ONLY

    # ...but NOT a full-data route, even though a relationship row exists.
    with pytest.raises(HTTPException) as exc_info:
        require_access(db, coach.id, client.id, allowed={AccessLevel.OWN, AccessLevel.COACH_FULL})
    assert exc_info.value.status_code == 403 