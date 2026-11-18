"""
(C, paso 1) Extrae de las series horarias ERA5-Land, para cada estacion elegible, las variables diarias que tambien tiene AEMET
(tmed, tmin, tmax, hrMedia, hrMax, hrMin) y el objetivo Td_B (media del Td horario). Guarda era5_td_diario_<a0>.npz
Uso: python era5_td_diario.py a0 a1   (indices en la lista ordenada de estaciones elegibles)
"""
import sys, zipfile
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
A, B = 17.67, 243.5
def rh_from(T, Td): return 100.0 * np.exp(A * Td / (B + Td) - A * T / (B + T))
ind = pd.read_csv(HERE / "indices_estacion_anual.csv", dtype={"estacion": str})
ok = ind[ind["año_aceptado"].astype(str).str.upper().isin(["SI", "SÍ"])]
n = ok.groupby("estacion").size(); elig = sorted(n[n >= 10].index)
a0, a1 = int(sys.argv[1]), int(sys.argv[2]); cols = []; cods = []
for code in elig[a0:a1]:
    f = HERE / "era5_horario" / f"{code}.csv"
    z = zipfile.ZipFile(f); t = pd.read_csv(z.open(z.namelist()[0]), parse_dates=["valid_time"]).dropna(subset=["t2m", "d2m"])
    if len(t) < 1000: continue
    t["T"] = t.t2m - 273.15; t["Td"] = np.minimum(t.d2m - 273.15, t["T"]); t["RH"] = np.clip(rh_from(t["T"], t.Td), 0.1, 100.0); t["dia"] = t.valid_time.dt.floor("D")
    g = t.groupby("dia").agg(tmed=("T", "mean"), tmin=("T", "min"), tmax=("T", "max"), hrm=("RH", "mean"), hrx=("RH", "max"), hrn=("RH", "min"), tdb=("Td", "mean"))
    g["est"] = len(cods); g["mes"] = g.index.month; g["anio"] = g.index.year; cols.append(g.reset_index(drop=True)); cods.append(code)
D = pd.concat(cols, ignore_index=True)
np.savez_compressed(HERE / f"era5_td_diario_{a0}.npz", **{c: D[c].values.astype("float32") for c in D.columns}, codigos=np.array(cods))
print(a0, a1, len(D), len(cods))
