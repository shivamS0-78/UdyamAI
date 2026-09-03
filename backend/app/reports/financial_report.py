"""
Financial Scenario Reporting Module for UdyamAI.
Generates structured Markdown reports for Worst case, Expected case, and Best case financial scenarios.
"""

from app.schemas.finance import FinancialScenarioResponse


def format_financial_scenario_report(
    scenarios: list[FinancialScenarioResponse],
    project_cost: float | None = None,
    loan_amount: float | None = None,
) -> str:
    """
    Renders a Markdown report table comparing Worst case, Expected case, and Best case financial scenarios.

    Fields formatted:
    - Revenue
    - Operating Costs
    - Surplus (Operating Surplus)
    - Loan Repayment (EMI)
    - Cash Surplus (Net Surplus)
    - Marked Assumptions & Data Source
    """
    report_lines: list[str] = [
        "# Financial Scenario Analysis Report",
        "",
    ]

    if project_cost is not None or loan_amount is not None:
        report_lines.append("## Project Summary")
        if project_cost is not None:
            report_lines.append(f"- **Project Cost**: ₹{project_cost:,.2f}")
        if loan_amount is not None:
            report_lines.append(f"- **Loan Amount**: ₹{loan_amount:,.2f}")
        report_lines.append("")

    if not scenarios:
        report_lines.append("No financial scenarios available.")
        return "\n".join(report_lines)

    # Check if sufficient assumptions exist across scenarios
    sufficient = any(s.sufficient_assumptions_exist for s in scenarios)

    report_lines.append("## Scenario Comparison")
    report_lines.append("")
    report_lines.append("| Metric | Worst Case | Expected Case | Best Case |")
    report_lines.append("| :--- | :--- | :--- | :--- |")

    scenarios_by_type = {s.scenario_type: s for s in scenarios}
    worst = scenarios_by_type.get("worst_case")
    expected = scenarios_by_type.get("expected_case")
    best = scenarios_by_type.get("best_case")

    def fmt_val(scen: FinancialScenarioResponse | None, attr: str) -> str:
        if scen is None or not scen.sufficient_assumptions_exist:
            return "N/A (No Revenue Input)"
        val = getattr(scen, attr, None)
        if val is None:
            return "N/A"
        return f"₹{val:,.2f}"

    report_lines.append(
        f"| **Revenue** | {fmt_val(worst, 'revenue')} | {fmt_val(expected, 'revenue')} | {fmt_val(best, 'revenue')} |"
    )
    report_lines.append(
        f"| **Operating Costs** | {fmt_val(worst, 'operating_costs')} | {fmt_val(expected, 'operating_costs')} | {fmt_val(best, 'operating_costs')} |"
    )
    report_lines.append(
        f"| **Surplus** | {fmt_val(worst, 'surplus')} | {fmt_val(expected, 'surplus')} | {fmt_val(best, 'surplus')} |"
    )
    report_lines.append(
        f"| **Loan Repayment (EMI)** | {fmt_val(worst, 'loan_repayment')} | {fmt_val(expected, 'loan_repayment')} | {fmt_val(best, 'loan_repayment')} |"
    )
    report_lines.append(
        f"| **Cash Surplus** | {fmt_val(worst, 'cash_surplus')} | {fmt_val(expected, 'cash_surplus')} | {fmt_val(best, 'cash_surplus')} |"
    )
    report_lines.append("")

    report_lines.append("## Marked Assumptions")
    report_lines.append("")

    if not sufficient:
        report_lines.append("> [!WARNING]")
        report_lines.append(
            "> **Insufficient Assumptions**: Local revenue numbers are **not invented**. Please provide explicit user revenue or verified benchmark data to generate full scenario modeling."
        )
    else:
        for s in scenarios:
            if s.sufficient_assumptions_exist and s.marked_assumptions:
                scen_name = s.scenario_type.replace("_", " ").title()
                ds = s.data_source or "N/A"
                report_lines.append(f"### {scen_name} (`{ds}`)")
                for k, v in s.marked_assumptions.items():
                    report_lines.append(f"- **{k.replace('_', ' ').title()}**: {v}")
                report_lines.append("")

    return "\n".join(report_lines)
