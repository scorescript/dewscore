"""
(D) Diagnostico de saturacion de humedad y de la serie de HHF.
 1) Estacion-anio con HHF>0.95: cuota de dias con hrMax==100 y >=99, y provincia.
 2) Serie anual de la red (estaciones aceptadas): HHF estacion vs HHF ERA5, hrMax medio, cuota hrMax==100.
Salidas: saturacion_diagnostico.csv (por anio), saturacion_resumen.txt
"""
import json
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
def num(v):
    try: return float(str(v).replace(",", "."))
    except Exception: return np.nan
ind = pd.read_csv(HERE / "indices_estacion_anual.csv", dtype={"estacion": str})
ok = ind[ind["año_aceptado"].astype(str).str.upper().isin(["SI", "SÍ"])]
n = ok.groupby("estacion").size(); elig = set(n[n >= 10].index); ok = ok[ok.estacion.isin(elig)]
acept = set(zip(ok.estacion, ok["año"]))
rows = []
for code in sorted(elig):
    f = HERE / "aemet_diario" / f"{code}.json"
    if not f.exists(): continue
    d = json.load(open(f, encoding="utf-8"))
    for lst in d.values():
        for r in lst:
            tmed, tmin, hr, hx = num(r.get("tmed")), num(r.get("tmin")), num(r.get("hrMedia")), num(r.get("hrMax"))
            if np.isnan([tmed, tmin, hr, hx]).any() or not (0 < hr <= 100): continue
            y = int(r["fecha"][:4])
            if (code, y) in acept: rows.append((code, y, hx))
D = pd.DataFrame(rows, columns=["estacion", "anio", "hrMax"])
g = D.groupby(["estacion", "anio"]).hrMax.agg(n="size", hhf=lambda x: (x > 95).mean(), s100=lambda x: (x >= 100).mean(), s99=lambda x: (x >= 99).mean(), media="mean").reset_index()
out = [f"Estacion-anios analizados: {len(g)}"]
sat = g[g.hhf > 0.95]
sp = pd.DataFrame(json.load(open(HERE / "estaciones_spain.json", encoding="utf-8")))[["indicativo", "provincia"]].rename(columns={"indicativo": "estacion"})
sat = sat.merge(sp, on="estacion", how="left")
out.append(f"Estacion-anio con HHF>0.95: {len(sat)}; estaciones {sat.estacion.nunique()}; cuota media de dias con hrMax==100 en ellos {sat.s100.mean()*100:.0f}% (resto de estacion-anios {g[g.hhf<=0.95].s100.mean()*100:.0f}%); cuota >=99: {sat.s99.mean()*100:.0f}% vs {g[g.hhf<=0.95].s99.mean()*100:.0f}%")
out.append("Provincias de las estaciones afectadas: " + ", ".join(f"{k} {v}" for k, v in sat.drop_duplicates('estacion').provincia.value_counts().items()))
P = pd.read_csv(HERE / "era5_validacion_estaciones.csv", dtype={"estacion": str})
sv = sat.merge(P[["estacion", "anio", "HHF", "HHF_era"]], on=["estacion", "anio"], how="inner")
out.append(f"ERA5 en esos estacion-anios (n={len(sv)}): HHF estacion {sv.HHF.mean():.2f} vs HHF ERA5 {sv.HHF_era.mean():.2f}")
y = g.groupby("anio").agg(n_est=("estacion", "nunique"), hhf=("hhf", "mean"), s100=("s100", "mean"), s99=("s99", "mean"), hrmax=("media", "mean"))
e = P.groupby("anio").agg(hhf_era=("HHF_era", "mean"), hhf_est=("HHF", "mean")); y = y.join(e)
y.to_csv(HERE / "saturacion_diagnostico.csv")
out.append("Serie anual de la red (media entre estaciones): anio, n estaciones, HHF estacion, HHF estacion (mismas 675 que ERA5), HHF ERA5, % dias hrMax==100, hrMax medio")
for a, r in y.iterrows(): out.append(f"  {a}: {int(r.n_est)}, {r.hhf:.3f}, {r.hhf_est:.3f}, {r.hhf_era:.3f}, {r.s100*100:.1f}%, {r.hrmax:.1f}")
(HERE / "saturacion_resumen.txt").write_text("\n".join(out), encoding="utf-8"); print("\n".join(out))
