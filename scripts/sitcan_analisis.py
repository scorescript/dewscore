"""Validacion con SITCAN (Canarias, 2023, 10 min): (1) T_d de medias diarias frente a T_d medido por el sensor; (2) indices frente a AEMET en pares cercanos.
Uso: python scripts\\sitcan_analisis.py   (requiere sitcan_diario_2023.csv y sitcan_estaciones.csv). Sin altitud de estacion en SITCAN: el emparejamiento usa solo la distancia."""
import re, numpy as np, pandas as pd
import xema_validacion as xv
HERE = xv.HERE; Y = 2023
D = pd.read_csv(HERE / "sitcan_diario_2023.csv"); E = pd.read_csv(HERE / "sitcan_estaciones.csv")
E[["lon", "lat"]] = E.location_coordinates.str.extract(r"POINT\(([-\d.]+) ([-\d.]+)\)").astype(float)
def idx(S, c):
    DF = (S.tmin <= S[c]).mean(); CFI = (S.tmin <= S[c] + 1).mean(); HHF = (S.hrx > 95).mean()
    e = S.hrm / 100 * 6.112 * np.exp(17.67 * S.tmed / (S.tmed + 243.5)); return DF, CFI, HHF, (216.7 * e / (S.tmed + 273.15)).mean()
import json
_, ok = xv.aemet_elegibles(); ia = ok.set_index(["estacion", "año"]); el = set(ok.estacion)
def _dms(v, w=2):
    s = v[:-1]; h = 1 if v[-1] in "NE" else -1; g = int(s[:-4]); return h * (g + int(s[-4:-2]) / 60 + int(s[-2:]) / 3600)
Aem = pd.DataFrame([(c["indicativo"], c["nombre"], _dms(c["latitud"]), _dms(c["longitud"]), float(c["altitud"])) for c in json.load(open(HERE / "estaciones_canarias.json", encoding="utf-8")) if c["indicativo"] in el], columns=["aemet", "nombre", "lat", "lon", "alt"])
print("Estaciones AEMET elegibles en Canarias:", len(Aem))
L1, L2 = [], []
for t, S in D.groupby("thing_id"):
    if len(S) < 292: continue
    S = S.copy(); S["tdB"] = S.td_sensor; a, b, c = idx(S, "tdA"), idx(S, "tdB"), idx(S, "tdC")
    L1.append((t, len(S), (S.tdA - S.tdB).mean(), (S.tdC - S.tdB).mean(), a[0] - b[0], c[0] - b[0], a[1] - b[1], c[1] - b[1], a[0], b[0]))
    e = E[E.thing_id == t].iloc[0]; best = None
    for _, p in Aem.iterrows():
        d = xv.haversine(p.lat, p.lon, e.lat, e.lon)
        if d <= 10 and (best is None or d < best[0]): best = (d, p.aemet)
    if best and (best[1], Y) in ia.index:
        r = ia.loc[(best[1], Y)]; L2.append((best[1], t, e.location_description, round(best[0], 2), r.DF, r.CFI, r.HHF, r.AWVC_g_m3, *idx(S, "tdA")))
R1 = pd.DataFrame(L1, columns=["thing", "dias", "dTd_A", "dTd_C", "dDF_A", "dDF_C", "dCFI_A", "dCFI_C", "DF_A", "DF_B"])
R2 = pd.DataFrame(L2, columns=["aemet", "thing", "lugar", "d_km", "DF_aemet", "CFI_aemet", "HHF_aemet", "AWVC_aemet", "DF_s", "CFI_s", "HHF_s", "AWVC_s"])
R1.to_csv(HERE / "sitcan_formulacion_estaciones.csv", index=False); R2.to_csv(HERE / "sitcan_comparacion_pares.csv", index=False)
o = [f"Año {Y}. (1) SITCAN, T_d medido por el sensor: {len(R1)} estaciones",
     f"    T_d (tmed = media 10 min) - T_d sensor: {R1.dTd_A.mean():+.2f} C (rango {R1.dTd_A.min():+.2f} a {R1.dTd_A.max():+.2f}); con tmed = (tmin+tmax)/2: {R1.dTd_C.mean():+.2f} C",
     f"    DF {R1.dDF_A.mean():+.3f} (A) y {R1.dDF_C.mean():+.3f} (C); CFI {R1.dCFI_A.mean():+.3f} (A) y {R1.dCFI_C.mean():+.3f} (C); Spearman DF A/B {R1.DF_A.rank().corr(R1.DF_B.rank()):.3f}",
     f"(2) Comparacion con AEMET: {len(R2)} pares (d <= 10 km; distancia mediana {R2.d_km.median():.1f} km; sin control de altitud)"]
for k in ("DF", "CFI", "HHF", "AWVC"):
    d = R2[f"{k}_s"] - R2[f"{k}_aemet"]; o.append(f"    {k}: sesgo (SITCAN-AEMET) {d.mean():+.3f}, MAE {d.abs().mean():.3f}, Spearman {R2[f'{k}_aemet'].rank().corr(R2[f'{k}_s'].rank()):.3f}")
(HERE / "sitcan_resumen.txt").write_text("\n".join(o), encoding="utf-8"); print("\n".join(o)); print(R2[["aemet", "lugar", "d_km"]].to_string(index=False))
