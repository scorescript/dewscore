"""
analisis_espana.py -- tablas, cifras y figuras del paper para España completa.

Entradas (scripts/): indices_municipio_anual.csv, asignacion_candidatas.csv,
                     sensibilidad_results.csv y tendencias_estacion.csv (opcionales)
                     + poligonos: frontend/espana.geojson, frontend/sur.geojson y frontend/<isla>.geojson
Salidas: paper_cg/figures/*.png|pdf, paper_cg/tables/*.tex, paper_cg/numbers_espana.txt
Uso: python scripts\\analisis_espana.py
"""
import json, unicodedata, math
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon, Rectangle

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PAPER = ROOT.parent / "paper_cg"
FIG, TAB = PAPER / "figures", PAPER / "tables"
FIG.mkdir(parents=True, exist_ok=True); TAB.mkdir(parents=True, exist_ok=True)
IND = ["DF", "CFI", "HHF", "AWVC"]
LAB = {"DF": "DF (fraction of days)", "CFI": "CFI (fraction of days)", "HHF": "HHF (fraction of days)", "AWVC": "AWVC (g m$^{-3}$)"}
ISLAS = {"el_hierro": "El Hierro", "la_palma": "La Palma", "la_gomera": "La Gomera", "tenerife": "Tenerife",
         "gran_canaria": "Gran Canaria", "fuerteventura": "Fuerteventura", "lanzarote": "Lanzarote"}
SHORT = {"Comunidad de Madrid": "Madrid", "Comunidad Foral de Navarra": "Navarra", "Principado de Asturias": "Asturias",
         "Región de Murcia": "Murcia", "Ciudad de Ceuta": "Ceuta", "Ciudad de Melilla": "Melilla"}
plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "figure.dpi": 100, "savefig.bbox": "tight"})


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return "".join(ch for ch in s if ch.isalnum())


def tex(s):
    return str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")


def rings(g):
    parts = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    return [p[0] for p in parts]


# ---------------------------------------------------------------- datos
def nombres_estaciones():
    try:
        return {e["indicativo"]: e["nombre"].title() for e in json.load(open(HERE / "estaciones_modelo.json", encoding="utf-8"))}
    except Exception:
        return {}


def cargar():
    mun = pd.read_csv(HERE / "indices_municipio_anual.csv").rename(columns={"AWVC_g_m3": "AWVC"})
    asg = pd.read_csv(HERE / "asignacion_candidatas.csv")
    feats = []                                              # (nombre, provincia, comunidad, geometria)
    for fn in ("espana.geojson", "sur.geojson"):
        for f in json.load(open(ROOT / "frontend" / fn, encoding="utf-8"))["features"]:
            p = f["properties"]; feats.append((p["nombre"], p["provincia"], p["comunidad"], f["geometry"]))
    can = []
    for fn, isla in ISLAS.items():
        for f in json.load(open(ROOT / "frontend" / f"{fn}.geojson", encoding="utf-8"))["features"]:
            can.append((f["properties"]["nameunit"], isla, f["geometry"]))
    ccaa = {(norm(n), norm(p)): c for n, p, c, _ in feats}
    asg["comunidad"] = [("Canarias" if i in ISLAS.values() else ccaa.get((norm(m), norm(i)))) for m, i in zip(asg.municipio, asg.isla)]
    # resumen por municipio
    g = mun.groupby("municipio_id")
    res = g[IND + ["T_media_C", "HR_media_pct", "Td_media_C"]].mean()
    res["n_anios"] = g["DF"].count()
    first = g[["estacion", "d_km", "dz_m", "baja_representatividad"]].first()
    res = res.join(first)
    res["flag"] = res["baja_representatividad"].notna() & (res["baja_representatividad"] != "")
    base = asg.set_index("id")[["municipio", "isla", "comunidad", "alt_media_m"]]
    tab = base.join(res, how="left")
    tab["con_datos"] = tab["DF"].notna()
    tab["sin_candidata"] = tab["estacion"].isna()
    return tab, feats, can


