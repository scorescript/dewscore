"""
(C, paso 2) Efecto de usar medias diarias en las 675 estaciones ERA5 y modelo de correccion lineal del Td.
 Td_A = Magnus(tmed, hrMedia) (metodo del paper); Td_B = media del Td horario; delta = Td_B - Td_A.
 Modelo: delta ~ lineal en [tmed, tmin, tmax, hrMedia, hrMax, hrMin, Td_A, tmax-tmin, hrMax-hrMin, sen/cos del mes]; ajuste en la mitad de las
 estaciones y evaluacion en la otra mitad (y viceversa). Luego se aplica el modelo (ajustado con todas) a los datos AEMET.
Salidas: era5_td_correccion_resumen.txt, era5_td_correccion_estaciones.csv
"""
import json, math
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
A, B = 17.67, 243.5
def td_from(T, RH): g = np.log(RH / 100.0) + A * T / (B + T); return B * g / (A - g)
def feats(tmed, tmin, tmax, hrm, hrx, hrn, mes):
    tda = td_from(tmed, hrm)
    return np.column_stack([np.ones(len(tmed)), tmed, tmin, tmax, hrm, hrx, hrn, tda, tmax - tmin, hrx - hrn, np.sin(2 * np.pi * mes / 12), np.cos(2 * np.pi * mes / 12)]), tda

Z = [np.load(HERE / f"era5_td_diario_{a}.npz", allow_pickle=True) for a in (0, 350)]
off = 0; parts = []; cods = []
for z in Z:
    d = {k: z[k] for k in ("tmed", "tmin", "tmax", "hrm", "hrx", "hrn", "tdb", "est", "mes", "anio")}; d["est"] = d["est"].astype(int) + off; parts.append(d); off += len(z["codigos"]); cods += list(z["codigos"])
D = {k: np.concatenate([p[k] for p in parts]).astype("float32") for k in parts[0]}; D["est"] = D["est"].astype(int)
tda = td_from(D["tmed"], D["hrm"]).astype("float32"); y = D["tdb"] - tda
def XF(ix): return feats(D["tmed"][ix], D["tmin"][ix], D["tmax"][ix], D["hrm"][ix], D["hrx"][ix], D["hrn"][ix], D["mes"][ix])[0].astype("float64")
nst = len(cods); out = [f"Estaciones: {nst}; dias: {len(y)}"]
out.append(f"Delta = Td_B - Td_A (todas las estaciones y dias): media {y.mean():+.3f} C, desviacion {y.std():.3f}; Td_A - Td_B = {-y.mean():+.3f}")
for m in (1, 4, 7, 10): out.append(f"  mes {m}: Td_A - Td_B medio {-y[D['mes']==m].mean():+.3f}")
def idx_ind(est_sel):
    msk = np.isin(D["est"], est_sel); return msk
def evalua(train, test, tag):
    mtr = idx_ind(train); mte = idx_ind(test)
    sub = np.where(mtr)[0]; rng = np.random.default_rng(1); sub = rng.choice(sub, min(600000, len(sub)), replace=False)
    beta = np.linalg.lstsq(XF(sub), y[sub].astype("float64"), rcond=None)[0]; te=np.where(mte)[0]; pred = np.zeros(len(y),dtype="float32"); pred[te] = XF(te) @ beta
    r0 = math.sqrt((y[mte] ** 2).mean()); r1 = math.sqrt(((y[mte] - pred[mte]) ** 2).mean())
    df = pd.DataFrame({"est": D["est"][mte], "anio": D["anio"][mte], "dfB": (D["tmin"][mte] <= D["tdb"][mte]), "dfA": (D["tmin"][mte] <= tda[mte]), "dfC": (D["tmin"][mte] <= tda[mte] + pred[mte]),
                       "cB": (D["tmin"][mte] <= D["tdb"][mte] + 1), "cA": (D["tmin"][mte] <= tda[mte] + 1), "cC": (D["tmin"][mte] <= tda[mte] + pred[mte] + 1)})
    s = df.groupby("est").mean(numeric_only=True)
    res = [f"[{tag}] estaciones de ajuste {len(train)}, de evaluacion {len(test)}; RMSE diario de delta sin correccion {r0:.3f} -> con correccion {r1:.3f}"]
    for a, c, nm in (("dfA", "dfC", "DF"), ("cA", "cC", "CFI")):
        b = {"DF": "dfB", "CFI": "cB"}[nm]
        res.append(f"   {nm}: sesgo medio (frente al horario) {((s[a]-s[b]).mean()):+.4f} -> {((s[c]-s[b]).mean()):+.4f}; MAE por estacion {(s[a]-s[b]).abs().mean():.4f} -> {(s[c]-s[b]).abs().mean():.4f}; Spearman con horario {s[a].rank().corr(s[b].rank()):.4f} -> {s[c].rank().corr(s[b].rank()):.4f}")
    return res, beta
