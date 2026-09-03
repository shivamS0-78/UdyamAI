"""API routes for Scheme data queries."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.database import get_session
from app.schemas.scheme import SchemeResponse
from app.services.scheme_service import SchemeService

router = APIRouter()


# ------------------------------------------------------------------ #
# Static paths FIRST (before /{scheme_id})
# ------------------------------------------------------------------ #


@router.get("/states", response_model=list[str])
def list_states(db: Session = Depends(get_session)):
    """Get distinct states that have schemes."""
    return SchemeService.get_states(db)


@router.get("/agencies", response_model=list[str])
def list_agencies(db: Session = Depends(get_session)):
    """Get distinct agency names."""
    return SchemeService.get_agencies(db)


# ------------------------------------------------------------------ #
# Schemes
# ------------------------------------------------------------------ #


@router.get("", response_model=list[SchemeResponse])
def list_schemes(
    state: str | None = Query(default=None, description="Filter by state"),
    agency_name: str | None = Query(default=None, description="Filter by agency"),
    active_only: bool = Query(default=True, description="Only active schemes"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_session),
):
    """List government schemes with optional filters."""
    return SchemeService.get_schemes(
        db, state=state, agency_name=agency_name, active_only=active_only, limit=limit
    )


@router.get("/{scheme_id}", response_model=SchemeResponse)
def get_scheme(scheme_id: UUID, db: Session = Depends(get_session)):
    """Get a single scheme by ID."""
    scheme = SchemeService.get_scheme_by_id(db, scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail=f"Scheme {scheme_id} not found")
    return scheme


# ------------------------------------------------------------------ #
# Scheme Rules
# ------------------------------------------------------------------ #


@router.get("/{scheme_id}/rules")
def list_scheme_rules(
    scheme_id: UUID,
    active_only: bool = Query(default=True, description="Only active rules"),
    db: Session = Depends(get_session),
):
    """Get all rules for a scheme."""
    # Verify scheme exists
    scheme = SchemeService.get_scheme_by_id(db, scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail=f"Scheme {scheme_id} not found")

    rules = SchemeService.get_scheme_rules(db, scheme_id, active_only=active_only)
    return [
        {
            "id": str(r.id),
            "scheme_id": str(r.scheme_id),
            "min_project_cost": r.min_project_cost,
            "max_project_cost": r.max_project_cost,
            "beneficiary_contribution_percent": r.beneficiary_contribution_percent,
            "loan_percent": r.loan_percent,
            "max_loan_amount": r.max_loan_amount,
            "interest_rate": r.interest_rate,
            "tenure_months": r.tenure_months,
            "moratorium_months": r.moratorium_months,
            "payment_frequency": r.payment_frequency,
            "moratorium_interest_treatment": r.moratorium_interest_treatment,
            "working_capital_percent": r.working_capital_percent,
            "min_age": r.min_age,
            "max_age": r.max_age,
            "income_limit": r.income_limit,
            "eligible_business_categories": r.eligible_business_categories,
            "eligible_locations": r.eligible_locations,
            "eligible_beneficiary_categories": r.eligible_beneficiary_categories,
            "other_conditions": r.other_conditions,
            "effective_from": str(r.effective_from) if r.effective_from else None,
            "effective_until": str(r.effective_until) if r.effective_until else None,
            "source_document_id": str(r.source_document_id) if r.source_document_id else None,
            "created_at": str(r.created_at),
        }
        for r in rules
    ]


@router.get("/{scheme_id}/rules/latest")
def get_latest_rule(scheme_id: UUID, db: Session = Depends(get_session)):
    """Get the most recent active rule for a scheme."""
    scheme = SchemeService.get_scheme_by_id(db, scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail=f"Scheme {scheme_id} not found")

    rule = SchemeService.get_latest_rule(db, scheme_id)
    if not rule:
        raise HTTPException(
            status_code=404,
            detail=f"No active rule found for scheme {scheme_id}",
        )
    return {
        "id": str(rule.id),
        "scheme_id": str(rule.scheme_id),
        "beneficiary_contribution_percent": rule.beneficiary_contribution_percent,
        "loan_percent": rule.loan_percent,
        "interest_rate": rule.interest_rate,
        "tenure_months": rule.tenure_months,
        "moratorium_months": rule.moratorium_months,
        "payment_frequency": rule.payment_frequency,
        "moratorium_interest_treatment": rule.moratorium_interest_treatment,
        "working_capital_percent": rule.working_capital_percent,
        "min_project_cost": rule.min_project_cost,
        "max_project_cost": rule.max_project_cost,
        "max_loan_amount": rule.max_loan_amount,
        "effective_from": str(rule.effective_from) if rule.effective_from else None,
        "effective_until": str(rule.effective_until) if rule.effective_until else None,
        "created_at": str(rule.created_at),
    }


# ------------------------------------------------------------------ #
# Scheme Eligibility Rules
# ------------------------------------------------------------------ #


@router.get("/{scheme_id}/eligibility-rules")
def list_eligibility_rules(
    scheme_id: UUID,
    rule_type: str | None = Query(default=None, description="Filter by rule type"),
    db: Session = Depends(get_session),
):
    """Get eligibility rules for a scheme."""
    scheme = SchemeService.get_scheme_by_id(db, scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail=f"Scheme {scheme_id} not found")

    if rule_type:
        rules = SchemeService.get_eligibility_rules_by_type(db, scheme_id, rule_type)
    else:
        rules = SchemeService.get_eligibility_rules(db, scheme_id)

    return [
        {
            "id": str(r.id),
            "scheme_id": str(r.scheme_id),
            "rule_type": r.rule_type,
            "field_name": r.field_name,
            "operator": r.operator,
            "expected_value": r.expected_value,
            "description": r.description,
            "source_document_id": str(r.source_document_id) if r.source_document_id else None,
            "created_at": str(r.created_at),
        }
        for r in rules
    ]


@router.get("/{scheme_id}/eligibility-rules/types", response_model=list[str])
def list_eligibility_rule_types(scheme_id: UUID, db: Session = Depends(get_session)):
    """Get distinct eligibility rule types for a scheme."""
    scheme = SchemeService.get_scheme_by_id(db, scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail=f"Scheme {scheme_id} not found")

    return SchemeService.get_rule_types(db, scheme_id)


# ------------------------------------------------------------------ #
# Scheme Matches (data lookup only)
# ------------------------------------------------------------------ #


@router.get("/matches/{analysis_run_id}")
def list_scheme_matches(analysis_run_id: UUID, db: Session = Depends(get_session)):
    """Get pre-computed scheme matches for an analysis run."""
    matches = SchemeService.get_scheme_matches(db, analysis_run_id)
    return [
        {
            "id": str(m.id),
            "analysis_run_id": str(m.analysis_run_id),
            "scheme_id": str(m.scheme_id),
            "match_status": m.match_status,
            "match_score": m.match_score,
            "matched_conditions": m.matched_conditions,
            "failed_conditions": m.failed_conditions,
            "missing_information": m.missing_information,
            "estimated_loan_amount": m.estimated_loan_amount,
            "estimated_project_cost": m.estimated_project_cost,
            "verification_required": m.verification_required,
            "created_at": str(m.created_at),
        }
        for m in matches
    ]
