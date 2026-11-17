"""
descargar_diario_todas.py  --  Bloque 2 de DewScore (version rapida, TODAS las estaciones)

AEMET permite pedir TODAS las estaciones en una sola llamada para ventanas de ~15 dias
(endpoint .../todasestaciones). Para 2008-2025 son ~470 llamadas en total, en lugar de
~36 por estacion (1764 solo para las 49 de Canarias), y de paso quedan descargadas todas
las estaciones de España (Andalucia, Murcia...) para la ampliacion.

  - Reanudable: guarda cada ventana en scripts/aemet_todas/AAAA-MM-DD.json; si se corta,
    relanza el mismo comando.
  - Al final reconstruye scripts/aemet_diario/<INDICATIVO>.json con el MISMO formato que
    descargar_diario_aemet.py (claves "AAAA-H1"/"AAAA-H2"), solo para las estaciones de
    estaciones_canarias.json (o todas con --todas). Un semestre solo se escribe si TODAS
    sus ventanas se descargaron; los semestres ya existentes no se tocan.

Uso (desde terra-main, con el venv activado):
  python scripts\\descargar_diario_todas.py
  python scripts\\descargar_diario_todas.py --solo-reconstruir      # sin llamadas a AEMET
  python scripts\\descargar_diario_todas.py --todas                 # fichero por cada estacion de España
"""
import os, sys, json, time, argparse
from datetime import date, timedelta
from pathlib import Path
import requests
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parent / "backend" / ".env")
KEY = os.getenv("AEMET_API_KEY")

Y0, Y1 = 2008, 2025
VENTANA = 14                                   # dias por llamada (limite AEMET ~15)
WIN = HERE / "aemet_todas"
OUT = HERE / "aemet_diario"
BASE = "https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos"
CAMPOS = ["fecha", "tmed", "tmin", "tmax", "hrMedia", "hrMax", "hrMin", "prec"]


def ventanas():
    d, fin = date(Y0, 1, 1), date(Y1, 12, 31)
    while d <= fin:
        h = min(d + timedelta(days=VENTANA - 1), fin)
        yield d, h
        d = h + timedelta(days=1)


def pedir(ini, fin):
    """Lista de registros, [] si no hay datos, None si hay que reintentar mas tarde."""
    url = (f"{BASE}/fechaini/{ini}T00:00:00UTC/fechafin/{fin}T23:59:59UTC/todasestaciones")
    for _ in range(8):
        try:
            r = requests.get(url, headers={"api_key": KEY}, timeout=60)
            if r.status_code in (429, 401):
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
                return []
            if est == 429:
                time.sleep(70)
                continue
            if est != 200:
                print(f"    AEMET estado {est}: {j.get('descripcion')}")
                time.sleep(20)
                continue
            time.sleep(1.5)
            d = requests.get(j["datos"], timeout=120)
            if d.status_code != 200:
                time.sleep(15)
                continue
            return d.json()
        except (requests.RequestException, ValueError) as e:
            print(f"    error de red ({type(e).__name__}): espero 20 s")
            time.sleep(20)
    return None


def descargar():
    WIN.mkdir(exist_ok=True)
    todas = list(ventanas())
    t0 = time.time()
    nuevas = fallidas = 0
    for i, (a, b) in enumerate(todas, 1):
        f = WIN / f"{a.isoformat()}.json"
        if f.exists():
            continue
        recs = pedir(a.isoformat(), b.isoformat())
        if recs is None:
            fallidas += 1
            print(f"  {a}..{b}: no se pudo descargar (se reintentara al relanzar)")
            continue
        out = [{"indicativo": r.get("indicativo"), **{k: r.get(k) for k in CAMPOS}} for r in recs]
        json.dump(out, open(f, "w", encoding="utf-8"))
        nuevas += 1
        if nuevas % 10 == 0:
            print(f"[{i}/{len(todas)}] {nuevas} ventanas nuevas | {(time.time()-t0)/60:.0f} min")
        time.sleep(2.5)
    print(f"\nVentanas nuevas: {nuevas} | pendientes por fallo: {fallidas}")


def reconstruir(codes):
    """Agrupa por estacion y semestre; solo escribe semestres completos."""
    OUT.mkdir(exist_ok=True)
    ok = {a for a, _ in ventanas() if (WIN / f"{a.isoformat()}.json").exists()}
    sem = {}                                      # (year,half) -> ventanas necesarias
    for a, b in ventanas():
        for d in (a, b):
            sem.setdefault((d.year, 1 if d.month <= 6 else 2), set()).add(a)
    completos = {k for k, v in sem.items() if v <= ok}
    stores, tags = {}, {}
    for a, _ in ventanas():
        f = WIN / f"{a.isoformat()}.json"
        if not f.exists():
            continue
        for r in json.load(open(f, encoding="utf-8")):
            c = r.get("indicativo")
            if codes is not None and c not in codes:
                continue
            y, m = int(r["fecha"][:4]), int(r["fecha"][5:7])
            h = 1 if m <= 6 else 2
            if (y, h) not in completos:
                continue
            tag = f"{y}-H{h}"
            stores.setdefault(c, {}).setdefault(tag, []).append({k: r.get(k) for k in CAMPOS})
    nuevos = 0
    for c, st in stores.items():
        f = OUT / f"{c}.json"
        cur = json.load(open(f, encoding="utf-8")) if f.exists() else {}
        for tag, recs in st.items():
            if tag not in cur:
                cur[tag] = sorted(recs, key=lambda r: r["fecha"])
                nuevos += 1
        json.dump(cur, open(f, "w", encoding="utf-8"))
    print(f"Estaciones escritas: {len(stores)} | semestres nuevos: {nuevos} | "
          f"semestres completos: {len(completos)} de {len(sem)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stations", default=str(HERE / "estaciones_canarias.json"))
    ap.add_argument("--todas", action="store_true")
    ap.add_argument("--solo-reconstruir", action="store_true")
    a = ap.parse_args()
    if not a.solo_reconstruir:
        if not KEY:
            sys.exit("Falta AEMET_API_KEY en backend/.env")
        descargar()
    codes = None if a.todas else {s["indicativo"] for s in json.load(open(a.stations, encoding="utf-8"))}
    reconstruir(codes)
    print("Siguiente: python scripts\\descargar_diario_aemet.py --solo-cobertura")


if __name__ == "__main__":
    main()
