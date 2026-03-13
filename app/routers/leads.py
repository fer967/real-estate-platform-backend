from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.lead import Lead
from app.schemas.lead_schema import LeadCreate
from app.services.lead_service import create_lead_service
# from app.integrations.hubspot import create_hubspot_contact
# from app.core.logger import logger

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("/{lead_id}")
def get_lead(lead_id: str, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    return lead


@router.post("/")
def create_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    return create_lead_service(
        db,
        lead.name,
        lead.phone,
        lead.message
    )


# @router.post("/")
# def create_lead(lead: LeadCreate, db: Session = Depends(get_db)):
#     new_lead = Lead(**lead.dict())
#     db.add(new_lead)
#     db.commit()
#     db.refresh(new_lead)
#     logger.info(f"Lead saved: {lead.name}")
#     try:
#         create_hubspot_contact(
#             lead.name,
#             lead.email,
#             lead.phone
#         )
#     except Exception as e:
#         logger.error(f"HubSpot integration failed: {str(e)}")
#     return new_lead


