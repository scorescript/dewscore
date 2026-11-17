@echo off
REM Cadena completa DewScore España. Uso (con el venv activado, desde terra-main):  scripts\cadena_completa.bat
REM Se detiene en el primer error. Se puede relanzar entera: todos los pasos son idempotentes.
pip install -q matplotlib pandas numpy
echo === 1/9 Descarga de la ventana pendiente (2008) y reconstruccion de series ===
python scripts\descargar_diario_todas.py --stations scripts\estaciones_modelo.json
if errorlevel 1 exit /b 1
echo === 2/9 Cobertura de estaciones ===
python scripts\descargar_diario_aemet.py --solo-cobertura --stations scripts\estaciones_modelo.json
if errorlevel 1 exit /b 1
echo === 3/9 Indices por estacion ===
python scripts\calcular_indices.py
if errorlevel 1 exit /b 1
echo === 4/9 Asignacion estacion-municipio ===
python scripts\asignar_estaciones.py --stations scripts\estaciones_modelo.json
if errorlevel 1 exit /b 1
echo === 5/9 Indices por municipio ===
python scripts\indices_municipio.py
if errorlevel 1 exit /b 1
echo === 6/9 Carga en Supabase ===
python scripts\cargar_indices_supabase.py --aplicar
if errorlevel 1 exit /b 1
echo === 7/9 Sensibilidad ===
python scripts\sensibilidad.py
if errorlevel 1 exit /b 1
echo === 8/9 Tendencias ===
python scripts\tendencias.py
if errorlevel 1 exit /b 1
echo === 9/9 Tablas y figuras del paper ===
python scripts\analisis_espana.py
if errorlevel 1 exit /b 1
echo.
echo CADENA TERMINADA
