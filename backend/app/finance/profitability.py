from typing import Any

from app.schemas.finance import FinancialScenarioResponse, ScenarioConfigInput


def generate_financial_scenarios(
    monthly_revenue: float | None = None,
    monthly_operating_cost: float | None = None,
    monthly_emi: float = 0.0,
    verified_revenue: float | None = None,
    verified_operating_cost: float | None = None,
    scenario_config: ScenarioConfigInput | None = None,
) -> list[FinancialScenarioResponse]:
    """
    Generates 3 financial scenarios (worst_case, expected_case, best_case) with DSCR repayment coverage.

    Fields supported:
    - revenue
    - operating costs
    - surplus (revenue - operating costs)
    - loan repayment (monthly EMI)
    - cash surplus (surplus - loan repayment)

    Data sources & rules:
    1. Verified data (verified_revenue, verified_operating_cost)
    2. Explicit user assumptions (monthly_revenue, monthly_operating_cost)
    3. Configurable assumptions (ScenarioConfigInput multipliers)
    Rule: Do not invent local revenue numbers. If insufficient revenue assumptions exist, return scenarios with sufficient_assumptions_exist=False.
    """
    # 1. Determine baseline revenue and operating cost source
    base_revenue: float | None = None
    base_cost: float = 0.0
    data_source: str | None = None

    if verified_revenue is not None and verified_revenue > 0:
        base_revenue = verified_revenue
        base_cost = (
            verified_operating_cost
            if verified_operating_cost is not None
            else (monthly_operating_cost or 0.0)
        )
        data_source = "verified_data"
    elif monthly_revenue is not None and monthly_revenue > 0:
        base_revenue = monthly_revenue
        base_cost = monthly_operating_cost if monthly_operating_cost is not None else 0.0
        data_source = "explicit_user_assumptions"

    scenario_names = ["worst_case", "expected_case", "best_case"]

    # 2. Check for sufficient assumptions ("Do not invent local revenue numbers")
    if base_revenue is None or base_revenue <= 0:
        scenario_responses: list[FinancialScenarioResponse] = []
        for name in scenario_names:
            scenario_responses.append(
                FinancialScenarioResponse(
                    scenario_type=name,
                    sufficient_assumptions_exist=False,
                    revenue=None,
                    operating_costs=None,
                    surplus=None,
                    loan_repayment=round(monthly_emi, 2),
                    cash_surplus=None,
                    monthly_revenue=None,
                    monthly_expenses=None,
                    monthly_profit=None,
                    repayment_coverage=None,
                    data_source=None,
                    marked_assumptions={
                        "status": "Insufficient revenue data or assumptions provided. Local revenue numbers are not invented.",
                        "local_revenue_invented": False,
                        "data_source": "none",
                    },
                    cash_flow={
                        "debt_service_emi": round(monthly_emi, 2),
                        "status": "Insufficient revenue assumptions",
                    },
                )
            )
        return scenario_responses

    # 3. Resolve scenario multipliers (configurable assumptions)
    config = scenario_config or ScenarioConfigInput()
    multipliers_map = {
        "worst_case": (
            config.worst_case.revenue_multiplier,
            config.worst_case.operating_cost_multiplier,
            "Worst Case",
        ),
        "expected_case": (
            config.expected_case.revenue_multiplier,
            config.expected_case.operating_cost_multiplier,
            "Expected Case",
        ),
        "best_case": (
            config.best_case.revenue_multiplier,
            config.best_case.operating_cost_multiplier,
            "Best Case",
        ),
    }

    if scenario_config is not None and data_source != "verified_data":
        data_source = "configurable_assumptions"

    scenario_responses = []

    for name in scenario_names:
        rev_mult, cost_mult, label = multipliers_map[name]

        scen_rev = round(base_revenue * rev_mult, 2)
        scen_cost = round(base_cost * cost_mult, 2)
        scen_surplus = round(scen_rev - scen_cost, 2)
        scen_emi = round(monthly_emi, 2)
        scen_cash_surplus = round(scen_surplus - scen_emi, 2)

        coverage = round(scen_surplus / scen_emi, 2) if scen_emi > 0 else None

        marked_assumptions: dict[str, Any] = {
            "data_source": data_source,
            "scenario": name,
            "label": label,
            "revenue_basis": f"Baseline revenue (₹{base_revenue:,.2f}) x {rev_mult * 100:.1f}% ({label})",
            "revenue_multiplier": rev_mult,
            "operating_cost_basis": f"Baseline operating cost (₹{base_cost:,.2f}) x {cost_mult * 100:.1f}% ({label})",
            "operating_cost_multiplier": cost_mult,
            "surplus_formula": "Revenue - Operating Costs",
            "loan_repayment_basis": "Calculated EMI from scheme loan terms",
            "cash_surplus_formula": "Surplus - Loan Repayment",
            "local_revenue_invented": False,
        }

        cash_flow_details = {
            "revenue": scen_rev,
            "operating_costs": scen_cost,
            "surplus": scen_surplus,
            "loan_repayment": scen_emi,
            "cash_surplus": scen_cash_surplus,
            "gross_revenue": scen_rev,
            "operating_expenses": scen_cost,
            "operating_cash_flow": scen_surplus,
            "debt_service_emi": scen_emi,
            "net_cash_flow": scen_cash_surplus,
            "data_source": data_source,
            "marked_assumptions": marked_assumptions,
        }

        scenario_responses.append(
            FinancialScenarioResponse(
                scenario_type=name,
                sufficient_assumptions_exist=True,
                revenue=scen_rev,
                operating_costs=scen_cost,
                surplus=scen_surplus,
                loan_repayment=scen_emi,
                cash_surplus=scen_cash_surplus,
                monthly_revenue=scen_rev,
                monthly_expenses=scen_cost,
                monthly_profit=scen_surplus,
                repayment_coverage=coverage,
                data_source=data_source,
                marked_assumptions=marked_assumptions,
                cash_flow=cash_flow_details,
            )
        )

    return scenario_responses
