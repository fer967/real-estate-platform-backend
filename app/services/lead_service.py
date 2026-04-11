from sqlalchemy.orm import Session
from app.models.lead import Lead
from app.integrations.hubspot import create_hubspot_contact
from app.core.logger import logger
from app.models.contact import Contact


def create_lead_service(
    db: Session,
    name: str,
    phone: str,
    message: str,
    email: str = None,
    property_id: str = None,
    source: str = "web"
):
    # 🔎 buscar contacto
    contact = db.query(Contact).filter(Contact.phone == phone).first()

    # 🆕 crear contacto si no existe
    if not contact:
        contact = Contact(
            name=name,
            phone=phone,
            email=email
        )
        db.add(contact)
        db.commit()
        db.refresh(contact)

        # 🔗 crear en HubSpot
        try:
            hubspot_id = create_hubspot_contact(
                name,
                email or f"{phone}@noemail.com",
                phone
            )
            contact.hubspot_id = hubspot_id
            db.commit()
        except Exception as e:
            logger.error(f"HubSpot integration failed: {str(e)}")

    # 💾 crear lead (historial)
    new_lead = Lead(
        contact_id=contact.id,
        name=name,
        phone=phone,  # lo dejamos por compatibilidad
        message=message,
        email=email,
        property_id=property_id,
        source=source
    )

    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)

    return new_lead


# def create_lead_service(
#     db: Session,
#     name: str,
#     phone: str,
#     message: str,
#     email: str = None,
#     property_id: str = None,
#     source: str = "web"
# ):
    
#     contact = db.query(Contact).filter(Contact.phone == phone).first()

#     if not contact:
#         contact = Contact(
#             name=name,
#             phone=phone,
#             email=email
#         )
#         db.add(contact)
#         db.commit()
#         db.refresh(contact)

#     # crear en HubSpot SOLO una vez
#     hubspot_id = create_hubspot_contact(
#         name,
#         email or f"{phone}@noemail.com",
#         phone
#     )
#     contact.hubspot_id = hubspot_id
#     db.commit()

# # siempre crear lead (historial)
#     new_lead = Lead(
#         contact_id=contact.id,
#         message=message,
#         property_id=property_id,
#         source=source
#     )
#     db.add(new_lead)
#     db.commit()
    
#     return new_lead





    
    
    








