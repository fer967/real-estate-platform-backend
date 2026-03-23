from fastapi import APIRouter
from app.services.idecor_service import buscar_parcela_por_cuenta
from fastapi.responses import Response
from app.services.idecor_service import generar_kml

router = APIRouter(prefix="/idecor", tags=["idecor"])

@router.get("/kml/{numero}")
def get_kml(numero: str):
    data = buscar_parcela_por_cuenta(numero)
    if not data or "geometry" not in data:
        return {"error": "No data"}
    kml = generar_kml(data["geometry"])
    return Response(
        content=kml,
        media_type="application/vnd.google-earth.kml+xml"
    )


@router.get("/parcela/{numero}")
def get_parcela(numero: str):
    return buscar_parcela_por_cuenta(numero)

