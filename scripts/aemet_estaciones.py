import requests
import os
from dotenv import load_dotenv
from pathlib import Path

# Apunta explícitamente al .env dentro de backend/
env_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("AEMET_API_KEY")

if not API_KEY:
    raise ValueError(f"No se encontró AEMET_API_KEY. Verifica que exista en: {env_path}")

def listar_estaciones():
    url = "https://opendata.aemet.es/opendata/api/valores/climatologicos/inventarioestaciones/todasestaciones"
    headers = {"api_key": API_KEY}
    
    response = requests.get(url, headers=headers)
    data = response.json()
    
    datos_url = data.get("datos")
    estaciones = requests.get(datos_url).json()
    
    gran_canaria = [e for e in estaciones if e.get("provincia") == "LAS PALMAS"]
    
    for e in gran_canaria:
        print(f"{e['indicativo']} | {e['nombre']} | lat: {e['latitud']} lon: {e['longitud']}")
    
    return gran_canaria

if __name__ == "__main__":
    listar_estaciones()