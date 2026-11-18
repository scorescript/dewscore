"""
Validacion con observaciones de la red de MeteoGalicia (Galicia, datos horarios) frente a AEMET, para un año (por defecto 2023).
  python scripts\\meteogalicia_validacion.py pares      -> estaciones AEMET elegibles de Galicia emparejadas con estaciones de MeteoGalicia (mg_pares.csv)
  python scripts\\meteogalicia_validacion.py descarga   -> descarga horaria (TA_AVG, TA_MAX, TA_MIN, HR_AVG) del año, en ventanas de 12 h y grupos de 6 estaciones (reanudable)
  python scripts\\meteogalicia_validacion.py analisis   -> (1) T_d de medias diarias frente a T_d horario; (2) indices de ambas redes en los pares
  python scripts\\meteogalicia_validacion.py autotest   -> prueba con datos sinteticos
Servicio: https://servizos.meteogalicia.gal/mgrss/observacion/ (listaEstacionsMeteo.action, datosHorariosEstacions.action). Marcas de tiempo en UTC.
Limitacion: en el dato horario solo hay humedad media horaria, de modo que HHF (humedad maxima > 95 %) se calcula con el maximo de las medias horarias.
"""
import json, sys, time, urllib.parse, urllib.request
import numpy as np, pandas as pd
import xema_validacion as xv

HERE = xv.HERE
CACHE = HERE / "mg_cache"; CACHE.mkdir(exist_ok=True)
SRV = "https://servizos.meteogalicia.gal/mgrss/observacion/"
YEAR = 2023
PARAMS = "TA_AVG_1.5m,TA_MAX_1.5m,TA_MIN_1.5m,HR_AVG_1.5m"
MAX_KM, MAX_DZ = 10.0, 150.0


def get(url, tries=6):
    for k in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=90) as r: return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print(f"  [reintento {k+1}/{tries}] {e}", flush=True); time.sleep(5 * (k + 1))
    raise RuntimeError("fallo de red persistente")


def pares():
    L = get(SRV + "listaEstacionsMeteo.action")["listaEstacionsMeteo"]
    X = pd.DataFrame(L)[["idEstacion", "estacion", "lat", "lon", "altitude"]]
    Aem, _ = xv.aemet_elegibles(); Aem = Aem[(Aem.lat > 41.7) & (Aem.lat < 43.9) & (Aem.lon > -9.4) & (Aem.lon < -6.7)]
    out = []
    for _, a in Aem.iterrows():
        best = None
        for _, x in X.iterrows():
            d = xv.haversine(a.lat, a.lon, x.lat, x.lon); dz = x.altitude - a.alt
            if d <= MAX_KM and abs(dz) <= MAX_DZ:
                s = (d / 5) ** 2 + (dz / 100) ** 2
                if best is None or s < best[0]: best = (s, x.idEstacion, x.estacion, d, dz)
        if best: out.append((a.aemet, a.nombre, int(best[1]), best[2], round(best[3], 2), round(best[4], 0)))
    P = pd.DataFrame(out, columns=["aemet", "nombre_aemet", "mg", "nombre_mg", "d_km", "dz_m"]).sort_values("d_km").drop_duplicates("mg")
    P.to_csv(HERE / "mg_pares.csv", index=False)
    print(f"Estaciones AEMET elegibles en Galicia: {len(Aem)}; pares: {len(P)}"); print(P.to_string(index=False))


def descarga():
    P = pd.read_csv(HERE / "mg_pares.csv"); ids = list(P.mg); grupos = [ids[i:i + 6] for i in range(0, len(ids), 6)]
    ini = pd.Timestamp(f"{YEAR}-01-01 00:00"); n = 0; total = len(grupos) * 730
    for gi, g in enumerate(grupos):
        for k in range(730):
            t = ini + pd.Timedelta(hours=12 * k); n += 1; f = CACHE / f"g{gi}_{t:%Y%m%d%H}.json"
            if f.exists(): continue
            q = urllib.parse.urlencode({"dataIni": t.strftime("%d/%m/%Y %H:%M"), "numHoras": 12, "idEst": ",".join(map(str, g)), "idParam": PARAMS})
            f.write_text(json.dumps(get(SRV + "datosHorariosEstacions.action?" + q)), encoding="utf-8")
            if n % 50 == 0: print(f"[{n}/{total}]", flush=True)
            time.sleep(0.3)
    print("Descarga completa.")


