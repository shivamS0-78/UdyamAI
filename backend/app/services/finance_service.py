"""
Finance Service for UdyamAI.
Handles database lookup for scheme rules, calculation orchestration, error handling, and DB persistence.
"""

import logging

from sqlmodel import Session, select

from app.config import settings
from app.finance.calculator import calculate_finance_engine
from app.models.finance import FinancialAnalysis, FinancialScenario, RepaymentSchedule
from app.models.scheme import SchemeRule
from app.schemas.finance import (
    FinanceCalculateRequest,
    FinanceCalculateResponse,
    SchemeRuleInput,
)

logger = logging.getLogger(__name__)


class FinanceService:
    @staticmethod
    def calculate_finance(
        request: FinanceCalculateRequest, session: Session | None = None
    ) -> FinanceCalculateResponse:
        """
        Orchestrates financial calculations using dynamic scheme rules.
        Handles database scheme lookup and DB persistence with structured error handling.
        """
        rule = None

        # 1. Look up scheme rule from DB if scheme_rule_id or scheme_id is provided
        if session is not None and (
            request.scheme_rule_id is not None or request.scheme_id is not None
        ):
            try:
                if request.scheme_rule_id is not None:
                    rule = session.exec(
                        select(SchemeRule).where(SchemeRule.id == request.scheme_rule_id)
                    ).first()
                elif request.scheme_id is not None:
                    # Select latest active rule for scheme ordered by created_at desc
                    rule = session.exec(
                        select(SchemeRule)
                        .where(SchemeRule.scheme_id == request.scheme_id)
                        .order_by(SchemeRule.created_at.desc())
                    ).first()
            except Exception as exc:
                logger.error(
                    "Database lookup failed for scheme rule (scheme_id=%s, rule_id=%s): %s",
                    request.scheme_id,
                    request.scheme_rule_id,
                    exc,
                    exc_info=True,
                )
                return FinanceCalculateResponse(
                    status="database_error",
                    available_capital=request.available_capital,
                    required_contribution=0.0,
                    message="Failed to fetch scheme rule from database due to a database error.",
                )

        # 2. Use scheme_rule_override if provided
        if rule is None and request.scheme_rule_override is not None:
            override = request.scheme_rule_override
            if override.beneficiary_contribution_percent <= 0:
                raise ValueError("beneficiary_contribution_percent must be greater than 0")
            rule = override

        # 3. Fallback to inline parameters provided directly on request
        if rule is None:
            b_percent = request.beneficiary_contribution_percent
            if b_percent is None:
                if request.loan_percent is not None:
                    b_percent = max(0.0, 100.0 - request.loan_percent)
                else:
                    b_percent = settings.DEFAULT_BENEFICIARY_CONTRIBUTION_PERCENT

            l_percent = request.loan_percent
            if l_percent is None:
                l_percent = max(0.0, 100.0 - b_percent)

            rule = SchemeRuleInput(
                beneficiary_contribution_percent=b_percent,
                loan_percent=l_percent,
                interest_rate=request.interest_rate
                if request.interest_rate is not None
                else settings.DEFAULT_INTEREST_RATE,
                tenure_months=request.tenure_months
                if request.tenure_months is not None
                else settings.DEFAULT_TENURE_MONTHS,
                moratorium_months=request.moratorium_months or 0,
                payment_frequency=request.payment_frequency or "monthly",
                moratorium_interest_treatment=request.moratorium_interest_treatment,
            )

        # Execute calculations
        response = calculate_finance_engine(request, rule)

        # 4. Optional DB persistence if analysis_run_id and session are present
        if (
            session is not None
            and request.analysis_run_id is not None
            and response.status == "success"
        ):
            FinanceService._persist_analysis_results(session, request, response)

        return response

    @staticmethod
    def _persist_analysis_results(
        session: Session,
        request: FinanceCalculateRequest,
        response: FinanceCalculateResponse,
    ) -> None:
        """
        Executes an atomic persistence transaction for financial analysis, repayment schedules, and financial scenarios.
        Uses a single transaction unit with session.flush() and session.commit() so that rollback reverts everything if any stage fails.
        """
        try:
            financial_record = FinancialAnalysis(
                analysis_run_id=request.analysis_run_id,
                scheme_id=request.scheme_id,
                available_capital=response.available_capital,
                required_contribution=response.required_contribution,
                desired_project_cost=response.desired_project_cost,
                feasible_project_cost=response.feasible_project_cost,
                margin_gap=response.shortfall,
                calculated_loan=response.potential_loan,
                interest_rate=response.interest_rate,
                tenure_months=response.tenure_months,
                moratorium_months=response.moratorium_months,
                monthly_emi=response.monthly_emi,
                total_interest=response.total_interest,
                total_repayment=response.total_repayment,
                working_capital=response.working_capital,
                monthly_revenue=request.monthly_revenue,
                monthly_operating_cost=request.monthly_operating_cost,
                monthly_profit=(
                    request.monthly_revenue - request.monthly_operating_cost
                    if request.monthly_revenue is not None
                    and request.monthly_operating_cost is not None
                    else None
                ),
                calculation_version="v2.0_phase5",
            )
            session.add(financial_record)
            session.flush()  # Populates financial_record.id atomically without committing transaction

            # Add repayment schedule items
            for item in response.repayment_schedule:
                sched_item = RepaymentSchedule(
                    financial_analysis_id=financial_record.id,
                    period_number=item.period_number,
                    opening_balance=item.opening_balance,
                    principal_amount=item.principal_amount,
                    interest_amount=item.interest_amount,
                    payment_amount=item.payment_amount,
                    remaining_principal=item.remaining_principal,
                    is_moratorium=item.is_moratorium,
                    verification_required=item.verification_required,
                )
                session.add(sched_item)

            # Add financial scenarios
            for scen in response.financial_scenarios:
                scen_item = FinancialScenario(
                    financial_analysis_id=financial_record.id,
                    scenario_type=scen.scenario_type,
                    monthly_revenue=scen.monthly_revenue,
                    monthly_expenses=scen.monthly_expenses,
                    monthly_profit=scen.monthly_profit,
                    cash_flow=scen.cash_flow,
                    repayment_coverage=scen.repayment_coverage,
                )
                session.add(scen_item)

            # Single atomic commit for entire object graph
            session.commit()
            logger.info(
                "Successfully persisted financial analysis results (analysis_run_id=%s, scheme_id=%s)",
                request.analysis_run_id,
                request.scheme_id,
            )
        except Exception as exc:
            logger.error(
                "Atomic persistence failed for financial analysis (analysis_run_id=%s, scheme_id=%s): %s",
                request.analysis_run_id,
                request.scheme_id,
                exc,
                exc_info=True,
            )
            session.rollback()
