"""Deterministic government scheme matching from database rules."""

from __future__ import annotations

import re
from datetime import date
from uuid import UUID

from sqlmodel import Session, col, select

from app.models.business import BusinessCategory
from app.models.location import District
from app.models.scheme import Scheme, SchemeMatch, SchemeRule
from app.schemas.common import SchemeMatchStatus


def _normalize_name(value: str | None) -> str:
    return (value or "").strip().lower()


def _category_tokens(value: str | None) -> set[str]:
    return {token for token in re.findall(r"[a-z]{3,}", _normalize_name(value))}


def _category_matches(rule: SchemeRule, category_name: str) -> bool:
    eligible = rule.eligible_business_categories or []
    if not eligible:
        return True
    target = _normalize_name(category_name)
    target_tokens = _category_tokens(category_name)
    for item in eligible:
        item_norm = _normalize_name(item)
        if item_norm == target:
            return True
        if target_tokens & _category_tokens(item):
            return True
    return False


def _location_matches(rule: SchemeRule, district: District | None) -> bool:
    locations = rule.eligible_locations or {}
    if not locations:
        return True
    geography = _normalize_name(str(locations.get("geography", "")))
    if not geography:
        return True
    if "maharashtra" in geography or "national" in geography or "rural" in geography:
        return True
    if district and district.name:
        return _normalize_name(district.name) in geography
    return True


def _project_cost_matches(rule: SchemeRule, project_cost: float) -> tuple[bool, dict[str, bool]]:
    matched: dict[str, bool] = {}
    if rule.min_project_cost is not None and project_cost < rule.min_project_cost:
        matched["min_project_cost"] = False
        return False, matched
    matched["min_project_cost"] = True
    if rule.max_project_cost is not None and project_cost > rule.max_project_cost:
        matched["max_project_cost"] = False
        return False, matched
    matched["max_project_cost"] = True
    return True, matched


def _estimate_subsidy(rule: SchemeRule, project_cost: float) -> float:
    other = rule.other_conditions or {}
    if other.get("subsidy_rate_special_rural") is not None:
        return round(project_cost * float(other["subsidy_rate_special_rural"]) / 100.0, 2)
    if other.get("subsidy_rate_rural") is not None:
        return round(project_cost * float(other["subsidy_rate_rural"]) / 100.0, 2)
    subsidy_text = str(other.get("credit_linked_capital_subsidy", ""))
    pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%", subsidy_text)
    if pct_match:
        rate = float(pct_match.group(1)) / 100.0
        cap_match = re.search(r"up to\s*([\d.]+)\s*lakh", subsidy_text, re.I)
        subsidy = project_cost * rate
        if cap_match:
            subsidy = min(subsidy, float(cap_match.group(1)) * 100_000.0)
        return round(subsidy, 2)
    return 0.0


def _score_match(
    *,
    category_ok: bool,
    location_ok: bool,
    cost_ok: bool,
    project_cost: float,
    rule: SchemeRule,
) -> float:
    score = 0.0
    if category_ok:
        score += 0.45
    if location_ok:
        score += 0.20
    if cost_ok:
        score += 0.20
    if rule.max_project_cost and project_cost <= rule.max_project_cost:
        score += 0.15 * min(1.0, project_cost / rule.max_project_cost)
    return round(min(score, 1.0), 3)


def _latest_active_rule(db: Session, scheme_id: UUID) -> SchemeRule | None:
    today = date.today()
    rules = db.exec(
        select(SchemeRule)
        .where(SchemeRule.scheme_id == scheme_id)
        .order_by(col(SchemeRule.created_at).desc())
    ).all()
    for rule in rules:
        if rule.effective_from and rule.effective_from > today:
            continue
        if rule.effective_until and rule.effective_until < today:
            continue
        return rule
    return rules[0] if rules else None


def match_schemes_for_analysis(
    db: Session,
    *,
    analysis_run_id: UUID,
    business_category: BusinessCategory,
    district: District | None,
    desired_project_cost: float,
    available_capital: float,
) -> list[SchemeMatch]:
    """Evaluate active schemes and persist deterministic matches for an analysis run."""
    schemes = db.exec(select(Scheme).where(Scheme.active).order_by(Scheme.name)).all()
    matches: list[SchemeMatch] = []

    for scheme in schemes:
        rule = _latest_active_rule(db, scheme.id)
        if not rule:
            continue

        category_ok = _category_matches(rule, business_category.name)
        location_ok = _location_matches(rule, district)
        cost_ok, cost_conditions = _project_cost_matches(rule, desired_project_cost)
        matched_conditions = {
            "category": category_ok,
            "location": location_ok,
            **cost_conditions,
        }
        failed_conditions = {
            key: value for key, value in matched_conditions.items() if value is False
        }

        if not category_ok or not location_ok or not cost_ok:
            status = SchemeMatchStatus.NOT_MATCH
            score = _score_match(
                category_ok=category_ok,
                location_ok=location_ok,
                cost_ok=cost_ok,
                project_cost=desired_project_cost,
                rule=rule,
            )
            matches.append(
                SchemeMatch(
                    analysis_run_id=analysis_run_id,
                    scheme_id=scheme.id,
                    match_status=status,
                    match_score=score,
                    matched_conditions=matched_conditions,
                    failed_conditions=failed_conditions or None,
                    estimated_loan_amount=0.0,
                    estimated_project_cost=desired_project_cost,
                    verification_required=True,
                )
            )
            continue
        if failed_conditions:
            status = SchemeMatchStatus.MISSING_INFORMATION
            score = _score_match(
                category_ok=category_ok,
                location_ok=location_ok,
                cost_ok=cost_ok,
                project_cost=desired_project_cost,
                rule=rule,
            )
        else:
            status = SchemeMatchStatus.POTENTIAL_MATCH
            score = _score_match(
                category_ok=category_ok,
                location_ok=location_ok,
                cost_ok=cost_ok,
                project_cost=desired_project_cost,
                rule=rule,
            )

        loan_percent = rule.loan_percent or max(
            0.0, 100.0 - (rule.beneficiary_contribution_percent or 10.0)
        )
        loan_amount = min(
            desired_project_cost * loan_percent / 100.0,
            rule.max_loan_amount or desired_project_cost,
        )

        match = SchemeMatch(
            analysis_run_id=analysis_run_id,
            scheme_id=scheme.id,
            match_status=status,
            match_score=score,
            matched_conditions=matched_conditions,
            failed_conditions=failed_conditions or None,
            estimated_loan_amount=round(loan_amount, 2),
            estimated_project_cost=desired_project_cost,
            verification_required=True,
        )
        db.add(match)
        matches.append(match)

    persistable = [m for m in matches if m.match_status != SchemeMatchStatus.NOT_MATCH]
    persistable.sort(key=lambda item: item.match_score or 0.0, reverse=True)
    if persistable:
        db.commit()
        for match in persistable:
            db.refresh(match)
    return persistable


def estimate_subsidy_for_match(db: Session, scheme_id: UUID, project_cost: float) -> float:
    rule = _latest_active_rule(db, scheme_id)
    if not rule:
        return 0.0
    return _estimate_subsidy(rule, project_cost)
