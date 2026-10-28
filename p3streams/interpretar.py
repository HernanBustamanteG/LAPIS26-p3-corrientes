"""Hito 6: donde caerian las corrientes observadas (Sgr, Orphan-Chenab, corrientes de S5) en la clasificacion.

Datos: trazas de galstreams (Mateu 2023; incluye las referencias de cada traza). Para cada corriente real:
  - posiciones de la traza -> marco de la MW (el mismo Sol que el resto del proyecto);
  - plano orbital: normal SVD de la traza por el centro de la MW (no necesita velocidades);
  - sentido de giro: si la traza tiene movimientos propios Y velocidad radial (has_pm y has_vrad), del polo
    medio L = x x v; si no, el sentido queda indeterminado y se usan las dos orientaciones;
  - rango de radios galactocentricos de la traza.
Luego se buscan en el catalogo las corrientes simuladas con polo de HOY (modelo D) a menos de `radio_deg` y con
rango de radios que se solapa, y se resume su clasificacion. Es una ubicacion aproximada (la grilla tiene polos
cada ~30 grados), no un ajuste de la corriente real.
"""

import numpy as np

# Corrientes a comparar (nombres de galstreams). Sgr y Orphan-Chenab, del enunciado; el resto son corrientes del
# sur con traza en galstreams que S5 observo (la referencia de cada traza va en la tabla). La lista exacta que usa
# Shipp et al. 2021 esta en su Tabla 1: conviene cotejarla antes de presentar.
REALES = ("Sagittarius-A20", "Orphan-K23", "AAU-ATLAS-L21", "AAU-AliqaUma-L21", "Elqui-S19", "Indus-S19",
          "Jhelum-a-B19", "Phoenix-S19", "Turranburra-S19", "TucanaIII-S19")


def cargar_galstreams():
    """MWStreams de galstreams. Con pandas >= 3 hay que desactivar el tipo 'str' por defecto (si no, falla al
    construir su tabla resumen); el aviso de pandas es esperado."""
    import warnings
    import pandas as pd
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pd.set_option("future.infer_string", False)
    except Exception:  # noqa: BLE001
        pass
    import galstreams
    return galstreams.MWStreams(verbose=False, implement_Off=False)


def corriente_real(mws, nombre):
    import astropy.units as u
    from . import metricas as Me
    tr = mws[nombre].track
    fila = mws.summary.loc[mws.summary["TrackName"] == nombre].iloc[0] if "TrackName" in mws.summary else None
    has_pm = bool(fila["has_pm"]) if fila is not None else False
    has_vr = bool(fila["has_vrad"]) if fila is not None else False
    g = tr.transform_to(Me.marco_galactocentrico())
    pos = np.column_stack([g.x.to_value(u.kpc), g.y.to_value(u.kpc), g.z.to_value(u.kpc)])
    r = np.linalg.norm(pos, axis=1)
    n = Me.normal_svd(pos)
    sentido = False
    if has_pm and has_vr:
        vel = np.column_stack([g.v_x.to_value(u.km / u.s), g.v_y.to_value(u.km / u.s), g.v_z.to_value(u.km / u.s)])
        L = Me.polo_medio(Me.polos(pos, vel))
        n = n if np.dot(n, L) > 0 else -n
        sentido = True
    return dict(nombre=nombre, normal=n, sentido_conocido=sentido, r_min=float(r.min()), r_max=float(r.max()),
                r_med=float(np.median(r)), n_puntos=len(r), has_pm=has_pm, has_vrad=has_vr,
                ref=str(fila["TrackRefs"]) if fila is not None else "")


def ubicar(real, df, radio_deg=30.0, polo="polo_todo_D"):
    """Corrientes del catalogo vecinas de una corriente real (polo de hoy y radios)."""
    from . import metricas as Me
    P = np.array(df[polo].tolist(), float)
    ang = Me.angulo(P, real["normal"])
    if not real["sentido_conocido"]:
        ang = np.minimum(ang, 180 - ang)
    solapa = (df["peri_kpc"] <= real["r_max"] * 1.25) & (df["apo_kpc"] >= real["r_min"] * 0.8)
    sel = (ang < radio_deg) & solapa.to_numpy()
    v = df.loc[sel].copy()
    v["ang_polo_deg"] = ang[sel]
    return v.sort_values("ang_polo_deg")


def resumen(reales, df, metrica="desalineamiento_deg", radio_deg=30.0):
    """Tabla: corriente real, radios, vecinos en el catalogo, mediana de f_reflex y clase."""
    import pandas as pd
    from . import metricas as Me
    filas = []
    for r in reales:
        v = ubicar(r, df, radio_deg)
        f = v["f_reflex_%s_todo" % metrica].to_numpy(float) if len(v) else np.array([])
        fp = v["dpolo_f_reflex_todo"].to_numpy(float) if len(v) else np.array([])
        filas.append(dict(stream=r["nombre"], r_kpc="%.0f-%.0f" % (r["r_min"], r["r_max"]),
                          sense_known=r["sentido_conocido"], n_neighbours=len(v),
                          f_reflex_misalignment=float(np.nanmedian(f)) if len(f) else np.nan,
                          f_reflex_pole=float(np.nanmedian(fp)) if len(fp) else np.nan,
                          class_misalignment=Me.clase(np.nanmedian(f)) if len(f) else "undetermined",
                          class_pole=Me.clase(np.nanmedian(fp)) if len(fp) else "undetermined"))
    return pd.DataFrame(filas)
