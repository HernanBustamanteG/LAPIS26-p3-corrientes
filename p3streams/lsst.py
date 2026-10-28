"""Hito 5 (segunda parte): 'observar' las corrientes del catalogo con LSST y decidir que se detecta.

Para cada corriente y modelo (A, B, C, D) se simulan las estrellas que LSST veria (observar.observar) y se
recalculan las metricas solo con esas estrellas, con su error por bootstrap (observar.metricas_observadas).

Criterios (escritos aqui y no en el notebook para que sean los mismos en todas partes):
  - Senal del reflejo, observable: |M_D - M_C| (con y sin reflejo, el resto igual), en unidades de
    sigma = sqrt(sigma_D^2 + sigma_C^2). Se detecta si es > 3 sigma.
  - Senal del tiron directo: |M_D - M_B| / sqrt(sigma_D^2 + sigma_B^2) > 3.
  - Cuantas corrientes hacen falta para distinguir: se suman en cuadratura las senales de corrientes tomadas
    al azar (chi^2 acumulado) hasta superar 3 sigma; se repite muchas veces y se da la mediana. Supone que la
    MW, la LMC y los progenitores se conocen (en la realidad se marginalizan): es una cota OPTIMISTA.
"""

import json
import os
import time
import zlib

import numpy as np

from . import config as C

METRICAS_OBS = ("tilt_plano_deg", "desalineamiento_deg", "tilt_polo_deg", "dispersion_polos_deg")
N_MAX = 20000      # maximo de estrellas por corriente para las metricas (si hay mas, se toma un subconjunto al azar:
#                    los sigma resultantes son una cota SUPERIOR para las corrientes mas ricas)


def _sub(obs, mascara, gaia=False):
    """Subconjunto de estrellas observadas. gaia=True: solo G < 21 (G ~ r), errores de Gaia DR3 y sin
    seguimiento espectroscopico."""
    n = obs["n"]
    if gaia:
        mascara = mascara & (obs["r"] < C.GAIA_G_LIM)
    o = {k: (v[mascara] if isinstance(v, np.ndarray) and len(v) == n else v) for k, v in obs.items()}
    o["n"] = int(mascara.sum())
    if gaia and o["n"]:
        sg = o["sigma_pm_gaia"]
        o["pmra_obs"] = o["pmra_true"] + (o["pmra_obs"] - o["pmra_true"]) * sg / o["sigma_pm"]
        o["pmdec_obs"] = o["pmdec_true"] + (o["pmdec_obs"] - o["pmdec_true"]) * sg / o["sigma_pm"]
        o["sigma_pm"] = sg
        o["pm_ok"] = np.ones(o["n"], bool)
        o.pop("vr_ok", None)
    return o


VARIANTES = ("lsst", "lider", "cola", "gaia")


