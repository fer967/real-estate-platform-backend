import requests
from shapely.geometry import shape

def generar_kml(geometry, idecor_data=None):
    import simplekml
    kml = simplekml.Kml()
    # 📋 armar descripción HTML
    description = ""
    if idecor_data:
        description = f"""
        <h3>Datos de la parcela</h3>
        <b>Cuenta:</b> {idecor_data.get("cuenta")}<br/>
        <b>Nomenclatura:</b> {idecor_data.get("nomenclatura")}<br/>
        <b>Designación:</b> {idecor_data.get("designacion")}<br/>
        <b>Tipo:</b> {idecor_data.get("tipo_inmueble")}<br/>
        <b>Estado:</b> {idecor_data.get("estado")}<br/>
        <b>Sup. Terreno:</b> {idecor_data.get("superficie_terreno")} m²<br/>
        <b>Sup. Edificada:</b> {idecor_data.get("superficie_mejoras")} m²<br/>
        <b>Valuación:</b> ${idecor_data.get("valuacion_total")}<br/>
        """
    for polygon in geometry["coordinates"]:
        for ring in polygon:
            coords = [(x, y) for x, y in ring]
            pol = kml.newpolygon(
                name="Parcela IDECOR",
                description=description,   # 👈 ACA está la magia
                outerboundaryis=coords
            )
            pol.style.linestyle.color = simplekml.Color.red
            pol.style.linestyle.width = 3
            pol.style.polystyle.outline = 1 
            pol.style.polystyle.color = simplekml.Color.changealphaint(
                100, simplekml.Color.red
            )
    return kml.kml()


WFS_URL = "https://idecor-ws.mapascordoba.gob.ar/geoserver/idecor/parcelas/wfs"

def buscar_parcela_por_cuenta(numero: str):
    numero = numero.strip()
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
        
        import time
        for i in range(2):
            try:
                response = requests.get(WFS_URL, params=params, timeout=25)
            except requests.exceptions.Timeout:
                print("Retry IDECOR...")
                time.sleep(2)
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
        try:
            geom = shape(geometry)
            centroid = geom.centroid
            lon = centroid.x
            lat = centroid.y
            print("ORIGINAL:", centroid.x, centroid.y)
            print("TRANSFORMED:", lat, lon)
        except Exception as e:
            print("GEOMETRY ERROR:", e)
            lat, lon = None, None
        return {
            "geometry": geometry,
            "latitude": lat,
            "longitude": lon,
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
            "properties": props
}

    except Exception as e:
        print("ERROR IDECOR:", str(e))
        return {"error": "Internal server error"}





# def generar_kml(geometry):
#     import simplekml
#     kml = simplekml.Kml()
#     for polygon in geometry["coordinates"]:
#         for ring in polygon:
#             coords = [(x, y) for x, y in ring]  
#             pol = kml.newpolygon(
#                 name="Parcela",
#                 outerboundaryis=coords
#             )
#             pol.style.linestyle.color = simplekml.Color.red  
#             pol.style.linestyle.width = 3 
#             pol.style.polystyle.outline = 1                   
#             pol.style.polystyle.color = simplekml.Color.changealphaint(
#             100, simplekml.Color.red
#             )  
#     return kml.kml()









