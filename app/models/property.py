from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from sqlalchemy.orm import relationship
from app.core.database import Base

class Property(Base):
    __tablename__ = "properties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(String)
    operation_type = Column(String)
    property_type = Column(String)
    price = Column(Float)
    currency = Column(String)
    area_m2 = Column(Float)
    bedrooms = Column(Integer)
    bathrooms = Column(Integer)
    city = Column(String)
    neighborhood = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    featured = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    image_url = Column(String, nullable=True)
    leads = relationship("Lead", back_populates="property")
    cadastral_number = Column(String)
    images = Column(JSON, nullable=True)