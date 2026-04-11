from app.core.database import SessionLocal
from app.models.lead import Lead
from app.models.contact import Contact
from app.models.property import Property

def run():
    db = SessionLocal()

    leads = db.query(Lead).all()

    for lead in leads:
        contact = db.query(Contact).filter(Contact.phone == lead.phone).first()

        if not contact:
            contact = Contact(
                name=lead.name,
                phone=lead.phone,
                email=lead.email
            )
            db.add(contact)
            db.commit()
            db.refresh(contact)

        lead.contact_id = contact.id

    db.commit()
    db.close()

    print("✅ Migración completada")

if __name__ == "__main__":
    run()