def observar_corriente(id_, carpeta_cat, fl=None, frac=C.FRACCION_ESTELAR, anios=10.0, espectro=True, n_boot=20,
                       semilla=C.SEMILLA, n_max=N_MAX, m_prog=None, variantes=VARIANTES):
    """Observaciones de los cuatro modelos de una corriente del catalogo. Devuelve un dict (una fila).
    Variantes: 'lsst' (toda la corriente), 'lider' y 'cola' (cada brazo con LSST) y 'gaia' (G < 21, errores de
    Gaia DR3). Columnas: obs_<metrica>_<modelo> (lsst) u obs_<variante>_<metrica>_<modelo>, y sus sig_."""
    from . import corrientes as Co, metricas as Me, observar as O
    fl = fl or O.FuncionLuminosidad()
    with open(os.path.join(carpeta_cat, "filas", id_ + ".json"), encoding="utf-8") as f:
        fila = json.load(f)
    m_prog = m_prog or fila["m_prog"]
    out = {"id": id_, "m_estelar": frac * m_prog, "anios": anios}
    for m in "ABCD":
        c = Co.cargar(os.path.join(carpeta_cat, "corrientes", "%s_%s.npz" % (id_, m)))
        pos, vel = c["pos"].astype(float), c["vel"].astype(float)
        Lm = Me.polo_medio(Me.polos(pos, vel))
        psi = Me.angulo_desenrollado(pos, c["release_time"], c["lead_trail"], c["prog_pos"], Lm)
        rng = np.random.default_rng([semilla, zlib.crc32(id_.encode()), ord(m)])   # reproducible
        obs = O.observar(c, frac * m_prog, rng, anios=anios, espectro=espectro, fl=fl)
        n_tot = obs.get("n", 0)
        out["n_obs_%s" % m] = int(n_tot)
        out["frac_footprint_%s" % m] = obs["n_en_footprint"] / obs["n_particulas"]
        # que parte de la corriente cae en el footprint (en angulo a lo largo de la corriente)
        sky = Me.a_icrs(pos, vel, corregir=False)
        pie = sky.dec.deg < C.LSST_DEC_MAX
        out["psi_footprint_%s" % m] = float(np.ptp(psi[pie]) / np.ptp(psi)) if pie.sum() > 2 else 0.0
        if n_tot == 0:
            continue
        out["n_gaia_%s" % m] = int(np.sum(obs["r"] < C.GAIA_G_LIM))
        if n_tot > n_max:
            k = np.sort(rng.choice(n_tot, n_max, replace=False))
            obs = {kk: (v[k] if isinstance(v, np.ndarray) and len(v) == n_tot else v) for kk, v in obs.items()}
            obs["n"] = n_max
        out["n_pm_%s" % m] = int(obs["pm_ok"].sum())
        out["d_med_obs_%s" % m] = float(np.median(obs["dist_true"]))
        out["d_max_obs_%s" % m] = float(np.max(obs["dist_true"]))
        out["r_med_%s" % m] = float(np.median(obs["r"]))
        brazo = c["lead_trail"][obs["idx"]]
        todos = np.ones(obs["n"], bool)
        for var in variantes:
            o = {"lsst": obs, "lider": _sub(obs, brazo == 1) if var == "lider" else None,
                 "cola": _sub(obs, brazo == -1) if var == "cola" else None,
                 "gaia": _sub(obs, todos, gaia=True) if var == "gaia" else None}[var]
            res = O.metricas_observadas(o, c, fila["polo"], psi, rng, n_boot=n_boot if var == "lsst" else n_boot // 2)
            pre = "" if var == "lsst" else var + "_"
            for k, (v, s_) in res.items():
                if k in METRICAS_OBS:
                    out["obs_%s%s_%s" % (pre, k, m)] = v
                    out["sig_%s%s_%s" % (pre, k, m)] = s_
    for var in variantes:
        pre = "" if var == "lsst" else var + "_"
        for k in METRICAS_OBS:
            def g(a, m):
                return out.get("%s_%s%s_%s" % (a, pre, k, m), np.nan)
            for nombre, (x, y) in (("reflejo", ("D", "C")), ("directo", ("D", "B"))):
                s_ = np.hypot(g("sig", x), g("sig", y))
                d = abs(g("obs", x) - g("obs", y))
                out["senal_%s%s_%s" % (pre, nombre, k)] = d
                out["snr_%s%s_%s" % (pre, nombre, k)] = d / s_ if s_ > 0 else np.nan
    return out


def _trabajador(args):
    id_, carpeta_cat, carpeta, kw = args
    ruta = os.path.join(carpeta, "filas", id_ + ".json")
    if os.path.exists(ruta):
        return id_, "ya estaba"
    try:
        out = observar_corriente(id_, carpeta_cat, **kw)
    except Exception as e:  # noqa: BLE001
        return id_, "error: %s" % str(e)[:200]
    with open(ruta, "x", encoding="utf-8") as f:
        json.dump(out, f, default=float)
    return id_, "ok"


def correr(ids, carpeta_cat, carpeta, procesos=1, **kw):
    """Pasada LSST sobre las corrientes guardadas de un catalogo (reanudable, como el catalogo)."""
    from .catalogo import _barra
    os.makedirs(os.path.join(carpeta, "filas"), exist_ok=True)
    pend = [i for i in ids if not os.path.exists(os.path.join(carpeta, "filas", i + ".json"))]
    print("Corrientes: %d, ya hechas %d, por hacer %d." % (len(ids), len(ids) - len(pend), len(pend)))
    t0, errores = time.time(), []
    args = [(i, carpeta_cat, carpeta, kw) for i in pend]
    if procesos > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(procesos) as ex:
            for j, (i, msg) in enumerate(ex.map(_trabajador, args)):
                errores += [(i, msg)] if msg.startswith("error") else []
                _barra(j + 1, len(pend), t0, i)
    else:
        for j, a in enumerate(args):
            i, msg = _trabajador(a)
            errores += [(i, msg)] if msg.startswith("error") else []
            _barra(j + 1, len(pend), t0, i)
    if errores:
        print("Errores: %s" % errores[:5])
    return errores


def leer(carpeta):
    import glob
    import pandas as pd
    filas = []
    for r in sorted(glob.glob(os.path.join(carpeta, "filas", "*.json"))):
        with open(r, encoding="utf-8") as f:
            filas.append(json.load(f))
    return pd.DataFrame(filas)


def n_necesarias(snr, umbral=3.0, n_mc=4000, semilla=0):
    """Numero de corrientes (tomadas al azar de la lista snr) cuya senal combinada en cuadratura supera el
    umbral. Devuelve (mediana, percentil 16, percentil 84) o (nan, ...) si ni todas juntas alcanzan."""
    s = np.asarray(snr, float)
    s = s[np.isfinite(s)]
    if not len(s) or np.sqrt(np.sum(s ** 2)) < umbral:
        return np.nan, np.nan, np.nan
    rng = np.random.default_rng(semilla)
    n = []
    for _ in range(n_mc):
        c = np.sqrt(np.cumsum(rng.permutation(s) ** 2))
        n.append(int(np.argmax(c >= umbral)) + 1)
    return tuple(float(x) for x in np.percentile(n, [50, 16, 84]))


def agregar_snr_escalada(df, cap=N_MAX):
    """Columnas snrx_*: la misma senal con los errores reescalados por sqrt(n_usadas / n_observadas) de cada
    modelo. Supone que el error de las metricas es estadistico (escala como 1/sqrt(N)) [deducido]: no corrige
    los sesgos de seleccion. Las snr_* originales (con a lo sumo N_MAX estrellas) son la version conservadora."""
    d = df.copy()
    f = {m: np.sqrt(np.minimum(d["n_obs_%s" % m].to_numpy(float), cap) / np.maximum(d["n_obs_%s" % m].to_numpy(float), 1))
         for m in "BCD"}
    for c in [c for c in d.columns if c.startswith("snr_")]:
        resto = c[4:]
        pre = ""
        for v in ("lider_", "cola_", "gaia_"):
            if resto.startswith(v):
                pre, resto = v, resto[len(v):]
        efecto, met = resto.split("_", 1)
        x, y = ("D", "C") if efecto == "reflejo" else ("D", "B")
        sx, sy = d.get("sig_%s%s_%s" % (pre, met, x)), d.get("sig_%s%s_%s" % (pre, met, y))
        if sx is None or sy is None:
            d["snrx_" + c[4:]] = np.nan          # metrica no medible en esta variante (p. ej. Gaia sin velocidades)
            continue
        fx, fy = (f[x], f[y]) if pre != "gaia_" else (1.0, 1.0)     # Gaia: nunca supera el tope
        s = np.hypot(sx.to_numpy(float) * fx, sy.to_numpy(float) * fy)
        with np.errstate(invalid="ignore", divide="ignore"):
            d["snrx_" + c[4:]] = d["senal_%s%s_%s" % (pre, efecto, met)].to_numpy(float) / s
    return d
