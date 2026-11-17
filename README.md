# DewScore

Geospatial platform of screening indicators for atmospheric water harvesting in Spain, computed from AEMET daily climatological series (2008-2025). Live at <https://dewscore.eu>.

## Indicators

| Indicator | Definition | Informs |
|---|---|---|
| DF | Share of days with minimum temperature <= dew point | Passive dew condensers |
| CFI | Share of days with minimum temperature <= dew point + 1 C | Active condensation |
| HHF | Share of days with maximum relative humidity > 95 % | Fog collector siting (screening only) |
| AWVC | Absolute water vapour density, g/m3 | Sorption and active systems |
| Delta Temp-Td, mean T, mean RH | Thermal margin and climatic context | Context |

The indicators are screening tools. They are not water yield estimates and do not replace on-site measurement.

Dew point uses the Magnus formula (a = 17.67, b = 243.5 C) following the Spanish DB-HE reference climates document (Ministerio de Fomento, 2017).

## Repository layout

- `backend/` FastAPI service (REST API and vector tiles)
- `frontend-next/` Next.js application and the Leaflet map (`public/map-app.js`)
- `frontend/` legacy static page
- `scripts/` data pipeline: AEMET download, station assignment (Copernicus DEM GLO-90), index computation, loading into Supabase/PostGIS, sensitivity and trend analyses

## Running it

Requires Python 3.11+, Node 20+, a Supabase/PostGIS project and an AEMET OpenData API key.

1. Copy `backend/.env.example` to `backend/.env` and `frontend-next/.env.example` to `frontend-next/.env.local`, then fill in your own values. Never commit them.
2. Backend: `pip install -r backend/requirements.txt` then `uvicorn main:app --reload` from `backend/`.
3. Frontend: `npm install` then `npm run dev` from `frontend-next/`.
4. Pipeline: see `scripts/cadena_completa.bat` for the order of steps.

## Data sources

AEMET OpenData (daily series), IGN (municipal boundaries), Copernicus DEM GLO-90 (elevation).

## Citation

See `CITATION.cff`.

## Licence

MIT. See `LICENSE`.
