from sqlalchemy.orm import Session
from app.models.lead import Lead
from app.integrations.hubspot import create_hubspot_contact, get_hubspot_contact, update_hubspot_contact
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


    hubspot_exists = False
    if contact.hubspot_id:
        hubspot_exists = get_hubspot_contact(contact.hubspot_id)
    if not contact.hubspot_id or not hubspot_exists:
        print("🔄 RECREATING HUBSPOT CONTACT")
        hubspot_id = create_hubspot_contact(
            name,
            email or f"{phone}@noemail.com",
            phone
        )
        if hubspot_id:   # 👈 VALIDAR
            contact.hubspot_id = hubspot_id
            update_hubspot_contact(hubspot_id, {
                "hs_lead_status": "NEW"
            })
            db.commit()
        else:
            print("❌ ERROR creando contacto en HubSpot")


    # 💾 guardar lead
    new_lead = Lead(
        contact_id=contact.id,
        name=name,
        phone=phone,
        message=message,
        email=email,
        property_id=property_id,
        source=source or "whatsapp",
        status="new"
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
#     # 🔎 buscar contacto
#     contact = db.query(Contact).filter(Contact.phone == phone).first()

#     # 🆕 crear si no existe
#     if not contact:
#         contact = Contact(
#             name=name,
#             phone=phone,
#             email=email
#         )
#         db.add(contact)
#         db.commit()
#         db.refresh(contact)

#     # 🔗 crear en HubSpot si no existe
#     if not contact.hubspot_id:
#         try:
#             hubspot_id = create_hubspot_contact(
#                 name,
#                 email or f"{phone}@noemail.com",
#                 phone
#             )
#             contact.hubspot_id = hubspot_id
#             update_hubspot_contact(hubspot_id, {
#                 "hs_lead_status": "NEW"
#             })
#             db.commit()
#         except Exception as e:
#             logger.error(f"HubSpot integration failed: {str(e)}")

#     # 💾 guardar lead
#     new_lead = Lead(
#         contact_id=contact.id,
#         name=name,
#         phone=phone,
#         message=message,
#         email=email,
#         property_id=property_id,
#         source=source
#     )
#     db.add(new_lead)
#     db.commit()
#     db.refresh(new_lead)

#     return new_lead




    # 🔗 crear en HubSpot si no tiene ID
    # print("🟡 CONTACT HUBSPOT ID:", contact.hubspot_id)
    # if not contact.hubspot_id or contact.hubspot_id == "":
    #     try:
    #         hubspot_id = create_hubspot_contact(
    #             name,
    #             email or f"{phone}@noemail.com",
    #             phone
    #         )
    #         print("🟢 HUBSPOT CREATED ID:", hubspot_id)
    #         contact.hubspot_id = hubspot_id
    #         # 🔥 importante: ver respuesta
    #         response = update_hubspot_contact(hubspot_id, {
    #             "hs_lead_status": "NEW"
    #         })
    #         print("🟣 HUBSPOT UPDATE:", response)
    #         db.commit()
    #     except Exception as e:
    #         logger.error(f"HubSpot integration failed: {str(e)}")



















