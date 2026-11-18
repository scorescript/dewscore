"""Agrega a diario (dia UTC) un año de SITCAN (datos de 10 min) por thing_id. Uso: python scripts\\sitcan_diario.py [AÑO=2023]
Salida: sitcan_diario_AÑO.csv (thing_id, fecha, n, tmed, tmin, tmax, hrm, hrx, td_sensor, tdA, tdC)."""
import sys, zipfile, pandas as pd, numpy as np
from pathlib import Path
import xema_validacion as xv
Y = int(sys.argv[1]) if len(sys.argv) > 1 else 2023
import urllib.request
zp = Path(__file__).parent / "sitcan_observaciones.zip"
URL = "https://opendata.sitcan.es/upload/meteorologia/observaciones.zip"
import time
def _total():
    r = urllib.request.Request(URL, headers={"Range": "bytes=0-0"})
    with urllib.request.urlopen(r, timeout=60) as x: return int(x.headers["Content-Range"].split("/")[-1])
tot = _total()
while (zp.stat().st_size if zp.exists() else 0) < tot:
    ya = zp.stat().st_size if zp.exists() else 0
    print(f"Descargando ZIP SITCAN: {ya/1e6:.0f} / {tot/1e6:.0f} MB (reanuda solo)", flush=True)
    try:
        with urllib.request.urlopen(urllib.request.Request(URL, headers={"Range": f"bytes={ya}-"}), timeout=60) as x, open(zp, "ab") as o:
            while True:
                b = x.read(1 << 20)
                if not b: break
                o.write(b)
    except Exception as e:
        print("  corte:", e, "-> reintento", flush=True); time.sleep(5)
M = {"Air temperature (avg.)": "T", "Air temperature (max.)": "Tx", "Air temperature (min.)": "Tn", "Relative humidity (avg.)": "RH", "Dew point (avg.)": "Td"}
parts = []
with zipfile.ZipFile(zp) as z, z.open(f"observaciones_{Y}.csv") as f:
    for i, c in enumerate(pd.read_csv(f, usecols=["thing_id", "datastream_name", "phenomenon_time_begin", "result", "observation_validity"], chunksize=5_000_000)):
        c = c[c.datastream_name.isin(M) & (c.observation_validity == "valid")]
        c = c.assign(v=c.datastream_name.map(M), fecha=pd.to_datetime(c.phenomenon_time_begin, utc=True).dt.date)
        parts.append(c.groupby(["thing_id", "fecha", "v"]).result.agg(["sum", "count", "min", "max"]).reset_index()); print("bloque", i, flush=True)
A = pd.concat(parts); g = A.groupby(["thing_id", "fecha", "v"])
S = pd.DataFrame({"sum": g["sum"].sum(), "n": g["count"].sum(), "min": g["min"].min(), "max": g["max"].max()}).reset_index()
P = S.pivot(index=["thing_id", "fecha"], columns="v")
D = pd.DataFrame({"n": P[("n", "T")], "tmed": P[("sum", "T")] / P[("n", "T")], "tmin": P[("min", "Tn")], "tmax": P[("max", "Tx")], "hrm": P[("sum", "RH")] / P[("n", "RH")], "hrx": P[("max", "RH")], "td_sensor": P[("sum", "Td")] / P[("n", "Td")]}).dropna().reset_index()
D = D[D.n >= 130]; D["tdA"] = xv.td_from(D.tmed, D.hrm); D["tdC"] = xv.td_from((D.tmin + D.tmax) / 2, D.hrm)
out = Path(__file__).parent / f"sitcan_diario_{Y}.csv"; D.to_csv(out, index=False); print(len(D), "filas ->", out)
print("tdA - td_sensor:", round((D.tdA - D.td_sensor).mean(), 2), " tdC - td_sensor:", round((D.tdC - D.td_sensor).mean(), 2))
