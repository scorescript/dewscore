import requests
import os
import time
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("AEMET_API_KEY")

if not API_KEY:
    raise ValueError(f"No se encontró AEMET_API_KEY. Verifica: {env_path}")

HEADERS = {"api_key": API_KEY}


def obtener_datos_estacion(codigo_estacion: str, fecha_inicio: str, fecha_fin: str):
    """
    Descarga datos climatológicos diarios de una estación AEMET
    entre fecha_inicio y fecha_fin (formato: AAAA-MM-DDTHH:MM:SSUTC)
    """
    url = (
        f"https://opendata.aemet.es/opendata/api/valores/climatologicos/"
        f"diarios/datos/fechaini/{fecha_inicio}/fechafin/{fecha_fin}/"
        f"estacion/{codigo_estacion}"
    )
    
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"Error en petición inicial: {response.status_code} - {response.text}")
        return None
    
    data = response.json()
    
    if data.get("estado") != 200:
        print(f"AEMET devolvió estado {data.get('estado')}: {data.get('descripcion')}")
        return None
    
    datos_url = data.get("datos")
    
    # Pequeña espera recomendada por AEMET entre petición y descarga real
    time.sleep(1)
    
    datos_response = requests.get(datos_url)
    
    if datos_response.status_code != 200:
        print(f"Error descargando datos reales: {datos_response.status_code}")
        return None
    
    return datos_response.json()


if __name__ == "__main__":
    # Prueba con Tejeda (C614H), un mes reciente de ejemplo
    resultado = obtener_datos_estacion(
        codigo_estacion="C614H",
        fecha_inicio="2025-01-01T00:00:00UTC",
        fecha_fin="2025-01-31T23:59:59UTC"
    )
    
    if resultado:
        print(f"Registros obtenidos: {len(resultado)}")
        print("Ejemplo de un día:")
        print(resultado[0])
    else:
        print("No se obtuvieron datos.")