"""
sensibilidad.py -- Bloque 5 de DewScore: sensibilidad de los rankings municipales.

(A) Definicion de indices (sobre las series diarias archivadas):
    - constantes de Magnus: (17.67, 243.5) base; (17.625, 243.04); (17.27, 237.7)
    - tolerancia epsilon de CFI: 0, 0.5, 1 (base), 2 °C
    - umbral de HR de HHF: 90, 93, 95 (base), 97 %
    - minimo de dias validos por año: 250, 292 (base), 330
(B) Regla de asignacion (sobre asignacion_candidatas.csv, top-3 candidatas):
    - D0 en {5, 10 (base), 20} km, Z0 en {100, 200 (base), 400} m
    - radio maximo en {15, 20, 30 (base)} km (solo sobre las 3 mejores candidatas)
Para cada variante: Spearman de los valores municipales frente a la linea base,
solapamiento del top-10 y numero de municipios cuya estacion cambia.
Salida: scripts/sensibilidad_results.txt y scripts/sensibilidad_results.csv
Uso: python scripts\\sensibilidad.py
"""
import json, math
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
AÑOS0 = 2008


def num(v):
    try:
        return None if v is None else float(str(v).replace(",", "."))
    except ValueError:
        return None


def cargar():
    datos = {}
    for f in sorted((HERE / "aemet_diario").glob("*.json")):
        st = json.load(open(f, encoding="utf-8"))
        por = {}
        for tag, recs in st.items():
            for r in recs:
                v = [num(r.get(k)) for k in ("tmed", "tmin", "hrMedia", "hrMax")]
                if None in v or not (0 < v[2] <= 100):
                    continue
                por.setdefault(tag[:4], []).append(v)
        datos[f.stem] = por
    return datos


def estacion_media(datos, a=17.67, b=243.5, eps=1.0, hr=95.0, mind=292):
    out = {}
    for c, por in datos.items():
        vals = {"DF": [], "CFI": [], "HHF": []}
        for y, rows in por.items():
            if len(rows) < mind:
                continue
            n = len(rows)
            df = cfi = hh = 0
            for tmed, tmin, h, hmax in rows:
                g = math.log(h / 100.0) + a * tmed / (b + tmed)
                td = b * g / (a - g)
                df += tmin <= td
                cfi += tmin <= td + eps
                hh += hmax > hr
            vals["DF"].append(df / n); vals["CFI"].append(cfi / n); vals["HHF"].append(hh / n)
        if vals["DF"] and len(vals["DF"]) >= 10:
            out[c] = {k: sum(v) / len(v) for k, v in vals.items()}
    return out


def a_municipios(med, asign):
    r = {}
    for mid, c in asign.items():
        if c in med:
            r[mid] = med[c]
    return pd.DataFrame(r).T


def comparar(base, var, col):
    j = base[[col]].join(var[[col]], rsuffix="_v", how="inner").dropna()
    rho = j[col].rank().corr(j[col + "_v"].rank())
    t1 = set(j[col].nlargest(10).index); t2 = set(j[col + "_v"].nlargest(10).index)
    k5 = max(1, int(round(0.05 * len(j))))
    u1 = set(j[col].nlargest(k5).index); u2 = set(j[col + "_v"].nlargest(k5).index)
    return rho, len(t1 & t2), len(j), len(u1 & u2) / k5


def main():
    datos = cargar()
    mun = pd.read_csv(HERE / "indices_municipio_anual.csv")
    asign = mun.groupby("municipio_id")["estacion"].first().to_dict()
    base = a_municipios(estacion_media(datos), asign)
    filas = []

    def reg(grupo, nombre, var, cols):
        for c in cols:
            rho, top, n, t5 = comparar(base, var, c)
            filas.append(dict(grupo=grupo, variante=nombre, indicador=c, spearman=round(rho, 3),
                              top10_comun=top, top5pc_comun=round(t5, 3), n=n))

    for a_, b_ in [(17.625, 243.04), (17.27, 237.7)]:
        reg("Magnus", f"a={a_}, b={b_}", a_municipios(estacion_media(datos, a=a_, b=b_), asign), ["DF", "CFI"])
    for e in (0, 0.5, 2):
        reg("epsilon", f"eps={e}", a_municipios(estacion_media(datos, eps=e), asign), ["CFI"])
    for h in (90, 93, 97):
        reg("umbral HR", f"HR>{h}", a_municipios(estacion_media(datos, hr=h), asign), ["HHF"])
    for m in (250, 330):
        v = a_municipios(estacion_media(datos, mind=m), asign)
        reg("min. dias", f">={m} dias", v, ["DF", "CFI", "HHF"])
        filas.append(dict(grupo="min. dias", variante=f">={m} dias", indicador="municipios con dato",
                          spearman=None, top10_comun=None, n=len(v)))

    # (B) asignacion
    cand = pd.read_csv(HERE / "asignacion_candidatas.csv")
    med = estacion_media(datos)
    def elegir(d0, z0, radio):
        res = {}
        for _, r in cand.iterrows():
            best = None
            for k in ("c1", "c2", "c3"):
                cid = r.get(k + "_id")
                if not isinstance(cid, str) or cid not in med:
                    continue
                d, dz = r[k + "_d_km"], r[k + "_dz_m"]
                if d > radio:
                    continue
                s = math.hypot(d / d0, dz / z0)
                if best is None or s < best[0]:
                    best = (s, cid)
            if best:
                res[int(r["id"])] = best[1]
        return res
    a0 = elegir(10, 200, 30)
    for d0, z0, rad in [(5, 200, 30), (20, 200, 30), (10, 100, 30), (10, 400, 30), (10, 200, 20), (10, 200, 15)]:
        a1 = elegir(d0, z0, rad)
        cambia = sum(1 for k in a0 if k in a1 and a1[k] != a0[k])
        perd = sum(1 for k in a0 if k not in a1)
        v = a_municipios(med, a1)
        for c in ("DF", "CFI", "HHF"):
            rho, top, n, t5 = comparar(a_municipios(med, a0), v, c)
            filas.append(dict(grupo="asignacion", variante=f"D0={d0}, Z0={z0}, radio={rad}", indicador=c,
                              spearman=round(rho, 3), top10_comun=top, top5pc_comun=round(t5, 3), n=n,
                              estacion_cambia=cambia, sin_candidata=perd))
    df = pd.DataFrame(filas)
    df.to_csv(HERE / "sensibilidad_results.csv", index=False)
    txt = df.to_string(index=False)
    (HERE / "sensibilidad_results.txt").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
