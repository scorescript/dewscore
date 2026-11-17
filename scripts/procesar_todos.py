import subprocess
import sys
from pathlib import Path

AÑOS = list(range(2000, 2026))

script_path = Path(__file__).resolve().parent / "procesar_atmosfera.py"

print(f"Procesando {len(AÑOS)} años: {AÑOS[0]} → {AÑOS[-1]}")
print("Tiempo estimado: ~5 horas\n")

for año in AÑOS:
    print(f"\n{'='*50}")
    print(f"INICIANDO AÑO {año}")
    print(f"{'='*50}")

    result = subprocess.run(
        [sys.executable, str(script_path), str(año)],
        capture_output=False
    )

    if result.returncode != 0:
        print(f"  ⚠️ Error en año {año}, continuando...")

print(f"\n{'='*50}")
print("PROCESO COMPLETO")
print(f"{'='*50}")