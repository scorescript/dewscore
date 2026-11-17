"""
Script 4 — climate_refuge_thresholds.py
Calcula umbrales cuantitativos para definir "climate refuge" municipales.

Resuelve: R1.9 — definición operacional de "climate refuge"

Salida:
  - climate_refuge_thresholds.csv  → tabla completa por municipio
  - climate_refuge_results.txt     → texto listo para el paper
"""

import os
import numpy as np
from dotenv import load_dotenv
from pathlib import Path
from supabase import create_client

# ── Config ────────────────────────────────────────────────────────────────────
env_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
load_dotenv(dotenv_path=env_path)

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

PERCENTIL_REFUGE = 75   # percentil para definir "climate refuge"
CV_MAX = 30.0           # coeficiente de variación máximo del thermal gap (%)

# ── Descarga datos ────────────────────────────────────────────────────────────
print("Descargando datos de Supabase...")
res = supabase.table("atmosfera") \
    .select("municipio_id, año, cfi, hhf, diferencia_temp_rocio, municipios(nombre, isla)") \
    .eq("tipo", "historico") \
    .execute()

datos = res.data
print(f"  {len(datos)} registros descargados")

# ── Agrupa por municipio ──────────────────────────────────────────────────────
from collections import defaultdict

municipios = defaultdict(lambda: {
    "nombre": None, "isla": None,
    "cfi": [], "hhf": [], "thermal_gap": []
})

for d in datos:
    mid = d["municipio_id"]
    municipios[mid]["nombre"] = d["municipios"]["nombre"]
    municipios[mid]["isla"]   = d["municipios"]["isla"]
    if d["cfi"]  is not None: municipios[mid]["cfi"].append(d["cfi"])
    if d["hhf"]  is not None: municipios[mid]["hhf"].append(d["hhf"])
    if d["diferencia_temp_rocio"] is not None:
        municipios[mid]["thermal_gap"].append(d["diferencia_temp_rocio"])

# ── Calcula estadísticos por municipio ────────────────────────────────────────
rows = []
for mid, m in municipios.items():
    if not m["cfi"] or not m["hhf"] or not m["thermal_gap"]:
        continue

    cfi_mean  = np.mean(m["cfi"])
    hhf_mean  = np.mean(m["hhf"])
    tgap_mean = np.mean(m["thermal_gap"])
    tgap_std  = np.std(m["thermal_gap"])
    tgap_cv   = (tgap_std / tgap_mean * 100) if tgap_mean > 0 else 999

    rows.append({
        "municipio_id": mid,
        "nombre":       m["nombre"],
        "isla":         m["isla"],
        "cfi_mean":     round(cfi_mean, 4),
        "hhf_mean":     round(hhf_mean, 4),
        "tgap_mean":    round(tgap_mean, 3),
        "tgap_cv_pct":  round(tgap_cv, 2),
        "n_años":       len(m["cfi"]),
    })

# ── Calcula percentiles regionales ───────────────────────────────────────────
all_cfi = [r["cfi_mean"] for r in rows]
all_hhf = [r["hhf_mean"] for r in rows]

cfi_threshold = np.percentile(all_cfi, PERCENTIL_REFUGE)
hhf_threshold = np.percentile(all_hhf, PERCENTIL_REFUGE)

print(f"\nUmbrales regionales (percentil {PERCENTIL_REFUGE}):")
print(f"  CFI ≥ {cfi_threshold:.4f}")
print(f"  HHF ≥ {hhf_threshold:.4f}")
print(f"  CV thermal gap ≤ {CV_MAX}%")

# ── Clasifica municipios ──────────────────────────────────────────────────────
refuges = []
for r in rows:
    is_refuge = (
        r["cfi_mean"]   >= cfi_threshold and
        r["hhf_mean"]   >= hhf_threshold and
        r["tgap_cv_pct"] <= CV_MAX
    )
    r["climate_refuge"] = is_refuge
    if is_refuge:
        refuges.append(r)

# ── Guarda CSV ────────────────────────────────────────────────────────────────
import csv
output_dir = Path(__file__).resolve().parent

csv_path = output_dir / "climate_refuge_thresholds.csv"
fieldnames = ["nombre", "isla", "cfi_mean", "hhf_mean",
              "tgap_mean", "tgap_cv_pct", "n_años", "climate_refuge"]

with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for r in sorted(rows, key=lambda x: x["cfi_mean"], reverse=True):
        writer.writerow({k: r[k] for k in fieldnames})

print(f"\nCSV guardado: {csv_path}")

# ── Genera texto para el paper ────────────────────────────────────────────────
txt_path = output_dir / "climate_refuge_results.txt"
with open(txt_path, "w", encoding="utf-8") as f:
    f.write("=== TEXTO PARA EL PAPER (R1.9) ===\n\n")
    f.write(f"A climate refuge is operationally defined as a municipality whose "
            f"22-year mean CFI lies at or above the "
            f"{PERCENTIL_REFUGE}th percentile of the regional distribution "
            f"(CFI >= {cfi_threshold:.4f}), whose mean HHF also lies at or above the "
            f"{PERCENTIL_REFUGE}th percentile (HHF >= {hhf_threshold:.4f}), "
            f"and whose thermal gap (T - T_d) coefficient of variation does not exceed "
            f"{CV_MAX}%, jointly indicating high average feasibility and low interannual variability. "
            f"Under this definition, {len(refuges)} of the {len(rows)} municipalities "
            f"in the study area qualify as climate refuges.\n\n")

    f.write("=== MUNICIPIOS CLIMATE REFUGE ===\n\n")
    for r in sorted(refuges, key=lambda x: x["cfi_mean"], reverse=True):
        f.write(f"{r['nombre']} ({r['isla']}) — "
                f"CFI={r['cfi_mean']:.4f}, HHF={r['hhf_mean']:.4f}, "
                f"CV={r['tgap_cv_pct']:.1f}%\n")

    f.write(f"\n=== ESTADÍSTICOS REGIONALES ===\n\n")
    f.write(f"Total municipios analizados: {len(rows)}\n")
    f.write(f"CFI regional — media: {np.mean(all_cfi):.4f}, "
            f"min: {min(all_cfi):.4f}, max: {max(all_cfi):.4f}\n")
    f.write(f"HHF regional — media: {np.mean(all_hhf):.4f}, "
            f"min: {min(all_hhf):.4f}, max: {max(all_hhf):.4f}\n")
    f.write(f"Percentil {PERCENTIL_REFUGE} CFI: {cfi_threshold:.4f}\n")
    f.write(f"Percentil {PERCENTIL_REFUGE} HHF: {hhf_threshold:.4f}\n")

print(f"Texto para el paper: {txt_path}")
print(f"\n{'='*50}")
print(f"RESULTADO: {len(refuges)} municipios clasificados como climate refuge")
print(f"{'='*50}")
for r in sorted(refuges, key=lambda x: x["cfi_mean"], reverse=True):
    print(f"  {r['nombre']:35} ({r['isla']})")
print(f"{'='*50}")
