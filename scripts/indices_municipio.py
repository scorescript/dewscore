"""
indices_municipio.py  --  Bloque 3, paso final

Une la asignacion municipio -> estacion (scripts/asignacion_candidatas.csv, columna c1,
generada por asignar_estaciones.py CON el filtro de cobertura ya aplicado) con los
indices por estacion (scripts/indices_estacion_anual.csv, de calcular_indices.py).

Salida: scripts/indices_municipio_anual.csv
  una fila por municipio y año, con la estacion usada, su distancia y desnivel respecto
  al municipio, la bandera de baja representatividad y los cuatro indices
  (DF, CFI, HHF, AWVC). Solo se incluyen años aceptados de la estacion (>= 292 dias validos).

Uso:  python scripts\\indices_municipio.py
"""
import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    asign = list(csv.DictReader(open(HERE / "asignacion_candidatas.csv", encoding="utf-8")))
    ind = {}
    for r in csv.DictReader(open(HERE / "indices_estacion_anual.csv", encoding="utf-8")):
        if r["año_aceptado"] == "SI":
            ind[(r["estacion"], int(r["año"]))] = r

    cols = ["municipio_id", "municipio", "isla", "año", "estacion", "d_km", "dz_m",
            "baja_representatividad", "n_dias_validos", "T_media_C", "HR_media_pct",
            "Td_media_C", "DF", "CFI", "HHF", "AWVC_g_m3"]
    rows, sin = [], []
    for a in asign:
        est = a["c1_id"]
        if not est:
            sin.append(a["municipio"])
            continue
        for (e, y), r in sorted(ind.items()):
            if e != est:
                continue
            rows.append({
                "municipio_id": a["id"], "municipio": a["municipio"], "isla": a["isla"], "año": y,
                "estacion": est, "d_km": a["c1_d_km"], "dz_m": a["c1_dz_m"],
                "baja_representatividad": a["baja_representatividad"],
                "n_dias_validos": r["n_dias_validos"], "T_media_C": r["T_media_C"],
                "HR_media_pct": r["HR_media_pct"], "Td_media_C": r["Td_media_C"],
                "DF": r["DF"], "CFI": r["CFI"], "HHF": r["HHF"], "AWVC_g_m3": r["AWVC_g_m3"],
            })

    out = HERE / "indices_municipio_anual.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    con = {r["municipio"] for r in rows}
    print(f"Filas municipio-año: {len(rows)} | municipios con datos: {len(con)} de {len(asign)}")
    if sin:
        print(f"Sin estacion candidata ({len(sin)}): {', '.join(sin)}")
    print(f"Guardado: {out}")


if __name__ == "__main__":
    main()
