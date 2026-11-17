"""
filtrar_estaciones_humedad.py  --  Bloque 6 (expansion a España), paso 2

Parte de scripts/estaciones_spain.json (lo genera descargar_inventario_aemet.py),
se queda con las estaciones de las provincias elegidas y prueba, con dos peticiones
cortas por estacion, si miden HUMEDAD (hrMedia y hrMax). Las que no, se descartan
antes de gastar horas en descargas completas.

Salida: scripts/estaciones_<nombre>.json  (mismo formato que estaciones_canarias.json
        mas el campo 'alt' para asignar_estaciones.py)  y  scripts/sondeo_humedad_<nombre>.json

Es reanudable: el sondeo se guarda tras cada estacion.

Uso (desde terra-main, venv activado):
  python scripts\\filtrar_estaciones_humedad.py --nombre sur
  python scripts\\filtrar_estaciones_humedad.py --nombre sur --provincias ALMERIA GRANADA
"""
import os, sys, json, time, argparse, unicodedata
from pathlib import Path
import requests
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parent / "backend" / ".env")
KEY = os.getenv("AEMET_API_KEY")

SUR = ["ALMERIA", "CADIZ", "CORDOBA", "GRANADA", "HUELVA", "JAEN", "MALAGA", "SEVILLA", "MURCIA"]
BASE = "https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos"
# dos ventanas de sondeo: invierno reciente y verano de hace años
VENTANAS = [("2024-01-01T00:00:00UTC", "2024-01-31T23:59:59UTC"),
            ("2015-07-01T00:00:00UTC", "2015-07-31T23:59:59UTC")]


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return s.upper().strip()


def pedir(cod, ini, fin):
    url = f"{BASE}/fechaini/{ini}/fechafin/{fin}/estacion/{cod}"
    for _ in range(8):
        try:
            r = requests.get(url, headers={"api_key": KEY}, timeout=40)
            if r.status_code in (401, 429):
                print(f"    AEMET pide calma (HTTP {r.status_code}): espero 60 s")
                time.sleep(60)
                continue
            if r.status_code != 200:
                time.sleep(20)
                continue
            j = r.json()
            if j.get("estado") == 404:
                return []
            if j.get("estado") in (401, 429):
                time.sleep(60)
                continue
            if j.get("estado") != 200:
                time.sleep(20)
                continue
            time.sleep(1.2)
            d = requests.get(j["datos"], timeout=40)
            if d.status_code != 200:
                time.sleep(15)
                continue
            return d.json()
        except (requests.RequestException, ValueError):
            time.sleep(20)
    return None


def tiene_hum(recs):
    return sum(1 for r in recs if r.get("hrMedia") not in (None, "") and r.get("hrMax") not in (None, ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nombre", default="sur")
    ap.add_argument("--provincias", nargs="*", default=SUR)
    a = ap.parse_args()
    if not KEY:
        sys.exit("Falta AEMET_API_KEY en backend/.env")

    prov = {norm(p) for p in a.provincias}
    inv = json.load(open(HERE / "estaciones_spain.json", encoding="utf-8"))
    cand = [e for e in inv if norm(e["provincia"]) in prov]
    print(f"Estaciones del inventario en {sorted(prov)}: {len(cand)}")

    sond_path = HERE / f"sondeo_humedad_{a.nombre}.json"
    sond = json.load(open(sond_path, encoding="utf-8")) if sond_path.exists() else {}

    t0 = time.time()
    for i, e in enumerate(cand, 1):
        cod = e["indicativo"]
        if cod in sond:
            continue
        n = 0
        ok_red = True
        for ini, fin in VENTANAS:
            recs = pedir(cod, ini, fin)
            if recs is None:
                ok_red = False
                break
            n += tiene_hum(recs)
            time.sleep(1.2)
        if not ok_red:
            print(f"[{i}/{len(cand)}] {cod}: fallo de red, se reintentara")
            continue
        sond[cod] = n
        json.dump(sond, open(sond_path, "w", encoding="utf-8"))
        print(f"[{i}/{len(cand)}] {cod} {e['nombre'][:30]:30s} dias con humedad: {n:3d}  ({(time.time()-t0)/60:.0f} min)")

    con = [e for e in cand if sond.get(e["indicativo"], 0) >= 10]
    out = [{"indicativo": e["indicativo"], "nombre": e["nombre"], "provincia": e["provincia"],
            "lat": e["lat"], "lon": e["lon"], "alt": e["altitud"], "altitud": e["altitud"]} for e in con]
    json.dump(out, open(HERE / f"estaciones_{a.nombre}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    from collections import Counter
    print(f"\nCon humedad: {len(con)} de {len(cand)} estaciones")
    for p, n in Counter(norm(e['provincia']) for e in con).most_common():
        print(f"  {p}: {n}")
    print(f"Guardado: scripts/estaciones_{a.nombre}.json")


if __name__ == "__main__":
    main()
