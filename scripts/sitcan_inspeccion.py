"""
Inspecciona, SIN descargar los 1,7 GB, el ZIP de observaciones de SITCAN (Gobierno de Canarias) leyendo solo el indice del ZIP y las primeras filas del primer CSV mediante peticiones HTTP por rango.
Uso: python scripts\\sitcan_inspeccion.py
"""
import struct, sys, zlib, urllib.request
URL = "https://opendata.sitcan.es/upload/meteorologia/observaciones.zip"


def rango(a, b):
    req = urllib.request.Request(URL, headers={"Range": f"bytes={a}-{b}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read(), r.headers.get("Content-Range")


def inspecciona(getter, size):
    tail, _ = getter(max(0, size - 70000), size - 1)
    i = tail.rfind(b"PK\x05\x06")
    if i < 0: raise RuntimeError("no se encuentra el final del ZIP")
    _, _, _, _, n, cd_size, cd_off, _ = struct.unpack("<4sHHHHLLH", tail[i:i + 22])
    cd, _ = getter(cd_off, cd_off + cd_size - 1)
    ents, p = [], 0
    for _ in range(n):
        (_, _, _, _, method, _, _, _, csize, usize, nl, el, cl, _, _, _, loff) = struct.unpack("<4s6H3L5H2L", cd[p:p + 46])
        ents.append((cd[p + 46:p + 46 + nl].decode("utf-8", "replace"), method, csize, usize, loff)); p += 46 + nl + el + cl
    return ents


def primeras_filas(getter, ent, nbytes=3_000_000):
    name, method, csize, usize, loff = ent
    head, _ = getter(loff, loff + 29)
    nl, el = struct.unpack("<HH", head[26:30]); start = loff + 30 + nl + el
    raw, _ = getter(start, start + min(csize, nbytes) - 1)
    data = raw if method == 0 else zlib.decompressobj(-15).decompress(raw)
    return data.decode("utf-8", "replace")


if __name__ == "__main__":
    _, cr = rango(0, 0); size = int(cr.split("/")[-1]); print("Tamaño del ZIP:", size, "bytes")
    ents = inspecciona(rango, size)
    for name, m, cs, us, lo in ents: print(f"  {name}: {us/1e6:.0f} MB sin comprimir ({cs/1e6:.0f} MB comprimidos)")
    txt = primeras_filas(rango, ents[0]); lines = txt.splitlines()[:-1]
    print("\nCabecera y primeras filas de", ents[0][0]); print("\n".join(lines[:6]))
    print("\nValores distintos por columna en las primeras filas (columnas con pocos valores):")
    cab = lines[0].split(",")
    for j, c in enumerate(cab):
        vals = {l.split(",")[j] for l in lines[1:] if len(l.split(",")) > j}
        if len(vals) <= 15: print(f"  {c}: {sorted(vals)[:15]}")
