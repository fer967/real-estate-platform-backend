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