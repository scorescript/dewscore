"""
Efecto de calcular el punto de rocio con medias diarias (metodo del paper) frente a valores horarios,
usando series horarias ERA5-Land (T2m, Td2m) en el punto de cada estacion de la muestra.
Metodo A (paper): Td_A = Magnus(T media diaria, HR media diaria); DF_A: tmin <= Td_A ; CFI_A: tmin <= Td_A+1
Metodo B (horario): Td_B = media diaria de Td horaria (Magnus aplicado a valores simultaneos); DF_B, CFI_B analogos
Magnus: a=17.67, b=243.5. Dia = dia UTC. Salidas: era5_formulacion_estaciones.csv, era5_formulacion_resumen.txt
"""
import zipfile, io, math
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
A, B = 17.67, 243.5
def td_from(T, RH):
    g = np.log(RH / 100.0) + A * T / (B + T); return B * g / (A - g)
def rh_from(T, Td):
    return 100.0 * np.exp(A * Td / (B + Td) - A * T / (B + T))

muestra = pd.read_csv(HERE / "era5_muestra_estaciones.csv", dtype={"indicativo": str}).set_index("indicativo")
muestra["banda"] = pd.cut(muestra.alt, [-1, 200, 600, 1000, 5000], labels=["<200", "200-600", "600-1000", ">1000"]).astype(str)
rows_d = []; rows_s = []
for code in muestra.index:
    f = HERE / "era5_horario" / f"{code}.csv"
    if not f.exists(): continue
    z = zipfile.ZipFile(f); t = pd.read_csv(z.open(z.namelist()[0]), parse_dates=["valid_time"])
    t["T"] = t.t2m - 273.15; t["Td"] = t.d2m - 273.15
    t["Td"] = np.minimum(t.Td, t["T"])          # Td no puede superar T
    t["RH"] = np.clip(rh_from(t["T"], t.Td), 0.1, 100.0)
    t["dia"] = t.valid_time.dt.floor("D")
    g = t.groupby("dia").agg(Tmean=("T", "mean"), Tmin=("T", "min"), RHmean=("RH", "mean"), RHmax=("RH", "max"), TdB=("Td", "mean"))
    g["TdA"] = td_from(g.Tmean, g.RHmean)
    g["dTd"] = g.TdA - g.TdB
    for k, col in (("DF", 0.0), ("CFI", 1.0)):
        g[f"{k}_A"] = (g.Tmin <= g.TdA + col).astype(float); g[f"{k}_B"] = (g.Tmin <= g.TdB + col).astype(float)
    g["HHF"] = (g.RHmax > 95).astype(float)
    g["anio"] = g.index.year
    an = g.groupby("anio").agg(DF_A=("DF_A", "mean"), DF_B=("DF_B", "mean"), CFI_A=("CFI_A", "mean"), CFI_B=("CFI_B", "mean"), dTd=("dTd", "mean"), TdA=("TdA", "mean"), TdB=("TdB", "mean"))
    an["estacion"] = code; rows_d.append(an.reset_index())
    mes = g.groupby(g.index.month).dTd.mean()
    rows_s.append(dict(estacion=code, alt=muestra.loc[code, "alt"], banda=muestra.loc[code, "banda"], dTd_mean=g.dTd.mean(), dTd_sd=g.dTd.std(), dTd_p5=g.dTd.quantile(.05), dTd_p95=g.dTd.quantile(.95),
                       dTd_ene=mes.get(1), dTd_jul=mes.get(7), DF_A=g.DF_A.mean(), DF_B=g.DF_B.mean(), CFI_A=g.CFI_A.mean(), CFI_B=g.CFI_B.mean()))
S = pd.DataFrame(rows_s); D = pd.concat(rows_d); S.to_csv(HERE / "era5_formulacion_estaciones.csv", index=False)
out = [f"Estaciones analizadas: {len(S)}", f"Dias por estacion: ~{len(g)}"]
out.append(f"Sesgo diario Td_A - Td_B (grados C): media de estaciones {S.dTd_mean.mean():+.3f} (rango {S.dTd_mean.min():+.3f} a {S.dTd_mean.max():+.3f}); desviacion tipica diaria media {S.dTd_sd.mean():.3f}; p5 medio {S.dTd_p5.mean():+.3f}, p95 medio {S.dTd_p95.mean():+.3f}")
out.append(f"Sesgo medio en enero {S.dTd_ene.mean():+.3f} y en julio {S.dTd_jul.mean():+.3f}")
for k in ("DF", "CFI"):
    d = S[f"{k}_A"] - S[f"{k}_B"]
    out.append(f"{k} multianual A-B: media {d.mean():+.4f}, MAE {d.abs().mean():.4f}, max |dif| {d.abs().max():.4f}; Spearman A vs B entre estaciones {S[f'{k}_A'].rank().corr(S[f'{k}_B'].rank()):.4f}")
    da = D[f"{k}_A"] - D[f"{k}_B"]; out.append(f"{k} anual (estacion-anio) A-B: MAE {da.abs().mean():.4f}, RMSE {math.sqrt((da**2).mean()):.4f}, n={len(D)}")
for b, g2 in S.groupby("banda", observed=True): out.append(f"banda {b} (n={len(g2)}): sesgo Td {g2.dTd_mean.mean():+.3f}; DF A-B {((g2.DF_A-g2.DF_B)).mean():+.4f}; CFI A-B {((g2.CFI_A-g2.CFI_B)).mean():+.4f}")
(HERE / "era5_formulacion_resumen.txt").write_text("\n".join(out), encoding="utf-8"); print("\n".join(out))
