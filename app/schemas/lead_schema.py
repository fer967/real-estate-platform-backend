from pydantic import BaseModel
from typing import Optional


class LeadCreate(BaseModel):

    name: str
    email: Optional[str]
    phone: Optional[str]
    message: Optional[str]

    property_id: Optional[str]
    source: Optional[str] = "web"