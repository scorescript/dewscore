"""Prueba: descarga 1 tesela Copernicus DEM GLO-90 (AWS, abierta) y lee la altitud de Granada (~680 m)."""
import math, sys, urllib.request
from pathlib import Path
D = Path(__file__).resolve().parent / "dem_cop90"; D.mkdir(exist_ok=True)
def tile_name(lat, lon):
    la, lo = math.floor(lat), math.floor(lon)
    ns = f"{'N' if la>=0 else 'S'}{abs(la):02d}_00"; ew = f"{'E' if lo>=0 else 'W'}{abs(lo):03d}_00"
    return f"Copernicus_DSM_COG_30_{ns}_{ew}_DEM"
n = tile_name(37.18, -3.6); f = D / f"{n}.tif"
if not f.exists():
    url = f"https://copernicus-dem-90m.s3.amazonaws.com/{n}/{n}.tif"
    print("Descargando", url); urllib.request.urlretrieve(url, f)
print("Tamaño: %.1f MB" % (f.stat().st_size/1e6))
try:
    import rasterio
    with rasterio.open(f) as src:
        v = next(src.sample([(-3.6, 37.18)]))[0]
    print("rasterio OK -> altitud Granada:", v)
except Exception as e:
    print("rasterio no disponible:", repr(e)[:120])
    try:
        import tifffile, numpy as np
        a = tifffile.imread(f); print("tifffile OK, forma", a.shape)
        h, w = a.shape; r = int((38 - 37.18) / 1.0 * (h - 1)); c = int((-3.6 + 4) / 1.0 * (w - 1))
        print("altitud Granada aprox:", a[r, c])
    except Exception as e2:
        print("tifffile tampoco:", repr(e2)[:160]); sys.exit(1)