def horarios(files):
    rows = []
    for f in files:
        j = json.loads(f.read_text(encoding="utf-8"))
        for e in j.get("listHorarios", []):
            for ins in e.get("listaInstantes", []):
                d = {m["codigoParametro"]: m["valor"] for m in ins.get("listaMedidas", []) if m.get("lnCodigoValidacion") in (1, None) and m.get("valor") is not None}
                rows.append((e["idEstacion"], pd.Timestamp(ins["instanteLecturaUTC"]), d.get("TA_AVG_1.5m"), d.get("TA_MAX_1.5m"), d.get("TA_MIN_1.5m"), d.get("HR_AVG_1.5m")))
    return pd.DataFrame(rows, columns=["est", "t", "T", "Tx", "Tn", "RH"])


def diarios(H):
    H = H.dropna(subset=["T", "RH"]); H = H[(H.RH > 0) & (H.RH <= 100) & (H["T"] > -50) & (H["T"] < 60)].copy()
    H["Td"] = xv.td_from(H["T"], H.RH); H["fecha"] = H.t.dt.date
    g = H.groupby(["est", "fecha"])
    D = pd.DataFrame({"n": g.size(), "tmed": g["T"].mean(), "tmin": g.Tn.min(), "tmax": g.Tx.max(), "hrm": g.RH.mean(), "hrx": g.RH.max(), "tdB": g.Td.mean()}).dropna()
    D = D[D.n >= 22]; D["tdA"] = xv.td_from(D.tmed, D.hrm); D["tdC"] = xv.td_from((D.tmin + D.tmax) / 2, D.hrm)
    return D.reset_index()


def indices(D, col):
    DF = (D.tmin <= D[col]).mean(); CFI = (D.tmin <= D[col] + 1).mean(); HHF = (D.hrx > 95).mean()
    e = D.hrm / 100 * 6.112 * np.exp(17.67 * D.tmed / (D.tmed + 243.5)); return DF, CFI, HHF, (216.7 * e / (D.tmed + 273.15)).mean()


