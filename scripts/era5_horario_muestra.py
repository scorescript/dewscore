"""
Paso 1 (validacion R1): descarga de series horarias ERA5-Land (T2m y Td2m) en el punto
de una muestra estratificada de estaciones AEMET con >=10 anios aceptados.
Sirve para cuantificar el efecto de calcular Td con medias diarias frente a valores horarios.

Uso (venv activado, desde terra-main):  python scripts\\era5_horario_muestra.py
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

est["banda"] = pd.cut(est.alt, [-1, 200, 600, 1000, 5000], labels=["<200", "200-600", "600-1000", ">1000"])
muestra = est.groupby("banda", observed=True, group_keys=False).apply(lambda g: g.sample(min(N_POR_BANDA, len(g)), random_state=SEED))
can = est[(est.provincia.isin(["LAS PALMAS", "SANTA CRUZ DE TENERIFE"])) & (~est.indicativo.isin(muestra.indicativo))]
muestra = pd.concat([muestra, can.sample(min(4, len(can)), random_state=SEED)])
muestra["banda"] = pd.cut(muestra.alt, [-1, 200, 600, 1000, 5000], labels=["<200", "200-600", "600-1000", ">1000"]).astype(str)
muestra[["indicativo", "nombre", "provincia", "alt", "lat", "lon", "banda"]].to_csv(HERE / "era5_muestra_estaciones.csv", index=False)
print(f"Muestra: {len(muestra)} estaciones -> era5_muestra_estaciones.csv")

c = cdsapi.Client()
for i, r in enumerate(muestra.itertuples(), 1):
    f = OUT / f"{r.indicativo}.csv"
    if f.exists() and f.stat().st_size > 1000:
        print(f"[{i}/{len(muestra)}] {r.indicativo} ya descargada"); continue
    print(f"[{i}/{len(muestra)}] {r.indicativo} {r.nombre} ({r.lat:.3f},{r.lon:.3f}, {r.alt:.0f} m) ...", flush=True)
    try:
        c.retrieve("reanalysis-era5-land-timeseries", {
            "variable": ["2m_temperature", "2m_dewpoint_temperature"],
            "location": {"longitude": round(r.lon, 3), "latitude": round(r.lat, 3)},
            "date": ["2008-01-01/2025-12-31"],
            "data_format": "csv",
        }, str(f))
    except Exception as e:
        print("  ERROR:", e); sys.exit(1)
print("Listo.")
