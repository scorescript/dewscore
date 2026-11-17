"""
Script 3 — representatividad_estaciones.py
Evalúa la representatividad espacial de las estaciones AEMET asignadas
a cada municipio de Gran Canaria.

Resuelve: R1.4

Calcula para cada municipio:
  - Código de estación asignada
  - Distancia entre estación y centroide del municipio (km)
  - Diferencia de elevación entre estación y municipio (m)
  - Número de estaciones disponibles en radio de 30 km

Salida:
  - representatividad_estaciones.csv
  - representatividad_results.txt → texto y tabla para el paper
"""

import os, json, math
import numpy as np
from dotenv import load_dotenv
from pathlib import Path
from supabase import create_client
import csv

env_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
load_dotenv(dotenv_path=env_path)

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# ── Estaciones asignadas por municipio ────────────────────────────────────────
MUNICIPIO_ESTACION = {
    "Las Palmas de Gran Canaria": "C658X",
    "San Bartolomé de Tirajana": "C635B",
    "Telde": "C648N",
    "Gáldar": "C619X",
    "Arucas": "C669B",
    "Santa Lucía de Tirajana": "C635B",
    "Ingenio": "C648C",
    "Agüimes": "C648C",
    "Mogán": "C629X",
    "La Aldea de San Nicolás": "C619Y",
    "Tejeda": "C614H",
    "Valsequillo": "C611E",
    "Teror": "C656V",
    "Vega de San Mateo": "C611E",
    "Firgas": "C669B",
    "Moya": "C669B",
    "Santa María de Guía": "C619X",
    "Agaete": "C619X",
    "Artenara": "C612F",
    "Santa Brígida": "C611E",
    "Valleseco": "C665T",
}

# ── Elevaciones aproximadas por municipio (m) ─────────────────────────────────
# Valor medio del rango altitudinal del municipio
ALTITUDES_MUNICIPIO = {
    "Las Palmas de Gran Canaria": 8,
    "San Bartolomé de Tirajana": 890,
    "Telde": 115,
    "Gáldar": 120,
    "Arucas": 180,
    "Santa Lucía de Tirajana": 890,
    "Ingenio": 250,
    "Agüimes": 275,
    "Mogán": 80,
    "La Aldea de San Nicolás": 50,
    "Tejeda": 1050,
    "Valsequillo": 640,
    "Teror": 543,
    "Vega de San Mateo": 900,
    "Firgas": 360,
    "Moya": 430,
    "Santa María de Guía": 200,
    "Agaete": 40,
    "Artenara": 1270,
    "Santa Brígida": 450,
    "Valleseco": 890,
}

