from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import SupportedLanguage


class ReportCreateRequest(BaseModel):
    analysis_run_id: UUID
    user_id: UUID
    title: str | None = Field(default=None, max_length=255)
    language: SupportedLanguage = Field(
        default=SupportedLanguage.EN, description="Supported report language ('en', 'hi', 'mr')"
    )


class ReportResponse(BaseModel):
    id: UUID
    analysis_run_id: UUID
    user_id: UUID
    title: str | None = Field(default=None, max_length=255)
    language: SupportedLanguage | None = Field(default=SupportedLanguage.EN)
    report_data: dict[str, Any] | None = None
    report_file_path: str | None = Field(default=None, max_length=500)
    created_at: datetime

    model_config = {"from_attributes": True}
