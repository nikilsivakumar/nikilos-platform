"""
The account-resolution logic for Google sign-in, kept separate from the
actual OAuth network round trip (see app/api/auth.py) so it can be tested
directly against the database without needing real Google credentials or
a browser.
"""

from sqlalchemy.orm import Session

from app.models.users import User


def get_or_create_user_from_google(db: Session, google_id: str, email: str, name: str) -> User:
    """
    Three cases, in order:
      1. A user already has this exact google_id -> that's them, return as-is.
      2. No user has this google_id, but one exists with this email (they
         signed up with email+password earlier) -> LINK this Google
         identity onto that existing account rather than creating a
         duplicate. This matters: without it, someone who signed up with
         email+password and later clicks "Sign in with Google" using the
         same email would silently get a second, disconnected account.
      3. Neither exists -> brand new user, Google-only (no password set).

    Known limitation, left deliberately unhandled: if someone's Google
    account email changes, this won't re-link automatically since lookup
    by google_id happens first and takes priority -- not a case worth
    solving at this stage.
    """
    user = db.query(User).filter(User.google_id == google_id).first()
    if user is not None:
        return user

    user = db.query(User).filter(User.email == email).first()
    if user is not None:
        user.google_id = google_id
        db.commit()
        db.refresh(user)
        return user

    user = User(email=email, name=name, google_id=google_id, hashed_password=None)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user