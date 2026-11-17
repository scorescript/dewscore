"""
descargar_diario_aemet.py  --  Bloque 2 de DewScore

Descarga los datos climatologicos DIARIOS de AEMET (con fecha) de cada estacion,
por tramos de 6 meses, y los archiva en disco para no depender nunca mas de la API.

  - Reanudable: si se corta, vuelve a lanzar el mismo comando y sigue donde estaba.
  - Guarda por estacion: scripts/aemet_diario/<INDICATIVO>.json
  - Al final (o con --solo-cobertura) genera scripts/cobertura_estaciones.json
    con {indicativo: {año: dias_validos}}; dia valido = tmed, tmin, hrMedia y hrMax presentes.

Uso (desde la carpeta terra-main, con el venv activado):
  python scripts\\descargar_diario_aemet.py                       # las 49 estaciones de Canarias
  python scripts\\descargar_diario_aemet.py --solo-cobertura      # solo recalcula cobertura
  python scripts\\descargar_diario_aemet.py --estaciones C614H C658X   # solo algunas
"""
import os, sys, json, time, argparse
from pathlib import Path
import requests
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parent / "backend" / ".env")
KEY = os.getenv("AEMET_API_KEY")

Y0, Y1 = 2008, 2025
OUT = HERE / "aemet_diario"
BASE = "https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos"
CAMPOS = ["fecha", "tmed", "tmin", "tmax", "hrMedia", "hrMax", "hrMin", "prec"]


def num(v):
    if v is None:
        return None
    try:
        return float(str(v).replace(",", "."))
    except ValueError:
        return None


def tramos():
    for y in range(Y0, Y1 + 1):
        yield f"{y}-H1", f"{y}-01-01T00:00:00UTC", f"{y}-06-30T23:59:59UTC"
        yield f"{y}-H2", f"{y}-07-01T00:00:00UTC", f"{y}-12-31T23:59:59UTC"


def pedir(cod, ini, fin):
    """Devuelve lista de registros, [] si no hay datos, o None si hay que reintentar."""
    url = f"{BASE}/fechaini/{ini}/fechafin/{fin}/estacion/{cod}"
    for intento in range(8):
        try:
            r = requests.get(url, headers={"api_key": KEY}, timeout=40)
            if r.status_code in (429, 401):
                # AEMET devuelve 401 o 429 de forma intermitente cuando se le piden
                # demasiadas peticiones seguidas: se enfria y se reintenta.
                print(f"    AEMET pide calma (HTTP {r.status_code}): espero 60 s")
                time.sleep(60)
                continue
            if r.status_code != 200:
                print(f"    HTTP {r.status_code}: espero 20 s")
                time.sleep(20)
                continue
            j = r.json()
            est = j.get("estado")
            if est == 404:
                return []                      # sin datos en ese tramo
            if est == 429:
                time.sleep(70)
                continue
            if est != 200:
                print(f"    AEMET estado {est}: {j.get('descripcion')}")
                time.sleep(20)
                continue
            time.sleep(1.2)
            d = requests.get(j["datos"], timeout=40)
            if d.status_code != 200:
                time.sleep(15)
                continue
            return d.json()
        except (requests.RequestException, ValueError) as e:
            print(f"    error de red ({type(e).__name__}): espero 20 s")
            time.sleep(20)
    return None


def descargar_estacion(cod):
    f = OUT / f"{cod}.json"
    store = json.load(open(f, encoding="utf-8")) if f.exists() else {}
    hechos = 0
    for tag, ini, fin in tramos():
        if tag in store:
            continue
        recs = pedir(cod, ini, fin)
        if recs is None:
            print(f"  {cod} {tag}: no se pudo descargar (se reintentara al relanzar)")
            continue
        store[tag] = [{k: r.get(k) for k in CAMPOS} for r in recs]
        json.dump(store, open(f, "w", encoding="utf-8"))
        hechos += 1
        time.sleep(2.5)
    return store, hechos


def dia_valido(r):
    return all(num(r.get(k)) is not None for k in ("tmed", "tmin", "hrMedia", "hrMax"))


def cobertura_de(store):
    out = {}
    for tag, recs in store.items():
        y = tag[:4]
        out[y] = out.get(y, 0) + sum(1 for r in recs if dia_valido(r))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stations", default=str(HERE / "estaciones_canarias.json"))
    ap.add_argument("--estaciones", nargs="*")
    ap.add_argument("--solo-cobertura", action="store_true")
    a = ap.parse_args()

    if not KEY and not a.solo_cobertura:
        sys.exit("Falta AEMET_API_KEY en backend/.env")
    OUT.mkdir(exist_ok=True)
    lista = json.load(open(a.stations, encoding="utf-8"))
    codes = [s["indicativo"] for s in lista]
    if a.estaciones:
        codes = [c for c in codes if c in a.estaciones]

    t0 = time.time()
    for i, cod in enumerate(codes, 1):
        if not a.solo_cobertura:
            print(f"[{i}/{len(codes)}] {cod}")
            store, n = descargar_estacion(cod)
            el = (time.time() - t0) / 60
            print(f"   {n} tramos nuevos | transcurridos {el:.0f} min")

    cob = {}
    for cod in [s["indicativo"] for s in lista]:
        f = OUT / f"{cod}.json"
        if f.exists():
            cob[cod] = cobertura_de(json.load(open(f, encoding="utf-8")))
    json.dump(cob, open(HERE / "cobertura_estaciones.json", "w", encoding="utf-8"), indent=1)

    ok = [c for c, y in cob.items() if sum(1 for n in y.values() if n >= 292) >= 10]
    print(f"\nEstaciones con cobertura (>=10 años con >=292 dias): {len(ok)} de {len(cob)}")
    print("Guardado: scripts/cobertura_estaciones.json")


if __name__ == "__main__":
    main()