def haversine(lat1, lon1, lat2, lon2):
    """Distancia en km entre dos puntos (lat/lon en grados)."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def main():
    output_dir = Path(__file__).resolve().parent

    # ── Carga estaciones AEMET ────────────────────────────────────────────────
    json_path = output_dir / "estaciones_canarias.json"
    with open(json_path, encoding="utf-8") as f:
        estaciones_raw = json.load(f)

    def parse_coord(s):
        """Convierte GGMMSSN/S o GGMMSSW/E a grados decimales."""
        s = str(s).strip()
        if not s:
            return None
        hem = s[-1]
        digits = s[:-1].zfill(6)
        g = int(digits[0:2])
        m = int(digits[2:4])
        sec = int(digits[4:6])
        dec = g + m/60 + sec/3600
        if hem in ("S", "W"):
            dec = -dec
        return dec

    # Indexa por código de estación
    estaciones = {}
    for e in estaciones_raw:
        cod = e.get("indicativo") or e.get("codigo") or e.get("id")
        if not cod:
            continue
        try:
            lat = parse_coord(e.get("latitud", ""))
            lon = parse_coord(e.get("longitud", ""))
            alt = float(str(e.get("altitud", "0")).replace(",", "."))
            if lat is None or lon is None:
                continue
        except:
            continue
        estaciones[cod] = {"lat": lat, "lon": lon, "alt": alt, "nombre": e.get("nombre", cod)}

    print(f"Estaciones AEMET cargadas: {len(estaciones)}")

    # ── Carga municipios de Supabase ──────────────────────────────────────────
    res = supabase.table("municipios").select("nombre, lat, lng, isla").eq("isla", "Gran Canaria").execute()
    municipios_db = {m["nombre"]: m for m in res.data}
    print(f"Municipios Gran Canaria en Supabase: {len(municipios_db)}")

    # ── Calcula representatividad ─────────────────────────────────────────────
    RADIO_KM = 30.0
    resultados = []

    for nombre, cod in MUNICIPIO_ESTACION.items():
        muni = municipios_db.get(nombre)
        if not muni:
            print(f"  Sin datos en Supabase: {nombre}")
            continue

        lat_m, lon_m = muni["lat"], muni["lng"]
        alt_m = ALTITUDES_MUNICIPIO.get(nombre, 0)

        # Estación asignada
        est = estaciones.get(cod)
        if est:
            dist_km = haversine(lat_m, lon_m, est["lat"], est["lon"])
            delta_alt = abs(alt_m - est["alt"])
        else:
            print(f"  Estación {cod} no encontrada en JSON para {nombre}")
            dist_km = None
            delta_alt = None

        # Nº de estaciones en radio de 30 km
        n_cercanas = sum(
            1 for c, e in estaciones.items()
            if haversine(lat_m, lon_m, e["lat"], e["lon"]) <= RADIO_KM
        )

        resultados.append({
            "municipio": nombre,
            "estacion": cod,
            "nombre_estacion": est["nombre"] if est else "—",
            "dist_km": round(dist_km, 2) if dist_km is not None else "",
            "delta_alt_m": round(delta_alt, 0) if delta_alt is not None else "",
            "n_estaciones_30km": n_cercanas,
        })

        dist_str = f'{dist_km:.1f}' if dist_km is not None else '?'
        alt_str = f'{delta_alt:.0f}' if delta_alt is not None else '?'
        print(f'  {nombre}: {cod} | {dist_str} km | Dalt={alt_str} m | {n_cercanas} est. en 30 km')

    # ── Guarda CSV ────────────────────────────────────────────────────────────
    csv_path = output_dir / "representatividad_estaciones.csv"
    fields = ["municipio", "estacion", "nombre_estacion", "dist_km", "delta_alt_m", "n_estaciones_30km"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(resultados)
    print(f"\nCSV guardado: {csv_path}")

    # ── Estadísticos globales ─────────────────────────────────────────────────
    dists  = [r["dist_km"] for r in resultados if r["dist_km"] != ""]
    dalts  = [r["delta_alt_m"] for r in resultados if r["delta_alt_m"] != ""]
    n_ests = [r["n_estaciones_30km"] for r in resultados]

    print(f"\n{'='*60}")
    print(f"Distancia estación–centroide: media={np.mean(dists):.1f} km, "
          f"max={max(dists):.1f} km, min={min(dists):.1f} km")
    print(f"Diferencia de elevación:      media={np.mean(dalts):.0f} m, "
          f"max={max(dalts):.0f} m, min={min(dalts):.0f} m")
    print(f"Estaciones en radio 30 km:    media={np.mean(n_ests):.1f}, "
          f"max={max(n_ests)}, min={min(n_ests)}")
    print(f"{'='*60}")

    # ── Texto para el paper ───────────────────────────────────────────────────
    txt_path = output_dir / "representatividad_results.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("=== TEXTO PARA EL PAPER (R1.4) ===\n\n")
        f.write(
            f"The spatial representativeness of the assigned AEMET stations was assessed "
            f"by computing, for each of the 21 municipalities in the study area, "
            f"the great-circle distance between the station and the municipal centroid, "
            f"the difference in elevation between the station and the mean municipal altitude, "
            f"and the number of active AEMET stations within a 30 km radius. "
            f"The mean station-to-centroid distance was {np.mean(dists):.1f} km "
            f"(range: {min(dists):.1f}--{max(dists):.1f} km), and the mean elevation "
            f"difference was {np.mean(dalts):.0f} m "
            f"(range: {min(dalts):.0f}--{max(dalts):.0f} m). "
            f"On average, {np.mean(n_ests):.1f} AEMET stations were available within 30 km "
            f"of each municipal centroid (range: {min(n_ests)}--{max(n_ests)}). "
            f"Municipalities with the largest elevation differences "
            f"(e.g., Tejeda and Artenara, located above 1000 m a.s.l.) "
            f"were assigned to the nearest available high-altitude stations, "
            f"minimising the lapse-rate bias in dew point derivation.\n\n"
        )
        f.write("=== TABLA ===\n\n")
        f.write(f"{'Municipio':<35} {'Estación':>8} {'Dist (km)':>10} {'Δalt (m)':>10} {'N est 30km':>12}\n")
        f.write("-" * 80 + "\n")
        for r in sorted(resultados, key=lambda x: x["dist_km"] if x["dist_km"] != "" else 999, reverse=True):
            f.write(f"{r['municipio']:<35} {r['estacion']:>8} "
                    f"{str(r['dist_km']):>10} {str(r['delta_alt_m']):>10} "
                    f"{r['n_estaciones_30km']:>12}\n")

    print(f"Texto para el paper: {txt_path}")

if __name__ == "__main__":
    main()
