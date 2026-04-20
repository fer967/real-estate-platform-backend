from uuid import UUID
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class LeadCreate(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    message: Optional[str] = None
    property_id: Optional[str] = None
    source: Optional[str] = "web"

class LeadResponse(BaseModel):
    id: UUID
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    message: Optional[str] = None
    property_id: Optional[UUID] = None
    source: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True   # 🔥 importante (antes orm_mode)


