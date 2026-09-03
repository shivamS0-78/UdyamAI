"""Supabase Auth integration for UdyamAI.

Verifies the access tokens that the Supabase JS client issues after a
user signs in (phone OTP / email / OAuth). Supabase access tokens are
standard JWTs. Newer Supabase projects sign user tokens with ES256
(asymmetric keys published in the project's JWKS endpoint), while the
project's JWT secret (HS256) is still used for older projects and for
API keys (anon/service). We support both so tokens verify without
calling the Supabase API.
"""

import json
import logging
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from jose import jwk as jose_jwk

from app.config import settings

logger = logging.getLogger(__name__)

SUPABASE_ISSUER_SUFFIX = ".supabase.co"
DEFAULT_JWT_ALGORITHM = "HS256"
JWKS_PATH = "/auth/v1/.well-known/jwks.json"
_JWKS_CACHE_TTL_SECONDS = 300

# kid -> (public key, fetched_at); keeps the ES256 public keys warm and
# refetches quickly if the project rotates its signing keys.
_jwks_cache: dict[str, tuple[Any, float]] = {}


def _get_jwks_public_key(issuer: str, kid: str) -> Any:
    """Return the project's public key for ``kid`` from the JWKS endpoint.

    The issuer in Supabase access tokens looks like
    ``https://<ref>.supabase.co/auth/v1``; the JWKS endpoint sits at the
    same origin under ``/.well-known/jwks.json``.
    """
    now = time.time()
    cached = _jwks_cache.get(kid)
    if cached and now - cached[1] < _JWKS_CACHE_TTL_SECONDS:
        return cached[0]

    base = issuer.rstrip("/")
    if base.endswith("/auth/v1"):
        base = base[: -len("/auth/v1")]
    jwks_url = base + JWKS_PATH

    with urllib.request.urlopen(jwks_url, timeout=10) as resp:
        data = resp.read().decode("utf-8")
    try:
        jwks: dict[str, Any] = json.loads(data)
    except json.JSONDecodeError as exc:  # pragma: no cover - network data
        raise RuntimeError("Supabase JWKS endpoint returned invalid JSON") from exc

    key_dict = next(
        (k for k in jwks.get("keys", []) if k.get("kid") == kid),
        None,
    )
    if key_dict is None:
        raise ValueError("Invalid or expired access token")

    public_key = jose_jwk.construct(key_dict, algorithm="ES256")
    _jwks_cache[kid] = (public_key, now)
    return public_key


def _token_header_alg(token: str) -> str | None:
    try:
        return jwt.get_unverified_header(token).get("alg")
    except JWTError:
        return None


@dataclass(frozen=True)
class AuthUser:
    """Identity extracted from a verified Supabase access token."""

    sub: str
    phone: str | None = None
    email: str | None = None
    role: str | None = None

    @property
    def id(self) -> UUID:
        return UUID(self.sub)


def _jwt_secret() -> str:
    secret = settings.SUPABASE_JWT_SECRET
    if not secret:
        raise ValueError(
            "Supabase auth is not configured: set SUPABASE_JWT_SECRET "
            "(Project Settings -> API -> JWT Settings) in the environment."
        )
    return secret


def verify_supabase_token(token: str) -> AuthUser:
    """Decode and validate a Supabase access token.

    Supports both HS256 tokens (verified with the project JWT secret) and
    ES256 tokens (verified with the project's public keys from the JWKS
    endpoint). Raises ``ValueError`` when the token is missing, malformed,
    expired, or signed with a different key, and ``RuntimeError`` when
    auth is not configured server-side.
    """
    if not token:
        raise ValueError("Missing access token")

    alg = _token_header_alg(token)
    if alg is None:
        raise ValueError("Invalid or expired access token")

    try:
        if alg == DEFAULT_JWT_ALGORITHM:
            try:
                key: Any = _jwt_secret()
            except ValueError as exc:
                logger.warning("Supabase auth misconfigured: %s", exc)
                raise RuntimeError(str(exc)) from exc
        else:
            try:
                claims_unverified: dict[str, Any] = jwt.get_unverified_claims(token)
                kid = jwt.get_unverified_header(token).get("kid")
                issuer = claims_unverified.get("iss") or f"https://{settings.SUPABASE_URL}"
            except (JWTError, TypeError) as exc:
                raise ValueError("Invalid or expired access token") from exc
            if not kid or not issuer:
                raise ValueError("Invalid or expired access token")
            key = _get_jwks_public_key(str(issuer), str(kid))

        try:
            claims: dict[str, Any] = jwt.decode(
                token,
                key,
                algorithms=[alg],
                options={"verify_aud": False, "require": ["exp", "sub"]},
            )
        except JWTError:
            if alg != DEFAULT_JWT_ALGORITHM:
                # The cached key may predate a key rotation: refetch once
                # and retry before declaring the token invalid.
                kid = jwt.get_unverified_header(token).get("kid")
                _jwks_cache.pop(str(kid), None)
                key = _get_jwks_public_key(str(issuer), str(kid))
                claims = jwt.decode(
                    token,
                    key,
                    algorithms=[alg],
                    options={"verify_aud": False, "require": ["exp", "sub"]},
                )
            else:
                raise
    except ValueError as exc:
        logger.info("Supabase token verification failed: %s", exc)
        raise
    except JWTError as exc:
        logger.info("Supabase token verification failed: %s", exc)
        raise ValueError("Invalid or expired access token") from exc

    # Belt-and-braces: reject tokens that are already expired even if the
    # verifier above was lenient.
    exp = claims.get("exp")
    if exp is not None:
        try:
            if datetime.fromtimestamp(exp, tz=timezone.utc) <= datetime.now(timezone.utc):
                raise ValueError("Invalid or expired access token")
        except (TypeError, OSError, OverflowError) as exc:
            raise ValueError("Invalid or expired access token") from exc

    sub = claims.get("sub")
    if not sub:
        raise ValueError("Access token is missing the subject claim")

    return AuthUser(
        sub=str(sub),
        phone=str(claims["phone"]) if claims.get("phone") else None,
        email=str(claims["email"]) if claims.get("email") else None,
        role=str(claims["role"]) if claims.get("role") else None,
    )


def get_bearer_token(authorization: str | None) -> str | None:
    """Extract the bearer token from an ``Authorization`` header."""
    if not authorization:
        return None
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() != "bearer" or not value.strip():
        return None
    return value.strip()
