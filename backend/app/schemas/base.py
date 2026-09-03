"""Shared Pydantic base models, configurations, and reusable validators across schemas."""

from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class ORMBaseModel(BaseModel):
    """Base model configured with from_attributes=True for ORM compatibility."""

    model_config = ConfigDict(from_attributes=True)


class LocationValidatedModel(BaseModel):
    """Base model for request schemas requiring either village_id or latitude and longitude."""

    @model_validator(mode="after")
    def validate_location(self) -> Any:
        return validate_location_coordinates(self)


def normalize_market_dict_keys(data: Any) -> Any:
    """Normalize legacy and alternative market dictionary keys to canonical field names."""
    if isinstance(data, dict):
        if "population_estimate" not in data and "total_population_reach" in data:
            data["population_estimate"] = data.get("total_population_reach")
        elif "population_estimate" not in data and "estimated_population_reach" in data:
            data["population_estimate"] = data.get("estimated_population_reach")

        if "household_estimate" not in data and "household_reach" in data:
            data["household_estimate"] = data.get("household_reach")
        elif "household_estimate" not in data and "estimated_household_reach" in data:
            data["household_estimate"] = data.get("estimated_household_reach")

        if "market_reach_estimate" not in data and "estimated_target_customers" in data:
            data["market_reach_estimate"] = data.get("estimated_target_customers")
    return data


def normalize_competition_dict_keys(data: Any) -> Any:
    """Normalize legacy and alternative competition dictionary keys to canonical field names."""
    if isinstance(data, dict):
        if "competitor_count" not in data and "total_competitors_count" in data:
            data["competitor_count"] = data.get("total_competitors_count")
    return data


def normalize_swot_dict_keys(data: Any) -> Any:
    """Normalize legacy SWOT dictionary keys (strengths, weaknesses, etc.) to indicators list."""
    if isinstance(data, dict):
        if "strength_indicators" not in data and "strengths" in data:
            data["strength_indicators"] = data.get("strengths") or []
        if "weakness_indicators" not in data and "weaknesses" in data:
            data["weakness_indicators"] = data.get("weaknesses") or []
        if "opportunity_indicators" not in data and "opportunities" in data:
            data["opportunity_indicators"] = data.get("opportunities") or []
        if "threat_indicators" not in data and "threats" in data:
            data["threat_indicators"] = data.get("threats") or []
    return data


def validate_location_coordinates(obj: Any) -> Any:
    """Validate that either village_id or both latitude and longitude coordinates are provided."""
    village_id = getattr(obj, "village_id", None)
    latitude = getattr(obj, "latitude", None)
    longitude = getattr(obj, "longitude", None)

    if not village_id and (latitude is None or longitude is None):
        raise ValueError(
            "Either village_id or both latitude and longitude coordinates must be provided."
        )
    return obj


def add_location_validator(cls: type) -> type:
    """Decorator to add location coordinates validation across schema classes."""

    @model_validator(mode="after")
    def _validate(self: Any) -> Any:
        return validate_location_coordinates(self)

    cls.validate_location = _validate
    return cls
