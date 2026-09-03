"""FastAPI dependencies for Supabase-authenticated requests.

``get_current_user`` guards a route with a valid Supabase session.
``get_current_profile`` additionally resolves (and lazily creates) the
app ``profiles`` row linked to the authenticated auth user. All
user-owned data lookups in routes should derive identity from these
dependencies instead of trusting client-supplied ids.
"""

import logging

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.database import get_session
from app.models.user import Profile
from app.services.auth_service import AuthUser, get_bearer_token, verify_supabase_token

logger = logging.getLogger(__name__)


def get_current_user(
    authorization: str | None = Header(default=None),
) -> AuthUser:
    """Validate the Supabase access token in the Authorization header."""
    token = get_bearer_token(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Provide a valid Supabase session token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return verify_supabase_token(token)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_profile(
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Profile:
    """Resolve the app profile for the authenticated user, creating it on first login.

    A database trigger normally creates the row at signup; this fallback
    also covers users that predate that trigger.
    """
    profile = session.exec(select(Profile).where(Profile.auth_user_id == user.id)).first()
    if profile:
        return profile

    profile = Profile(
        auth_user_id=user.id,
        email=user.email,
        phone=user.phone,
    )
    session.add(profile)
    try:
        session.commit()
    except IntegrityError:
        # The auth.users -> profiles trigger may have created the row between
        # our SELECT and INSERT (signup happens concurrently).
        session.rollback()
        created = session.exec(select(Profile).where(Profile.auth_user_id == user.id)).first()
        if created:
            return created
        raise
    session.refresh(profile)
    logger.info("Auto-created profile %s for auth user %s", profile.id, user.id)
    return profile
