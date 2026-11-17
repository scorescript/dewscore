"""
Punto 2 — asignar_estaciones.py
Regla explícita y reproducible: estación AEMET -> municipio.

REGLA
  1. Candidatas: estaciones del inventario a <= RADIUS_KM del centroide del municipio.
  2. Puntuación de cada candidata:
         score = sqrt( (d / D0)^2 + (dz / Z0)^2 )
       d  = distancia horizontal estación-centroide (km)
       dz = altitud de la estación - altitud media del municipio (m, DEM)
     Con D0 = 10 km y Z0 = 200 m, 1 km pesa lo mismo que 20 m de desnivel.
  3. Se elige la candidata de menor score que tenga datos suficientes
     (>= MIN_YEARS años con >= MIN_DAYS días válidos). Este filtro se aplica
     solo si existe scripts/cobertura_estaciones.json (se genera en la descarga).
  4. Marca de baja representatividad si |dz| > FLAG_DZ_M o d > FLAG_D_KM.
     Esos municipios se reportan, no se ocultan.

ALTITUD MUNICIPAL: media de N_POINTS puntos aleatorios (semilla fija) dentro del
polígono, consultados al DEM Copernicus GLO-90 (90 m) descargado en local.

SALIDAS (en scripts/):
  asignacion_candidatas.csv   -> top-3 candidatas por municipio + comparación con la asignación actual
  altitudes_municipios.json   -> caché de altitudes (no se vuelve a consultar el DEM)

USO
  python scripts/asignar_estaciones.py
  python scripts/asignar_estaciones.py --isla "Gran Canaria"
  python scripts/asignar_estaciones.py --stations scripts/estaciones_spain.json
"""

import os, sys, json, math, time, csv, argparse, asyncio
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ── Parámetros de la regla (todos configurables) ──────────────────────────────
RADIUS_KM = 30.0
D0_KM     = 10.0
Z0_M      = 200.0
FLAG_DZ_M = 300.0
FLAG_D_KM = 15.0
N_POINTS  = 25
SEED      = 42
MIN_YEARS = 10
MIN_DAYS  = 292          # 80 % de 365

# Asignación actual (procesar_atmosfera.py), solo Gran Canaria, para comparar
ASIGNACION_ACTUAL = {
    "Las Palmas de Gran Canaria": "C658X", "San Bartolomé de Tirajana": "C635B",
    "Telde": "C648N", "Gáldar": "C619X", "Arucas": "C669B",
    "Santa Lucía de Tirajana": "C635B", "Ingenio": "C648C", "Agüimes": "C648C",
    "Mogán": "C629X", "La Aldea de San Nicolás": "C619Y", "Tejeda": "C614H",
    "Valsequillo": "C611E", "Teror": "C656V", "Vega de San Mateo": "C611E",
    "Firgas": "C669B", "Moya": "C669B", "Santa María de Guía": "C619X",
    "Agaete": "C619X", "Artenara": "C612F", "Santa Brígida": "C611E",
    "Valleseco": "C665T",
}


# ── Utilidades puras (se pueden probar sin base de datos) ─────────────────────
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def parse_coord(v):
    """Acepta grados decimales (float) o formato AEMET GGMMSS[N|S|E|W]."""
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        pass
    hem = s[-1].upper()
    digits = s[:-1].zfill(6)
    dec = int(digits[0:2]) + int(digits[2:4]) / 60 + int(digits[4:6]) / 3600
    return -dec if hem in ("S", "W") else dec


def load_stations(path):
    raw = json.load(open(path, encoding="utf-8"))
    out = []
    for e in raw:
        cod = e.get("indicativo") or e.get("codigo") or e.get("id")
        lat = parse_coord(e.get("lat", e.get("latitud")))
        lon = parse_coord(e.get("lon", e.get("longitud")))
        try:
            alt = float(str(e.get("altitud", "")).replace(",", "."))
        except ValueError:
            alt = None
        if cod and lat is not None and lon is not None and alt is not None:
            out.append({"id": cod, "nombre": e.get("nombre", cod), "lat": lat, "lon": lon, "alt": alt})
    return out


def score(d_km, dz_m):
    return math.sqrt((d_km / D0_KM) ** 2 + (dz_m / Z0_M) ** 2)


