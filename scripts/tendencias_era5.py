"""
(A) Contraste de las tendencias con ERA5-Land y significancia global (de campo) por permutacion de anios.
Usa era5_validacion_estaciones.csv (pares estacion-anio, solo anios aceptados) y tendencias_v2.csv.
Salidas: tendencias_era5.csv, tendencias_era5_resumen.txt
"""
import math
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
IND = ["DF", "CFI", "HHF", "AWVC_g_m3"]
P = pd.read_csv(HERE / "era5_validacion_estaciones.csv", dtype={"estacion": str})
T = pd.read_csv(HERE / "tendencias_v2.csv", dtype={"estacion": str})
def ncdf(z): return 0.5 * math.erfc(-z / math.sqrt(2))
def mk_p(x):
    n = len(x); s = 0
    for i in range(n - 1): s += np.sign(x[i + 1:] - x[i]).sum()
    var = n * (n - 1) * (2 * n + 5) / 18.0; z = (s - np.sign(s)) / math.sqrt(var) if s != 0 else 0.0
    return 2 * (1 - ncdf(abs(z)))
def sen(x, t): return np.median([(x[j] - x[i]) / (t[j] - t[i]) for i in range(len(x)) for j in range(i + 1, len(x)) if t[j] != t[i]]) * 10
out = []; rows = []
for code, g in P.groupby("estacion"):
    g = g.sort_values("anio")
    if len(g) < 10: continue
    t = g.anio.values.astype(float)
    for k in IND:
        rows.append(dict(estacion=code, indicador=k, n=len(g), sen_est=sen(g[k].values, t), p_est=mk_p(g[k].values), sen_era=sen(g[k + "_era"].values, t), p_era=mk_p(g[k + "_era"].values)))
R = pd.DataFrame(rows); R.to_csv(HERE / "tendencias_era5.csv", index=False)
out.append(f"Estaciones con >=10 pares estacion-anio: {R.estacion.nunique()}")
Tf = T[["estacion", "indicador", "fdr_corr"]]
R = R.merge(Tf, on=["estacion", "indicador"], how="left")
for k in IND:
    g = R[R.indicador == k]; nm = k.replace("_g_m3", "")
    same = (np.sign(g.sen_est) == np.sign(g.sen_era)).mean()
    out.append(f"{nm}: mediana pendiente/decada estacion {g.sen_est.median():+.4f} ; ERA5 {g.sen_era.median():+.4f} ; correlacion entre pendientes {g.sen_est.corr(g.sen_era):.3f} ; mismo signo {same*100:.0f}% ; "
               f"significativas (MK, p<0.05) estacion {(g.p_est<.05).sum()} vs ERA5 {(g.p_era<.05).sum()} de {len(g)}")
    f = g[g.fdr_corr == True]
    if len(f): out.append(f"     entre las {len(f)} estaciones significativas tras FDR: mismo signo en ERA5 {(np.sign(f.sen_est)==np.sign(f.sen_era)).mean()*100:.0f}% ; mediana ERA5 {f.sen_era.median():+.4f}")
# significancia de campo: permutar los anios de forma conjunta en todas las estaciones (conserva la dependencia espacial)
anios = sorted(P.anio.unique()); A = len(anios); idx = {a: i for i, a in enumerate(anios)}
rng = np.random.default_rng(42); NP = 2000
out.append(f"Significancia de campo (permutacion conjunta de anios, {NP} permutaciones; no conserva la autocorrelacion temporal):")
for k in IND:
    W = P.pivot(index="estacion", columns="anio", values=k).reindex(columns=anios).values  # estaciones x anios, NaN si no aceptado
    ok = ~np.isnan(W); n = ok.sum(1); keep = n >= 10; W = W[keep]; ok = ok[keep]; n = n[keep]
    def cuenta(Wp):
        okp = ~np.isnan(Wp); x = np.where(okp, Wp, 0.0)
        d = x[:, None, :] - x[:, :, None]                 # d[s,i,j] = x_j - x_i
        m = okp[:, None, :] & okp[:, :, None]
        iu = np.triu(np.ones((A, A), bool), 1)[None]
        S = (np.sign(d) * m * iu).sum((1, 2)); nn = okp.sum(1)
        var = nn * (nn - 1) * (2 * nn + 5) / 18.0
        z = (S - np.sign(S)) / np.sqrt(var); p = np.array([2 * (1 - ncdf(abs(v))) for v in z])
        return int((p < 0.05).sum()), int(((p < 0.05) & (S > 0)).sum()), int(((p < 0.05) & (S < 0)).sum())
    obs = cuenta(W); nulos = np.array([cuenta(W[:, rng.permutation(A)]) for _ in range(NP)])
    pg = (1 + (nulos[:, 0] >= obs[0]).sum()) / (NP + 1)
    out.append(f"  {k.replace('_g_m3','')}: observado {obs[0]} estaciones significativas ({obs[1]} +, {obs[2]} -) con este test simplificado; bajo la hipotesis nula: media {nulos[:,0].mean():.0f}, percentil 95 {np.percentile(nulos[:,0],95):.0f}, maximo {nulos[:,0].max()}; p de campo {pg:.4f}")
(HERE / "tendencias_era5_resumen.txt").write_text("\n".join(out), encoding="utf-8"); print("\n".join(out))
