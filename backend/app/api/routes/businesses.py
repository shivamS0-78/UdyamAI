"""API routes for Business data queries.

`router` is mounted under /business-categories (category master data).
`records_router` is mounted under /businesses (business establishment
records).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.database import get_session
from app.schemas.business import (
    BusinessCategoryResponse,
    BusinessModelResponse,
    BusinessResponse,
)
from app.services.business_service import BusinessService

router = APIRouter()
records_router = APIRouter()


@router.get("", response_model=list[BusinessCategoryResponse])
def get_business_categories(db: Session = Depends(get_session)):
    return BusinessService.get_business_categories(db)


@router.get("/models", response_model=list[BusinessModelResponse])
def get_business_models(
    business_category_id: UUID | None = Query(
        default=None, description="Filter by business category UUID"
    ),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_session),
):
    """List business models (startup cost / assumption reference data)."""
    return BusinessService.get_business_models(
        db, business_category_id=business_category_id, limit=limit
    )


@records_router.get("", response_model=list[BusinessResponse])
def list_businesses(
    business_category_id: UUID | None = Query(
        default=None, description="Filter by business category UUID"
    ),
    location_id: UUID | None = Query(default=None, description="Filter by village location UUID"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_session),
):
    """List business establishments with optional filters."""
    return BusinessService.get_businesses(
        db,
        business_category_id=business_category_id,
        location_id=location_id,
        limit=limit,
    )


@records_router.get("/{business_id}", response_model=BusinessResponse)
def get_business(business_id: UUID, db: Session = Depends(get_session)):
    """Get a single business establishment by ID."""
    business = BusinessService.get_business_by_id(db, business_id)
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found")
    return business