def has_coverage(cod, cobertura):
    if cobertura is None:
        return True
    years = cobertura.get(cod, {})
    return sum(1 for n in years.values() if n >= MIN_DAYS) >= MIN_YEARS


def rank_candidates(clat, clon, z_mean, stations, cobertura=None):
    cands = []
    for st in stations:
        d = haversine(clat, clon, st["lat"], st["lon"])
        if d > RADIUS_KM:
            continue
        dz = st["alt"] - z_mean
        cands.append({
            "id": st["id"], "nombre": st["nombre"], "d_km": d, "dz_m": dz,
            "score": score(d, dz), "cobertura_ok": has_coverage(st["id"], cobertura),
        })
    cands.sort(key=lambda c: c["score"])
    valid = [c for c in cands if c["cobertura_ok"]]
    return valid if cobertura is not None else cands


# ── Acceso a datos externos ───────────────────────────────────────────────────
async def fetch_municipios(isla):
    import asyncpg
    from dotenv import load_dotenv
    load_dotenv(HERE.parent / "backend" / ".env")
    url = os.getenv("DATABASE_URL")
    if not url:
        sys.exit("Falta DATABASE_URL en backend/.env")
    q_seed = """
        SELECT m.id, m.nombre, m.isla,
               ST_Y(ST_Transform(ST_Centroid(m.geom), 4326)) AS clat,
               ST_X(ST_Transform(ST_Centroid(m.geom), 4326)) AS clon,
               pts.ys, pts.xs
        FROM municipios m
        CROSS JOIN LATERAL (
            SELECT array_agg(ST_Y(d.geom)) AS ys, array_agg(ST_X(d.geom)) AS xs
            FROM ST_Dump(ST_GeneratePoints(ST_Transform(m.geom, 4326), $1, $2)) AS d
        ) pts
        WHERE m.geom IS NOT NULL AND ($3::text IS NULL OR m.isla = $3)
        ORDER BY m.id
    """
    q_noseed = q_seed.replace("$1, $2)", "$1)").replace("$3::text IS NULL OR m.isla = $3", "$2::text IS NULL OR m.isla = $2")
    conn = await asyncpg.connect(url, statement_cache_size=0)
    try:
        try:
            return await conn.fetch(q_seed, N_POINTS, SEED, isla)
        except asyncpg.exceptions.UndefinedFunctionError:
            print("AVISO: PostGIS sin semilla en ST_GeneratePoints; los puntos no serán reproducibles.")
            return await conn.fetch(q_noseed, N_POINTS, isla)
    finally:
        await conn.close()


def get_elevations(lats, lons):
    """DEM local Copernicus GLO-90 (ver dem_cop90.py): sin limites de consulta y reproducible."""
    sys.path.insert(0, str(HERE))
    from dem_cop90 import elevations
    return elevations(list(lats), list(lons))


