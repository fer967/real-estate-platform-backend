from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.models.lead import Lead
from app.schemas.lead_schema import LeadCreate
from app.services.lead_service import create_lead_service
from fastapi import HTTPException

router = APIRouter(prefix="/leads", tags=["leads"])

@router.get("/")
def get_leads(db: Session = Depends(get_db)):
    leads = db.query(Lead).options(joinedload(Lead.property)).all()
    return leads

@router.get("/{lead_id}")
def get_lead(lead_id: str, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    return lead

@router.post("/")
def create_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    return create_lead_service(
    db=db,
    name=lead.name,
    phone=lead.phone,
    message=lead.message,
    email=lead.email,
    property_id=lead.property_id,
    source=lead.source
)


@router.put("/{lead_id}/status")
def update_lead_status(lead_id: str, status: str, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.status = status
    db.commit()
    db.refresh(lead)
    return lead



