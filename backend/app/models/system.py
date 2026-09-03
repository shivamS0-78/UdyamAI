from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import Profile


class RecycleBinItem(SQLModel, table=True):
    """Stores deleted items for recovery or permanent deletion"""

    __tablename__ = "recycle_bin_items"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    profile_id: UUID = Field(foreign_key="profiles.id", nullable=False, index=True)
    item_type: str = Field(
        nullable=False,
        description="expense, cash_flow, savings_goal, budget, debt, borrowing, credit_score",
    )
    item_id: UUID = Field(nullable=False, description="Original item ID")
    item_data: str = Field(nullable=False, description="JSON serialized item data for recovery")
    deleted_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = Field(default=None, description="Auto-purge date")
    restored: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    profile: "Profile" = Relationship(back_populates="recycle_bin_items")


class PrivacyConsent(SQLModel, table=True):
    """Tracks user data sharing and privacy preferences"""

    __tablename__ = "privacy_consents"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    profile_id: UUID = Field(foreign_key="profiles.id", nullable=False, index=True)
    consent_type: str = Field(
        nullable=False,
        description="data_sharing, analytics, marketing, ai_processing, third_party_sharing",
    )
    granted: bool = Field(nullable=False)
    granted_at: datetime | None = Field(default=None)
    revoked_at: datetime | None = Field(default=None)
    version: str = Field(default="1.0", description="Consent policy version")
    ip_address: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    profile: "Profile" = Relationship(back_populates="privacy_consents")


class UserSettings(SQLModel, table=True):
    """Application settings and preferences"""

    __tablename__ = "user_settings"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    profile_id: UUID = Field(foreign_key="profiles.id", nullable=False, index=True, unique=True)
    currency: str = Field(default="INR")
    date_format: str = Field(default="DD/MM/YYYY")
    notification_email: bool = Field(default=True)
    notification_sms: bool = Field(default=False)
    notification_push: bool = Field(default=True)
    language: str = Field(default="en", description="en, hi, mr")
    theme: str = Field(default="light", description="light, dark, system")
    default_view: str = Field(default="dashboard", description="dashboard, expenses, cashflow")
    auto_backup: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    profile: "Profile" = Relationship(back_populates="settings")