# ---------------------------------------------------------------- mapa
def mapa(tab, feats, can):
    key = {(norm(m), norm(i)): idx for idx, (m, i) in zip(tab.index, zip(tab.municipio, tab.isla))}
    polys = []                                              # (idx, anillos, canarias?)
    for n, p, c, g in feats:
        idx = key.get((norm(n), norm(p)))
        polys.append((idx, rings(g), False))
    for n, isla, g in can:
        k = norm(n); cand = [(kk, v) for kk, v in key.items() if kk[1] == norm(isla) and (kk[0] == k or k.startswith(kk[0]))]
        idx = cand[0][1] if len(cand) >= 1 else None
        polys.append((idx, rings(g), True))
    sin = sum(1 for p in polys if p[0] is None)
    print("poligonos:", len(polys), "| sin correspondencia:", sin)
    DX, DY = 8.6, 6.6
    fig, axs = plt.subplots(2, 2, figsize=(12.5, 10.2))
    for ax, col in zip(axs.ravel(), IND):
        vals = tab[col].dropna()
        nm = matplotlib.colors.Normalize(vals.quantile(0.02), vals.quantile(0.98), clip=True)
        cmap = plt.get_cmap("magma" if col == "AWVC" else "viridis")
        fcs, rr, hh = [], [], []
        for idx, rs, isc in polys:
            for r in rs:
                arr = np.asarray(r)
                if isc:
                    arr = arr + np.array([DX, DY])
                v = tab[col].get(idx, np.nan) if idx is not None else np.nan
                fcs.append("#d4d4d4" if pd.isna(v) else cmap(nm(v)))
                rr.append(Polygon(arr, closed=True))
                if idx is not None and bool(tab["flag"].get(idx, False)):
                    hh.append(Polygon(arr, closed=True))
        ax.add_collection(PatchCollection(rr, facecolor=fcs, edgecolor="none", linewidth=0))
        ax.add_collection(PatchCollection(hh, facecolor="none", edgecolor="#555555", hatch="//////", linewidth=0))
        ax.add_patch(Rectangle((-18.7 + DX, 27.3 + DY), 5.6, 2.5, fill=False, edgecolor="#888888", linewidth=0.6))
        ax.set_xlim(-10.5, 4.8); ax.set_ylim(33.6, 44.1); ax.set_aspect(1.28)
        ax.set_xticks([]); ax.set_yticks([]); ax.set_title(LAB[col])
        for s in ax.spines.values(): s.set_visible(False)
        fig.colorbar(plt.cm.ScalarMappable(norm=nm, cmap=cmap), ax=ax, fraction=0.04, pad=0.01, extend="both")
    fig.text(0.5, 0.01, "Grey: no eligible station within 30 km or no accepted year. Hatched: low representativeness (|dz| > 300 m or d > 15 km). "
             "Colour scale clipped at the 2nd and 98th percentiles. Canary Islands shown in the inset box.", ha="center", fontsize=8)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"mapa_espana.{ext}", dpi=200)
    plt.close(fig)
    return sin


