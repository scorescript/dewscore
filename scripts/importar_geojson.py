import json
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

env_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def importar_poligonos():
    geojson_path = Path(__file__).resolve().parent.parent / "frontend" / "gran_canaria.geojson"
    
    with open(geojson_path, encoding="utf-8") as f:
        geojson = json.load(f)

    features = geojson.get("features", [])
    print(f"Total polígonos a importar: {len(features)}")

    for feature in features:
        nameunit = feature["properties"].get("nameunit", "")
        geometry = feature["geometry"]
        geom_str = json.dumps(geometry)

        # Buscar el municipio en Supabase por nombre aproximado
        res = supabase.table("municipios").select("id, nombre").execute()
        municipios = res.data

        match = None
        for m in municipios:
            nombre = m["nombre"].lower().strip()
            name = nameunit.lower().strip()
            if nombre == name or nombre in name or name in nombre:
                match = m
                break

        if not match:
            print(f"  ⚠️ Sin match: {nameunit}")
            continue

        # Actualizar geometría usando SQL directo via RPC
        supabase.rpc("actualizar_geom", {
            "municipio_id": match["id"],
            "geom_geojson": geom_str
        }).execute()

        print(f"  ✅ {nameunit} → {match['nombre']}")

if __name__ == "__main__":
    importar_poligonos()