"""
Validacion independiente de los indices por estacion contra indices calculados con ERA5-Land (mismas definiciones diarias):
 Td = Magnus(Tmed, HRmed); DF: Tmin<=Td; CFI: Tmin<=Td+1; HHF: HRmax>95; AWVC (g/m3). Dia UTC; T y HR horarias de ERA5-Land
 (HR derivada de T y Td por Magnus). Se comparan medias multianuales (entre estaciones) y valores anuales (dentro de estacion).
Solo anios aceptados de cada estacion. Salidas: era5_validacion_estaciones.csv, era5_validacion_resumen.txt
"""
import zipfile, math, sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
A, B = 17.67, 243.5
IND = ["DF", "CFI", "HHF", "AWVC_g_m3"]
def td_from(T, RH): g = np.log(RH / 100.0) + A * T / (B + T); return B * g / (A - g)
def rh_from(T, Td): return 100.0 * np.exp(A * Td / (B + Td) - A * T / (B + T))

ind = pd.read_csv(HERE / "indices_estacion_anual.csv", dtype={"estacion": str})
ok = ind[ind["año_aceptado"].astype(str).str.upper().isin(["SI", "SÍ"])].copy()
n = ok.groupby("estacion").size(); elig = list(n[n >= 10].index)
a0, a1 = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 0)
PART = len(sys.argv) > 2
rows = []
for k, code in enumerate(elig[a0:a1], 1):
    f = HERE / "era5_horario" / f"{code}.csv"
    if not f.exists(): continue
    z = zipfile.ZipFile(f); t = pd.read_csv(z.open(z.namelist()[0]), parse_dates=["valid_time"]).dropna(subset=["t2m", "d2m"])
    t["T"] = t.t2m - 273.15; t["Td"] = np.minimum(t.d2m - 273.15, t["T"])
    t["RH"] = np.clip(rh_from(t["T"], t.Td), 0.1, 100.0); t["dia"] = t.valid_time.dt.floor("D")
    g = t.groupby("dia").agg(Tm=("T", "mean"), Tmin=("T", "min"), RHm=("RH", "mean"), RHx=("RH", "max"))
    g["Td"] = td_from(g.Tm, g.RHm)
    es = 6.112 * np.exp(A * g.Tm / (g.Tm + B)); g["AWVC"] = 216.7 * (g.RHm / 100 * es) / (g.Tm + 273.15)
    g["DF"] = (g.Tmin <= g.Td).astype(float); g["CFI"] = (g.Tmin <= g.Td + 1).astype(float); g["HHF"] = (g.RHx > 95).astype(float)
    a = g.groupby(g.index.year)[["DF", "CFI", "HHF", "AWVC"]].mean().rename(columns={"AWVC": "AWVC_g_m3"})
    s = ok[ok.estacion == code].set_index("año")[IND]
    j = s.join(a, lsuffix="_est", rsuffix="_era", how="inner")
    for y, r in j.iterrows(): rows.append(dict(estacion=code, anio=y, **{c: r[f"{c}_est"] for c in IND}, **{c + "_era": r[f"{c}_era"] for c in IND}))
    if k % 100 == 0: print(k, "estaciones", flush=True)
P = pd.DataFrame(rows)
if PART:
    P.to_csv(HERE / f"era5_validacion_parte_{a0}.csv", index=False); print("parte", a0, a1, len(P)); sys.exit(0)
if (HERE / "era5_validacion_parte_0.csv").exists():
    P = pd.concat([pd.read_csv(f, dtype={"estacion": str}) for f in sorted(HERE.glob("era5_validacion_parte_*.csv"), key=lambda p: int(p.stem.split("_")[-1]))], ignore_index=True)
P.to_csv(HERE / "era5_validacion_estaciones.csv", index=False)
M = P.groupby("estacion")[IND + [c + "_era" for c in IND]].mean()
out = [f"Estaciones: {len(M)}; pares estacion-anio: {len(P)}"]
def rk(x, y): return x.rank().corr(y.rank())
for c in IND:
    nm = c.replace("_g_m3", ""); d = M[c + "_era"] - M[c]
    out.append(f"{nm} medias multianuales (entre estaciones): Spearman {rk(M[c], M[c + '_era']):.3f}, Pearson {M[c].corr(M[c + '_era']):.3f}, sesgo ERA5-estacion {d.mean():+.3f}, MAE {d.abs().mean():.3f}, RMSE {math.sqrt((d**2).mean()):.3f}")
for c in IND:
    nm = c.replace("_g_m3", "")
    ea = P[c] - P.groupby("estacion")[c].transform("mean"); er = P[c + "_era"] - P.groupby("estacion")[c + "_era"].transform("mean")
    out.append(f"{nm} anomalias anuales (dentro de estacion): Pearson {ea.corr(er):.3f}")
# por tramo de ranking: coincidencia del decil superior
for c in ["DF", "CFI", "HHF", "AWVC_g_m3"]:
    k10 = max(1, len(M) // 10); a = set(M[c].nlargest(k10).index); b = set(M[c + "_era"].nlargest(k10).index)
    out.append(f"{c.replace('_g_m3','')}: coincidencia del 10% superior (estacion vs ERA5): {len(a & b) / k10:.2f}")
(HERE / "era5_validacion_resumen.txt").write_text("\n".join(out), encoding="utf-8"); print("\n".join(out))
