"""
Robustez final del Paper 1 (puntos 3 y 5), sin dependencias externas salvo numpy/pandas.
 (3) HHF cerca de saturacion: ranking de HHF por estacion con y sin los estacion-anio con HHF>0.95 y sin las estaciones afectadas.
 (5) Tendencias: Mann-Kendall original, Mann-Kendall con correccion de autocorrelacion (Hamed y Rao 1998), pendiente de Sen,
     test de ruptura de Pettitt (anual), tendencias sin estaciones con ruptura, y control de la tasa de falsos descubrimientos (Benjamini-Hochberg).
Salidas: tendencias_v2.csv, robustez_final_resumen.txt
"""
import math
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
IND = ["DF", "CFI", "HHF", "AWVC_g_m3"]
ind = pd.read_csv(HERE / "indices_estacion_anual.csv", dtype={"estacion": str})
ok = ind[ind["año_aceptado"].astype(str).str.upper().isin(["SI", "SÍ"])].copy()
n_ok = ok.groupby("estacion").size(); elig = n_ok[n_ok >= 10].index
ok = ok[ok.estacion.isin(elig)]
out = []

# ---------- (3) HHF cerca de saturacion ----------
base = ok.groupby("estacion").HHF.mean()
sin_sat = ok[ok.HHF <= 0.95].groupby("estacion").HHF.mean().reindex(base.index)
est_afect = ok[ok.HHF > 0.95].estacion.unique()
sin_est = base.drop(est_afect)
def rk(a, b): j = pd.concat([a, b], axis=1).dropna(); return j.iloc[:, 0].rank().corr(j.iloc[:, 1].rank()), len(j)
def top(a, b, f=0.10):
    j = pd.concat([a, b], axis=1).dropna(); k = max(1, int(len(j) * f)); return len(set(j.iloc[:, 0].nlargest(k).index) & set(j.iloc[:, 1].nlargest(k).index)) / k
out.append(f"(3) Estacion-anios con HHF>0.95: {(ok.HHF > 0.95).sum()} de {len(ok)}; estaciones afectadas: {len(est_afect)} de {len(base)}")
r, n = rk(base, sin_sat); out.append(f"    HHF sin los estacion-anio >0.95 vs base: Spearman {r:.3f} (n={n}); coincidencia del 10% superior {top(base, sin_sat):.2f}")
r, n = rk(base.loc[sin_est.index], sin_est); out.append(f"    HHF sin las estaciones afectadas (ranking del resto) vs base: Spearman {r:.3f} (n={n}); posiciones top-10% que ocupaban las afectadas: {len(set(base.nlargest(max(1,len(base)//10)).index) & set(est_afect))} de {max(1,len(base)//10)}")

# ---------- (5) Tendencias ----------
def ncdf(z): return 0.5 * math.erfc(-z / math.sqrt(2))
def mk(x, t, corr=False):
    n = len(x); s = 0
    for i in range(n - 1): s += np.sign(x[i + 1:] - x[i]).sum()
    # varianza con correccion de empates
    _, c = np.unique(x, return_counts=True)
    var = (n * (n - 1) * (2 * n + 5) - sum(k * (k - 1) * (2 * k + 5) for k in c if k > 1)) / 18.0
    if corr:
        slope = np.median([(x[j] - x[i]) / (t[j] - t[i]) for i in range(n) for j in range(i + 1, n) if t[j] != t[i]])
        d = x - slope * t; R = pd.Series(d).rank().values; R = R - R.mean(); den = (R ** 2).sum(); f = 0.0
        for k in range(1, n - 1):
            rk_ = (R[:-k] * R[k:]).sum() / den
            if abs(rk_) > 1.96 / math.sqrt(n): f += (n - k) * (n - k - 1) * (n - k - 2) * rk_
        var *= max(1.0, 1 + 2 * f / (n * (n - 1) * (n - 2)))
    z = (s - np.sign(s)) / math.sqrt(var) if s != 0 else 0.0
    return z, 2 * (1 - ncdf(abs(z)))
def sen(x, t): return np.median([(x[j] - x[i]) / (t[j] - t[i]) for i in range(len(x)) for j in range(i + 1, len(x)) if t[j] != t[i]]) * 10
def pettitt(x):
    n = len(x); r = pd.Series(x).rank().values; U = np.array([2 * r[:k].sum() - k * (n + 1) for k in range(1, n + 1)])
    K = np.abs(U).max(); p = min(1.0, 2 * math.exp(-6 * K ** 2 / (n ** 3 + n ** 2))); return int(np.abs(U).argmax()), p
rows = []
for code, g in ok.groupby("estacion"):
    g = g.sort_values("año"); t = g["año"].values.astype(float)
    for k in IND:
        x = g[k].values.astype(float)
        z0, p0 = mk(x, t); z1, p1 = mk(x, t, True); b = sen(x, t); ib, pb = pettitt(x)
        rows.append(dict(estacion=code, indicador=k, n=len(x), z=z0, p=p0, p_corr=p1, sen_decada=b, ruptura_p=pb, ruptura_anio=int(t[ib])))
T = pd.DataFrame(rows)
def bh(p, q=0.05):
    p = np.asarray(p); o = np.argsort(p); m = len(p); thr = q * (np.arange(1, m + 1)) / m; ok_ = p[o] <= thr
    kmax = np.where(ok_)[0].max() + 1 if ok_.any() else 0; res = np.zeros(m, bool); res[o[:kmax]] = True; return res
T["fdr_corr"] = False
for k in IND: T.loc[T.indicador == k, "fdr_corr"] = bh(T.loc[T.indicador == k, "p_corr"].values)
T["ruptura"] = T.ruptura_p < 0.05
T.to_csv(HERE / "tendencias_v2.csv", index=False)
out.append("(5) Tendencias por indicador sobre %d estaciones:" % T.estacion.nunique())
for k in IND:
    g = T[T.indicador == k]; ns = g.estacion.nunique()
    sig0 = g.p < 0.05; sig1 = g.p_corr < 0.05; sinr = g[~g.ruptura]
    out.append(f"  {k.replace('_g_m3','')}: MK original p<0.05: {sig0.sum()} ({sig0.mean()*100:.0f}%) | con correccion de autocorrelacion: {sig1.sum()} ({sig1.mean()*100:.0f}%) | tras control FDR 5%: {g.fdr_corr.sum()} | "
               f"estaciones con ruptura (Pettitt p<0.05): {g.ruptura.sum()} ({g.ruptura.mean()*100:.0f}%) | sin rupturas, p_corr<0.05: {(sinr.p_corr<0.05).sum()} de {len(sinr)} ({(sinr.p_corr<0.05).mean()*100:.0f}%); mediana Sen/decada todas {g.sen_decada.median():+.4f}, sin rupturas {sinr.sen_decada.median():+.4f}")
    pos = (g[g.fdr_corr].sen_decada > 0).sum(); out.append(f"      significativas tras FDR: {pos} positivas y {g.fdr_corr.sum()-pos} negativas")
# esperado por azar
out.append("  (por azar se esperaria ~5% de estaciones con p<0.05)")
(HERE / "robustez_final_resumen.txt").write_text("\n".join(out), encoding="utf-8"); print("\n".join(out))
