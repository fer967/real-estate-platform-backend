from pydantic import BaseModel
from typing import Optional


class PropertyBase(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    city: str
    image_url: Optional[str] = None


class PropertyCreate(PropertyBase):
    pass


class PropertyResponse(PropertyBase):
    id: str

    class Config:
        orm_mode = True