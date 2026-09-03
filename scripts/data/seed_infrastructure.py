#!/usr/bin/env python3
"""Derive infrastructure facility records from imported markets and businesses."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from sqlmodel import Session, select

from app.database import engine, init_db
from app.ingestion.importer import _point_wkt
from app.models.business import Business, BusinessCategory
from app.models.infrastructure import Infrastructure
from app.models.market import Market


def seed_infrastructure() -> None:
    init_db()
    created = 0
    with Session(engine) as db:
        existing = {
            (row.facility_type, row.name, row.latitude, row.longitude)
            for row in db.exec(select(Infrastructure)).all()
        }

        for market in db.exec(select(Market)).all():
            if market.latitude is None or market.longitude is None:
                continue
            key = ("mandi", market.name, market.latitude, market.longitude)
            if key in existing:
                continue
            db.add(
                Infrastructure(
                    location_id=market.location_id,
                    facility_type="mandi",
                    name=market.name,
                    latitude=market.latitude,
                    longitude=market.longitude,
                    geog=_point_wkt(market.latitude, market.longitude),
                    source=market.source or "Government Registries",
                    source_url=market.source_url,
                )
            )
            existing.add(key)
            created += 1

        for business in db.exec(select(Business)).all():
            if business.latitude is None or business.longitude is None:
                continue
            category = db.get(BusinessCategory, business.business_category_id) if business.business_category_id else None
            category_name = (category.name if category else business.name or "").lower()
            if "cold storage" in category_name or "logistics" in category_name:
                facility_type = "cold_storage"
            elif "engineering" in category_name or "repair" in category_name:
                facility_type = "warehouse"
            elif "dairy" in category_name or "food" in category_name or "agro" in category_name:
                facility_type = "processing_unit"
            else:
                facility_type = "msme_cluster"

            key = (facility_type, business.name, business.latitude, business.longitude)
            if key in existing:
                continue
            db.add(
                Infrastructure(
                    location_id=business.location_id,
                    facility_type=facility_type,
                    name=business.name,
                    latitude=business.latitude,
                    longitude=business.longitude,
                    geog=_point_wkt(business.latitude, business.longitude),
                    source=business.source or "MSME Registry",
                    source_url=business.source_url,
                )
            )
            existing.add(key)
            created += 1

        db.commit()
    print(f"Seeded {created} infrastructure facility records.")


if __name__ == "__main__":
    seed_infrastructure()
