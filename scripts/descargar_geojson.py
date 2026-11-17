import requests
import json
from pathlib import Path

def descargar_municipios_gran_canaria():
    """
    Descarga los límites municipales de Gran Canaria usando
    la API OGC del IGN (evolución moderna del WFS, devuelve GeoJSON directamente).
    Gran Canaria está en la provincia 35.
    """
    
    # Bounding box de Gran Canaria
    bbox = "-15.85,27.73,-15.35,28.20"
    
    url = (
        f"https://api-features.ign.es/collections/administrativeunit/items"
        f"?bbox={bbox}"
        f"&limit=100"
        f"&f=json"
    )

    print("Descargando límites municipales del IGN (API OGC)...")
    response = requests.get(url, timeout=30)

    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text[:200]}")
        return

    data = response.json()
    features = data.get("features", [])
    print(f"Features descargadas: {len(features)}")

    if not features:
        print("No se obtuvieron features. Revisando respuesta completa:")
        print(json.dumps(data, indent=2)[:500])
        return

    # Filtrar solo nivel municipal (nationalLevel 4 o 5 según INSPIRE)
    municipios = [
        f for f in features
        if f.get("properties", {}).get("nationalLevel") in ["4th order", "5th order", 4, 5]
        or "municipio" in str(f.get("properties", {})).lower()
    ]

    print(f"Municipios encontrados: {len(municipios)}")

    # Si no filtra bien, usamos todos los que vinieron
    if len(municipios) == 0:
        print("Usando todas las features sin filtrar...")
        municipios = features

    # Mostrar propiedades del primer elemento para entender la estructura
    if municipios:
        print("\nEjemplo de propiedades:")
        print(json.dumps(municipios[0].get("properties", {}), indent=2))

    geojson = {
        "type": "FeatureCollection",
        "features": municipios
    }

    output_path = Path(__file__).resolve().parent.parent / "frontend" / "gran_canaria.geojson"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    print(f"\nGeoJSON guardado en: {output_path}")

if __name__ == "__main__":
    descargar_municipios_gran_canaria()