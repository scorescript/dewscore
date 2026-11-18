"""Efecto de definir tmed como (tmin+tmax)/2 (como en los registros diarios de AEMET) en lugar de la media de las lecturas, con sensores XEMA."""
import numpy as np, pandas as pd
import xema_validacion as xv
P = pd.read_csv(xv.HERE / "xema_pares.csv", dtype={"xema": str}); L = []
for x in P.xema:
    D = xv.diarios_xema(x)
    if D is None: continue
    ny = D.groupby("anio").size(); D = D[D.anio.isin([y for y in ny.index if ny[y] >= 292])]
    if D.anio.nunique() < 5: continue
    D = D.copy(); D["tdC"] = xv.td_from((D.tmin + D.tmax) / 2, D.hrm)
    L.append((x, (D.tmed - (D.tmin + D.tmax) / 2).mean(), (D.tdA - D.tdB).mean(), (D.tdC - D.tdB).mean(),
              (D.tmin <= D.tdA).mean() - (D.tmin <= D.tdB).mean(), (D.tmin <= D.tdC).mean() - (D.tmin <= D.tdB).mean(),
              (D.tmin <= D.tdA + 1).mean() - (D.tmin <= D.tdB + 1).mean(), (D.tmin <= D.tdC + 1).mean() - (D.tmin <= D.tdB + 1).mean()))
R = pd.DataFrame(L, columns=["xema", "tmed_menos_extremos", "dTd_A", "dTd_C", "dDF_A", "dDF_C", "dCFI_A", "dCFI_C"]); R.to_csv(xv.HERE / "xema_tmed_extremos.csv", index=False)
o = [f"Estaciones: {len(R)}",
     f"Media de las lecturas - (tmin+tmax)/2: {R.tmed_menos_extremos.mean():+.2f} C",
     f"Td con tmed = media de lecturas (A) menos Td semihorario: {R.dTd_A.mean():+.2f} C; DF {R.dDF_A.mean():+.3f}; CFI {R.dCFI_A.mean():+.3f}",
     f"Td con tmed = (tmin+tmax)/2 (definicion AEMET, C) menos Td semihorario: {R.dTd_C.mean():+.2f} C; DF {R.dDF_C.mean():+.3f}; CFI {R.dCFI_C.mean():+.3f}"]
(xv.HERE / "xema_tmed_extremos_resumen.txt").write_text("\n".join(o), encoding="utf-8"); print("\n".join(o))
