"""LLM provider abstraction.

Keeps the AI Advisor decoupled from any specific model/provider — swapping
providers should mean an env var change, not touching advisor.py, prompts.py,
or guardrails.py.
"""

from __future__ import annotations

import logging
import os

from app.config import settings

logger = logging.getLogger(__name__)

# Ordered fallback lists — tried in sequence when the preferred model fails.
# To switch providers, change AI_PROVIDER / AI_MODEL env vars; never edit this file.
_GEMINI_MODELS = (
    "gemini-3.6-flash",
    "gemini-3-flash-preview",
    "gemini-2.5-flash",
)
_OPENAI_MODELS = (
    "gpt-4o-mini",
    "gpt-4.1-mini",
    "gpt-4o",
)


class LLMError(Exception):
    """Raised on provider failure/timeout/misconfiguration."""

    def __init__(self, message: str, *, error_code: str = "AI_PROVIDER_UNAVAILABLE") -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


def _configured_provider() -> str:
    return (os.getenv("AI_PROVIDER") or settings.AI_PROVIDER or "gemini").lower()


def _configured_model() -> str | None:
    return os.getenv("AI_MODEL") or settings.AI_MODEL


def _error_code_for_exception(exc: Exception) -> str:
    text = str(exc).lower()
    if "timeout" in text or "timed out" in text:
        return "AI_TIMEOUT"
    if "rate limit" in text or "429" in text or "too many requests" in text:
        return "AI_RATE_LIMITED"
    if "content filter" in text or "safety" in text or "blocked" in text:
        return "AI_CONTENT_FILTERED"
    if "context" in text or "token" in text or "too large" in text:
        return "AI_CONTEXT_TOO_LARGE"
    return "AI_PROVIDER_UNAVAILABLE"


def _unique(models: list[str | None]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for model in models:
        if not model:
            continue
        if model in seen:
            continue
        seen.add(model)
        ordered.append(model)
    return ordered


def _gemini_models() -> list[str]:
    """Return Gemini model IDs to try, env-configured model first."""
    configured = _configured_model()
    preferred = configured if configured and "gpt" not in configured.lower() else None
    return _unique([preferred, *_GEMINI_MODELS])


def _openai_models() -> list[str]:
    """Return OpenAI model IDs to try, env-configured model first."""
    configured = _configured_model()
    preferred = configured if configured and not configured.lower().startswith("gemini") else None
    return _unique([preferred, *_OPENAI_MODELS])


def generate(prompt: str) -> str:
    """Call the configured provider and return its raw text response.

    Tries the preferred provider first, then the other provider, using
    provider-specific model names (never send a Gemini model id to OpenAI).
    """
    preferred = _configured_provider()
    order = ["gemini", "openai"] if preferred != "openai" else ["openai", "gemini"]
    errors: list[str] = []

    for provider in order:
        try:
            if provider == "gemini" and settings.GEMINI_API_KEY:
                return _generate_gemini(prompt)
            if provider == "openai" and settings.OPENAI_API_KEY:
                return _generate_openai(prompt)
        except LLMError as exc:
            logger.warning("%s generation failed: %s", provider, exc)
            errors.append(f"{provider}: {exc}")
            continue

    detail = "; ".join(errors) if errors else "No AI provider is configured"
    raise LLMError(detail, error_code="AI_PROVIDER_UNAVAILABLE")


def _generate_openai(prompt: str) -> str:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise LLMError(
            "openai package not installed", error_code="AI_PROVIDER_UNAVAILABLE"
        ) from exc

    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise LLMError("OPENAI_API_KEY not configured", error_code="AI_PROVIDER_UNAVAILABLE")

    client = OpenAI(api_key=api_key, timeout=30.0)
    last_error: Exception | None = None
    for model in _openai_models():
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=500,
            )
        except Exception as exc:
            last_error = exc
            logger.warning("OpenAI model %s failed: %s", model, exc)
            continue

        try:
            content = response.choices[0].message.content
        except (IndexError, AttributeError, TypeError) as exc:
            last_error = exc
            continue

        if content:
            return content

    raise LLMError(
        str(last_error) if last_error else "OpenAI returned empty content",
        error_code=_error_code_for_exception(last_error) if last_error else "AI_INVALID_OUTPUT",
    )


def _extract_gemini_text(response: object) -> str | None:
    text = getattr(response, "text", None)
    if text:
        return str(text)
    parts: list[str] = []
    for candidate in getattr(response, "candidates", None) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", None) or []:
            part_text = getattr(part, "text", None)
            if part_text:
                parts.append(str(part_text))
    return "\n".join(parts) if parts else None


def _generate_gemini(prompt: str) -> str:
    try:
        from google import genai
    except ImportError as exc:
        raise LLMError(
            "google-genai package not installed", error_code="AI_PROVIDER_UNAVAILABLE"
        ) from exc

    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise LLMError("GEMINI_API_KEY not configured", error_code="AI_PROVIDER_UNAVAILABLE")

    try:
        client = genai.Client(api_key=api_key, http_options={"timeout": 25_000})
    except TypeError:
        client = genai.Client(api_key=api_key)

    last_error: Exception | None = None
    for model in _gemini_models():
        try:
            response = client.models.generate_content(model=model, contents=prompt)
        except Exception as exc:
            last_error = exc
            logger.warning("Gemini model %s failed: %s", model, exc)
            continue

        text = _extract_gemini_text(response)
        if text:
            return text
        last_error = LLMError("Gemini returned no usable content", error_code="AI_INVALID_OUTPUT")

    raise LLMError(
        str(last_error) if last_error else "Gemini returned no usable content",
        error_code=_error_code_for_exception(last_error) if last_error else "AI_INVALID_OUTPUT",
    )
