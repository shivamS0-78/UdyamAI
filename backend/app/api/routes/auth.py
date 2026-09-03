"""Supabase Auth routes."""

from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import get_current_profile, get_current_user
from app.models.user import Profile
from app.services.auth_service import AuthUser

router = APIRouter()


@router.get("/me")
def get_me(
    user: AuthUser = Depends(get_current_user),
    profile: Profile = Depends(get_current_profile),
) -> dict[str, Any]:
    """Return the authenticated Supabase user and the linked app profile."""
    return {
        "user": {
            "id": str(user.id),
            "phone": user.phone,
            "email": user.email,
            "role": user.role,
        },
        "profile": {
            "id": str(profile.id),
            "name": profile.name,
            "email": profile.email,
            "phone": profile.phone,
            "business_name": profile.business_name,
            "business_type": profile.business_type,
            "preferred_language": profile.preferred_language,
        },
    }
