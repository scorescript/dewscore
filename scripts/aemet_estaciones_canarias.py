import requests
import json
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("AEMET_API_KEY")
HEADERS = {"api_key": API_KEY}

def listar_estaciones_canarias():
    url = "https://opendata.aemet.es/opendata/api/valores/climatologicos/inventarioestaciones/todasestaciones"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    datos_url = data.get("datos")
    estaciones = requests.get(datos_url).json()

    provincias = ["LAS PALMAS", "SANTA CRUZ DE TENERIFE"]
    canarias = [e for e in estaciones if e.get("provincia") in provincias]

    print(f"Total estaciones Canarias: {len(canarias)}\n")

    for e in canarias:
        print(f"{e['indicativo']} | {e['nombre']} | {e['provincia']} | lat: {e['latitud']} lon: {e['longitud']}")

    # Guardar en JSON para referencia
    output = Path(__file__).resolve().parent / "estaciones_canarias.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(canarias, f, ensure_ascii=False, indent=2)

    print(f"\nGuardado en: {output}")
    return canarias

if __name__ == "__main__":
    listar_estaciones_canarias()