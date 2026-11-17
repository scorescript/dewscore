"""Carga municipios (y poligonos) en Supabase. Idempotente: clave = codigo INE (o nombre+provincia en filas antiguas sin INE).
Requiere haber ejecutado scripts/migracion_espana.sql.  Por defecto SIMULA; --aplicar escribe.
Uso: python scripts\\ampliar_espana_2_cargar.py [--aplicar] [--regeom] [--geojson ruta ...]
  --regeom : reescribe tambien la geometria de municipios ya existentes (por defecto solo los nuevos)"""
import os, sys, json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parent / "backend" / ".env")
args = sys.argv[1:]
paths = [HERE.parent / "frontend" / "sur.geojson", HERE.parent / "frontend" / "espana.geojson"]
if "--geojson" in args:
    paths = [Path(a) for a in args[args.index("--geojson") + 1:] if not a.startswith("--")]
feats = []
for p in paths:
    if p.exists():
        feats += json.loads(p.read_text(encoding="utf-8"))["features"]
    else:
        print("AVISO: no existe", p)
print(len(feats), "municipios en los GeoJSON")
if "--aplicar" not in args:
    print("Dry-run. Añade --aplicar para escribir."); sys.exit(0)
from supabase import create_client
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
def todos():
    out, i = [], 0
    while True:
        r = sb.table("municipios").select("id,nombre,provincia,ine").order("id").range(i, i + 999).execute().data
        out += r
        if len(r) < 1000: return out
        i += 1000
ex = todos()
por_ine = {m["ine"]: m["id"] for m in ex if m.get("ine")}
por_nom = {(m["nombre"], m["provincia"]): m["id"] for m in ex if not m.get("ine")}
nuevos, regeom, backfill = [], [], []
for f in feats:
    p = f["properties"]
    mid = por_ine.get(p["ine"])
    if mid is None:
        mid = por_nom.pop((p["nombre"], p["provincia"]), None)
        if mid is not None: backfill.append((mid, p["ine"]))
    if mid is None: nuevos.append(f)
    elif "--regeom" in args: regeom.append((mid, f))
print(f"nuevos: {len(nuevos)} | a completar con INE: {len(backfill)} | geometria a reescribir: {len(regeom)}")
def multi(g):
    return {"type": "MultiPolygon", "coordinates": [g["coordinates"]]} if g["type"] == "Polygon" else g
ids = {}
for i in range(0, len(nuevos), 200):
    lote = nuevos[i:i + 200]
    rows = [{"nombre": f["properties"]["nombre"], "comunidad": f["properties"]["comunidad"], "provincia": f["properties"]["provincia"],
             "isla": f["properties"]["provincia"], "lat": f["properties"]["lat"], "lng": f["properties"]["lng"], "ine": f["properties"]["ine"]} for f in lote]
    res = sb.table("municipios").insert(rows).execute().data
    por = {r["ine"]: r["id"] for r in res}
    for f in lote: ids[por[f["properties"]["ine"]]] = f
    print(f"  insertados {min(i + 200, len(nuevos))}/{len(nuevos)}")
import threading, time
_tl = threading.local()
def cli():
    if not hasattr(_tl, "c"):
        _tl.c = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    return _tl.c
def retry(fn, n=6):
    for k in range(n):
        try:
            return fn()
        except Exception as e:
            _tl.c = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"]); err = e; time.sleep(1 + 2 * k)
    print("  fallo definitivo:", repr(err)[:100])
def set_ine(t): retry(lambda: cli().table("municipios").update({"ine": t[1]}).eq("id", t[0]).execute())
def set_geom(t):
    retry(lambda: cli().rpc("actualizar_geom", {"municipio_id": t[0], "geom_geojson": json.dumps(multi(t[1]["geometry"]))}).execute())

# 1) completar INE (solo filas antiguas)
with ThreadPoolExecutor(4) as ex_:
    list(ex_.map(set_ine, backfill))
# 2) geometrias que faltan: todas las filas con geom nula (se detecta en la base, asi se puede relanzar sin riesgo)
sin, i = [], 0
while True:
    r = sb.table("municipios").select("id,ine").is_("geom", "null").order("id").range(i, i + 999).execute().data
    sin += r
    if len(r) < 1000: break
    i += 1000
por_feat = {f["properties"]["ine"]: f for f in feats}
work = [(m["id"], por_feat[m["ine"]]) for m in sin if m.get("ine") in por_feat]
work += [x for x in regeom if x[0] not in {w[0] for w in work}]
print(f"geometrias a escribir: {len(work)}")
with ThreadPoolExecutor(4) as ex_:
    for k, _ in enumerate(ex_.map(set_geom, work), 1):
        if k % 250 == 0: print(f"  geometria {k}/{len(work)}")
print("Listo.")
