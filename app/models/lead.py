from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.core.database import Base
from sqlalchemy.orm import relationship

class Lead(Base):
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    message = Column(String, nullable=True)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"))
    source = Column(String)  # web, whatsapp, bot
    status = Column(String, default="new")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    property = relationship("Property", back_populates="leads")