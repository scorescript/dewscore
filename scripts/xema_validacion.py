"""
Validacion con observaciones: red XEMA de Meteocat (Cataluña, datos semihorarios, 2009-) frente a AEMET.
Pasos (reanudable; la descarga guarda cache en xema_cache/):
  python scripts\\xema_validacion.py pares        -> empareja estaciones AEMET elegibles con estaciones XEMA proximas (xema_pares.csv)
  python scripts\\xema_validacion.py descarga     -> descarga T (32) y HR (33) semihorarias de las estaciones emparejadas, 2008-2025
  python scripts\\xema_validacion.py analisis     -> (1) T_d de medias diarias frente a T_d de valores semihorarios (sensores reales)
                                                    (2) comparacion de DF, CFI, HHF y AWVC entre redes en los pares
  python scripts\\xema_validacion.py autotest     -> prueba la logica con datos sinteticos (sin red)
Datos: Meteocat, Dades meteorologiques de la XEMA (datos abiertos de Cataluña, dataset nzvn-apee; estaciones yqwd-vj5e).
Todos los valores semihorarios con codi_estat 'V' (validos). Las marcas de tiempo son UTC.
"""
import json, math, sys, time, urllib.request, urllib.parse
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
CACHE = HERE / "xema_cache"; CACHE.mkdir(exist_ok=True)
BASE = "https://analisi.transparenciacatalunya.cat/resource/"
A, B = 17.67, 243.5
Y0, Y1 = 2008, 2025
MAX_KM, MAX_DZ = 10.0, 150.0


def get(url, tries=6):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"Accept": "application/json"}), timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            wait = 5 * (k + 1)
            print(f"  [reintento {k+1}/{tries}] {e}; espero {wait}s", flush=True); time.sleep(wait)
    raise RuntimeError("fallo de red persistente: " + url[:120])


def haversine(lat1, lon1, lat2, lon2):
    p = math.pi / 180; a = math.sin((lat2 - lat1) * p / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(a))


def td_from(T, RH):
    g = np.log(RH / 100.0) + A * T / (B + T); return B * g / (A - g)


def rh_from(T, Td):
    return 100.0 * np.exp(A * Td / (B + Td) - A * T / (B + T))


def aemet_elegibles():
    ind = pd.read_csv(HERE / "indices_estacion_anual.csv", dtype={"estacion": str})
    ok = ind[ind["año_aceptado"].astype(str).str.upper().isin(["SI", "SÍ"])]
    n = ok.groupby("estacion").size(); elig = set(n[n >= 10].index)
    est = {e["indicativo"]: e for e in json.load(open(HERE / "estaciones_spain.json", encoding="utf-8"))}
    rows = [(c, est[c]["nombre"], est[c]["lat"], est[c]["lon"], est[c]["altitud"]) for c in sorted(elig) if c in est and est[c].get("lat") is not None]
    return pd.DataFrame(rows, columns=["aemet", "nombre", "lat", "lon", "alt"]), ok


def pares():
    meta = get(BASE + "yqwd-vj5e.json?$limit=2000")
    X = pd.DataFrame(meta)[["codi_estacio", "nom_estacio", "latitud", "longitud", "altitud", "data_inici", "data_fi", "nom_estat_ema"]].copy()
    for c in ("latitud", "longitud", "altitud"): X[c] = pd.to_numeric(X[c], errors="coerce")
    X = X.dropna(subset=["latitud", "longitud", "altitud"])
    X["ini"] = pd.to_datetime(X.data_inici, errors="coerce"); X["fin"] = pd.to_datetime(X.data_fi, errors="coerce")
    # estaciones con al menos 8 años de funcionamiento dentro de 2009-2025
    X["anios"] = [((min(f, pd.Timestamp("2025-12-31")) if pd.notna(f) else pd.Timestamp("2025-12-31")) - max(i, pd.Timestamp("2009-01-01"))).days / 365.25 for i, f in zip(X.ini, X.fin)]
    X = X[X.anios >= 8]
    Aem, _ = aemet_elegibles()
    Aem = Aem[(Aem.lat > 40.4) & (Aem.lat < 43.0) & (Aem.lon > 0.0) & (Aem.lon < 3.5)]
    out = []
    for _, a in Aem.iterrows():
        best = None
        for _, x in X.iterrows():
            d = haversine(a.lat, a.lon, x.latitud, x.longitud); dz = x.altitud - a.alt
            if d <= MAX_KM and abs(dz) <= MAX_DZ:
                s = math.sqrt((d / 5) ** 2 + (dz / 100) ** 2)
                if best is None or s < best[0]: best = (s, x.codi_estacio, x.nom_estacio, d, dz)
        if best: out.append((a.aemet, a.nombre, best[1], best[2], round(best[3], 2), round(best[4], 0)))
    P = pd.DataFrame(out, columns=["aemet", "nombre_aemet", "xema", "nombre_xema", "d_km", "dz_m"])
    P = P.sort_values("d_km").drop_duplicates("xema")  # una estacion XEMA por par
    P.to_csv(HERE / "xema_pares.csv", index=False)
    print(f"Estaciones AEMET elegibles en Cataluña: {len(Aem)}; pares AEMET-XEMA (<= {MAX_KM} km y |dz| <= {MAX_DZ} m): {len(P)}")
    print(P.to_string(index=False))