# ---------------------------------------------------------------- tablas y figuras
def tablas(tab):
    N = len(tab); d = tab[tab.con_datos]
    out = []
    out.append(f"municipios_total={N}")
    out.append(f"con_datos={len(d)} ({100*len(d)/N:.1f} %)")
    out.append(f"sin_candidata_30km={int(tab.sin_candidata.sum())}")
    out.append(f"candidata_pero_sin_anio_aceptado={int((~tab.sin_candidata & ~tab.con_datos).sum())}")
    out.append(f"baja_representatividad={int(d.flag.sum())} ({100*d.flag.mean():.1f} % de los {len(d)} con datos)")
    out.append(f"estaciones_distintas_asignadas={d.estacion.nunique()}")
    out.append(f"d_km mediana={d.d_km.median():.1f} P90={d.d_km.quantile(.9):.1f} | |dz| mediana={d.dz_m.abs().median():.0f} P90={d.dz_m.abs().quantile(.9):.0f}")
    out.append(f"n_anios mediana={d.n_anios.median():.0f} min={d.n_anios.min():.0f} max={d.n_anios.max():.0f}")
    for c in IND:
        out.append(f"{c}: mediana={d[c].median():.3f} Q1={d[c].quantile(.25):.3f} Q3={d[c].quantile(.75):.3f} min={d[c].min():.3f} max={d[c].max():.3f}")
    r = d[IND].rank().corr()
    out.append("Spearman entre indicadores (municipios): " + "; ".join(f"{a}-{b}={r.loc[a, b]:.2f}" for i, a in enumerate(IND) for b in IND[i + 1:]))
    # --- por comunidad
    rows = []
    for c, g in tab.groupby("comunidad"):
        gd = g[g.con_datos]
        rows.append(dict(c=SHORT.get(c, c), n=len(g), datos=len(gd), sin=int(g.sin_candidata.sum()), flag=100 * gd.flag.mean() if len(gd) else np.nan,
                         est=gd.estacion.nunique(), d=gd.d_km.median() if len(gd) else np.nan, dz=gd.dz_m.abs().median() if len(gd) else np.nan,
                         **{k: gd[k].median() if len(gd) else np.nan for k in IND},
                         **{k + "_q1": gd[k].quantile(.25) if len(gd) else np.nan for k in IND},
                         **{k + "_q3": gd[k].quantile(.75) if len(gd) else np.nan for k in IND}))
    C = pd.DataFrame(rows).sort_values("c", key=lambda s: s.map(lambda x: unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode().lower()))
    C.to_csv(TAB / "resumen_por_comunidad.csv", index=False)
    L = ["\\begin{tabular}{lrrrrrrr}", "\\toprule",
         "Region & Mun. & With data & No station & Low repr.\\ (\\%) & Stations & $d$ (km) & $|\\Delta z|$ (m) \\\\", "\\midrule"]
    for _, x in C.iterrows():
        L.append(f"{tex(x.c)} & {x.n:d} & {x.datos:d} & {x.sin:d} & {x.flag:.0f} & {x.est:d} & {x.d:.1f} & {x.dz:.0f} \\\\")
    tot = d
    L += ["\\midrule", f"Spain & {N} & {len(d)} & {int(tab.sin_candidata.sum())} & {100*d.flag.mean():.0f} & {d.estacion.nunique()} & {d.d_km.median():.1f} & {d.dz_m.abs().median():.0f} \\\\",
          "\\bottomrule", "\\end{tabular}"]
    (TAB / "tab_comunidades.tex").write_text("\n".join(L), encoding="utf-8")
    L = ["\\begin{tabular}{lcccc}", "\\toprule", "Region & DF & CFI & HHF & AWVC (g m$^{-3}$) \\\\", "\\midrule"]
    for _, x in C.iterrows():
        cells = [f"{x[k]:.2f} [{x[k+'_q1']:.2f}--{x[k+'_q3']:.2f}]" if k != "AWVC" else f"{x[k]:.1f} [{x[k+'_q1']:.1f}--{x[k+'_q3']:.1f}]" for k in IND]
        L.append(f"{tex(x.c)} & " + " & ".join(cells) + " \\\\")
    L += ["\\midrule", "Spain & " + " & ".join((f"{d[k].median():.2f} [{d[k].quantile(.25):.2f}--{d[k].quantile(.75):.2f}]" if k != "AWVC" else f"{d[k].median():.1f} [{d[k].quantile(.25):.1f}--{d[k].quantile(.75):.1f}]") for k in IND) + " \\\\",
          "\\bottomrule", "\\end{tabular}"]
    (TAB / "tab_medianas_comunidad.tex").write_text("\n".join(L), encoding="utf-8")
    # --- rankings: rango con empates (1=, 1=, ...) porque el valor municipal es el de su estacion
    nm = nombres_estaciones()
    sh = d.groupby("estacion").size()
    out.append(f"municipios_por_estacion: mediana={sh.median():.0f} max={sh.max()} | municipios que comparten estacion con otro={int((d.estacion.map(sh) > 1).sum())} ({100*(d.estacion.map(sh) > 1).mean():.1f} %)")
    for k in IND:
        rk = d[k].round(4).rank(method="min", ascending=False)
        top = d.assign(rk=rk).sort_values([ "rk", "municipio"]).head(10)
        L = ["\\begin{tabular}{rllllrr}", "\\toprule", f"Rank & Municipality & Province & Station & {k} & $d$ (km) & $\\Delta z$ (m) \\\\", "\\midrule"]
        for idx, x in top.iterrows():
            mark = "$^\\dagger$" if x.flag else ""
            tie = "=" if (rk == x.rk).sum() > 1 else ""
            L.append(f"{int(x.rk)}{tie} & {tex(x.municipio)}{mark} & {tex(x.isla)} & {tex(x.estacion)} & {x[k]:.3f} & {x.d_km:.1f} & {x.dz_m:+.0f} \\\\")
        L += ["\\bottomrule", "\\end{tabular}"]
        (TAB / f"tab_rank_{k}.tex").write_text("\n".join(L), encoding="utf-8")
        out.append(f"top10_{k}: " + "; ".join(f"{int(x.rk)} {x.municipio} ({x.isla}, est. {x.estacion}) {x[k]:.3f}{'†' if x.flag else ''}" for _, x in top.iterrows()))
        out.append(f"bottom5_{k}: " + "; ".join(f"{x.municipio} ({x.isla}) {x[k]:.3f}" for _, x in d.sort_values(k).head(5).iterrows()))
    # --- guia indicador -> tecnologia (solo municipios sin marca de baja representatividad y >= 10 años)
    ok = d[(~d.flag) & (d.n_anios >= 10)]
    TECH = [("DF", "Passive dew condensers", "Nights with $T_{min}\\le T_d$"),
            ("CFI", "Active condensation (thermoelectric, vapour-compression)", "Nights within $\\varepsilon=1$ \\textdegree C of $T_d$"),
            ("HHF", "Fog collectors (screening only)", "Days with RH$_{max}>95$\\,\\%"),
            ("AWVC", "Sorption-based and active systems", "Mean vapour content, g m$^{-3}$")]
    L = ["\\begin{tabular}{p{3.0cm}p{2.2cm}p{4.0cm}p{5.2cm}}", "\\toprule",
         "Technology & Indicator & Regions with the highest median & Highest-ranked municipalities$^{a}$ \\\\", "\\midrule"]
    for k, tech, what in TECH:
        reg = C.dropna(subset=[k]).sort_values(k, ascending=False).head(3)
        rtxt = "; ".join(f"{tex(x.c)} ({x[k]:.2f})" if k != "AWVC" else f"{tex(x.c)} ({x[k]:.1f})" for _, x in reg.iterrows())
        mt = ok.sort_values(k, ascending=False).head(3)
        mtxt = "; ".join(f"{tex(x.municipio)} ({x[k]:.2f})" if k != "AWVC" else f"{tex(x.municipio)} ({x[k]:.1f})" for _, x in mt.iterrows())
        L.append(f"{tech} & {k} & {rtxt} & {mtxt} \\\\")
        out.append(f"guia_{k}: regiones " + rtxt.replace("\\", "") + " | municipios " + mtxt.replace("\\", ""))
    L += ["\\bottomrule", "\\end{tabular}"]
    (TAB / "tab_guia_tecnologia.tex").write_text("\n".join(L), encoding="utf-8")
    out.append(f"municipios_para_guia (sin marca y >=10 años)={len(ok)}")
    # --- figuras
    Cf = C[C.datos >= 5]
    fig, axs = plt.subplots(1, 3, figsize=(11.5, 3.4))
    axs[0].hist(d.d_km, bins=40, color="#4c78a8"); axs[0].axvline(15, color="k", ls="--", lw=0.8); axs[0].set_xlabel("Distance to assigned station (km)"); axs[0].set_ylabel("Municipalities")
    axs[1].hist(d.dz_m.clip(-1000, 1000), bins=50, color="#4c78a8"); axs[1].axvline(-300, color="k", ls="--", lw=0.8); axs[1].axvline(300, color="k", ls="--", lw=0.8)
    axs[1].set_xlabel("Station altitude minus municipal mean altitude (m)")
    Cs = Cf.sort_values("flag"); axs[2].barh(Cs.c, Cs.flag, color="#4c78a8"); axs[2].set_xlabel("Low representativeness (% of municipalities)")
    axs[2].tick_params(axis="y", labelsize=7)
    fig.tight_layout()
    for ext in ("png", "pdf"): fig.savefig(FIG / f"representatividad_espana.{ext}", dpi=200)
    plt.close(fig)
    fig, axs = plt.subplots(2, 2, figsize=(12, 8.2))
    order = list(Cf.sort_values("DF").c)
    for ax, k in zip(axs.ravel(), IND):
        data = [d[d.comunidad.map(lambda c: SHORT.get(c, c)) == c][k].dropna() for c in order]
        ax.boxplot(data, vert=False, labels=order, showfliers=False, medianprops=dict(color="k"), boxprops=dict(color="#4c78a8"), whiskerprops=dict(color="#4c78a8"))
        ax.set_xlabel(LAB[k]); ax.tick_params(axis="y", labelsize=7)
    fig.tight_layout()
    for ext in ("png", "pdf"): fig.savefig(FIG / f"comunidades_cajas.{ext}", dpi=200)
    plt.close(fig)
    fig, axs = plt.subplots(1, 4, figsize=(15, 4.6))
    for ax, k in zip(axs, IND):
        st = ok.groupby("estacion").agg(v=(k, "first"), n=(k, "size"), prov=("isla", "first")).sort_values("v", ascending=False).head(12).iloc[::-1]
        ax.barh([f"{nm.get(c, c)} ({p}) [{n}]" for c, p, n in zip(st.index, st.prov, st.n)], st.v, color="#4c78a8")
        ax.set_xlabel(LAB[k]); ax.tick_params(axis="y", labelsize=6.2)
    fig.text(0.5, -0.01, "Stations ranked by their multi-year mean; [n] = municipalities assigned to the station (not flagged for low representativeness, >= 10 accepted years).", ha="center", fontsize=7.5)
    fig.tight_layout()
    for ext in ("png", "pdf"): fig.savefig(FIG / f"rankings_espana.{ext}", dpi=200)
    plt.close(fig)
    (PAPER / "numbers_espana.txt").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))
    return C


