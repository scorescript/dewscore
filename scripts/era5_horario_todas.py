"""
Descarga de series horarias ERA5-Land (T2m y Td2m) para TODAS las estaciones elegibles (>=10 anios aceptados),
en orden aleatorio (seed 42) para que cualquier corte deje una muestra representativa. Para validar los indices (punto 4).

Uso (venv activado, desde terra-main):  python scripts\\era5_horario_todas.py
Requisitos: pip install cdsapi  y clave de CDS en C:\\Users\\<usuario>\\.cdsapirc
Es reanudable: salta las estaciones ya descargadas.
"""
import json, sys
from pathlib import Path
import pandas as pd
import cdsapi

HERE = Path(__file__).resolve().parent
OUT = HERE / "era5_horario"; OUT.mkdir(exist_ok=True)
N_POR_BANDA = 12
SEED = 42

def dms(s):
    """'285811N' -> 28.9697 ; '134125W' -> -13.6903"""
    h = s[-1]; d = s[:-1]
    g = int(d[:-4]); m = int(d[-4:-2]); sec = int(d[-2:])
    v = g + m / 60 + sec / 3600
    return -v if h in "WS" else v

# Coordenadas: estaciones_spain.json (decimales) + estaciones_modelo.json (grados-minutos-segundos, Canarias)
sp = pd.DataFrame(json.load(open(HERE / "estaciones_spain.json", encoding="utf-8")))
sp = sp.rename(columns={"altitud": "alt"})[["indicativo", "nombre", "provincia", "lat", "lon", "alt"]]
mo = pd.DataFrame(json.load(open(HERE / "estaciones_modelo.json", encoding="utf-8"))).dropna(subset=["latitud", "longitud"]).copy()
mo["lat"] = mo.latitud.map(dms); mo["lon"] = mo.longitud.map(dms); mo["alt"] = pd.to_numeric(mo.altitud, errors="coerce")
mo = mo[["indicativo", "nombre", "provincia", "lat", "lon", "alt"]]
est = pd.concat([sp, mo[~mo.indicativo.isin(sp.indicativo)]], ignore_index=True)
ind = pd.read_csv(HERE / "indices_estacion_anual.csv", dtype={"estacion": str})
acc = ind[ind["año_aceptado"].astype(str).str.upper().isin(["SI", "SÍ", "TRUE", "1"])].groupby("estacion").size()
acc = acc[acc >= 10].index
est = est[est.indicativo.isin(acc)].dropna(subset=["alt", "lat", "lon"]).copy()
print(f"Estaciones elegibles: {len(est)}")


muestra_ya = set(pd.read_csv(HERE / "era5_muestra_estaciones.csv").indicativo) if (HERE / "era5_muestra_estaciones.csv").exists() else set()
orden = est[~est.indicativo.isin(muestra_ya)].sample(frac=1, random_state=SEED).reset_index(drop=True)  # las 52 de la muestra las descarga el otro script
print(f"Total: {len(orden)} estaciones (orden aleatorio)")
c = cdsapi.Client()
fallos = 0
for i, r in enumerate(orden.itertuples(), 1):
    f = OUT / f"{r.indicativo}.csv"
    if f.exists() and f.stat().st_size > 1000:
        continue
    print(f"[{i}/{len(orden)}] {r.indicativo} {r.nombre} ({r.lat:.3f},{r.lon:.3f}, {r.alt:.0f} m) ...", flush=True)
    try:
        c.retrieve("reanalysis-era5-land-timeseries", {
            "variable": ["2m_temperature", "2m_dewpoint_temperature"],
            "location": {"longitude": round(r.lon, 3), "latitude": round(r.lat, 3)},
            "date": ["2008-01-01/2025-12-31"],
            "data_format": "csv",
        }, str(f))
        fallos = 0
    except Exception as e:
        fallos += 1; print("  ERROR:", e, flush=True)
        if f.exists(): f.unlink()
        if fallos >= 3:
            print("3 errores seguidos: se detiene para no saturar el servicio. Relanza mas tarde."); sys.exit(1)
print("Listo.")
