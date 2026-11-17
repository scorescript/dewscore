"""
Script — descargar_inventario_aemet.py
Descarga el inventario completo de estaciones AEMET de España
y guarda un JSON con código, nombre, provincia, lat, lon, altitud.

Salida:
  scripts/estaciones_spain.json
"""

import os, json, math, requests
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
load_dotenv(dotenv_path=env_path)

AEMET_KEY = os.getenv("AEMET_API_KEY")
HEADERS   = {"api_key": AEMET_KEY}

def parse_coord(s):
    """Convierte GGMMSSN/S o GGMMSSW/E a grados decimales."""
    s = str(s).strip()
    if not s:
        return None
    hem    = s[-1]
    digits = s[:-1].zfill(6)
    g      = int(digits[0:2])
    m      = int(digits[2:4])
    sec    = int(digits[4:6])
    dec    = g + m/60 + sec/3600
    if hem in ("S", "W"):
        dec = -dec
    return round(dec, 6)

def main():
    output_dir = Path(__file__).resolve().parent
    out_path   = output_dir / "estaciones_spain.json"

    print("Descargando inventario de estaciones AEMET...")
    url = "https://opendata.aemet.es/opendata/api/valores/climatologicos/inventarioestaciones/todasestaciones"
    import time as _t
    for intento in range(1, 11):
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            break
        print(f"  intento {intento}/10: HTTP {r.status_code} (AEMET pide calma); espero 65 s...")
        _t.sleep(65)
    if r.status_code != 200:
        print(f"Error: {r.status_code}")
        return

    data = r.json()
    if data.get("estado") != 200:
        print(f"AEMET error: {data.get('descripcion')}")
        return

    import time
    time.sleep(2)
    dr = None
    for intento in range(1, 11):
        dr = requests.get(data["datos"], timeout=30)
        if dr.status_code == 200: break
        print(f"  datos: HTTP {dr.status_code}; reintento en 65 s...")
        time.sleep(65)
    estaciones_raw = dr.json()
    print(f"  {len(estaciones_raw)} estaciones descargadas")

    # Parsea y limpia
    estaciones = []
    sin_coords = 0
    for e in estaciones_raw:
        lat = parse_coord(e.get("latitud", ""))
        lon = parse_coord(e.get("longitud", ""))
        if lat is None or lon is None:
            sin_coords += 1
            continue
        try:
            alt = float(str(e.get("altitud", "0")).replace(",", "."))
        except:
            alt = 0.0

        estaciones.append({
            "indicativo": e.get("indicativo", ""),
            "nombre":     e.get("nombre", ""),
            "provincia":  e.get("provincia", ""),
            "lat":        lat,
            "lon":        lon,
            "altitud":    alt,
        })

    print(f"  {len(estaciones)} estaciones con coordenadas válidas")
    print(f"  {sin_coords} estaciones sin coordenadas (descartadas)")

    # Estadísticas por provincia
    from collections import Counter
    provincias = Counter(e["provincia"] for e in estaciones)
    print(f"\n  Provincias con más estaciones:")
    for prov, n in provincias.most_common(10):
        print(f"    {prov}: {n}")

    # Filtra solo estaciones en España (lat 27-44, lon -10 a 5)
    spain = [e for e in estaciones if 27 <= e["lat"] <= 44 and -10 <= e["lon"] <= 5]
    print(f"\n  Estaciones en España (bbox): {len(spain)}")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(spain, f, ensure_ascii=False, indent=2)

    print(f"\nGuardado: {out_path}")
    print(f"Total estaciones útiles: {len(spain)}")

if __name__ == "__main__":
    main()
