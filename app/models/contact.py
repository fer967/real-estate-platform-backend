from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=True)
    phone = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, nullable=True)
    hubspot_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="bot")  # bot | human
    messenger_id = Column(String, nullable=True)
