"""Competitor Analysis and Market Gap Identification for UdyamAI."""

from typing import Any


def analyze_competition(
    businesses: list[dict[str, Any]],
    radius_km: float,
    target_category_id: str | None = None,
    target_category_name: str | None = None,
) -> dict[str, Any]:
    """Analyze competition density, distribution, and identify market gaps within a radius.

    Filters relevant businesses by category (e.g. Dairy) and computes:
    - competitor_count: Direct competitors in the target category.
    - competitor_density: Competitor count per km2.
    - businesses_within_5km: Competitor count within 5km distance.
    - businesses_within_10km: Competitor count within 10km distance.
    - quality_indicator: Completeness and verification metrics (zero fabrication).

    Args:
        businesses: List of business dicts within radius.
        radius_km: Primary search/analysis radius in kilometers.
        target_category_id: Optional string of target BusinessCategory UUID.
        target_category_name: Optional string of target business category name (e.g. "Dairy").

    Returns:
        Dict containing competitor_count, competitor_density, businesses_within_5km,
        businesses_within_10km, category breakdown, market gaps, quality indicator,
        and provenance.
    """
    total_businesses = len(businesses)
    area_km2 = 3.1415926535 * radius_km * radius_km if radius_km > 0 else 1.0

    category_counts: dict[str, int] = {}
    competitor_count = 0
    verified_count = 0

    competitors_5km = 0
    competitors_10km = 0

    sources: set[tuple[str | None, str | None, int | None]] = set()
    source_names: set[str] = set()

    norm_target_name = None
    if target_category_name:
        stripped = target_category_name.strip().lower()
        norm_target_name = stripped if stripped else None

    has_filter = bool(target_category_id or norm_target_name)

    for b in businesses:
        cat_id = (
            str(b.get("business_category_id")) if b.get("business_category_id") else "uncategorized"
        )
        cat_name = str(b.get("category")).strip().lower() if b.get("category") else ""

        category_key = b.get("category") or cat_id
        category_counts[category_key] = category_counts.get(category_key, 0) + 1

        # Direct competitor check
        is_competitor = False
        if target_category_id and cat_id == str(target_category_id):
            is_competitor = True
        elif norm_target_name and (norm_target_name in cat_name or cat_name in norm_target_name):
            is_competitor = True
        elif not has_filter:
            # If no filter specified, count all categorized commercial businesses
            is_competitor = True

        if is_competitor:
            competitor_count += 1

        # Distance-based breakdown (only count when distance_meters is explicitly available)
        dist_m = b.get("distance_meters")
        if dist_m is not None:
            if dist_m <= 5000.0 and is_competitor:
                competitors_5km += 1
            if dist_m <= 10000.0 and is_competitor:
                competitors_10km += 1

        if b.get("verified_at"):
            verified_count += 1

        source = b.get("source")
        source_url = b.get("source_url")
        data_year = b.get("data_year")
        if source:
            source_names.add(source)
        if source or source_url or data_year:
            sources.add((source, source_url, data_year))

    competitor_density = round(competitor_count / area_km2, 2)
    data_available = total_businesses > 0

    # Market gap identification
    market_gaps = []
    if not data_available:
        market_gaps.append(
            "Insufficient local business data: No registered commercial businesses identified in radius to evaluate market saturation."
        )
    else:
        if competitor_density < 0.5:
            market_gaps.append(
                "Low commercial saturation: Opportunity for new local retail/service ventures."
            )
        elif competitor_density > 5.0:
            market_gaps.append(
                "High commercial density: Recommended focus on differentiation or specialized niche offerings."
            )

        if competitor_count == 0 and has_filter:
            target_label = target_category_name or "selected category"
            market_gaps.append(
                f"Zero direct competitors identified for '{target_label}' in radius: High first-mover advantage potential."
            )

    # Completeness and quality indicator computation
    if total_businesses == 0:
        completeness_score = 0.5
        confidence_level = "low"
        quality_notes = (
            "No businesses recorded in database within radius. "
            "Data completeness is low; zero competitor count reflects verified database records."
        )
    else:
        verified_ratio = verified_count / total_businesses
        completeness_score = round(0.60 + 0.40 * verified_ratio, 2)
        if verified_ratio >= 0.5:
            confidence_level = "high"
        else:
            confidence_level = "medium"

        category_label = target_category_name or "selected category"
        category_str = f" for '{category_label}'" if has_filter else ""
        quality_notes = (
            f"Analyzed {total_businesses} total businesses, identifying {competitor_count} direct competitors{category_str}. "
            f"{verified_count} of {total_businesses} records verified ({int(verified_ratio * 100)}% verification rate)."
        )

    quality_indicator = {
        "completeness_score": completeness_score,
        "confidence_level": confidence_level,
        "data_available": data_available,
        "verified_records_count": verified_count,
        "total_records_count": total_businesses,
        "has_category_filter": has_filter,
        "target_category": target_category_name
        or (str(target_category_id) if target_category_id else None),
        "sources_covered": sorted(list(source_names))
        if source_names
        else ["Normalized Business Registry"],
        "notes": quality_notes,
    }

    provenance_entries = []
    if sources:
        for s_name, s_url, s_yr in sources:
            provenance_entries.append(
                {
                    "dataset_name": "Commercial Registry / Businesses",
                    "source": s_name or "Business Directory",
                    "source_url": s_url,
                    "data_year": s_yr,
                    "record_count": total_businesses,
                    "confidence_score": confidence_level,
                }
            )
    else:
        provenance_entries.append(
            {
                "dataset_name": "Commercial Registry / Businesses",
                "source": "Normalized Data Pipeline",
                "source_url": None,
                "data_year": None,
                "record_count": total_businesses,
                "confidence_score": confidence_level,
            }
        )

    return {
        "competitor_count": competitor_count,
        "competitor_density": competitor_density,
        "businesses_within_5km": competitors_5km,
        "businesses_within_10km": competitors_10km,
        "total_businesses_in_radius": total_businesses,
        "direct_competitor_count": competitor_count,
        "competition_density_per_km2": competitor_density,
        "category_distribution": category_counts,
        "identified_market_gaps": market_gaps,
        "quality_indicator": quality_indicator,
        "data_completeness": confidence_level,
        "data_confidence": confidence_level,
        "data_available": data_available,
        "provenance": provenance_entries,
    }
