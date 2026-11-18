"""
(B) Estimador con varias estaciones vecinas e intervalos de prediccion empiricos (validacion cruzada dejando una estacion fuera).
Estimadores de la media multianual de cada estacion con las otras estaciones elegibles a <=30 km:
  k=1 (regla actual), k=2, 3, 5 con pesos 1/score^2 (score = sqrt((d/10)^2 + (dz/200)^2)), y linea base: media nacional de las demas estaciones.
Intervalos: semiancho = cuantil del error absoluto del estimador k=1, calibrado en una mitad aleatoria de estaciones y evaluado en la otra (200 repeticiones).
Salidas: loso_multivecino.csv, loso_multivecino_resumen.txt
"""
import json, math
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
IND = ["DF", "CFI", "HHF", "AWVC_g_m3"]
def dms(s):
    h = s[-1]; d = s[:-1]; v = int(d[:-4]) + int(d[-4:-2]) / 60 + int(d[-2:]) / 3600
    return -v if h in "WS" else v
sp = pd.DataFrame(json.load(open(HERE / "estaciones_spain.json", encoding="utf-8"))).rename(columns={"altitud": "alt"})[["indicativo", "lat", "lon", "alt"]]
mo = pd.DataFrame(json.load(open(HERE / "estaciones_modelo.json", encoding="utf-8"))).dropna(subset=["latitud", "longitud"]).copy()
mo["lat"] = mo.latitud.map(dms); mo["lon"] = mo.longitud.map(dms); mo["alt"] = pd.to_numeric(mo.altitud, errors="coerce"); mo = mo[["indicativo", "lat", "lon", "alt"]]
est = pd.concat([sp, mo[~mo.indicativo.isin(sp.indicativo)]], ignore_index=True).drop_duplicates("indicativo").set_index("indicativo")
ind = pd.read_csv(HERE / "indices_estacion_anual.csv", dtype={"estacion": str})
ok = ind[ind["año_aceptado"].astype(str).str.upper().isin(["SI", "SÍ"])]
n = ok.groupby("estacion").size(); elig = n[n >= 10].index
m = ok[ok.estacion.isin(elig)].groupby("estacion")[IND].mean().join(est, how="inner").dropna(subset=["lat", "lon", "alt"])
lat = np.radians(m.lat.values); lon = np.radians(m.lon.values); alt = m.alt.values; V = m[IND].values; N = len(m)
rows = []
for i in range(N):
    dlat = lat - lat[i]; dlon = lon - lon[i]
    d = 2 * 6371.0 * np.arcsin(np.sqrt(np.sin(dlat / 2) ** 2 + np.cos(lat[i]) * np.cos(lat) * np.sin(dlon / 2) ** 2))
    dz = alt - alt[i]; sc = np.sqrt((d / 10) ** 2 + (dz / 200) ** 2); sc[i] = np.inf; sc[d > 30] = np.inf
    o = np.argsort(sc); o = o[np.isfinite(sc[o])]
    if len(o) == 0: continue
    r = dict(estacion=m.index[i], nvec=len(o), dzmax=abs(dz[o[0]]), d1=d[o[0]], dz1=dz[o[0]])
    for k in (1, 2, 3, 5):
        kk = o[:k]; w = 1.0 / (sc[kk] ** 2 + 1e-6); w /= w.sum()
        est_k = (V[kk] * w[:, None]).sum(0)
        for j, c in enumerate(IND): r[f"e{k}_{c}"] = est_k[j] - V[i, j]
    mean_rest = (V.sum(0) - V[i]) / (N - 1)
    for j, c in enumerate(IND): r[f"base_{c}"] = mean_rest[j] - V[i, j]
    rows.append(r)
L = pd.DataFrame(rows); L.to_csv(HERE / "loso_multivecino.csv", index=False)
out = [f"Estaciones evaluadas: {len(L)} de {N}"]
for c in IND:
    nm = c.replace("_g_m3", ""); b = L[f"base_{c}"].abs().mean()
    s = f"{nm}: MAE k=1 {L[f'e1_{c}'].abs().mean():.3f}, k=2 {L[f'e2_{c}'].abs().mean():.3f}, k=3 {L[f'e3_{c}'].abs().mean():.3f}, k=5 {L[f'e5_{c}'].abs().mean():.3f}; media nacional {b:.3f}"
    s += f" | habilidad k=1 {1 - L[f'e1_{c}'].abs().mean() / b:.2f}, k=3 {1 - L[f'e3_{c}'].abs().mean() / b:.2f}"
    out.append(s)
out.append("RMSE k=1 / k=3: " + "; ".join(f"{c.replace('_g_m3','')} {math.sqrt((L[f'e1_{c}']**2).mean()):.3f}/{math.sqrt((L[f'e3_{c}']**2).mean()):.3f}" for c in IND))
# intervalos empiricos (estimador k=1): semiancho por clase de |dz| (<300 / >=300), calibracion en mitad aleatoria, cobertura en la otra
rng = np.random.default_rng(42)
for nivel in (0.80, 0.90):
    res = {}
    for c in IND:
        cov = []; hw_lo = []; hw_hi = []
        for _ in range(200):
            msk = rng.random(len(L)) < 0.5; cal = L[msk]; tst = L[~msk]
            h_lo = cal[cal.dzmax < 300][f"e1_{c}"].abs().quantile(nivel); h_hi = cal[cal.dzmax >= 300][f"e1_{c}"].abs().quantile(nivel)
            h = np.where(tst.dzmax < 300, h_lo, h_hi); cov.append((tst[f"e1_{c}"].abs() <= h).mean()); hw_lo.append(h_lo); hw_hi.append(h_hi)
        res[c] = (np.mean(cov), np.mean(hw_lo), np.mean(hw_hi))
    out.append(f"Intervalos {int(nivel*100)}%: " + "; ".join(f"{c.replace('_g_m3','')} semiancho |dz|<300 m {v[1]:.3f}, >=300 m {v[2]:.3f}, cobertura fuera de muestra {v[0]*100:.0f}%" for c, v in res.items()))
(HERE / "loso_multivecino_resumen.txt").write_text("\n".join(out), encoding="utf-8"); print("\n".join(out))
