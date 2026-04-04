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
    
    existing_contact = db.query(Lead).filter(Lead.phone == phone).first()

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

# 👉 solo crear contacto en HubSpot si es la primera vez
    if not existing_contact:
        try:
            create_hubspot_contact(name, email, phone)
        except Exception as e:
            logger.error(f"HubSpot integration failed: {str(e)}")

    return new_lead
    
    
    
    
    
    # new_lead = Lead(
    #     name=name,
    #     phone=phone,
    #     message=message,
    #     email=email,
    #     property_id=property_id,
    #     source=source
    # )
    # db.add(new_lead)
    # db.commit()
    # db.refresh(new_lead)
    # logger.info(f"Lead saved: {name}")
    # try:
    #     create_hubspot_contact(name, email, phone)
    # except Exception as e:
    #     logger.error(f"HubSpot integration failed: {str(e)}")
    # return new_lead








