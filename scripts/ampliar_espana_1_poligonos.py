"""Descarga limites municipales del IGN de TODA España salvo Canarias, Andalucia y Murcia (ya cargadas).
Salida: frontend/espana.geojson y scripts/municipios_espana.csv.  Requiere: pip install requests shapely
Uso: python scripts\\ampliar_espana_1_poligonos.py"""
import json, csv, time, requests
from pathlib import Path
from shapely.geometry import shape, mapping
HERE = Path(__file__).resolve().parent
URL = "https://api-features.ign.es/collections/administrativeunit/items"
CCAA = {"ES11":"Galicia","ES12":"Principado de Asturias","ES13":"Cantabria","ES21":"País Vasco","ES22":"Comunidad Foral de Navarra",
        "ES23":"La Rioja","ES24":"Aragón","ES30":"Comunidad de Madrid","ES41":"Castilla y León","ES42":"Castilla-La Mancha",
        "ES43":"Extremadura","ES51":"Cataluña","ES52":"Comunitat Valenciana","ES53":"Illes Balears",
        "ES63":"Ciudad de Ceuta","ES64":"Ciudad de Melilla"}
PROV = {"01":"Álava","02":"Albacete","03":"Alicante","05":"Ávila","06":"Badajoz","07":"Illes Balears","08":"Barcelona","09":"Burgos",
 "10":"Cáceres","12":"Castellón","13":"Ciudad Real","15":"A Coruña","16":"Cuenca","17":"Girona","19":"Guadalajara","20":"Gipuzkoa",
 "22":"Huesca","24":"León","25":"Lleida","26":"La Rioja","27":"Lugo","28":"Madrid","31":"Navarra","32":"Ourense","33":"Asturias",
 "34":"Palencia","36":"Pontevedra","37":"Salamanca","39":"Cantabria","40":"Segovia","42":"Soria","43":"Tarragona","44":"Teruel",
 "45":"Toledo","46":"Valencia","47":"Valladolid","48":"Bizkaia","49":"Zamora","50":"Zaragoza","51":"Ceuta","52":"Melilla"}
TOL = 0.0003
BOXES = [(lo, la, lo + 1.0, la + 1.0) for lo in [x * 1.0 for x in range(-10, 5)] for la in [y * 1.0 for y in range(36, 44)]]
BOXES += [(-3.1, 35.2, -2.8, 35.4)]   # Melilla
def pagina(bbox, offset, limit=200):
    for intento in range(5):
        try:
            r = requests.get(URL, params={"bbox": ",".join(map(str, bbox)), "limit": limit, "offset": offset, "f": "json"}, timeout=90)
            if r.status_code == 200: return r.json().get("features", [])
        except requests.RequestException:
            pass
        time.sleep(3 * (intento + 1))
    print("  AVISO: fallo persistente en", bbox, offset); return []
vistos, out = set(), []
for k, bbox in enumerate(BOXES, 1):
    off = 0
    while True:
        fs = pagina(bbox, off)
        for f in fs:
            p = f.get("properties", {})
            if p.get("codnut2") not in CCAA or p.get("nationallevelname") != "Municipio": continue
            ine = str(p.get("nationalcode", ""))[-5:]
            if ine[:2] not in PROV or ine in vistos: continue
            vistos.add(ine)
            g = shape(f["geometry"]).simplify(TOL, preserve_topology=True)
            c = g.representative_point()
            out.append({"ine": ine, "nombre": p["nameunit"], "comunidad": CCAA[p["codnut2"]], "provincia": PROV[ine[:2]],
                        "lat": round(c.y, 5), "lng": round(c.x, 5), "geom": mapping(g)})
        if len(fs) < 200: break
        off += 200
    if k % 10 == 0 or k == len(BOXES): print(f"cuadricula {k}/{len(BOXES)}: acumulados {len(out)}")
fc = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {k: v for k, v in o.items() if k != "geom"}, "geometry": o["geom"]} for o in out]}
dest = HERE.parent / "frontend" / "espana.geojson"
dest.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
with open(HERE / "municipios_espana.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["ine","nombre","comunidad","provincia","lat","lng"]); w.writeheader()
    for o in out: w.writerow({k: o[k] for k in w.fieldnames})
por = {}
for o in out: por[o["provincia"]] = por.get(o["provincia"], 0) + 1
print("\nMunicipios por provincia:", dict(sorted(por.items())))
print("TOTAL", len(out), "| GeoJSON %.1f MB" % (dest.stat().st_size / 1e6))
