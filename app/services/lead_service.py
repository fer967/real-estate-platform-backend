from sqlalchemy.orm import Session
from app.models.lead import Lead
from app.integrations.hubspot import create_hubspot_contact
from app.core.logger import logger

def create_lead_service(db: Session, name: str, phone: str, message: str):
    new_lead = Lead(
        name=name,
        phone=phone,
        message=message,
        source="whatsapp"
    )
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    logger.info(f"Lead saved: {name}")
    try:
        create_hubspot_contact(name, None, phone)
    except Exception as e:
        logger.error(f"HubSpot integration failed: {str(e)}")
    return new_lead