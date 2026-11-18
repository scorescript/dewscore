"""
Validacion cruzada dejando una estacion fuera (LOSO) para cuantificar el error de la regla de asignacion.
Para cada estacion con >=10 anios aceptados se predicen sus medias multianuales de DF, CFI, HHF y AWVC
con la MEJOR otra estacion elegible (misma regla que para municipios: score = sqrt((d/10 km)^2 + (dz/200 m)^2),
radio 30 km) y se mide el error en funcion de la distancia d y de la diferencia de altitud dz.
Salidas: loso_estaciones.csv, loso_resumen.txt
"""
import json, math
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
IND = ["DF", "CFI", "HHF", "AWVC_g_m3"]

def dms(s):
    h = s[-1]; d = s[:-1]; v = int(d[:-4]) + int(d[-4:-2]) / 60 + int(d[-2:]) / 3600
    return -v if h in "WS" else v

sp = pd.DataFrame(json.load(open(HERE / "estaciones_spain.json", encoding="utf-8"))).rename(columns={"altitud": "alt"})[["indicativo", "nombre", "lat", "lon", "alt"]]
mo = pd.DataFrame(json.load(open(HERE / "estaciones_modelo.json", encoding="utf-8"))).dropna(subset=["latitud", "longitud"]).copy()
mo["lat"] = mo.latitud.map(dms); mo["lon"] = mo.longitud.map(dms); mo["alt"] = pd.to_numeric(mo.altitud, errors="coerce")
mo = mo[["indicativo", "nombre", "lat", "lon", "alt"]]
est = pd.concat([sp, mo[~mo.indicativo.isin(sp.indicativo)]], ignore_index=True).drop_duplicates("indicativo").set_index("indicativo")

ind = pd.read_csv(HERE / "indices_estacion_anual.csv", dtype={"estacion": str})
ok = ind[ind["año_aceptado"].astype(str).str.upper().isin(["SI", "SÍ"])]
n = ok.groupby("estacion").size(); elig = n[n >= 10].index
m = ok[ok.estacion.isin(elig)].groupby("estacion")[IND].mean()
m = m.join(est[["lat", "lon", "alt"]], how="inner").dropna(subset=["lat", "lon", "alt"])
print("estaciones elegibles con coordenadas:", len(m))

R = 6371.0
lat = np.radians(m.lat.values); lon = np.radians(m.lon.values); alt = m.alt.values
def dist(i):
    dlat = lat - lat[i]; dlon = lon - lon[i]
    a = np.sin(dlat / 2) ** 2 + np.cos(lat[i]) * np.cos(lat) * np.sin(dlon / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))
rows = []
for i, code in enumerate(m.index):
    d = dist(i); dz = alt - alt[i]; sc = np.sqrt((d / 10) ** 2 + (dz / 200) ** 2)
    sc[i] = np.inf; sc[d > 30] = np.inf
    j = int(np.argmin(sc))
    if not np.isfinite(sc[j]): continue
    r = dict(estacion=code, vecina=m.index[j], d_km=d[j], dz_m=dz[j])
    for k in IND: r[f"err_{k}"] = m[k].iloc[j] - m[k].iloc[i]
    rows.append(r)
L = pd.DataFrame(rows); L.to_csv(HERE / "loso_estaciones.csv", index=False)

out = [f"Estaciones evaluadas con vecina elegible a <=30 km: {len(L)} de {len(m)}"]
def resumen(g, nombre):
    s = f"{nombre}: n={len(g)}"
    for k in IND:
        e = g[f"err_{k}"]; s += f" | {k.replace('_g_m3','')} MAE={e.abs().mean():.3f} RMSE={math.sqrt((e**2).mean()):.3f}"
    out.append(s)
resumen(L, "Todas")
L["flag"] = (L.dz_m.abs() > 300) | (L.d_km > 15)
resumen(L[~L.flag], "Sin marca (|dz|<=300 m y d<=15 km)"); resumen(L[L.flag], "Con marca de baja representatividad")
for lo, hi in [(0, 5), (5, 10), (10, 15), (15, 30)]: resumen(L[(L.d_km > lo) & (L.d_km <= hi)], f"d en ({lo},{hi}] km")
for lo, hi in [(0, 100), (100, 200), (200, 300), (300, 5000)]: resumen(L[(L.dz_m.abs() >= lo) & (L.dz_m.abs() < hi)], f"|dz| en [{lo},{hi}) m")
# relacion lineal del error absoluto con d y |dz|
for k in IND:
    X = np.column_stack([np.ones(len(L)), L.d_km, L.dz_m.abs()]); y = L[f"err_{k}"].abs().values
    b = np.linalg.lstsq(X, y, rcond=None)[0]; out.append(f"|error {k}| ~ {b[0]:.4f} + {b[1]:.5f}*d_km + {b[2]:.6f}*|dz|_m")
(HERE / "loso_resumen.txt").write_text("\n".join(out), encoding="utf-8"); print("\n".join(out))