def descarga():
    P = pd.read_csv(HERE / "xema_pares.csv", dtype=str)
    total = len(P) * (Y1 - Y0 + 1) * 2; hecho = 0
    for _, p in P.iterrows():
        for var in ("32", "33"):
            for y in range(Y0, Y1 + 1):
                f = CACHE / f"{p.xema}_{var}_{y}.csv"; hecho += 1
                if f.exists(): continue
                where = f"codi_estacio='{p.xema}' AND codi_variable='{var}' AND codi_estat='V' AND data_lectura >= '{y}-01-01T00:00:00' AND data_lectura < '{y+1}-01-01T00:00:00'"
                q = urllib.parse.urlencode({"$select": "data_lectura,valor_lectura", "$where": where, "$order": "data_lectura", "$limit": 50000})
                rows = get(BASE + "nzvn-apee.json?" + q)
                pd.DataFrame(rows, columns=["data_lectura", "valor_lectura"]).to_csv(f, index=False)
                print(f"[{hecho}/{total}] {p.xema} var {var} {y}: {len(rows)} filas", flush=True); time.sleep(0.4)
    print("Descarga completa.")


def diarios_xema(xema, years=None):
    """Devuelve un DataFrame diario con medias y extremos, a partir de la cache semihoraria."""
    fr = []
    for y in range(Y0, Y1 + 1):
        if years is not None and y not in years: continue
        d = {}
        for var, nm in (("32", "T"), ("33", "RH")):
            f = CACHE / f"{xema}_{var}_{y}.csv"
            if not f.exists(): break
            t = pd.read_csv(f)
            if t.empty: break
            d[nm] = t.set_index(pd.to_datetime(t.data_lectura))["valor_lectura"].astype(float)
        else:
            fr.append(pd.concat(d, axis=1).dropna())
    if not fr: return None
    S = pd.concat(fr)
    S = S[(S.RH > 0) & (S.RH <= 100) & (S["T"] > -50) & (S["T"] < 60)]
    S["Td"] = td_from(S["T"], S.RH); S["fecha"] = S.index.date
    g = S.groupby("fecha")
    D = pd.DataFrame({"n": g.size(), "tmed": g["T"].mean(), "tmin": g["T"].min(), "tmax": g["T"].max(), "hrm": g.RH.mean(), "hrx": g.RH.max(), "tdB": g.Td.mean()})
    D = D[D.n >= 44]  # >= 44 de 48 lecturas semihorarias
    D["tdA"] = td_from(D.tmed, D.hrm)
    D["anio"] = pd.to_datetime(D.index).year
    return D


def indices(D, col_td):
    DF = (D.tmin <= D[col_td]).mean(); CFI = (D.tmin <= D[col_td] + 1).mean(); HHF = (D.hrx > 95).mean()
    e = D.hrm / 100 * 6.112 * np.exp(17.67 * D.tmed / (D.tmed + 243.5)); AW = (216.7 * e / (D.tmed + 273.15)).mean()
    return DF, CFI, HHF, AW


