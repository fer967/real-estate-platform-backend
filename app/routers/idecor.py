from fastapi import APIRouter
from app.services.idecor_service import buscar_parcela_por_cuenta

router = APIRouter(prefix="/idecor", tags=["idecor"])

@router.get("/parcela/{numero}")
def get_parcela(numero: str):
    return buscar_parcela_por_cuenta(numero)