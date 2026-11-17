from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from supabase import create_client
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="DewScore API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db_pool = None

@app.on_event("startup")
async def startup():
    global db_pool
    db_pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=2,
        max_size=20,
        command_timeout=10,
        statement_cache_size=0
    )

@app.on_event("shutdown")
async def shutdown():
    if db_pool:
        await db_pool.close()

@app.get("/api")
def home():
    return {"status": "DewScore API funcionando"}

def fetch_all(build, page=1000):
    """PostgREST devuelve como maximo 1000 filas por peticion: se pagina con range()."""
    out, i = [], 0
    while True:
        rows = build().range(i, i + page - 1).execute().data
        out.extend(rows)
        if len(rows) < page:
            return out
        i += page

@app.get("/api/municipios")
def get_municipios():
    return fetch_all(lambda: supabase.table("municipios").select("id, nombre, comunidad, provincia, isla, lat, lng, radiacion_solar_kwh").order("id"))

@app.get("/api/atmosfera/{year}")
def get_atmosfera(year: int):
    return fetch_all(lambda: (
        supabase.table("atmosfera")
        .select("*, municipios(nombre, lat, lng, isla, comunidad, provincia, radiacion_solar_kwh)")
        .eq("año", year)
        .order("municipio_id")
        .order("tipo")
    ))

@app.get("/api/serie/{municipio_id}")
def get_serie(municipio_id: int):
    response = (
        supabase.table("atmosfera")
        .select("año, temp_media_c, humedad_relativa_pct, punto_rocio_c, diferencia_temp_rocio, cfi, dew_frequency, hhf, awvc")
        .eq("municipio_id", municipio_id)
        .eq("tipo", "historico")
        .order("año")
        .execute()
    )
    return response.data

@app.get("/api/solar/{municipio_id}")
def get_solar(municipio_id: int, año: int = None):
    """Serie solar mensual para un municipio. Si se pasa año, filtra por ese año."""
    query = (
        supabase.table("solar_mensual")
        .select("año, mes, radiacion_kwh_m2, radiacion_media_diaria, viento_max_kmh, viento_medio_kmh, calima_media, calima_max")
        .eq("municipio_id", municipio_id)
        .order("año")
        .order("mes")
    )
    if año:
        query = query.eq("año", año)
    return query.execute().data

@app.get("/api/solar_anual/{year}")
def get_solar_anual(year: int, mes: int = None):
    """Datos solares de todos los municipios para un año y mes dado."""
    query = (
        supabase.table("solar_mensual")
        .select("*, municipios(nombre, lat, lng, isla, radiacion_solar_kwh)")
        .eq("año", year)
    )
    if mes:
        query = query.eq("mes", mes)
    return query.execute().data

@app.get("/api/tiles/{z}/{x}/{y}")
async def get_tile(z: int, x: int, y: int):
    query = """
        SELECT ST_AsMVT(q, 'municipios', 4096, 'geom') as tile
        FROM (
            SELECT
                m.id,
                m.nombre,
                m.isla,
                m.comunidad,
                a.temp_media_c,
                a.humedad_relativa_pct,
                a.punto_rocio_c,
                a.diferencia_temp_rocio,
                a.cfi,
                a.dew_frequency,
                a.hhf,
                a.awvc,
                a.radiacion_solar_kwh,
                ST_AsMVTGeom(
                    ST_SimplifyPreserveTopology(m.geom_3857, $4::float),
                    ST_TileEnvelope($1, $2, $3),
                    4096, 64, true
                ) as geom
            FROM municipios m
            LEFT JOIN atmosfera a ON a.municipio_id = m.id AND a.año = 2025
            WHERE m.geom_3857 IS NOT NULL
            AND m.geom_3857 && ST_TileEnvelope($1, $2, $3)
        ) q
    """
    async with db_pool.acquire() as conn:
        tol = 0.0 if z >= 12 else 156543.03 / (2 ** z) * 0.5   # ~0.5 px del nivel de zoom
        tile = await conn.fetchval(query, z, x, y, tol)

    if tile:
        return Response(
            content=bytes(tile),
            media_type="application/x-protobuf",
            headers={"Cache-Control": "public, max-age=3600"}
        )
    return Response(content=b"", media_type="application/x-protobuf")

@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    path = os.path.join(os.path.dirname(__file__), "../frontend/index.html")
    with open(path, encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content, headers={
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    })

app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")