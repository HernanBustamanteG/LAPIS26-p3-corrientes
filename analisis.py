"""Hito 5: clasificacion y tendencias a partir del catalogo (funciones usadas por los notebooks 05 a 08)."""

import numpy as np

from . import metricas as Me

# metricas que se analizan, con su nombre en ingles para las figuras. 'dpolo' es la version vectorial del cambio
# del polo (angulo entre el polo medio de cada modelo y el del modelo A): no la contamina la precesion por el
# disco, que esta igual en los cuatro modelos.
METRICAS = {"dpolo": "change of the mean pole (deg)", "desalineamiento_deg": "PM misalignment (deg)",
            "tilt_polo_deg": "pole tilt from initial pole (deg)", "tilt_plano_deg": "plane tilt, SVD (deg)",
            "dispersion_polos_deg": "pole spread (deg)"}


def col(metrica, que, parte="todo"):
    """Nombre de columna del catalogo. que: 'reflex', 'direct', 'full', 'f', 'nl' (no lineal) o 'A' (piso)."""
    if metrica == "dpolo":
        return {"reflex": "dpolo_B", "direct": "dpolo_C", "full": "dpolo_D", "f": "dpolo_f_reflex"}[que] + "_" + parte
    if que == "A":
        return "%s_%s_A" % (metrica, parte)
    pref = {"reflex": "dM_reflex", "direct": "dM_direct", "full": "dM_full", "f": "f_reflex", "nl": "no_lineal"}[que]
    return "%s_%s_%s" % (pref, metrica, parte)


def direccion_aMW(sis, t_min=-1000.0):
    """Direccion media de a_MW en el ultimo Gyr, pesada por |a_MW| (apunta hacia la LMC)."""
    t = sis.t[sis.t >= t_min]
    a = sis.a_mw(t)
    return Me.unit(np.sum(a, axis=0))


def agregar_geometria(df, sis):
    """Columnas de orientacion: n0 . L_LMC (sentido de giro respecto de la LMC) y |n0 . a_MW| (1: la fuerza
    uniforme es perpendicular al plano de la corriente)."""
    from .figuras import polo_lmc
    d = df.copy()
    n0 = Me.unit(np.array(d["polo"].tolist(), float))
    d["cos_polo_lmc"] = n0 @ polo_lmc(sis)
    d["perp_aMW"] = np.abs(n0 @ direccion_aMW(sis))
    d["sentido_lmc"] = np.where(d["cos_polo_lmc"] > 0, "prograde", "retrograde")
    return d


def clases(df, metrica, parte="todo"):
    return [Me.clase(x) for x in df[col(metrica, "f", parte)].to_numpy(float)]


def tabla_sensibilidad(df, parte="todo"):
    """Por metrica: piso en A, medianas de |dM_reflex|, |dM_direct|, |dM_full|, fraccion de corrientes en que cada
    efecto supera el piso, y conteo de clases."""
    import pandas as pd
    filas = []
    for m, nombre in METRICAS.items():
        r = np.abs(df[col(m, "reflex", parte)].to_numpy(float))
        d = np.abs(df[col(m, "direct", parte)].to_numpy(float))
        f = np.abs(df[col(m, "full", parte)].to_numpy(float))
        piso = df[col(m, "A", parte)].to_numpy(float) if m != "dpolo" else np.zeros(len(df))
        piso_med = np.nanmedian(piso) if m != "dpolo" else np.nan
        ref = np.nanmedian(df["dispersion_polos_deg_%s_A" % parte]) if m == "dpolo" else piso_med
        c = pd.Series(clases(df, m, parte)).value_counts()
        filas.append({"metric": nombre, "floor_A": piso_med, "median |dM_reflex|": np.nanmedian(r),
                      "median |dM_direct|": np.nanmedian(d), "median |dM_full|": np.nanmedian(f),
                      "frac reflex > floor": np.nanmean(r > ref), "frac direct > floor": np.nanmean(d > ref),
                      "reflex": int(c.get("reflex", 0)), "mixed": int(c.get("mixed", 0)),
                      "torque": int(c.get("torque", 0))})
    return pd.DataFrame(filas)


def medianas_por_tramo(x, y, bordes, n_min=4):
    """Mediana y percentiles 16-84 de y en tramos de x."""
    c, med, lo, hi = [], [], [], []
    for a, b in zip(bordes[:-1], bordes[1:]):
        s = (x >= a) & (x < b) & np.isfinite(y)
        if s.sum() >= n_min:
            c.append(np.median(x[s]))
            med.append(np.median(y[s]))
            lo.append(np.percentile(y[s], 16))
            hi.append(np.percentile(y[s], 84))
    return np.array(c), np.array(med), np.array(lo), np.array(hi)


def cancelaciones(df, parte="todo", umbral=0.5):
    """Corrientes donde el efecto total es menor que una fraccion del mayor de los dos efectos separados
    (cambio vectorial del polo): el reflejo y el tiron directo se compensan."""
    b, c, d = (df[col("dpolo", k, parte)].to_numpy(float) for k in ("reflex", "direct", "full"))
    return (d < umbral * np.maximum(b, c)) & (np.maximum(b, c) > 1.0)


def no_linealidad(df, metrica, parte="todo"):
    """|dM_full - (dM_reflex + dM_direct)| / (|dM_reflex| + |dM_direct|)."""
    r, d, f = (df[col(metrica, k, parte)].to_numpy(float) for k in ("reflex", "direct", "full"))
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.abs(f - (r + d)) / (np.abs(r) + np.abs(d))


def por_radio(carpeta, ids=None, bordes=(5, 10, 15, 20, 30, 40, 60, 80, 120, 200)):
    """Diagnostico estrella a estrella. Como los cuatro modelos usan la misma semilla, la estrella i es la misma
    en A, B, C y D (mismo tiempo de liberacion y brazo). Para cada estrella: el angulo entre su polo orbital en B
    (o C, D) y en A, en funcion de su radio galactocentrico hoy en A. Devuelve un DataFrame con la mediana y los
    percentiles 16-84 por tramo de radio, y el numero de estrellas."""
    import glob
    import os
    import pandas as pd
    from . import corrientes as Co
    if ids is None:
        ids = sorted({os.path.basename(r)[:-6] for r in glob.glob(os.path.join(carpeta, "corrientes", "*_A.npz"))})
    acum = {k: [] for k in "BCD"}
    radios = []
    for i in ids:
        c = {m: Co.cargar(os.path.join(carpeta, "corrientes", "%s_%s.npz" % (i, m))) for m in "ABCD"}
        LA = Me.polos(c["A"]["pos"].astype(float), c["A"]["vel"].astype(float))
        radios.append(np.linalg.norm(c["A"]["pos"], axis=1))
        for m in "BCD":
            acum[m].append(Me.angulo(Me.polos(c[m]["pos"].astype(float), c[m]["vel"].astype(float)), LA))
    r = np.concatenate(radios)
    filas = []
    for a, b in zip(bordes[:-1], bordes[1:]):
        s = (r >= a) & (r < b)
        if s.sum() < 200:
            continue
        f = {"r_min": a, "r_max": b, "r_med": float(np.median(r[s])), "n_estrellas": int(s.sum())}
        for m in "BCD":
            v = np.concatenate(acum[m])[s]
            f["med_%s" % m], f["p16_%s" % m], f["p84_%s" % m] = np.percentile(v, [50, 16, 84])
        filas.append(f)
    return pd.DataFrame(filas)
