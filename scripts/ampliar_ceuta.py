"""Añade Ceuta (51001) a frontend/espana.geojson y scripts/municipios_espana.csv. Uso: python scripts\\ampliar_ceuta.py"""
import json, csv, requests
from pathlib import Path
from shapely.geometry import shape, mapping
HERE = Path(__file__).resolve().parent
gj = HERE.parent / "frontend" / "espana.geojson"
fc = json.loads(gj.read_text(encoding="utf-8"))
if any(f["properties"]["ine"] == "51001" for f in fc["features"]):
    print("Ceuta ya estaba"); raise SystemExit
r = requests.get("https://api-features.ign.es/collections/administrativeunit/items",
                 params={"bbox": "-5.5,35.8,-5.2,36.0", "limit": 200, "f": "json"}, timeout=90).json()
for f in r.get("features", []):
    p = f["properties"]
    if p.get("codnut2") == "ES63" and p.get("nationallevelname") == "Municipio":
        g = shape(f["geometry"]).simplify(0.0003, preserve_topology=True); c = g.representative_point()
        props = {"ine": "51001", "nombre": p["nameunit"], "comunidad": "Ciudad de Ceuta", "provincia": "Ceuta", "lat": round(c.y, 5), "lng": round(c.x, 5)}
        fc["features"].append({"type": "Feature", "properties": props, "geometry": mapping(g)})
        gj.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
        with open(HERE / "municipios_espana.csv", "a", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerow([props[k] for k in ["ine", "nombre", "comunidad", "provincia", "lat", "lng"]])
        print("Ceuta añadida:", props["nombre"], "| total", len(fc["features"])); break
else:
    print("No se encontró Ceuta")
