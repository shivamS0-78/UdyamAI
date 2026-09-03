"""Infrastructure Analysis for Market Assessment in UdyamAI."""

from typing import Any


def analyze_relevant_infrastructure(
    facilities: list[dict[str, Any]],
) -> dict[str, Any]:
    """Analyze and categorize relevant infrastructure facilities within a radius.

    Args:
        facilities: List of facility dicts with keys like 'name', 'facility_type',
            'distance_meters', 'capacity', 'source', etc.

    Returns:
        Dict containing facility counts by type, detailed summaries, and provenance.
    """
    categorized: dict[str, list[dict[str, Any]]] = {}
    facility_summaries = []

    sources: set[tuple[str | None, str | None, int | None]] = set()

    for f in facilities:
        ftype = f.get("facility_type") or "other"
        distance_km = round((f.get("distance_meters") or 0.0) / 1000.0, 2)
        summary_item = {
            "id": f.get("id"),
            "name": f.get("name") or f"{ftype.title()} Facility",
            "facility_type": ftype,
            "distance_km": distance_km,
            "capacity": f.get("capacity"),
        }
        facility_summaries.append(summary_item)

        if ftype not in categorized:
            categorized[ftype] = []
        categorized[ftype].append(summary_item)

        source = f.get("source")
        source_url = f.get("source_url")
        data_year = f.get("data_year")
        if source or source_url or data_year:
            sources.add((source, source_url, data_year))

    counts_by_type = {ftype: len(items) for ftype, items in categorized.items()}

    provenance_entries = []
    if sources:
        for s_name, s_url, s_yr in sources:
            provenance_entries.append(
                {
                    "dataset_name": "Infrastructure & Facilities",
                    "source": s_name or "GIS Infrastructure Registry",
                    "source_url": s_url,
                    "data_year": s_yr,
                    "record_count": len(facilities),
                    "confidence_score": "high",
                }
            )
    else:
        provenance_entries.append(
            {
                "dataset_name": "Infrastructure & Facilities",
                "source": "Normalized Data Pipeline",
                "source_url": None,
                "data_year": None,
                "record_count": len(facilities),
                "confidence_score": "medium",
            }
        )

    return {
        "total_facilities": len(facilities),
        "facility_counts_by_type": counts_by_type,
        "facility_summaries": facility_summaries,
        "provenance": provenance_entries,
    }