def sens_y_tend():
    f = HERE / "sensibilidad_results.csv"
    if f.exists():
        s = pd.read_csv(f); s = s[s.spearman.notna()]
        s["et"] = s.grupo + ": " + s.variante.astype(str) + " [" + s.indicador + "]"
        s = s.iloc[::-1]
        fig, ax = plt.subplots(figsize=(7.5, max(4, 0.17 * len(s))))
        ax.barh(s.et, s.spearman, color="#4c78a8"); ax.set_xlim(max(0, s.spearman.min() - 0.02), 1.0); ax.set_xlabel("Spearman correlation with baseline ranking")
        ax.tick_params(axis="y", labelsize=6); fig.tight_layout()
        for ext in ("png", "pdf"): fig.savefig(FIG / f"sensibilidad_espana.{ext}", dpi=200)
        plt.close(fig)
    f = HERE / "tendencias_estacion.csv"
    if f.exists():
        t = pd.read_csv(f); ks = ["DF", "CFI", "HHF", "AWVC_g_m3"]
        fig, axs = plt.subplots(1, 4, figsize=(12.5, 3.2))
        for ax, k in zip(axs, ks):
            g = t[t.indicador == k]; ax.hist(g.sen_por_decada, bins=40, color="#4c78a8"); ax.axvline(0, color="k", lw=0.8)
            ax.set_xlabel(f"Sen slope of {k.replace('_g_m3', '')} (per decade)")
        axs[0].set_ylabel("Stations"); fig.tight_layout()
        for ext in ("png", "pdf"): fig.savefig(FIG / f"tendencias_espana.{ext}", dpi=200)
        plt.close(fig)


if __name__ == "__main__":
    tab, feats, can = cargar()
    mapa(tab, feats, can)
    tablas(tab)
    sens_y_tend()
    print("Listo. Figuras en", FIG, "| tablas en", TAB)
