from fastapi import APIRouter
from app.services.analysis_service import (
    get_market_analysis,
    extract_data_from_message
)

router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.get("/from-lead")
def analysis_from_lead(message: str):
    city, property_type = extract_data_from_message(message)
    result = get_market_analysis(city, property_type)
    if not city or not property_type:
        return {
            "error": "Missing data",
            "detail": "No se pudo extraer ciudad o tipo"
        }
    if not result:
        return {
            "error": "No data",
            "avg_price": 0,
            "min_price": 0,
            "max_price": 0,
            "avg_m2": 0,
            "count": 0
        }
    return result