def municipal_altitudes(rows, cache_path, refresh=False):
    cache = {}
    if cache_path.exists() and not refresh:
        cache = json.load(open(cache_path, encoding="utf-8"))
    pending = [r for r in rows if str(r["id"]) not in cache]
    if pending:
        print(f"Consultando DEM para {len(pending)} municipios ({len(pending) * (N_POINTS + 1)} puntos)...")
        lats, lons, spans = [], [], []
        for r in pending:
            pts_lat = [r["clat"]] + list(r["ys"])
            pts_lon = [r["clon"]] + list(r["xs"])
            spans.append((len(lats), len(pts_lat)))
            lats += pts_lat
            lons += pts_lon
        elev = get_elevations(lats, lons)
        for r, (start, n) in zip(pending, spans):
            z = elev[start:start + n]
            zc, zp = z[0], z[1:]
            cache[str(r["id"])] = {
                "alt_media": round(sum(zp) / len(zp), 1), "alt_min": round(min(zp), 1),
                "alt_max": round(max(zp), 1), "alt_centroide": round(zc, 1), "n_puntos": len(zp),
            }
        json.dump(cache, open(cache_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return cache


# ── Programa principal ────────────────────────────────────────────────────────
def main():
    global RADIUS_KM, D0_KM, Z0_M
    ap = argparse.ArgumentParser()
    ap.add_argument("--stations", default=str(HERE / "estaciones_canarias.json"))
    ap.add_argument("--isla", default=None)
    ap.add_argument("--radius", type=float, default=RADIUS_KM)
    ap.add_argument("--d0", type=float, default=D0_KM)
    ap.add_argument("--z0", type=float, default=Z0_M)
    ap.add_argument("--refresh", action="store_true", help="vuelve a consultar el DEM")
    a = ap.parse_args()
    RADIUS_KM, D0_KM, Z0_M = a.radius, a.d0, a.z0

    stations = load_stations(a.stations)
    est_by_id = {s["id"]: s for s in stations}
    print(f"Estaciones cargadas: {len(stations)}")

    cob_path = HERE / "cobertura_estaciones.json"
    cobertura = json.load(open(cob_path, encoding="utf-8")) if cob_path.exists() else None
    print("Filtro de cobertura:", "ACTIVO" if cobertura is not None else
          "no aplicado (aún no existe cobertura_estaciones.json)")

    rows = asyncio.run(fetch_municipios(a.isla))
    print(f"Municipios: {len(rows)}")
    alts = municipal_altitudes(rows, HERE / "altitudes_municipios.json", a.refresh)

    out_rows, resumen = [], {"sin_candidata": 0, "flag": 0, "distintas": []}
    for r in rows:
        alt = alts[str(r["id"])]
        cands = rank_candidates(r["clat"], r["clon"], alt["alt_media"], stations, cobertura)
        rec = {"id": r["id"], "municipio": r["nombre"], "isla": r["isla"],
               "alt_media_m": alt["alt_media"], "alt_min_m": alt["alt_min"], "alt_max_m": alt["alt_max"]}
        for k in range(3):
            c = cands[k] if k < len(cands) else None
            rec[f"c{k+1}_id"] = c["id"] if c else ""
            rec[f"c{k+1}_nombre"] = c["nombre"] if c else ""
            rec[f"c{k+1}_d_km"] = round(c["d_km"], 1) if c else ""
            rec[f"c{k+1}_dz_m"] = round(c["dz_m"]) if c else ""
            rec[f"c{k+1}_score"] = round(c["score"], 2) if c else ""
        if not cands:
            resumen["sin_candidata"] += 1
        flag = bool(cands) and (abs(cands[0]["dz_m"]) > FLAG_DZ_M or cands[0]["d_km"] > FLAG_D_KM)
        rec["baja_representatividad"] = "SI" if flag else ""
        resumen["flag"] += flag

        act = ASIGNACION_ACTUAL.get(r["nombre"]) if r["isla"] == "Gran Canaria" else None
        rec["asignada_actual"] = act or ""
        if act and act in est_by_id:
            s = est_by_id[act]
            d = haversine(r["clat"], r["clon"], s["lat"], s["lon"])
            dz = s["alt"] - alt["alt_media"]
            rec.update({"actual_d_km": round(d, 1), "actual_dz_m": round(dz), "actual_score": round(score(d, dz), 2)})
            rec["coincide_con_c1"] = "SI" if cands and cands[0]["id"] == act else "NO"
            if cands and cands[0]["id"] != act:
                resumen["distintas"].append((r["nombre"], act, round(score(d, dz), 2),
                                             cands[0]["id"], round(cands[0]["score"], 2),
                                             round(cands[0]["dz_m"])))
        out_rows.append(rec)

    fields = list(out_rows[0].keys())
    for extra in ("actual_d_km", "actual_dz_m", "actual_score", "coincide_con_c1"):
        if extra not in fields:
            fields.append(extra)
    with open(HERE / "asignacion_candidatas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out_rows)

    print("\n" + "=" * 64)
    print(f"Municipios sin ninguna candidata a <= {RADIUS_KM:.0f} km: {resumen['sin_candidata']}")
    print(f"Municipios con baja representatividad (|dz|>{FLAG_DZ_M:.0f} m o d>{FLAG_D_KM:.0f} km): {resumen['flag']}")
    print(f"Municipios de Gran Canaria donde la asignación actual NO es la mejor candidata: {len(resumen['distintas'])}")
    for n, act, sa, c1, sc, dz in resumen["distintas"]:
        print(f"  {n:<28} actual {act} (score {sa})  ->  mejor {c1} (score {sc}, dz {dz:+d} m)")
    print("=" * 64)
    print("Guardado: scripts/asignacion_candidatas.csv")


if __name__ == "__main__":
    main()