rng = np.random.default_rng(42); perm = rng.permutation(nst); h1, h2 = perm[: nst // 2], perm[nst // 2:]
r1, _ = evalua(h1, h2, "ajuste mitad 1, evaluacion mitad 2"); r2, _ = evalua(h2, h1, "ajuste mitad 2, evaluacion mitad 1"); out += r1 + r2
sub = np.random.default_rng(3).choice(len(y), 800000, replace=False); beta = np.linalg.lstsq(XF(sub), y[sub].astype("float64"), rcond=None)[0]
out.append("Coeficientes del modelo final (1, tmed, tmin, tmax, hrMedia, hrMax, hrMin, Td_A, tmax-tmin, hrMax-hrMin, sen, cos): " + ", ".join(f"{b:.4f}" for b in beta))
# aplicacion a datos AEMET
def num(v):
    try: return float(str(v).replace(",", "."))
    except Exception: return np.nan
ind = pd.read_csv(HERE / "indices_estacion_anual.csv", dtype={"estacion": str})
ok = ind[ind["año_aceptado"].astype(str).str.upper().isin(["SI", "SÍ"])]; n = ok.groupby("estacion").size(); elig = set(n[n >= 10].index); acept = set(zip(ok.estacion, ok["año"]))
parts_s = []; ndias = 0; csum = 0.0
for code in sorted(elig):
    f = HERE / "aemet_diario" / f"{code}.json"
    if not f.exists(): continue
    rows = []
    for lst in json.load(open(f, encoding="utf-8")).values():
        for r in lst:
            v = [num(r.get(k)) for k in ("tmed", "tmin", "tmax", "hrMedia", "hrMax", "hrMin")]
            if np.isnan(v).any() or not (0 < v[3] <= 100): continue
            y_ = int(r["fecha"][:4])
            if (code, y_) in acept: rows.append((y_, int(r["fecha"][5:7]), *v))
    if not rows: continue
    q = pd.DataFrame(rows, columns=["anio", "mes", "tmed", "tmin", "tmax", "hrm", "hrx", "hrn"])
    q = q[(q.hrx >= q.hrm) & (q.hrm >= q.hrn) & (q.tmax >= q.tmin)]
    if q.empty: continue
    XQ, tdaQ = feats(q.tmed.values, q.tmin.values, q.tmax.values, q.hrm.values, q.hrx.values, q.hrn.values, q.mes.values); pr = XQ @ beta
    q["dfA"] = q.tmin <= tdaQ; q["dfC"] = q.tmin <= tdaQ + pr; q["cA"] = q.tmin <= tdaQ + 1; q["cC"] = q.tmin <= tdaQ + pr + 1; q["corr"] = pr
    g = q[["anio", "dfA", "dfC", "cA", "cC", "corr"]].groupby("anio").mean().mean(); g["est"] = code; parts_s.append(g); ndias += len(q); csum += pr.sum()
    if len(parts_s) % 100 == 0: print(len(parts_s), flush=True)
S = pd.DataFrame(parts_s).set_index("est"); S.to_csv(HERE / "era5_td_correccion_estaciones.csv")
out.append(f"Aplicacion a AEMET: {ndias} dias de {S.shape[0]} estaciones; correccion media del Td {csum/ndias:+.3f} C")
for a, c, nm in (("dfA", "dfC", "DF"), ("cA", "cC", "CFI")):
    k = max(1, len(S) // 10); t1 = set(S[a].nlargest(k).index); t2 = set(S[c].nlargest(k).index)
    out.append(f"   {nm}: nivel medio baseline {S[a].mean():.3f} -> corregido {S[c].mean():.3f} (cambio {S[c].mean()-S[a].mean():+.4f}); Spearman baseline-corregido {S[a].rank().corr(S[c].rank()):.4f}; coincidencia del 10% superior {len(t1&t2)/k:.2f}")
(HERE / "era5_td_correccion_resumen.txt").write_text("\n".join(out), encoding="utf-8"); print("\n".join(out))
