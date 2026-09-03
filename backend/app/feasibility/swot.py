"""SWOT Indicator Builder for UdyamAI.

Extracts structured empirical strength, weakness, opportunity, and threat indicators
from numerical data, infrastructure maps, competition metrics, and scheme matches.
These structured indicators are passed to the AI narrative generator.
"""


def build_swot_indicators(
    market_scores: dict[str, float] | None = None,
    population_reach: int = 0,
    household_reach: int = 0,
    available_capital: float = 0.0,
    desired_project_cost: float = 0.0,
    estimated_subsidy: float = 0.0,
    competition_density: float = 0.0,
    facility_counts: dict[str, int] | None = None,
    identified_risk_flags: list[str] | None = None,
    matched_scheme_names: list[str] | None = None,
    nearest_market_distance_km: float | None = None,
    competition_data_available: bool = True,
    market_data_available: bool = True,
    financial_data_available: bool = True,
    infrastructure_data_available: bool = True,
    risk_data_available: bool = True,
) -> dict[str, list[str]]:
    """Build structured SWOT indicators based on empirical rules.

    Returns:
        Dict containing:
        - strength_indicators: list[str]
        - weakness_indicators: list[str]
        - opportunity_indicators: list[str]
        - threat_indicators: list[str]
    """
    if market_scores is None:
        market_scores = {}
    if facility_counts is None:
        facility_counts = {}
    if identified_risk_flags is None:
        identified_risk_flags = []
    if matched_scheme_names is None:
        matched_scheme_names = []

    strengths: list[str] = []
    weaknesses: list[str] = []
    opportunities: list[str] = []
    threats: list[str] = []

    # 1. Strengths
    if market_data_available:
        if population_reach >= 10000:
            strengths.append(
                f"High population reach: {population_reach:,} residents within primary analysis radius."
            )
        elif population_reach >= 5000:
            strengths.append(
                f"Moderate population reach: {population_reach:,} residents available locally."
            )

    if financial_data_available and desired_project_cost > 0:
        equity_pct = (available_capital / desired_project_cost) * 100.0
        if equity_pct >= 30.0:
            strengths.append(
                f"Strong financial equity position: {equity_pct:.1f}% self-contribution available (INR {available_capital:,.0f})."
            )

    if competition_data_available:
        if competition_density <= 2.0:
            strengths.append(
                f"Favorable competitive environment: Low competitor density of {competition_density:.2f} units/km²."
            )

    fin_infra = facility_counts.get("bank", 0) + facility_counts.get("atm", 0)
    if infrastructure_data_available and fin_infra >= 2:
        strengths.append(
            f"Established financial access: {fin_infra} formal banking/ATM facilities in radius."
        )

    # 2. Weaknesses
    if not competition_data_available:
        weaknesses.append(
            "Insufficient data to assess competition: No commercial business records found within analysis radius."
        )

    if not market_data_available:
        weaknesses.append(
            "Insufficient data to assess market access: No local commercial market or population records identified."
        )

    if financial_data_available and desired_project_cost > 0:
        equity_pct = (available_capital / desired_project_cost) * 100.0
        if equity_pct < 15.0:
            weaknesses.append(
                f"Low self-capital contribution: Only {equity_pct:.1f}% equity available, requiring high debt financing."
            )

    logistics_infra = facility_counts.get("cold_storage", 0) + facility_counts.get("warehouse", 0)
    if infrastructure_data_available:
        if logistics_infra == 0:
            weaknesses.append(
                "Logistics infrastructure deficit: Zero cold storage or warehousing facilities identified within radius."
            )
        if fin_infra == 0:
            weaknesses.append(
                "Financial infrastructure gap: Zero formal banking or ATM facilities within radius."
            )

    if (
        market_data_available
        and nearest_market_distance_km is not None
        and nearest_market_distance_km > 10.0
    ):
        weaknesses.append(
            f"Distant market access: Nearest commercial mandi is {nearest_market_distance_km:.1f}km away."
        )

    # 3. Opportunities
    if matched_scheme_names:
        schemes_str = ", ".join(matched_scheme_names[:3])
        opportunities.append(
            f"Government scheme eligibility: Qualified for subsidy support under {schemes_str}."
        )

    if estimated_subsidy > 0:
        opportunities.append(
            f"Capital subsidy potential: Estimated financial support of up to INR {estimated_subsidy:,.0f} available."
        )

    if competition_data_available and 0.0 <= competition_density <= 3.0:
        opportunities.append(
            "Early market entrant opportunity: Unmet local demand with low competitor saturation."
        )

    if infrastructure_data_available and logistics_infra > 0:
        opportunities.append(
            f"Existing logistics access: {logistics_infra} storage/cold chain facilities available for supply chain integration."
        )

    # 4. Threats
    if competition_data_available and competition_density >= 6.0:
        threats.append(
            f"High market competition: {competition_density:.2f} competitors/km² identified in local market."
        )

    if not risk_data_available:
        threats.append("Market Risk: Insufficient data to evaluate local market risk indicators.")
    else:
        for flag in identified_risk_flags:
            threats.append(f"Market Risk: {flag}")

    return {
        "strength_indicators": strengths,
        "weakness_indicators": weaknesses,
        "opportunity_indicators": opportunities,
        "threat_indicators": threats,
    }
