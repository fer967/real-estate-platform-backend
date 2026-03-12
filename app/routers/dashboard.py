from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.property import Property
from app.models.lead import Lead

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_properties = db.query(Property).count()
    total_leads = db.query(Lead).count()
    leads_by_source_query = (
        db.query(Lead.source, func.count(Lead.id))
        .group_by(Lead.source)
        .all()
    )
    leads_by_source = {source: count for source, count in leads_by_source_query}
    return {
        "total_properties": total_properties,
        "total_leads": total_leads,
        "leads_by_source": leads_by_source
    }


@router.get("/top-properties")
def get_top_properties(db: Session = Depends(get_db)):
    results = (
        db.query(
            Property.id,
            Property.title,
            func.count(Lead.id).label("leads")
        )
        .join(Lead, Lead.property_id == Property.id)
        .group_by(Property.id)
        .order_by(func.count(Lead.id).desc())
        .limit(5)
        .all()
    )
    response = []
    for property_id, title, leads in results:
        response.append({
            "property_id": str(property_id),
            "title": title,
            "leads": leads
        })
    return response

@router.get("/leads-per-day")
def get_leads_per_day(db: Session = Depends(get_db)):
    results = (
        db.query(
            func.date(Lead.created_at).label("date"),
            func.count(Lead.id).label("leads")
        )
        .group_by(func.date(Lead.created_at))
        .order_by(func.date(Lead.created_at))
        .all()
    )
    response = []
    for date, leads in results:
        response.append({
            "date": str(date),
            "leads": leads
        })
    return response