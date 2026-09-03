from fastapi import APIRouter, HTTPException

from app.config import settings
from app.database import verify_db_connection

router = APIRouter()


@router.get("")
def health_check():
    db_ok = verify_db_connection()
    status = "healthy" if db_ok else "unhealthy"

    if not db_ok:
        raise HTTPException(
            status_code=503,
            detail={"status": status, "version": settings.VERSION, "database": "disconnected"},
        )

    return {"status": status, "version": settings.VERSION, "database": "connected"}


@router.get("/llm")
def llm_health():
    """Check LLM provider availability and report active configuration.

    Does NOT consume API credits — only validates configuration and package
    availability.  A full probe (actual generation) is intentionally avoided
    here so this endpoint stays cheap to call.
    """
    from app.ai.llm import _configured_model, _configured_provider, _gemini_models, _openai_models

    provider = _configured_provider()
    model = _configured_model()
    gemini_key_set = bool(settings.GEMINI_API_KEY)
    openai_key_set = bool(settings.OPENAI_API_KEY)

    # Check package availability
    gemini_pkg = False
    openai_pkg = False
    try:
        import google.genai  # noqa: F401

        gemini_pkg = True
    except ImportError:
        pass
    try:
        import openai  # noqa: F401

        openai_pkg = True
    except ImportError:
        pass

    # Build provider status
    providers = {}
    if provider == "gemini":
        providers["gemini"] = {
            "configured": gemini_key_set,
            "package_installed": gemini_pkg,
            "preferred_model": model,
            "fallback_models": _gemini_models()[1:],  # skip primary (same as preferred)
            "status": "ready" if gemini_key_set and gemini_pkg else "not_configured",
        }
        if openai_key_set or openai_pkg:
            providers["openai"] = {
                "configured": openai_key_set,
                "package_installed": openai_pkg,
                "preferred_model": None,
                "fallback_models": _openai_models(),
                "status": "fallback_only",
            }
    else:
        providers["openai"] = {
            "configured": openai_key_set,
            "package_installed": openai_pkg,
            "preferred_model": model,
            "fallback_models": _openai_models()[1:],
            "status": "ready" if openai_key_set and openai_pkg else "not_configured",
        }
        if gemini_key_set or gemini_pkg:
            providers["gemini"] = {
                "configured": gemini_key_set,
                "package_installed": gemini_pkg,
                "preferred_model": None,
                "fallback_models": _gemini_models(),
                "status": "fallback_only",
            }

    # Overall status
    primary_ready = providers.get(provider, {}).get("status") == "ready"
    any_fallback = any(
        p.get("status") == "ready" for name, p in providers.items() if name != provider
    )
    overall = "healthy" if primary_ready else ("degraded" if any_fallback else "unavailable")

    return {
        "status": overall,
        "provider": provider,
        "configured_model": model,
        "providers": providers,
    }
