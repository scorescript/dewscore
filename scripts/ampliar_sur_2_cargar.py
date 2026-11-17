"""Paso 2: inserta los municipios de Andalucia y Murcia en Supabase (tabla municipios) y sus poligonos.
Usa isla = provincia para reutilizar el selector del mapa. Por defecto SIMULA; --aplicar escribe.
Requiere haber ejecutado el paso 1 y tener backend/.env.  Uso: python scripts\\ampliar_sur_2_cargar.py [--aplicar]"""
import os, sys, json
from pathlib import Path
from dotenv import load_dotenv
HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parent / "backend" / ".env")
fc = json.loads((HERE.parent / "frontend" / "sur.geojson").read_text(encoding="utf-8"))
feats = fc["features"]
print(len(feats), "municipios en sur.geojson")
if "--aplicar" not in sys.argv:
    print("Dry-run. Añade --aplicar para escribir."); sys.exit(0)
from supabase import create_client
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
existentes = {(m["nombre"], m["provincia"]): m["id"] for m in sb.table("municipios").select("id,nombre,provincia").execute().data}
nuevos = 0
for i, f in enumerate(feats, 1):
    p = f["properties"]
    mid = existentes.get((p["nombre"], p["provincia"]))
    if mid is None:
        r = sb.table("municipios").insert({"nombre": p["nombre"], "comunidad": p["comunidad"], "provincia": p["provincia"],
                                            "isla": p["provincia"], "lat": p["lat"], "lng": p["lng"]}).execute()
        mid = r.data[0]["id"]; nuevos += 1
    g = f["geometry"]
    if g["type"] == "Polygon":
        g = {"type": "MultiPolygon", "coordinates": [g["coordinates"]]}
    sb.rpc("actualizar_geom", {"municipio_id": mid, "geom_geojson": json.dumps(g)}).execute()
    if i % 50 == 0: print(f"  {i}/{len(feats)}")
print(f"Listo: {nuevos} municipios nuevos, {len(feats)-nuevos} ya existían (solo se actualizó la geometría).")
