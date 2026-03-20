import requests

WFS_URL = "https://idecor-ws.mapascordoba.gob.ar/geoserver/idecor/parcelas/wfs"

def buscar_parcela_por_cuenta(numero: str):

    params = {
        "service": "WFS",
        "version": "1.0.0",
        "request": "GetFeature",
        "typeName": "idecor:parcelas",
        "outputFormat": "application/json",
        "CQL_FILTER": f"Nro_Cuenta='{numero}'"
    }

    response = requests.get(WFS_URL, params=params)

    if response.status_code != 200:
        return None

    data = response.json()

    if not data["features"]:
        return None

    feature = data["features"][0]

    geometry = feature["geometry"]
    props = feature["properties"]

    # calcular centroide (simple)
    coords = geometry["coordinates"][0][0]
    lon = sum(p[0] for p in coords) / len(coords)
    lat = sum(p[1] for p in coords) / len(coords)

    return {
        "geometry": geometry,
        "latitude": lat,
        "longitude": lon,
        "area": props.get("superficie"),
        "properties": props
    }