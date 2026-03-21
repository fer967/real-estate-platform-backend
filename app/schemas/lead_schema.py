from pydantic import BaseModel, EmailStr
from typing import Optional

class LeadCreate(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    message: Optional[str] = None
    property_id: Optional[str] = None
    source: Optional[str] = "web"