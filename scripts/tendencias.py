"""
tendencias.py -- Bloque 6 de DewScore: tendencias de los indicadores por estacion.

Mann-Kendall (con correccion de empates, aproximacion normal) y pendiente de Sen sobre
los valores anuales aceptados (>= MIN_DIAS dias validos) de cada estacion con >= 10 años.
No se corrige la autocorrelacion serial y se hacen tantas pruebas como estaciones x
indicadores: los resultados son descriptivos, no una inferencia climatica.
Salida: scripts/tendencias_estacion.csv y scripts/tendencias_results.txt
"""
import math
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent


def mk_sen(y, x):
    n = len(y)
    s = 0
    pend = []
    for i in range(n - 1):
        for j in range(i + 1, n):
            s += (y[j] > y[i]) - (y[j] < y[i])
            pend.append((y[j] - y[i]) / (x[j] - x[i]))
    from collections import Counter
    t = Counter(y).values()
    var = (n * (n - 1) * (2 * n + 5) - sum(k * (k - 1) * (2 * k + 5) for k in t)) / 18
    z = 0 if s == 0 else (s - math.copysign(1, s)) / math.sqrt(var)
    p = math.erfc(abs(z) / math.sqrt(2))
    pend.sort()
    m = len(pend)
    sen = pend[m // 2] if m % 2 else 0.5 * (pend[m // 2 - 1] + pend[m // 2])
    return z, p, sen


def main():
    d = pd.read_csv(HERE / "indices_estacion_anual.csv")
    d = d[d["año_aceptado"] == "SI"]
    filas = []
    for c, g in d.groupby("estacion"):
        g = g.sort_values("año")
        if len(g) < 10:
            continue
        x = g["año"].tolist()
        for k in ("DF", "CFI", "HHF", "AWVC_g_m3", "Td_media_C"):
            z, p, sen = mk_sen(g[k].tolist(), x)
            filas.append(dict(estacion=c, indicador=k, n_años=len(g), primer=x[0], ultimo=x[-1],
                              z=round(z, 3), p=round(p, 4), sen_por_decada=round(sen * 10, 4)))
    r = pd.DataFrame(filas)
    r.to_csv(HERE / "tendencias_estacion.csv", index=False)
    out = []
    for k, g in r.groupby("indicador"):
        sig = g[g.p < 0.05]
        out.append(f"{k}: {len(g)} estaciones; p<0.05: {len(sig)} ({(sig.sen_por_decada>0).sum()} positivas, "
                   f"{(sig.sen_por_decada<0).sum()} negativas); mediana pendiente por decada {g.sen_por_decada.median():.4f}; "
                   f"rango {g.sen_por_decada.min():.4f} a {g.sen_por_decada.max():.4f}")
    (HERE / "tendencias_results.txt").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
