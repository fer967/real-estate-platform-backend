from pydantic import BaseModel
from typing import Optional


class PropertyBase(BaseModel):
    title: str
    description: Optional[str] = None
    operation_type: Optional[str] = None
    property_type: Optional[str] = None
    price: float
    currency: Optional[str] = None
    area_m2: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    city: str
    neighborhood: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    featured: Optional[bool] = False
    image_url: Optional[str] = None


class PropertyCreate(PropertyBase):
    pass


class PropertyResponse(PropertyBase):
    id: str

    class Config:
        from_attributes = True
        
        # class Config:
        #     orm_mode = True
        
        
#         model_config = {
#     "from_attributes": True
# }