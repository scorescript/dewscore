import os
from dotenv import load_dotenv
from pathlib import Path
from supabase import create_client

env_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

MUNICIPIOS = [
    # TENERIFE
    {"nombre": "Santa Cruz de Tenerife", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 211000, "lat": 28.4636, "lng": -16.2518},
    {"nombre": "San Cristóbal de La Laguna", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 160000, "lat": 28.4853, "lng": -16.3167},
    {"nombre": "Arona", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 101000, "lat": 28.0997, "lng": -16.6810},
    {"nombre": "Adeje", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 56000, "lat": 28.1227, "lng": -16.7260},
    {"nombre": "La Orotava", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 43000, "lat": 28.3908, "lng": -16.5228},
    {"nombre": "Granadilla de Abona", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 49000, "lat": 28.1175, "lng": -16.5692},
    {"nombre": "Los Realejos", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 38000, "lat": 28.3847, "lng": -16.5900},
    {"nombre": "Puerto de la Cruz", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 31000, "lat": 28.4136, "lng": -16.5481},
    {"nombre": "Güímar", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 19000, "lat": 28.3111, "lng": -16.4122},
    {"nombre": "Candelaria", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 28000, "lat": 28.3564, "lng": -16.3728},
    {"nombre": "Tacoronte", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 24000, "lat": 28.4747, "lng": -16.4131},
    {"nombre": "El Rosario", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 18000, "lat": 28.4386, "lng": -16.3075},
    {"nombre": "Tegueste", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 11000, "lat": 28.5136, "lng": -16.3322},
    {"nombre": "Icod de los Vinos", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 23000, "lat": 28.3694, "lng": -16.7158},
    {"nombre": "Garachico", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 5000, "lat": 28.3728, "lng": -16.7636},
    {"nombre": "Buenavista del Norte", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 5000, "lat": 28.3783, "lng": -16.8644},
    {"nombre": "Los Silos", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 5000, "lat": 28.3783, "lng": -16.8203},
    {"nombre": "El Tanque", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 3000, "lat": 28.3522, "lng": -16.7772},
    {"nombre": "Santiago del Teide", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 11000, "lat": 28.2978, "lng": -16.8158},
    {"nombre": "Guía de Isora", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 21000, "lat": 28.2100, "lng": -16.7731},
    {"nombre": "Arico", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 8000, "lat": 28.1667, "lng": -16.4833},
    {"nombre": "Fasnia", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 3000, "lat": 28.2333, "lng": -16.4167},
    {"nombre": "Arafo", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 5000, "lat": 28.2833, "lng": -16.4167},
    {"nombre": "San Miguel de Abona", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 19000, "lat": 28.1500, "lng": -16.6167},
    {"nombre": "Vilaflor", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 2000, "lat": 28.1667, "lng": -16.6333},
    {"nombre": "La Matanza de Acentejo", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 10000, "lat": 28.4667, "lng": -16.4333},
    {"nombre": "La Victoria de Acentejo", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 9000, "lat": 28.4500, "lng": -16.4500},
    {"nombre": "El Sauzal", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 9000, "lat": 28.4667, "lng": -16.4167},
    {"nombre": "Santa Úrsula", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 15000, "lat": 28.4333, "lng": -16.4833},
    {"nombre": "San Juan de la Rambla", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 5000, "lat": 28.3833, "lng": -16.6333},
    {"nombre": "La Guancha", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "Tenerife", "poblacion_2025": 5000, "lat": 28.3500, "lng": -16.6833},

    # LANZAROTE
    {"nombre": "Arrecife", "comunidad": "Canarias", "provincia": "Las Palmas", "isla": "Lanzarote", "poblacion_2025": 62000, "lat": 28.9636, "lng": -13.5478},
    {"nombre": "San Bartolomé", "comunidad": "Canarias", "provincia": "Las Palmas", "isla": "Lanzarote", "poblacion_2025": 20000, "lat": 28.9981, "lng": -13.6244},
    {"nombre": "Teguise", "comunidad": "Canarias", "provincia": "Las Palmas", "isla": "Lanzarote", "poblacion_2025": 22000, "lat": 29.0597, "lng": -13.5617},
    {"nombre": "Tías", "comunidad": "Canarias", "provincia": "Las Palmas", "isla": "Lanzarote", "poblacion_2025": 22000, "lat": 28.9586, "lng": -13.6419},
    {"nombre": "Tinajo", "comunidad": "Canarias", "provincia": "Las Palmas", "isla": "Lanzarote", "poblacion_2025": 6000, "lat": 29.0667, "lng": -13.7000},
    {"nombre": "Haría", "comunidad": "Canarias", "provincia": "Las Palmas", "isla": "Lanzarote", "poblacion_2025": 5000, "lat": 29.1333, "lng": -13.5000},
    {"nombre": "Yaiza", "comunidad": "Canarias", "provincia": "Las Palmas", "isla": "Lanzarote", "poblacion_2025": 17000, "lat": 28.9500, "lng": -13.7667},

    # FUERTEVENTURA
    {"nombre": "Puerto del Rosario", "comunidad": "Canarias", "provincia": "Las Palmas", "isla": "Fuerteventura", "poblacion_2025": 42000, "lat": 28.5000, "lng": -13.8628},
    {"nombre": "Pájara", "comunidad": "Canarias", "provincia": "Las Palmas", "isla": "Fuerteventura", "poblacion_2025": 20000, "lat": 28.3333, "lng": -14.1000},
    {"nombre": "La Oliva", "comunidad": "Canarias", "provincia": "Las Palmas", "isla": "Fuerteventura", "poblacion_2025": 25000, "lat": 28.6167, "lng": -13.9333},
    {"nombre": "Antigua", "comunidad": "Canarias", "provincia": "Las Palmas", "isla": "Fuerteventura", "poblacion_2025": 13000, "lat": 28.4333, "lng": -14.0167},
    {"nombre": "Tuineje", "comunidad": "Canarias", "provincia": "Las Palmas", "isla": "Fuerteventura", "poblacion_2025": 13000, "lat": 28.3167, "lng": -14.0500},
    {"nombre": "Betancuria", "comunidad": "Canarias", "provincia": "Las Palmas", "isla": "Fuerteventura", "poblacion_2025": 800, "lat": 28.4219, "lng": -14.0572},

    # LA PALMA
    {"nombre": "Santa Cruz de la Palma", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "La Palma", "poblacion_2025": 17000, "lat": 28.6833, "lng": -17.7667},
    {"nombre": "Los Llanos de Aridane", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "La Palma", "poblacion_2025": 21000, "lat": 28.6567, "lng": -17.9136},
    {"nombre": "El Paso", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "La Palma", "poblacion_2025": 8000, "lat": 28.6500, "lng": -17.8667},
    {"nombre": "Breña Alta", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "La Palma", "poblacion_2025": 7000, "lat": 28.6500, "lng": -17.7833},
    {"nombre": "Breña Baja", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "La Palma", "poblacion_2025": 5000, "lat": 28.6333, "lng": -17.7667},
    {"nombre": "Tazacorte", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "La Palma", "poblacion_2025": 5000, "lat": 28.6333, "lng": -17.9333},
    {"nombre": "Tijarafe", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "La Palma", "poblacion_2025": 3000, "lat": 28.7167, "lng": -17.9500},
    {"nombre": "Puntagorda", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "La Palma", "poblacion_2025": 2000, "lat": 28.7667, "lng": -17.9833},
    {"nombre": "Garafía", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "La Palma", "poblacion_2025": 2000, "lat": 28.8333, "lng": -17.9500},
    {"nombre": "Barlovento", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "La Palma", "poblacion_2025": 2000, "lat": 28.8167, "lng": -17.8167},
    {"nombre": "San Andrés y Sauces", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "La Palma", "poblacion_2025": 5000, "lat": 28.8000, "lng": -17.7833},
    {"nombre": "Puntallana", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "La Palma", "poblacion_2025": 3000, "lat": 28.7500, "lng": -17.7667},
    {"nombre": "Villa de Mazo", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "La Palma", "poblacion_2025": 5000, "lat": 28.6000, "lng": -17.7833},
    {"nombre": "Fuencaliente de la Palma", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "La Palma", "poblacion_2025": 2000, "lat": 28.5167, "lng": -17.8333},

    # LA GOMERA
    {"nombre": "San Sebastián de La Gomera", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "La Gomera", "poblacion_2025": 9000, "lat": 28.0919, "lng": -17.1133},
    {"nombre": "Hermigua", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "La Gomera", "poblacion_2025": 2000, "lat": 28.1667, "lng": -17.1833},
    {"nombre": "Agulo", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "La Gomera", "poblacion_2025": 1000, "lat": 28.1833, "lng": -17.2167},
    {"nombre": "Vallehermoso", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "La Gomera", "poblacion_2025": 3000, "lat": 28.2000, "lng": -17.2667},
    {"nombre": "Valle Gran Rey", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "La Gomera", "poblacion_2025": 4000, "lat": 28.0833, "lng": -17.3333},
    {"nombre": "Alajeró", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "La Gomera", "poblacion_2025": 2000, "lat": 28.0500, "lng": -17.2333},

    # EL HIERRO
    {"nombre": "Valverde", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "El Hierro", "poblacion_2025": 5000, "lat": 27.8089, "lng": -17.9144},
    {"nombre": "Frontera", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "El Hierro", "poblacion_2025": 4000, "lat": 27.7500, "lng": -18.0167},
    {"nombre": "El Pinar de El Hierro", "comunidad": "Canarias", "provincia": "Santa Cruz de Tenerife", "isla": "El Hierro", "poblacion_2025": 2000, "lat": 27.7167, "lng": -17.9167},
]


def insertar_municipios():
    # Obtener nombres existentes para no duplicar
    existentes = supabase.table("municipios").select("nombre").execute()
    nombres_existentes = {m["nombre"] for m in existentes.data}

    nuevos = [m for m in MUNICIPIOS if m["nombre"] not in nombres_existentes]
    print(f"Municipios existentes: {len(nombres_existentes)}")
    print(f"Municipios nuevos a insertar: {len(nuevos)}\n")

    for m in nuevos:
        supabase.table("municipios").insert({
            "nombre": m["nombre"],
            "comunidad": m["comunidad"],
            "provincia": m["provincia"],
            "poblacion_2025": m["poblacion_2025"],
            "lat": m["lat"],
            "lng": m["lng"]
        }).execute()
        print(f"  ✅ {m['nombre']} ({m.get('isla', '')})")

    print(f"\nTotal insertados: {len(nuevos)}")


if __name__ == "__main__":
    insertar_municipios()