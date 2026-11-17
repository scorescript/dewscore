"""
calcular_indices.py  --  Bloque 3 de DewScore

Calcula los indices anuales POR ESTACION a partir de las series diarias archivadas
(scripts/aemet_diario/<INDICATIVO>.json, generadas por descargar_diario_aemet.py).

Definiciones (todas diarias, solo sobre dias validos):
  T_d,dia  = punto de rocio de Magnus con T = tmed y HR = hrMedia
             constantes de Fomento (2017, Apendice A.1) / Bolton (1980): a = 17.67, b = 243.5
  DF       = fraccion de dias con  tmin <= T_d,dia
  CFI      = fraccion de dias con  tmin <= T_d,dia + 1 °C
  HHF      = fraccion de dias con  hrMax > 95 %          (High-Humidity Frequency; antes FCE)
  AWVC     = media anual del contenido de vapor de agua, g/m3, con tmed y hrMedia
             e_sat = 6.112 * exp(17.67 T / (T + 243.5))  [hPa]   (Atmospheric Water Vapour Content; antes AWGP)
             rho_v = 216.7 * e / (T + 273.15)
  T_d anual = media de los T_d,dia
  Dia valido = tmed, tmin, hrMedia y hrMax presentes y 0 < hrMedia <= 100.
  Año aceptado = al menos MIN_DIAS dias validos (por defecto 292, ~80 %).

Salida: scripts/indices_estacion_anual.csv  (una fila por estacion y año)

Uso:  python scripts\\calcular_indices.py
      python scripts\\calcular_indices.py --estaciones C658X
"""
import json, csv, math, argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent
A, B = 17.67, 243.5
EPS = 1.0          # tolerancia de CFI, °C
HR_HHF = 95.0      # umbral de HHF, %
MIN_DIAS = 292


def num(v):
    if v is None:
        return None
    try:
        return float(str(v).replace(",", "."))
    except ValueError:
        return None


def dew_point(t, hr):
    """Magnus (Fomento 2017, A.1). hr en %."""
    g = math.log(hr / 100.0) + A * t / (B + t)
    return B * g / (A - g)


def vapour_density(t, hr):
    """Contenido de vapor de agua en g/m3."""
    e_sat = 6.112 * math.exp(A * t / (t + B))
    e = e_sat * hr / 100.0
    return 216.7 * e / (t + 273.15)


def indices_anio(recs):
    n_all = len(recs)
    td, df, cfi, hhf, aw, tm, hm = [], 0, 0, 0, [], [], []
    for r in recs:
        tmed, tmin = num(r.get("tmed")), num(r.get("tmin"))
        hr, hrmax = num(r.get("hrMedia")), num(r.get("hrMax"))
        if None in (tmed, tmin, hr, hrmax) or not (0 < hr <= 100):
            continue
        d = dew_point(tmed, hr)
        td.append(d)
        tm.append(tmed)
        hm.append(hr)
        df += tmin <= d
        cfi += tmin <= d + EPS
        hhf += hrmax > HR_HHF
        aw.append(vapour_density(tmed, hr))
    n = len(td)
    if n == 0:
        return None
    return {
        "n_dias_registro": n_all, "n_dias_validos": n,
        "T_media_C": round(sum(tm) / n, 2), "HR_media_pct": round(sum(hm) / n, 2),
        "Td_media_C": round(sum(td) / n, 2),
        "DF": round(df / n, 4), "CFI": round(cfi / n, 4), "HHF": round(hhf / n, 4),
        "AWVC_g_m3": round(sum(aw) / n, 3),
        "año_aceptado": "SI" if n >= MIN_DIAS else "NO",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--estaciones", nargs="*")
    a = ap.parse_args()

    files = sorted((HERE / "aemet_diario").glob("*.json"))
    if a.estaciones:
        files = [f for f in files if f.stem in a.estaciones]
    rows = []
    for f in files:
        store = json.load(open(f, encoding="utf-8"))
        por_año = {}
        for tag, recs in store.items():
            por_año.setdefault(tag[:4], []).extend(recs)
        for y in sorted(por_año):
            ind = indices_anio(por_año[y])
            if ind:
                rows.append({"estacion": f.stem, "año": int(y), **ind})

    out = HERE / "indices_estacion_anual.csv"
    cols = ["estacion", "año", "n_dias_registro", "n_dias_validos", "T_media_C", "HR_media_pct",
            "Td_media_C", "DF", "CFI", "HHF", "AWVC_g_m3", "año_aceptado"]
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    ok = [r for r in rows if r["año_aceptado"] == "SI"]
    print(f"Estaciones: {len(files)} | filas estacion-año: {len(rows)} | años aceptados (>= {MIN_DIAS} dias): {len(ok)}")
    if ok:
        for k in ("DF", "CFI", "HHF", "AWVC_g_m3"):
            v = sorted(r[k] for r in ok)
            print(f"  {k:10s} min {v[0]:.3f}  mediana {v[len(v)//2]:.3f}  max {v[-1]:.3f}")
    print(f"Guardado: {out}")


if __name__ == "__main__":
    main()
