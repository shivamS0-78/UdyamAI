"""Demand Indicators and Market Demand Analysis for UdyamAI."""

from typing import Any


def calculate_demand_indicators(
    population_reach: int,
    household_reach: int,
    working_population: int,
    economic_records: list[dict[str, Any]],
    agriculture_records: list[dict[str, Any]],
    radius_km: float,
) -> dict[str, Any]:
    """Calculate demand indicators for a location within a given radius.

    Args:
        population_reach: Total population in radius.
        household_reach: Total households in radius.
        working_population: Total working population in radius.
        economic_records: List of economic indicator records in area.
        agriculture_records: List of agriculture records in area.
        radius_km: Search radius in km.

    Returns:
        Dict containing calculated demand metrics, purchasing power index, and provenance.
    """
    working_ratio = round(working_population / population_reach, 3) if population_reach > 0 else 0.0

    avg_household_size = (
        round(population_reach / household_reach, 2) if household_reach > 0 else 0.0
    )

    # Compute crop revenue proxy if agricultural records exist
    total_agri_production = sum(rec.get("production") or 0.0 for rec in agriculture_records)
    total_cultivated_area = sum(rec.get("cultivated_area") or 0.0 for rec in agriculture_records)

    # Compute economic indicators summary
    econ_summary = {}
    for rec in economic_records:
        name = rec.get("indicator_name")
        val = rec.get("indicator_value")
        if name and val is not None:
            econ_summary[name] = val

    # Demand score (0.0 to 100.0) based on population density and working ratio
    density_per_km2 = (
        round(population_reach / (3.14159 * radius_km * radius_km), 1) if radius_km > 0 else 0.0
    )
    demand_score = min(100.0, round((density_per_km2 * 0.4) + (working_ratio * 100 * 0.6), 1))

    # Provenance tracking
    provenance_entries = []
    if economic_records:
        provenance_entries.append(
            {
                "dataset_name": "Economic Indicators",
                "source": economic_records[0].get("source") or "Government Statistics",
                "source_url": economic_records[0].get("source_url"),
                "data_year": economic_records[0].get("data_year"),
                "record_count": len(economic_records),
                "confidence_score": "high",
            }
        )

    if agriculture_records:
        provenance_entries.append(
            {
                "dataset_name": "Agriculture & Crops",
                "source": agriculture_records[0].get("source") or "Agri Dept",
                "source_url": agriculture_records[0].get("source_url"),
                "data_year": agriculture_records[0].get("data_year"),
                "record_count": len(agriculture_records),
                "confidence_score": "high",
            }
        )

    return {
        "demand_score": demand_score,
        "population_density_per_km2": density_per_km2,
        "working_population_ratio": working_ratio,
        "average_household_size": avg_household_size,
        "agricultural_production_units": total_agri_production,
        "total_cultivated_area_hectares": total_cultivated_area,
        "economic_indicators_summary": econ_summary,
        "provenance": provenance_entries,
    }
