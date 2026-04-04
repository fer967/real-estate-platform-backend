from sqlalchemy.orm import Session
from app.models.property import Property

def create_property(db: Session, property_data):
    new_property = Property(**property_data.dict())
    db.add(new_property)
    db.commit()
    db.refresh(new_property)
    return new_property

def get_properties(db: Session):
    return db.query(Property).all()

def get_property_by_id(db: Session, property_id: str):
    return db.query(Property).filter(Property.id == property_id).first()

def delete_property(db: Session, property):
    db.delete(property)
    db.commit()

def get_properties_by_property_type(db: Session, property_type: str):
    properties = (
        db.query(Property)
        .filter(Property.property_type.ilike(f"%{property_type}%"))
        .limit(3)
        .all()
    )
    return properties

def format_properties_message(properties):
    if not properties:
        return "No encontramos propiedades con ese criterio."
    message = "Estas son algunas propiedades disponibles:\n\n"
    for p in properties:
        message += f"🏠 {p.title}\n"
        message += f"💰 {p.price}\n"
        message += f"📍 {p.city} {p.neighborhood or ''}\n\n"
    return message


def get_properties_by_operation(db: Session, operation_type: str):
    return (
        db.query(Property)
        .filter(Property.operation_type.ilike(f"%{operation_type}%"))
        .limit(3)
        .all()
    )
        