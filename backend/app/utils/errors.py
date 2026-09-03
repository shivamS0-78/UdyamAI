import logging
import re
from typing import Any

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("udyam_ai")

# Regex pattern to catch sensitive secrets, credentials, or tokens
SENSITIVE_PATTERNS = re.compile(
    r"(eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*|sb_p_[A-Za-z0-9]+|pk_(?:live|test)_[A-Za-z0-9]+|sk_(?:live|test)_[A-Za-z0-9]+|secret_[A-Za-z0-9]+|password\s*=\s*\S+|key\s*=\s*\S+|token\s*=\s*\S+)",
    re.IGNORECASE,
)
SENSITIVE_PATTERN = SENSITIVE_PATTERNS


class AppException(StarletteHTTPException):
    """Custom application exception with structured error code and message."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(
            status_code=status_code,
            detail={"code": code, "message": message},
            headers=headers,
        )
        self.code = code
        self.message = message


def _sanitize_message(msg: str) -> str:
    """Removes sensitive secrets, passwords, or keys from user-facing error messages."""
    return SENSITIVE_PATTERNS.sub("[REDACTED]", msg)


def _map_status_to_code(status_code: int, detail_str: str) -> tuple[str, str]:
    """Helper mapping standard HTTP status codes and detail strings to structured error codes."""
    detail_lower = detail_str.lower()
    if "required" in detail_lower or "missing" in detail_lower:
        return (
            "MISSING_REQUIRED_FIELD",
            detail_str or "A required field or parameter is missing.",
        )
    if "location" in detail_lower or "village" in detail_lower or "taluka" in detail_lower:
        return "LOCATION_NOT_FOUND", detail_str or "The selected village could not be found."
    if "category" in detail_lower or "business" in detail_lower:
        return (
            "BUSINESS_CATEGORY_NOT_FOUND",
            detail_str or "The selected business category could not be found.",
        )
    if "margin" in detail_lower or "capital" in detail_lower or "shortfall" in detail_lower:
        return (
            "INSUFFICIENT_MARGIN",
            detail_str or "Available capital is insufficient for the required project margin.",
        )
    if "scheme" in detail_lower or "rule" in detail_lower:
        return "INVALID_SCHEME_RULE", detail_str or "Invalid scheme rule parameter provided."
    if "calculation" in detail_lower or "math" in detail_lower:
        return "CALCULATION_ERROR", detail_str or "Financial or feasibility calculation failed."
    if "ai" in detail_lower or "advisor" in detail_lower or "llm" in detail_lower:
        return "AI_UNAVAILABLE", detail_str or "AI advice service is currently unavailable."
    if "data" in detail_lower:
        return "MISSING_DATA", detail_str or "Required analysis data is missing or incomplete."

    if status_code == 404:
        return "NOT_FOUND", detail_str
    if status_code == 400:
        return "BAD_REQUEST", detail_str
    if status_code == 422:
        return "UNPROCESSABLE_ENTITY", detail_str
    return "HTTP_ERROR", detail_str


def _is_database_error(exc: Exception) -> bool:
    """Determines whether an exception is related to database operations without false positives."""
    if isinstance(exc, SQLAlchemyError):
        return True

    exc_module = getattr(exc.__class__, "__module__", "")
    if exc_module and any(
        exc_module.startswith(pkg)
        for pkg in ("sqlalchemy", "psycopg", "asyncpg", "sqlite3", "geoalchemy2")
    ):
        return True

    exc_str = str(exc).lower()
    db_patterns = (
        r"\bsqlalchemy\b",
        r"\bpsycopg\b",
        r"\bpostgres(?:ql)?\b",
        r"\bsqlite\b",
        r"\bdatabase\b",
        r"\boperationalerror\b",
        r"\bintegrityerror\b",
        r"\bprogrammingerror\b",
        r"\binterfaceerror\b",
        r"\bdataerror\b",
    )
    return any(re.search(pat, exc_str) for pat in db_patterns)


def setup_exception_handlers(app: Any) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.error(f"HTTP error on {request.url.path}: {exc.detail}")

        if isinstance(exc.detail, dict):
            if "code" in exc.detail and "message" in exc.detail:
                code = exc.detail["code"]
                message = _sanitize_message(str(exc.detail["message"]))
            else:
                code = f"HTTP_{exc.status_code}"
                message = _sanitize_message(str(exc.detail))
            detail = exc.detail
        elif isinstance(exc.detail, str):
            code, message = _map_status_to_code(exc.status_code, exc.detail)
            message = _sanitize_message(message)
            detail = message
        else:
            code = f"HTTP_{exc.status_code}"
            message = _sanitize_message(str(exc.detail))
            detail = str(exc.detail)

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": code,
                    "message": message,
                },
                "detail": detail,
                "error_code": code,
                "status_code": exc.status_code,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        raw_errors = jsonable_encoder(exc.errors())
        logger.error(f"Validation error on {request.url.path}: {raw_errors}")
        first_err = exc.errors()[0] if exc.errors() else {}
        loc_str = " -> ".join(str(loc_item) for loc_item in first_err.get("loc", []))
        msg = f"Validation failed at {loc_str}: {first_err.get('msg', 'invalid input')}"
        msg = _sanitize_message(msg)

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": msg,
                },
                "detail": msg,
                "errors": raw_errors,
                "error_code": "VALIDATION_ERROR",
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled error on {request.url.path}: {str(exc)}")

        if _is_database_error(exc):
            code = "DATABASE_ERROR"
            message = "A database operation failed."
        else:
            code = "INTERNAL_SERVER_ERROR"
            message = "An unexpected server error occurred."

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": code,
                    "message": message,
                },
                "detail": message,
                "error_code": code,
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            },
        )
