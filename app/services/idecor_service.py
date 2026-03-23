import requests
from pyproj import Transformer
from shapely.geometry import shape

import simplekml

def generar_kml(geometry):
    import simplekml
    kml = simplekml.Kml()
    for polygon in geometry["coordinates"]:
        for ring in polygon:
            coords = [(x, y) for x, y in ring]  # ya están en lon/lat
            pol = kml.newpolygon(
                name="Parcela",
                outerboundaryis=coords
            )
            pol.style.linestyle.width = 2
            pol.style.polystyle.fill = 0
    return kml.kml()

# def generar_kml(geometry):
#     kml = simplekml.Kml()
#     for polygon in geometry["coordinates"]:
#         for ring in polygon:
#             coords = [(x, y) for x, y in ring]
#             pol = kml.newpolygon(
#                 name="Parcela",
#                 outerboundaryis=coords
#             )
#             pol.style.linestyle.width = 2
#             pol.style.polystyle.fill = 0
#     return kml.kml()

transformer = Transformer.from_crs("EPSG:22185", "EPSG:4326", always_xy=True)
# transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

WFS_URL = "https://idecor-ws.mapascordoba.gob.ar/geoserver/idecor/parcelas/wfs"

def buscar_parcela_por_cuenta(numero: str):
    try:
        params = {
            "service": "WFS",
            "version": "1.0.0",
            "request": "GetFeature",
            "typeName": "idecor:parcelas",
            "outputFormat": "application/json",
            "CQL_FILTER": f"Nro_Cuenta='{numero}'",
            "srsName": "EPSG:4326" 
        }

        response = requests.get(WFS_URL, params=params, timeout=10)

        print("STATUS:", response.status_code)

        if response.status_code != 200:
            return {"error": "IDECOR request failed"}

        # ⚠️ validar JSON
        try:
            data = response.json()
        except Exception:
            print("RESPONSE TEXT:", response.text[:500])
            return {"error": "Invalid response from IDECOR"}

        features = data.get("features", [])

        if not features:
            return {"error": "No parcel found"}

        feature = features[0]

        geometry = feature.get("geometry")

        if not geometry:
            return {"error": "No geometry found"}

        props = feature.get("properties", {})

        # ⚠️ proteger shapely
        try:
            geom = shape(geometry)
            centroid = geom.centroid
            lon, lat = transformer.transform(centroid.x, centroid.y)
            print("ORIGINAL:", centroid.x, centroid.y)
            print("TRANSFORMED:", lat, lon)
        except Exception as e:
            print("GEOMETRY ERROR:", e)
            lat, lon = None, None
            
        return {
            "geometry": geometry,
            "latitude": lat,
            "longitude": lon,

    # datos listos para UI 👇
            "idecor": {
                "cuenta": props.get("Nro_Cuenta"),
                "nomenclatura": props.get("Nomenclatura"),
                "designacion": props.get("desig_oficial"),
                "tipo_inmueble": props.get("Tipo_Parcela"),
                "tipo_valuacion": props.get("Tipo_Valuacion"),
                "estado": props.get("Estado"),
                "superficie_terreno": props.get("Superficie_Tierra_Urbana"),
                "superficie_mejoras": props.get("Superficie_Mejoras"),
                "valuacion_total": props.get("Valuacion"),
                "valuacion_tierra": props.get("Valuacion_Tierra_Urbana"),
                "valuacion_mejoras": props.get("Valuacion_Mejoras"),
                "localidad": props.get("localidad"),
                "departamento": props.get("departamento"),
},
    # opcional: debug completo
            "properties": props
}

    except Exception as e:
        print("ERROR IDECOR:", str(e))
        return {"error": "Internal server error"}