def analisis():
    P = pd.read_csv(HERE / "mg_pares.csv", dtype={"aemet": str})
    D = diarios(horarios(sorted(CACHE.glob("g*_*.json"))))
    _, ok = xv.aemet_elegibles(); ia = ok.set_index(["estacion", "año"])
    L1, L2 = [], []
    for _, p in P.iterrows():
        S = D[D.est == p.mg]
        if len(S) < 292: continue
        a, b, c = indices(S, "tdA"), indices(S, "tdB"), indices(S, "tdC")
        L1.append((p.mg, len(S), (S.tdA - S.tdB).mean(), (S.tdC - S.tdB).mean(), a[0] - b[0], c[0] - b[0], a[1] - b[1], c[1] - b[1], a[0], b[0], a[1], b[1]))
        if (p.aemet, YEAR) in ia.index:
            r = ia.loc[(p.aemet, YEAR)]; L2.append((p.aemet, p.mg, p.d_km, p.dz_m, r.DF, r.CFI, r.HHF, r.AWVC_g_m3, *indices(S, "tdA")))
    R1 = pd.DataFrame(L1, columns=["mg", "dias", "dTd_A", "dTd_C", "dDF_A", "dDF_C", "dCFI_A", "dCFI_C", "DF_A", "DF_B", "CFI_A", "CFI_B"])
    R2 = pd.DataFrame(L2, columns=["aemet", "mg", "d_km", "dz_m", "DF_aemet", "CFI_aemet", "HHF_aemet", "AWVC_aemet", "DF_mg", "CFI_mg", "HHF_mg", "AWVC_mg"])
    R1.to_csv(HERE / "mg_formulacion_estaciones.csv", index=False); R2.to_csv(HERE / "mg_comparacion_pares.csv", index=False)
    o = [f"Año {YEAR}. (1) Formulacion de T_d con sensores de MeteoGalicia: {len(R1)} estaciones",
         f"    T_d (tmed = media horaria) - T_d horario: {R1.dTd_A.mean():+.2f} C (rango {R1.dTd_A.min():+.2f} a {R1.dTd_A.max():+.2f}); con tmed = (tmin+tmax)/2: {R1.dTd_C.mean():+.2f} C",
         f"    DF +{R1.dDF_A.mean():.3f} (A) y +{R1.dDF_C.mean():.3f} (C); CFI +{R1.dCFI_A.mean():.3f} (A) y +{R1.dCFI_C.mean():.3f} (C); Spearman DF A/B {R1.DF_A.rank().corr(R1.DF_B.rank()):.3f}"]
    def blk(R, et):
        o.append(f"(2) Comparacion entre redes, {et}: {len(R)} pares (distancia mediana {R.d_km.median():.1f} km, |dz| mediana {R.dz_m.abs().median():.0f} m)")
        for k in ("DF", "CFI", "HHF", "AWVC"):
            d = R[f"{k}_mg"] - R[f"{k}_aemet"]; o.append(f"    {k}: sesgo (MG-AEMET) {d.mean():+.3f}, MAE {d.abs().mean():.3f}, Spearman {R[f'{k}_aemet'].rank().corr(R[f'{k}_mg'].rank()):.3f}")
    blk(R2, "todos los pares"); blk(R2[(R2.d_km <= 5) & (R2.dz_m.abs() <= 50)], "pares cercanos (d <= 5 km y |dz| <= 50 m)")
    (HERE / "mg_resumen.txt").write_text("\n".join(o), encoding="utf-8"); print("\n".join(o))


def autotest():
    import tempfile
    global CACHE; CACHE = pathlib_tmp = __import__("pathlib").Path(tempfile.mkdtemp())
    rng = np.random.default_rng(1); idx = pd.date_range("2023-01-01", "2023-03-31 23:00", freq="h")
    T = 10 + 5 * np.sin(2 * np.pi * (idx.hour - 9) / 24) + rng.normal(0, .5, len(idx)); Td = np.minimum(T - 2 - 3 * np.abs(np.sin(np.pi * idx.hour / 24)), T)
    RH = np.clip(xv.rh_from(T, Td), 1, 100); ins = [{"instanteLecturaUTC": t.strftime("%Y-%m-%dT%H:%M:%S"), "listaMedidas": [
        {"codigoParametro": "TA_AVG_1.5m", "lnCodigoValidacion": 1, "valor": float(a)}, {"codigoParametro": "TA_MAX_1.5m", "lnCodigoValidacion": 1, "valor": float(a + .3)},
        {"codigoParametro": "TA_MIN_1.5m", "lnCodigoValidacion": 1, "valor": float(a - .3)}, {"codigoParametro": "HR_AVG_1.5m", "lnCodigoValidacion": 1, "valor": float(r)}]} for t, a, r in zip(idx, T, RH)]
    (CACHE / "g0_x.json").write_text(json.dumps({"listHorarios": [{"idEstacion": 1, "listaInstantes": ins}]}))
    D = diarios(horarios(list(CACHE.glob("g*_*.json")))); print("dias", len(D), "Td_A - Td_B:", round((D.tdA - D.tdB).mean(), 3), "Td_C - Td_B:", round((D.tdC - D.tdB).mean(), 3))


if __name__ == "__main__":
    {"pares": pares, "descarga": descarga, "analisis": analisis, "autotest": autotest}[sys.argv[1] if len(sys.argv) > 1 else "autotest"]()
