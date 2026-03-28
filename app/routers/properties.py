from importlib.metadata import files

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.property_schema import PropertyCreate
from app.services import property_service 
from app.integrations.supabase_client import supabase, SUPABASE_URL
import uuid
from app.models.property import Property
from typing import List

router = APIRouter(prefix="/properties", tags=["properties"])


@router.post("/")
def create_property(property: PropertyCreate, db: Session = Depends(get_db)):
    return property_service.create_property(db, property)


@router.get("/")
def get_properties(db: Session = Depends(get_db)):
    return property_service.get_properties(db)


@router.get("/{property_id}")
def get_property(property_id: str, db: Session = Depends(get_db)):
    property = property_service.get_property_by_id(db, property_id)
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
    return property


@router.post("/create-with-image")
async def create_property_with_image(
    title: str = Form(...),
    description: str = Form(None),
    price: float = Form(...),
    city: str = Form(...),
    files: List[UploadFile] = File(...),  
    db: Session = Depends(get_db),
    operation_type: str = Form(...),
    property_type: str = Form(...),
    bedrooms: int = Form(None),
    bathrooms: int = Form(None),
    area_m2: float = Form(None),
    neighborhood: str = Form(None),
    featured: bool = Form(False),
    cadastral_number: str = Form(None),
    latitude: float = Form(None),
    longitude: float = Form(None),
):

    image_urls = []
    for file in files:
        file_extension = file.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{file_extension}"
        file_content = await file.read()
        supabase.storage.from_("properties").upload(
            filename,
            file_content
        )
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/properties/{filename}"
        image_urls.append(public_url)
        
    new_property = Property(
        title=title,
        description=description,
        price=price,
        city=city,
        image_url=image_urls[0] if image_urls else None,  
        images=image_urls,  
        operation_type=operation_type,
        property_type=property_type,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        area_m2=area_m2,
        neighborhood=neighborhood,
        featured=featured,
        cadastral_number=cadastral_number,
        latitude=latitude,
        longitude=longitude
    )
    db.add(new_property)
    db.commit()
    db.refresh(new_property)
    return new_property

@router.get("/{property_id}/leads")
def get_property_leads(property_id: str, db: Session = Depends(get_db)):
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
    return property.leads


@router.put("/{property_id}")
def update_property(
    property_id: str,
    property_data: PropertyCreate,
    db: Session = Depends(get_db)
):
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
    property.title = property_data.title
    property.description = property_data.description
    property.price = property_data.price
    property.city = property_data.city
    db.commit()
    db.refresh(property)
    return property


@router.put("/{property_id}/with-images")
async def update_property_with_images(
    property_id: str,
    title: str = Form(...),
    description: str = Form(None),
    price: float = Form(...),
    city: str = Form(...),
    existing_images: str = Form(None),  # 👈 JSON string
    files: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    import json
    db_property = db.query(Property).filter(Property.id == property_id).first()
    if not db_property:
        raise HTTPException(status_code=404, detail="Property not found")
    # actualizar datos
    db_property.title = title
    db_property.description = description
    db_property.price = price
    db_property.city = city
    # 🔹 imágenes existentes (las que el usuario dejó)
    current_images = []
    if existing_images:
        current_images = json.loads(existing_images)
    # 🔹 nuevas imágenes
    new_images = []
    if files:
        for file in files:
            file_extension = file.filename.split(".")[-1]
            filename = f"{uuid.uuid4()}.{file_extension}"
            content = await file.read()
            supabase.storage.from_("properties").upload(filename, content)
            url = f"{SUPABASE_URL}/storage/v1/object/public/properties/{filename}"
            new_images.append(url)
    # 🔹 combinación final
    final_images = current_images + new_images
    db_property.images = final_images
    db_property.image_url = final_images[0] if final_images else None
    db.commit()
    db.refresh(db_property)
    return db_property


# @router.put("/{property_id}/with-images")
# async def update_property_with_images(
#     property_id: str,
#     title: str = Form(...),
#     description: str = Form(None),
#     price: float = Form(...),
#     city: str = Form(...),
#     files: List[UploadFile] = File(None),
#     db: Session = Depends(get_db),
# ):
#     db_property = db.query(Property).filter(Property.id == property_id).first()

#     if not db_property:
#         raise HTTPException(status_code=404, detail="Property not found")

#     # actualizar datos básicos
#     db_property.title = title
#     db_property.description = description
#     db_property.price = price
#     db_property.city = city

#     # si vienen imágenes nuevas
#     if files:
#         image_urls = []

#         for file in files:
#             file_extension = file.filename.split(".")[-1]
#             filename = f"{uuid.uuid4()}.{file_extension}"

#             content = await file.read()

#             supabase.storage.from_("properties").upload(filename, content)

#             url = f"{SUPABASE_URL}/storage/v1/object/public/properties/{filename}"
#             image_urls.append(url)

#         db_property.image_url = image_urls[0]
#         db_property.images = image_urls

#     db.commit()
#     db.refresh(db_property)

#     return db_property



@router.delete("/{property_id}")
def delete_property(property_id: str, db: Session = Depends(get_db)):
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
    db.delete(property)
    db.commit()
    return {"message": "Property deleted"}




