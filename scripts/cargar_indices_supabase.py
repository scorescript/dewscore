"""Carga indices_municipio_anual.csv en Supabase (tabla atmosfera).
Por defecto SIMULA (dry-run). Con --aplicar escribe. Requiere haber ejecutado migracion_hhf_awvc.sql.
Uso:  python scripts\\cargar_indices_supabase.py [--aplicar]"""
import os, sys, math
import pandas as pd
try:
    from dotenv import load_dotenv; load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env")); load_dotenv()
except ImportError:
    pass
CSV = os.path.join(os.path.dirname(__file__), "indices_municipio_anual.csv")
df = pd.read_csv(CSV)
def n(v):
    return None if (v is None or (isinstance(v, float) and math.isnan(v))) else v
rows = []
for r in df.itertuples(index=False):
    rows.append({
        "municipio_id": int(r.municipio_id), "año": int(r.año), "tipo": "historico",
        "temp_media_c": n(r.T_media_C), "humedad_relativa_pct": n(r.HR_media_pct),
        "punto_rocio_c": n(r.Td_media_C),
        "diferencia_temp_rocio": None if pd.isna(r.T_media_C) or pd.isna(r.Td_media_C) else round(r.T_media_C - r.Td_media_C, 2),
        "cfi": n(r.CFI), "dew_frequency": n(r.DF), "hhf": n(r.HHF), "awvc": n(r.AWVC_g_m3),
        "estacion_id": n(r.estacion), "d_km": n(r.d_km), "dz_m": n(r.dz_m),
        "baja_representatividad": bool(r.baja_representatividad) if not pd.isna(r.baja_representatividad) else False,
        "n_dias_validos": None if pd.isna(r.n_dias_validos) else int(r.n_dias_validos),
    })
print(f"{len(rows)} filas, {df.municipio_id.nunique()} municipios, años {df['año'].min()}-{df['año'].max()}")
if "--aplicar" not in sys.argv:
    print("Dry-run: no se escribe nada. Añade --aplicar para cargar."); sys.exit(0)
from supabase import create_client
sb = create_client(os.environ["SUPABASE_URL"], os.environ.get("SUPABASE_SERVICE_KEY") or os.environ["SUPABASE_KEY"])
import time
for i in range(0, len(rows), 200):
    for k in range(6):
        try:
            sb.table("atmosfera").upsert(rows[i:i+200], on_conflict="municipio_id,año").execute(); break
        except Exception as e:
            print("  reintento", k + 1, repr(e)[:80]); time.sleep(2 + 3 * k)
            sb = create_client(os.environ["SUPABASE_URL"], os.environ.get("SUPABASE_SERVICE_KEY") or os.environ["SUPABASE_KEY"])
    else:
        raise SystemExit(f"Fallo definitivo en el lote {i}. Relanza: es idempotente.")
    if (i // 200) % 20 == 0: print("cargadas", min(i+200, len(rows)), "de", len(rows))
