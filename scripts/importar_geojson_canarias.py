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

ISLAS = ["tenerife", "lanzarote", "fuerteventura", "la_palma", "la_gomera", "el_hierro"]

def matchear_nombre(nameunit, municipios):
    """Busca el municipio en Supabase que mejor coincide con el nombre del IGN."""
    n = nameunit.lower().strip()
    
    # 1. Exacto
    match = next((m for m in municipios if m["nombre"].lower().strip() == n), None)
    if match: return match
    
    # 2. El nombre de Supabase empieza por el del IGN
    match = next((m for m in municipios if m["nombre"].lower().strip().startswith(n)), None)
    if match: return match
    
    # 3. El nombre del IGN empieza por el de Supabase
    match = next((m for m in municipios if n.startswith(m["nombre"].lower().strip())), None)
    if match: return match
    
    # 4. Palabras clave
    match = next((m for m in municipios 
                  if any(w in n for w in m["nombre"].lower().split() if len(w) > 4)), None)
    return match

def importar_isla(nombre_isla):
    geojson_path = Path(__file__).resolve().parent.parent / "frontend" / f"{nombre_isla}.geojson"
    
    if not geojson_path.exists():
        print(f"  ⚠️ No existe: {geojson_path}")
        return

    with open(geojson_path, encoding="utf-8") as f:
        geojson = json.load(f)

    features = geojson.get("features", [])
    print(f"\n{nombre_isla.upper()} — {len(features)} polígonos")

    # Cargar todos los municipios de Supabase
    municipios = supabase.table("municipios").select("id, nombre").execute().data

    for feature in features:
        nameunit = feature["properties"].get("nameunit", "")
        geometry = feature["geometry"]
        geom_str = json.dumps(geometry)

        match = matchear_nombre(nameunit, municipios)

        if not match:
            print(f"  ⚠️ Sin match: {nameunit}")
            continue

        supabase.rpc("actualizar_geom", {
            "municipio_id": match["id"],
            "geom_geojson": geom_str
        }).execute()

        print(f"  ✅ {nameunit} → {match['nombre']}")

if __name__ == "__main__":
    for isla in ISLAS:
        importar_isla(isla)
    print("\n\nImportación completa.")