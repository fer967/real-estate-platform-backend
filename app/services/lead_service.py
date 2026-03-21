from sqlalchemy.orm import Session
from app.models.lead import Lead
from app.integrations.hubspot import create_hubspot_contact
from app.core.logger import logger

def create_lead_service(
    db: Session,
    name: str,
    phone: str,
    message: str,
    email: str = None,
    property_id: str = None,
    source: str = "web"
):
    existing_lead = db.query(Lead).filter(Lead.phone == phone).first()
    if existing_lead:
        existing_lead.message = message
        db.commit()
        db.refresh(existing_lead)
        return existing_lead
    new_lead = Lead(
        name=name,
        phone=phone,
        message=message,
        email=email,
        property_id=property_id,
        source=source
    )
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    logger.info(f"Lead saved: {name}")
    try:
        create_hubspot_contact(name, email, phone)
    except Exception as e:
        logger.error(f"HubSpot integration failed: {str(e)}")
    return new_lead



