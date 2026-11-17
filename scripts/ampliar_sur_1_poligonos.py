"""Paso 1 de la extension a Andalucia y Murcia: descarga limites municipales del IGN.
Salida: frontend/sur.geojson (poligonos simplificados) y scripts/municipios_sur.csv
Requiere: pip install requests shapely
Uso: python scripts\\ampliar_sur_1_poligonos.py"""
import json, csv, time, requests
from pathlib import Path
from shapely.geometry import shape, mapping
HERE = Path(__file__).resolve().parent
URL = "https://api-features.ign.es/collections/administrativeunit/items"
CCAA = {"ES61": "Andalucía", "ES62": "Región de Murcia"}
PROV = {"04":"Almería","11":"Cádiz","14":"Córdoba","18":"Granada","21":"Huelva","23":"Jaén","29":"Málaga","41":"Sevilla","30":"Murcia"}
# cuadrículas que cubren Andalucía y Murcia (lon_min, lat_min, lon_max, lat_max)
BOXES = [(-7.6,35.9,-5.8,38.8),(-5.8,35.9,-4.0,38.8),(-4.0,36.4,-2.4,38.8),(-2.4,36.6,-0.6,38.9)]
TOL = 0.0003  # ~30 m de simplificacion
def pagina(bbox, offset, limit=200):
    for intento in range(4):
        r = requests.get(URL, params={"bbox": ",".join(map(str, bbox)), "limit": limit, "offset": offset, "f": "json"}, timeout=90)
        if r.status_code == 200: return r.json().get("features", [])
        time.sleep(3 * (intento + 1))
    raise SystemExit(f"IGN error {r.status_code}: {r.text[:200]}")
vistos, out = {}, []
for bbox in BOXES:
    off = 0
    while True:
        fs = pagina(bbox, off)
        for f in fs:
            p = f.get("properties", {})
            if p.get("codnut2") not in CCAA or p.get("nationallevelname") != "Municipio": continue
            code = str(p.get("nationalcode", ""))
            ine = code[-5:]
            if ine[:2] not in PROV or ine in vistos: continue
            vistos[ine] = 1
            g = shape(f["geometry"]).simplify(TOL, preserve_topology=True)
            c = g.representative_point()
            out.append({"ine": ine, "nombre": p["nameunit"], "comunidad": CCAA[p["codnut2"]], "provincia": PROV[ine[:2]],
                        "lat": round(c.y, 5), "lng": round(c.x, 5), "geom": mapping(g)})
        print(f"bbox {bbox} offset {off}: {len(fs)} features, acumulados {len(out)}")
        if len(fs) < 200: break
        off += 200
fc = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {k: v for k, v in o.items() if k != 'geom'}, "geometry": o["geom"]} for o in out]}
dest = HERE.parent / "frontend" / "sur.geojson"
dest.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
with open(HERE / "municipios_sur.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["ine","nombre","comunidad","provincia","lat","lng"]); w.writeheader()
    for o in out: w.writerow({k: o[k] for k in w.fieldnames})
por = {}
for o in out: por[o["provincia"]] = por.get(o["provincia"], 0) + 1
print("\nMunicipios por provincia:", por, "| total", len(out), "| GeoJSON %.1f MB" % (dest.stat().st_size/1e6))
