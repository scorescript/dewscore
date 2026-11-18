"""Diagnostico del sesgo entre redes: compara dia a dia las variables diarias AEMET y XEMA en los pares cercanos."""
import json
from pathlib import Path
import numpy as np, pandas as pd
import xema_validacion as xv
HERE = xv.HERE
P = pd.read_csv(HERE / "xema_pares.csv", dtype={"aemet": str, "xema": str}); P = P[(P.d_km <= 5) & (P.dz_m.abs() <= 50)]
_, ok = xv.aemet_elegibles(); acept = {(e, int(a)) for e, a in zip(ok.estacion, ok["año"])}
def num(v):
    try: return float(str(v).replace(",", "."))
    except Exception: return np.nan
rows = []; lag = {-1: [], 0: [], 1: []}
for _, p in P.iterrows():
    D = xv.diarios_xema(p.xema)
    if D is None: continue
    D.index = pd.to_datetime(D.index)
    f = HERE / "aemet_diario" / f"{p.aemet}.json"
    if not f.exists(): continue
    R = []
    for lst in json.load(open(f, encoding="utf-8")).values():
        for r in lst:
            v = [num(r.get(k)) for k in ("tmed", "tmin", "tmax", "hrMedia", "hrMax")]
            if np.isnan(v).any() or not (0 < v[3] <= 100): continue
            R.append((pd.Timestamp(r["fecha"]), *v))
    A = pd.DataFrame(R, columns=["fecha", "tmed_a", "tmin_a", "tmax_a", "hrm_a", "hrx_a"]).set_index("fecha")
    A = A[[(p.aemet, d.year) in acept for d in A.index]]
    for k in (-1, 0, 1):
        J = A.join(D.shift(k, freq="D")[["tmed", "tmin", "hrm", "hrx"]], how="inner")
        if len(J) > 200: lag[k].append(np.corrcoef(J.tmin_a, J.tmin)[0, 1])
    J = A.join(D[["tmed", "tmin", "hrm", "hrx", "tdA"]], how="inner")
    if len(J) < 300: continue
    tda_a = xv.td_from(J.tmed_a, J.hrm_a)
    rows.append((p.aemet, p.xema, len(J), (J.tmed - J.tmed_a).mean(), (J.tmin - J.tmin_a).mean(), (J.hrm - J.hrm_a).mean(), (J.hrx - J.hrx_a).mean(), (J.tdA - tda_a).mean(),
                 ((J.tmin <= J.tdA) == (J.tmin_a <= tda_a)).mean(), (J.tmin_a <= tda_a).mean(), (J.tmin <= J.tdA).mean(), (J.tmed_a - (J.tmin_a + J.tmax_a) / 2).mean()))
Rd = pd.DataFrame(rows, columns=["aemet", "xema", "dias", "d_tmed", "d_tmin", "d_hrm", "d_hrx", "d_td", "concord_DF_dia", "DF_aemet", "DF_xema", "tmed_menos_media_extremos_aemet"])
Rd.to_csv(HERE / "xema_diagnostico_pares.csv", index=False)
o = [f"Pares: {len(Rd)}; dias comparados por par (mediana) {Rd.dias.median():.0f}",
     f"Diferencia media XEMA - AEMET (por dia, media de pares): tmed {Rd.d_tmed.mean():+.2f} C, tmin {Rd.d_tmin.mean():+.2f} C, HR media {Rd.d_hrm.mean():+.2f} %, HR max {Rd.d_hrx.mean():+.2f} %, Td_A {Rd.d_td.mean():+.2f} C",
     f"Coincidencia dia a dia del evento DF (tmin<=Td): {Rd.concord_DF_dia.mean():.3f}; frecuencia DF en dias comunes: AEMET {Rd.DF_aemet.mean():.3f}, XEMA {Rd.DF_xema.mean():.3f}",
     f"En AEMET, tmed - (tmin+tmax)/2 = {Rd.tmed_menos_media_extremos_aemet.mean():+.2f} C",
     "Correlacion de tmin entre redes segun desfase de dias de XEMA (-1, 0, +1): " + ", ".join(f"{k}: {np.mean(v):.3f}" for k, v in lag.items())]
(HERE / "xema_diagnostico_resumen.txt").write_text("\n".join(o), encoding="utf-8"); print("\n".join(o))
