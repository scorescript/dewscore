import urllib.request, pandas as pd
from pathlib import Path
f = Path(__file__).parent / "sitcan_estaciones.csv"
f.write_bytes(urllib.request.urlopen("https://opendata.sitcan.es/upload/meteorologia/estaciones.csv", timeout=60).read())
d = pd.read_csv(f); print(len(d), "estaciones"); print(list(d.columns)); print(d.head(5).to_string())
