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
    return result



# from fastapi import APIRouter, Query
# from app.services.analysis_service import get_market_analysis

# router = APIRouter(prefix="/analysis", tags=["analysis"])

# @router.get("/")
# def market_analysis(city: str = Query(...), type: str = Query(...)):
#     result = get_market_analysis(city, type)
#     if not result:
#         return {"message": "No data available"}
#     return result


