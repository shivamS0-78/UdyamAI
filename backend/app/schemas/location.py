from uuid import UUID

from pydantic import BaseModel, Field


class DistrictResponse(BaseModel):
    id: UUID
    name: str = Field(..., min_length=1, max_length=150)
    state: str = Field(..., min_length=1, max_length=150)
    lgd_code: str | None = Field(default=None, max_length=20)

    model_config = {"from_attributes": True}


class TalukaResponse(BaseModel):
    id: UUID
    name: str = Field(..., min_length=1, max_length=150)
    district_id: UUID
    lgd_code: str | None = Field(default=None, max_length=20)

    model_config = {"from_attributes": True}


class VillageResponse(BaseModel):
    id: UUID
    name: str = Field(..., min_length=1, max_length=150)
    district_id: UUID
    taluka_id: UUID
    gram_panchayat_id: UUID | None = None
    lgd_code: str | None = Field(default=None, max_length=20)
    pin_code: str | None = Field(
        default=None, pattern=r"^\d{6}$", description="6-digit Indian PIN code"
    )
    latitude: float | None = Field(
        default=None, ge=-90.0, le=90.0, description="Latitude between -90 and 90"
    )
    longitude: float | None = Field(
        default=None, ge=-180.0, le=180.0, description="Longitude between -180 and 180"
    )

    model_config = {"from_attributes": True}


class LocationQuery(BaseModel):
    search: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    district_id: UUID | None = None
    taluka_id: UUID | None = None
    limit: int = Field(default=50, ge=1, le=500, description="Maximum number of items to return")
    offset: int = Field(default=0, ge=0, description="Pagination offset")


# --- Normalization Schemas ---


class NormalizeRequest(BaseModel):
    """Request to normalize a raw location name."""

    name: str = Field(
        ..., min_length=1, max_length=200, description="Raw location name to normalize"
    )
    level: str = Field(
        default="village",
        pattern=r"^(district|taluka|gram_panchayat|village)$",
        description="Location hierarchy level",
    )


class NormalizeResponse(BaseModel):
    """Response from name normalization."""

    original: str
    normalized: str
    level: str


# --- Deduplication Schemas ---


class DedupGroupRecord(BaseModel):
    """A single record within a dedup group."""

    id: UUID
    name: str
    normalized: str
    lgd_code: str | None = None


class DedupGroup(BaseModel):
    """A group of potential duplicate locations."""

    normalized_name: str
    count: int
    records: list[DedupGroupRecord]
    district_id: str | None = None
    taluka_id: str | None = None


class DedupDetectResponse(BaseModel):
    """Response from dedup detection."""

    level: str
    total_groups: int
    groups: list[DedupGroup]


class MergeRequest(BaseModel):
    """Request to merge duplicate locations into one canonical record."""

    keep_id: UUID = Field(..., description="UUID of the record to keep (canonical)")
    merge_ids: list[UUID] = Field(
        ..., min_length=1, description="UUIDs of duplicate records to merge into keep_id"
    )
    level: str = Field(
        default="village",
        pattern=r"^(district|taluka|gram_panchayat|village)$",
        description="Location hierarchy level",
    )


class MergeResponse(BaseModel):
    """Response from a merge operation."""

    keep_id: UUID
    merged_count: int
    summary: dict[str, int]


# --- Nearby Query & Response Schemas ---


class NearbyQuery(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0, description="Center latitude")
    lng: float = Field(..., ge=-180.0, le=180.0, description="Center longitude")
    radius_km: float = Field(default=10.0, gt=0.0, le=100.0, description="Search radius in km")
    limit: int = Field(default=50, ge=1, le=200, description="Maximum results")


class NearbyVillageResponse(BaseModel):
    id: UUID
    name: str
    district_id: UUID
    taluka_id: UUID
    gram_panchayat_id: UUID | None = None
    pin_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    distance_meters: float = Field(..., description="Distance from center point in meters")

    model_config = {"from_attributes": True}


class NearbyBusinessResponse(BaseModel):
    id: UUID
    name: str | None = None
    category: str | None = None
    business_category_id: UUID | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    distance_meters: float = Field(..., description="Distance from center point in meters")

    model_config = {"from_attributes": True}


class NearbyMarketResponse(BaseModel):
    id: UUID
    name: str | None = None
    market_type: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    distance_meters: float = Field(..., description="Distance from center point in meters")

    model_config = {"from_attributes": True}


class NearbyFacilityResponse(BaseModel):
    id: UUID
    name: str | None = None
    facility_type: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    capacity: float | None = None
    distance_meters: float = Field(..., description="Distance from center point in meters")

    model_config = {"from_attributes": True}
