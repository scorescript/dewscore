import requests
import json
from pathlib import Path

ISLAS = {
    "tenerife":       "-16.93,27.97,-16.10,28.60",
    "lanzarote":      "-13.87,28.82,-13.40,29.25",
    "fuerteventura":  "-14.55,27.97,-13.75,28.75",
    "la_palma":       "-18.05,28.45,-17.70,28.88",
    "la_gomera":      "-17.40,27.97,-17.05,28.25",
    "el_hierro":      "-18.20,27.63,-17.85,27.85",
}

def descargar_isla(nombre, bbox):
    print(f"\nDescargando {nombre}...")
    url = (
        f"https://api-features.ign.es/collections/administrativeunit/items"
        f"?bbox={bbox}&limit=100&f=json"
    )
    response = requests.get(url, timeout=30)
    if response.status_code != 200:
        print(f"  Error: {response.status_code}")
        return

    data = response.json()
    features = data.get("features", [])
    municipios = [f for f in features if "Municipio" in str(f.get("properties", {}))]

    if not municipios:
        municipios = features

    print(f"  Municipios encontrados: {len(municipios)}")
    if municipios:
        print(f"  Ejemplo: {municipios[0]['properties'].get('nameunit', '?')}")

    output_path = Path(__file__).resolve().parent.parent / "frontend" / f"{nombre}.geojson"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": municipios}, f, ensure_ascii=False, indent=2)

    print(f"  Guardado: {output_path}")
    return municipios

if __name__ == "__main__":
    for nombre, bbox in ISLAS.items():
        descargar_isla(nombre, bbox)
    print("\nTodo descargado.")