import requests
import os
import time
import math
from dotenv import load_dotenv
from pathlib import Path
from supabase import create_client

env_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
load_dotenv(dotenv_path=env_path)

AEMET_KEY = os.getenv("AEMET_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
HEADERS = {"api_key": AEMET_KEY}

MUNICIPIO_ESTACION = {
    # TENERIFE
    "Santa Cruz de Tenerife": "C449C",
    "San Cristóbal de La Laguna": "C447A",
    "Arona": "C429I",
    "Adeje": "C429I",
    "La Orotava": "C447A",
    "Granadilla de Abona": "C429I",
    "Los Realejos": "C447A",
    "Puerto de la Cruz": "C447A",
    "Güímar": "C439J",
    "Candelaria": "C439J",
    "Tacoronte": "C447A",
    "El Rosario": "C449C",
    "Tegueste": "C447A",
    "Icod de los Vinos": "C447A",
    "Garachico": "C447A",
    "Buenavista del Norte": "C447A",
    "Los Silos": "C447A",
    "El Tanque": "C447A",
    "Santiago del Teide": "C429I",
    "Guía de Isora": "C429I",
    "Arico": "C429I",
    "Fasnia": "C439J",
    "Arafo": "C439J",
    "San Miguel de Abona": "C429I",
    "Vilaflor": "C429I",
    "La Matanza de Acentejo": "C447A",
    "La Victoria de Acentejo": "C447A",
    "El Sauzal": "C447A",
    "Santa Úrsula": "C447A",
    "San Juan de la Rambla": "C447A",
    "La Guancha": "C447A",
    # LANZAROTE
    "Arrecife": "C029O",
    "San Bartolomé": "C029O",
    "Teguise": "C839I",
    "Tías": "C018J",
    "Tinajo": "C048W",
    "Haría": "C038N",
    "Yaiza": "C019V",
    # FUERTEVENTURA
    "Puerto del Rosario": "C249I",
    "Pájara": "C229J",
    "La Oliva": "C258K",
    "Antigua": "C248E",
    "Tuineje": "C239N",
    "Betancuria": "C248E",
    # LA PALMA
    "Santa Cruz de la Palma": "C139E",
    "Los Llanos de Aridane": "C129Z",
    "El Paso": "C129Z",
    "Breña Alta": "C139E",
    "Breña Baja": "C139E",
    "Tazacorte": "C129Z",
    "Tijarafe": "C129Z",
    "Puntagorda": "C101A",
    "Garafía": "C101A",
    "Barlovento": "C101A",
    "San Andrés y Sauces": "C101A",
    "Puntallana": "C139E",
    "Villa de Mazo": "C139E",
    "Fuencaliente de la Palma": "C139E",
    # LA GOMERA
    "San Sebastián de La Gomera": "C419L",
    "Hermigua": "C419L",
    "Agulo": "C419L",
    "Vallehermoso": "C419L",
    "Valle Gran Rey": "C419L",
    "Alajeró": "C419L",
    # EL HIERRO
    "Valverde": "C929I",
    "Frontera": "C929I",
    "El Pinar de El Hierro": "C929I",
}

AÑOS = list(range(2008, 2026))


def punto_de_rocio(temp_c, hr):
    a, b = 17.27, 237.7
    alpha = ((a * temp_c) / (b + temp_c)) + math.log(hr / 100.0)
    return round((b * alpha) / (a - alpha), 2)


def calcular_awgp(temp_c, hr):
    e_sat = 6.112 * math.exp((17.67 * temp_c) / (temp_c + 243.5))
    return round((e_sat * hr * 2.1674) / (273.15 + temp_c), 3)


def parsear(valor):
    if not valor or str(valor).strip() == "":
        return None
    try:
        return float(str(valor).replace(",", "."))
    except:
        return None


def obtener_datos(codigo, fecha_ini, fecha_fin, reintentos=3):
    url = (
        f"https://opendata.aemet.es/opendata/api/valores/climatologicos/"
        f"diarios/datos/fechaini/{fecha_ini}/fechafin/{fecha_fin}/estacion/{codigo}"
    )
    for intento in range(reintentos):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 429:
                time.sleep(20 * (intento + 1))
                continue
            if r.status_code != 200:
                return None
            data = r.json()
            if data.get("estado") != 200:
                return None
            time.sleep(2)
            dr = requests.get(data["datos"], timeout=20)
            if dr.status_code != 200:
                return None
            result = dr.json()
            if isinstance(result, list):
                return result
        except Exception as e:
            print(f"      Error: {e}")
            time.sleep(10)
    return None


def obtener_año(codigo, año):
    t1 = obtener_datos(codigo, f"{año}-01-01T00:00:00UTC", f"{año}-06-30T23:59:59UTC")
    time.sleep(8)
    t2 = obtener_datos(codigo, f"{año}-07-01T00:00:00UTC", f"{año}-12-31T23:59:59UTC")
    datos = []
    if t1: datos.extend(t1)
    if t2: datos.extend(t2)
    return datos if datos else None


def ya_existe(municipio_id, año):
    res = supabase.table("atmosfera").select("id").eq("municipio_id", municipio_id).eq("año", año).eq("tipo", "historico").execute()
    return len(res.data) > 0


def procesar(nombre, codigo, año, municipio_id):
    if ya_existe(municipio_id, año):
        print(f"    ⏭ Ya existe {nombre} {año}")
        return

    datos = obtener_año(codigo, año)
    if not datos:
        print(f"    ✗ Sin datos: {nombre} {año}")
        return

    temps, hums = [], []
    cfi_d, df_d, niebla_d = 0, 0, 0
    awgp_vals = []
    validos = 0

    for dia in datos:
        if not isinstance(dia, dict): continue
        t_med = parsear(dia.get("tmed"))
        t_min = parsear(dia.get("tmin"))
        hr = parsear(dia.get("hrMedia"))
        hr_max = parsear(dia.get("hrMax"))
        if t_med: temps.append(t_med)
        if hr: hums.append(hr)
        if t_min is not None and hr is not None:
            td = punto_de_rocio(t_min, hr)
            if t_min <= td + 1: cfi_d += 1
            if t_min <= td: df_d += 1
            awgp_vals.append(calcular_awgp(t_med or t_min, hr))
            validos += 1
        if hr_max and hr_max > 95: niebla_d += 1

    if not temps or not hums:
        print(f"    ✗ Datos insuficientes: {nombre} {año}")
        return

    temp_med = round(sum(temps) / len(temps), 2)
    hum_med = round(sum(hums) / len(hums), 2)
    td = punto_de_rocio(temp_med, hum_med)

    supabase.table("atmosfera").insert({
        "municipio_id": municipio_id,
        "año": año,
        "tipo": "historico",
        "temp_media_c": temp_med,
        "humedad_relativa_pct": hum_med,
        "punto_rocio_c": td,
        "diferencia_temp_rocio": round(temp_med - td, 2),
        "cfi": round(cfi_d / validos, 3) if validos else None,
        "dew_frequency": round(df_d / validos, 3) if validos else None,
        "fce": round(niebla_d / len(datos), 3) if datos else None,
        "awgp": round(sum(awgp_vals) / len(awgp_vals), 3) if awgp_vals else None,
        "fuente": "AEMET OpenData"
    }).execute()

    print(f"    ✓ {nombre} {año} — T:{temp_med}°C CFI:{round(cfi_d/validos,3) if validos else 0}")


def main():
    # Cargar IDs de municipios una sola vez
    print("Cargando municipios de Supabase...")
    res = supabase.table("municipios").select("id, nombre").execute()
    id_map = {m["nombre"]: m["id"] for m in res.data}

    total = len(MUNICIPIO_ESTACION) * len(AÑOS)
    procesado = 0

    for año in AÑOS:
        print(f"\n{'='*50}")
        print(f"AÑO {año}")
        print(f"{'='*50}")

        for nombre, codigo in MUNICIPIO_ESTACION.items():
            municipio_id = id_map.get(nombre)
            if not municipio_id:
                print(f"  ⚠ No encontrado en Supabase: {nombre}")
                continue

            print(f"  → {nombre} ({codigo})")
            procesar(nombre, codigo, año, municipio_id)
            procesado += 1

            # Pausa entre municipios — no entre años
            if procesado < total:
                time.sleep(10)

    print(f"\n{'='*50}")
    print("PROCESO COMPLETO")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()