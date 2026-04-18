from fastapi import APIRouter, Query
from app.services.analysis_service import get_market_analysis

router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.get("/")
def market_analysis(city: str = Query(...), type: str = Query(...)):
    result = get_market_analysis(city, type)
    if not result:
        return {"message": "No data available"}
    return result