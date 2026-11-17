"""Altitudes desde el modelo digital de elevacion Copernicus DEM GLO-90 (90 m, ESA/Airbus, acceso abierto en AWS).
Descarga cada tesela de 1x1 grado la primera vez (cache en scripts/dem_cop90/); sin limites de consulta.
Teselas inexistentes (mar abierto) se consideran nivel del mar (0 m)."""
import math, urllib.request, urllib.error
from pathlib import Path
import rasterio
D = Path(__file__).resolve().parent / "dem_cop90"; D.mkdir(exist_ok=True)
BASE = "https://copernicus-dem-90m.s3.amazonaws.com"

def tile_name(lat, lon):
    la, lo = math.floor(lat), math.floor(lon)
    return f"Copernicus_DSM_COG_30_{'N' if la>=0 else 'S'}{abs(la):02d}_00_{'E' if lo>=0 else 'W'}{abs(lo):03d}_00_DEM"

def _get_tile(name):
    f, miss = D / f"{name}.tif", D / f"{name}.missing"
    if f.exists(): return f
    if miss.exists(): return None
    try:
        print(f"  descargando tesela {name} ...")
        urllib.request.urlretrieve(f"{BASE}/{name}/{name}.tif", f)
        return f
    except urllib.error.HTTPError as e:
        if e.code in (403, 404):
            miss.write_text("no existe (mar)"); 
            if f.exists(): f.unlink()
            return None
        raise

def elevations(lats, lons):
    out = [0.0] * len(lats)
    groups = {}
    for i, (la, lo) in enumerate(zip(lats, lons)):
        groups.setdefault(tile_name(la, lo), []).append(i)
    for name, idx in groups.items():
        f = _get_tile(name)
        if f is None: continue
        with rasterio.open(f) as src:
            vals = src.sample([(lons[i], lats[i]) for i in idx])
            for i, v in zip(idx, vals):
                v = float(v[0])
                out[i] = 0.0 if (src.nodata is not None and v == src.nodata) else v
    return out