def analisis():
    P = pd.read_csv(HERE / "xema_pares.csv", dtype={"aemet": str, "xema": str})
    _, ok = aemet_elegibles()
    acept = {(e, int(a)) for e, a in zip(ok.estacion, ok["año"])}
    ind_a = ok.set_index(["estacion", "año"])
    L1, L2, out = [], [], []
    for _, p in P.iterrows():
        D = diarios_xema(p.xema)
        if D is None or D.empty: continue
        # (1) formulacion de T_d con sensores reales (todos los años XEMA con >= 292 dias)
        ny = D.groupby("anio").size(); anios = [y for y in ny.index if ny[y] >= 292]
        Dy = D[D.anio.isin(anios)]
        if len(anios) < 5: continue
        a = indices(Dy, "tdA"); b = indices(Dy, "tdB")
        L1.append((p.xema, len(anios), (Dy.tdA - Dy.tdB).mean(), (Dy.tdA - Dy.tdB).std(), a[0], b[0], a[1], b[1], (Dy.tdA - Dy.tdB)[pd.to_datetime(Dy.index).month == 1].mean(), (Dy.tdA - Dy.tdB)[pd.to_datetime(Dy.index).month == 7].mean()))
        # (2) comparacion entre redes en los años aceptados de AEMET con >= 292 dias XEMA
        comunes = [y for y in anios if (p.aemet, y) in acept]
        if len(comunes) < 5: continue
        Dc = D[D.anio.isin(comunes)]; x = indices(Dc, "tdA")
        sub = ind_a.loc[[(p.aemet, y) for y in comunes]]
        aem = (sub.DF.mean(), sub.CFI.mean(), sub.HHF.mean(), sub.AWVC_g_m3.mean())
        L2.append((p.aemet, p.xema, p.d_km, p.dz_m, len(comunes), *aem, *x))
    if not L1: print("No hay datos en la cache; ejecuta primero 'descarga'."); return
    R1 = pd.DataFrame(L1, columns=["xema", "anios", "tdA_menos_tdB", "sd_dia", "DF_A", "DF_B", "CFI_A", "CFI_B", "dif_enero", "dif_julio"])
    R2 = pd.DataFrame(L2, columns=["aemet", "xema", "d_km", "dz_m", "anios", "DF_aemet", "CFI_aemet", "HHF_aemet", "AWVC_aemet", "DF_xema", "CFI_xema", "HHF_xema", "AWVC_xema"])
    R1.to_csv(HERE / "xema_formulacion_estaciones.csv", index=False); R2.to_csv(HERE / "xema_comparacion_pares.csv", index=False)
    out.append(f"(1) Formulacion de T_d con sensores reales de la XEMA: {len(R1)} estaciones")
    out.append(f"    T_d (medias diarias) - T_d (media de valores semihorarios): media {R1.tdA_menos_tdB.mean():+.3f} C (rango de estaciones {R1.tdA_menos_tdB.min():+.2f} a {R1.tdA_menos_tdB.max():+.2f}); enero {R1.dif_enero.mean():+.2f}, julio {R1.dif_julio.mean():+.2f}")
    out.append(f"    DF: {R1.DF_A.mean():.3f} (medias diarias) frente a {R1.DF_B.mean():.3f} (semihorario), diferencia {(R1.DF_A-R1.DF_B).mean():+.4f}; CFI: {R1.CFI_A.mean():.3f} frente a {R1.CFI_B.mean():.3f}, diferencia {(R1.CFI_A-R1.CFI_B).mean():+.4f}")
    out.append(f"    Spearman entre estaciones DF A/B {R1.DF_A.rank().corr(R1.DF_B.rank()):.3f}; CFI {R1.CFI_A.rank().corr(R1.CFI_B.rank()):.3f}")
    def bloque(R, etiqueta):
        out.append(f"(2) Comparacion entre redes, {etiqueta}: {len(R)} pares (distancia mediana {R.d_km.median():.1f} km, |dz| mediana {R.dz_m.abs().median():.0f} m)")
        for k in ("DF", "CFI", "HHF", "AWVC"):
            d = R[f"{k}_xema"] - R[f"{k}_aemet"]
            out.append(f"    {k}: sesgo (XEMA-AEMET) {d.mean():+.3f}, MAE {d.abs().mean():.3f}, Spearman {R[f'{k}_aemet'].rank().corr(R[f'{k}_xema'].rank()):.3f}, Pearson {R[f'{k}_aemet'].corr(R[f'{k}_xema']):.3f}")
    bloque(R2, "todos los pares")
    bloque(R2[(R2.d_km <= 5) & (R2.dz_m.abs() <= 50)], "pares cercanos (d <= 5 km y |dz| <= 50 m)")
    (HERE / "xema_resumen.txt").write_text("\n".join(out), encoding="utf-8"); print("\n".join(out))


def autotest():
    import tempfile
    global CACHE
    CACHE = Path(tempfile.mkdtemp())
    rng = np.random.default_rng(0)
    idx = pd.date_range("2010-01-01", "2014-12-31 23:30", freq="30min")
    T = 15 + 8 * np.sin(2 * np.pi * (idx.dayofyear - 110) / 365.25) + 5 * np.sin(2 * np.pi * (idx.hour + idx.minute / 60 - 9) / 24) + rng.normal(0, 0.5, len(idx))
    Td = T - 4 - 6 * np.abs(np.sin(2 * np.pi * (idx.hour - 3) / 24)) + rng.normal(0, 0.5, len(idx)); Td = np.minimum(Td, T)
    T = np.asarray(T); Td = np.asarray(Td); RH = np.clip(rh_from(T, Td), 1, 100)
    for var, v in (("32", T), ("33", RH)):
        for y in range(2010, 2015):
            m = idx.year == y
            pd.DataFrame({"data_lectura": idx[m].strftime("%Y-%m-%dT%H:%M:%S.000"), "valor_lectura": v[m]}).to_csv(CACHE / f"TEST_{var}_{y}.csv", index=False)
    global Y0, Y1; Y0, Y1 = 2010, 2014
    D = diarios_xema("TEST"); print("dias", len(D), "dif media Td (A-B):", round((D.tdA - D.tdB).mean(), 3), "DF A/B:", [round(x, 3) for x in (indices(D, "tdA")[0], indices(D, "tdB")[0])])


if __name__ == "__main__":
    {"pares": pares, "descarga": descarga, "analisis": analisis, "autotest": autotest}[sys.argv[1] if len(sys.argv) > 1 else "autotest"]()
