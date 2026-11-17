"""
mapas_paper.py -- figura del paper: mapas municipales de DF, CFI, HHF y AWVC (media de los años aceptados).
Une los poligonos de frontend/*.geojson con scripts/resumen_municipios_multianual.csv por nombre.
Municipios sin estacion: gris; baja representatividad: trama diagonal.
Salida: paper_cg/figures/mapa_indicadores.png  (y .pdf)
Uso: python scripts\\mapas_paper.py
"""
import json, unicodedata
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["hatch.color"] = "#777777"
plt.rcParams["hatch.linewidth"] = 0.4
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ISLAS = ["el_hierro", "la_palma", "la_gomera", "tenerife", "gran_canaria", "fuerteventura", "lanzarote"]


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return "".join(ch for ch in s if ch.isalnum())


def polys(geom):
    if geom["type"] == "Polygon":
        return [geom["coordinates"]]
    return geom["coordinates"]


def main():
    res = pd.read_csv(HERE / "resumen_municipios_multianual.csv")
    res["k"] = res["municipio"].map(norm)
    tab = res.set_index("k")
    feats = []
    for isla in ISLAS:
        d = json.load(open(ROOT / "frontend" / f"{isla}.geojson", encoding="utf-8"))
        for f in d["features"]:
            k = norm(f["properties"]["nameunit"])
            if k not in tab.index:                      # nombres largos: "Valsequillo de Gran Canaria"
                m = [i for i in tab.index if k.startswith(i) and len(i) >= 6]
                k = m[0] if len(m) == 1 else k
            feats.append((k, f["properties"]["nameunit"], f["geometry"]))
    sin = [n for k, n, g in feats if k not in tab.index]
    print("poligonos:", len(feats), "| sin dato:", len(sin), sin)
    cfg = [("DF", "DF (fraction of days)", "viridis"), ("CFI", "CFI (fraction of days)", "viridis"),
           ("HHF", "HHF (fraction of days)", "viridis"), ("AWVC", "AWVC (g m$^{-3}$)", "magma")]
    fig, axs = plt.subplots(2, 2, figsize=(11, 5.0))
    for ax, (col, lab, cm) in zip(axs.ravel(), cfg):
        vals = tab[col]
        norm_ = matplotlib.colors.Normalize(vals.quantile(0.02), vals.quantile(0.98), clip=True)
        cmap = plt.get_cmap(cm)
        for k, n, g in feats:
            if k in tab.index:
                fc = cmap(norm_(tab.loc[k, col])); hatch = "////" if bool(tab.loc[k, "flag"]) else None
            else:
                fc, hatch = "#d0d0d0", None
            pc = PatchCollection([Polygon(r[0], closed=True) for p in polys(g) for r in [p]],
                                 facecolor=fc, edgecolor="#555555", linewidth=0.25, hatch=hatch)
            ax.add_collection(pc)
        ax.set_xlim(-18.4, -13.3); ax.set_ylim(27.55, 29.5); ax.set_aspect(1.13, adjustable="box")
        ax.set_xticks([]); ax.set_yticks([]); ax.set_title(lab, fontsize=10)
        sm = plt.cm.ScalarMappable(norm=norm_, cmap=cmap)
        fig.colorbar(sm, ax=ax, fraction=0.035, pad=0.01, extend="both")
    fig.text(0.5, 0.005, "Grey: no eligible station within 30 km. Hatched: low representativeness "
             "(|dz| > 300 m or d > 15 km). Colour scale clipped at the 2nd and 98th percentiles.", ha="center", fontsize=8)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    out = ROOT.parent / "paper_cg" / "figures"
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / "mapa_indicadores.png", dpi=250)
    print("guardado", out / "mapa_indicadores.png")


if __name__ == "__main__":
    main()
