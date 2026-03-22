import requests
from shapely.geometry import shape

WFS_URL = "https://idecor-ws.mapascordoba.gob.ar/geoserver/idecor/parcelas/wfs"

def buscar_parcela_por_cuenta(numero: str):

    params = {
        "service": "WFS",
        "version": "1.0.0",
        "request": "GetFeature",
        "typeName": "idecor:parcelas",
        "outputFormat": "application/json",
        "CQL_FILTER": f"NRO_CUENTA='{numero}'"
    }

    response = requests.get(WFS_URL, params=params)

    if response.status_code != 200:
        return None

    data = response.json()

    if not data.get("features"):
        return None

    feature = data["features"][0]

    geometry = feature["geometry"]
    props = feature["properties"]

    # centroid real
    geom = shape(geometry)
    centroid = geom.centroid

    return {
        "geometry": geometry,
        "latitude": centroid.y,
        "longitude": centroid.x,
        "area": props.get("SUP_TERR") or props.get("superficie"),
        "nomenclatura": props.get("NOMENCLATURA"),
        "designacion": props.get("DESIGNACION"),
        "properties": props
    }



# import requests

# WFS_URL = "https://idecor-ws.mapascordoba.gob.ar/geoserver/idecor/parcelas/wfs"

# def buscar_parcela_por_cuenta(numero: str):

#     params = {
#         "service": "WFS",
#         "version": "1.0.0",
#         "request": "GetFeature",
#         "typeName": "idecor:parcelas",
#         "outputFormat": "application/json",
#         "CQL_FILTER": f"Nro_Cuenta='{numero}'"
#     }

#     response = requests.get(WFS_URL, params=params)

#     if response.status_code != 200:
#         return None

#     data = response.json()

#     if not data["features"]:
#         return None

#     feature = data["features"][0]

#     geometry = feature["geometry"]
#     props = feature["properties"]

#     # calcular centroide (simple)
#     coords = geometry["coordinates"][0][0]
#     lon = sum(p[0] for p in coords) / len(coords)
#     lat = sum(p[1] for p in coords) / len(coords)

#     return {
#         "geometry": geometry,
#         "latitude": lat,
#         "longitude": lon,
#         "area": props.get("superficie"),
#         "properties": props
#     }