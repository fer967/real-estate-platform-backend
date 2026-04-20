from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.core.database import Base
from sqlalchemy.orm import relationship
from datetime import datetime


class Lead(Base):
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    message = Column(String, nullable=True)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"))
    source = Column(String)  # web, whatsapp, bot
    status = Column(String, default="new", nullable=False)  # new, contacted, qualified, lost
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    property = relationship("Property", back_populates="leads")
    contact_id = Column(String, ForeignKey("contacts.id"))
    contact = relationship("Contact", backref="leads")
