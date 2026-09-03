"""Market Size and Population Reach calculations for UdyamAI.

Calculates estimated population reach, estimated household reach across villages,
and target customer conversion (differentiating total population from customer base).
"""

from typing import Any


def calculate_population_and_household_reach(
    villages_within_radius: list[dict[str, Any]],
    population_by_village: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Calculate aggregate estimated population reach and household reach.

    Args:
        villages_within_radius: List of village dictionaries found within the radius.
        population_by_village: Map of village_id (str) -> Population data dict
            (e.g., {'population_total': 1200, 'households': 250, 'working_population': 600, ...}).

    Returns:
        Dict with total population reach, household reach, working population,
        village count, and provenance details.
    """
    total_population = 0
    total_households = 0
    total_working = 0
    villages_with_pop_data = 0

    sources: set[tuple[str | None, str | None, int | None]] = set()

    for v in villages_within_radius:
        v_id = str(v.get("id"))
        pop_rec = population_by_village.get(v_id)
        if pop_rec:
            pop_val = pop_rec.get("population_total") or 0
            hh_val = pop_rec.get("households") or 0
            work_val = pop_rec.get("working_population") or 0

            total_population += pop_val
            total_households += hh_val
            total_working += work_val
            villages_with_pop_data += 1

            source = pop_rec.get("source")
            source_url = pop_rec.get("source_url")
            data_year = pop_rec.get("data_year")
            if source or source_url or data_year:
                sources.add((source, source_url, data_year))

    # Provenance summary for population dataset
    provenance_entries = []
    if sources:
        for s_name, s_url, s_yr in sources:
            provenance_entries.append(
                {
                    "dataset_name": "Census Population & Households",
                    "source": s_name or "Government Census / Data Pipeline",
                    "source_url": s_url,
                    "data_year": s_yr,
                    "record_count": villages_with_pop_data,
                    "confidence_score": "high" if s_name else "medium",
                }
            )
    else:
        provenance_entries.append(
            {
                "dataset_name": "Census Population & Households",
                "source": "Normalized Data Pipeline",
                "source_url": None,
                "data_year": None,
                "record_count": len(villages_within_radius),
                "confidence_score": "medium",
            }
        )

    return {
        "estimated_population_reach": total_population,
        "estimated_household_reach": total_households,
        "estimated_working_population": total_working,
        "villages_analyzed": len(villages_within_radius),
        "villages_with_data": villages_with_pop_data,
        "provenance": provenance_entries,
    }


def estimate_target_customers(
    estimated_population_reach: int,
    estimated_household_reach: int,
    conversion_rate: float = 0.05,
    household_targeting: bool = False,
) -> int:
    """Estimate addressable target customer reach from demographic numbers.

    CRITICAL PRINCIPLE: Total population is NOT automatically the customer base.
    Target customers are derived via targeting rules, conversion rates, and business model type.

    Args:
        estimated_population_reach: Total population in radius.
        estimated_household_reach: Total households in radius.
        conversion_rate: Target customer conversion/penetration percentage (0.0 to 1.0).
        household_targeting: If True, targeting unit is households instead of individuals.

    Returns:
        Estimated integer count of target customers.
    """
    base_count = estimated_household_reach if household_targeting else estimated_population_reach
    if base_count <= 0:
        return 0

    target = int(round(base_count * max(0.0, min(1.0, conversion_rate))))
    return target
