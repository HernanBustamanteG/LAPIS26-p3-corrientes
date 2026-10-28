"""Grilla de progenitores, corrida de los cuatro modelos por corriente y catalogo (hito 4).

Cada corriente se guarda en su propio archivo (corrientes/<id>_<modelo>.npz) y su fila en filas/<id>.json:
si la sesion de Colab se corta, la corrida se retoma desde donde quedo (nada se recalcula ni se pisa).
"""

import json
import os
import time

import numpy as np

from . import config as C

# Tres familias de longitud (medidas en la MW aislada con t_start = 5 Gyr; notebook 04):
#   corta: r_apo = 100 kpc, 1e7 Msun   -> ~0.3 vueltas
#   larga: r_apo = 60 kpc,  5e7 Msun   -> ~1.1 vueltas
#   doble: r_apo = 40 kpc,  1e8 Msun   -> ~1.7 vueltas
FAMILIAS = {"corta": dict(r_apo=100.0, m_prog=1e7), "larga": dict(r_apo=60.0, m_prog=5e7),
            "doble": dict(r_apo=40.0, m_prog=1e8)}


def grilla(n_polos=12, sentidos=True, familias=("corta", "larga", "doble"), fases=(0.0,), f=C.F_TANG,
           t_start=C.T_START, polos="fibonacci"):
    """Lista de progenitores (dicts). polos: 'fibonacci' (n_polos) o 'healpy' (n_polos = nside).
    familias: nombres de FAMILIAS o un dict propio {nombre: dict(r_apo=..., m_prog=...)}."""
    from . import corrientes as Co
    fams = familias if isinstance(familias, dict) else {k: FAMILIAS[k] for k in familias}
    P = Co.polos_fibonacci(n_polos) if polos == "fibonacci" else Co.polos_healpy(n_polos)
    filas = []
    for ip, n in enumerate(P):
        for sentido in ((1, -1) if sentidos else (1,)):
            for fam, par in fams.items():
                for psi in fases:
                    pid = "p%02d%s_%s_f%03d" % (ip, "+" if sentido > 0 else "-", fam, int(round(psi)))
                    filas.append(dict(id=pid, polo=(sentido * n).tolist(), polo_idx=ip, sentido=sentido,
                                      familia=fam, psi_deg=float(psi), f=f, t_start=t_start, **par))
    return filas


def _fila_metricas(fila, res_por_modelo, prefijo=""):
    from . import metricas as Me
    out = {}
    for m, res in res_por_modelo.items():
        out["%slongitud_vueltas_%s" % (prefijo, m)] = res.get("longitud_vueltas", np.nan)
        for parte in Me.PARTES:
            for met in Me.METRICAS:
                out["%s%s_%s_%s" % (prefijo, met, parte, m)] = res.get(parte, {}).get(met, np.nan)
            if parte in res:
                out["%spolo_%s_%s" % (prefijo, parte, m)] = list(map(float, res[parte]["polo"]))
    for parte in Me.PARTES:
        for met in Me.METRICAS:
            p = Me.perturbaciones(res_por_modelo, met, parte)
            for k, v in p.items():
                out["%s%s_%s_%s" % (prefijo, k, met, parte)] = v
        cp = Me.cambio_polo(res_por_modelo, parte)
        for k, v in cp.items():
            out["%sdpolo_%s_%s" % (prefijo, k, parte)] = v
    return out


def correr_corriente(fila, sis, carpeta, modelos=None, guardar_corrientes=True):
    """Los cuatro modelos de un progenitor: orbitas, corrientes, metricas. Devuelve la fila del catalogo."""
    from . import corrientes as Co, metricas as Me, potenciales as P
    t0 = time.time()
    modelos = modelos or P.modelos(sis)
    x0, v0 = Co.condiciones_iniciales(fila["polo"], fila["r_apo"], fila["f"], fila["psi_deg"])
    t_ini = -fila["t_start"]
    out = dict(fila)
    out.update({"x0": x0.tolist(), "v0_kms": v0.tolist()})
    oa = Co.orbita(modelos["A"], x0, v0, t_ini)
    out.update(Co.resumen_orbita(oa))
    od = Co.orbita(modelos["D"], x0, v0, t_ini)
    out["dmin_lmc_kpc"], out["t_dmin_lmc_Myr"] = Co.acercamiento_lmc(od, sis)
    out["dmin_lmc_kpc_A"], _ = Co.acercamiento_lmc(oa, sis)
    res = {}
    for m in "ABCD":
        c = Co.generar(modelos[m], x0, v0, m_prog=fila["m_prog"], t_inicio=t_ini)
        if guardar_corrientes:
            ruta = os.path.join(carpeta, "corrientes", "%s_%s.npz" % (fila["id"], m))
            if not os.path.exists(ruta):
                Co.guardar(c, ruta, polo=np.asarray(fila["polo"]), modelo=np.asarray(m))
        res[m], _ = Me.medir(c, fila["polo"])
    out.update(_fila_metricas(fila, res))
    out["segundos"] = round(time.time() - t0, 1)
    return out


def _trabajador(args):
    fila, ruta_sis, carpeta = args
    from . import potenciales as P
    global _CACHE
    try:
        _CACHE
    except NameError:
        _CACHE = {}
    if ruta_sis not in _CACHE:
        s = P.Sistema.cargar(ruta_sis)
        _CACHE.clear()
        _CACHE[ruta_sis] = (s, P.modelos(s))
    s, mods = _CACHE[ruta_sis]
    ruta = os.path.join(carpeta, "filas", fila["id"] + ".json")
    if os.path.exists(ruta):
        return fila["id"], "ya estaba"
    try:
        out = correr_corriente(fila, s, carpeta, mods)
    except Exception as e:  # noqa: BLE001
        return fila["id"], "error: %s" % str(e)[:200]
    with open(ruta, "x", encoding="utf-8") as f:
        json.dump(out, f, default=float)
    return fila["id"], "ok %.0f s" % out["segundos"]


def correr_grilla(filas, ruta_sis, carpeta, procesos=1, progreso=True):
    """Corre (o retoma) una grilla. carpeta: la de esta corrida (con subcarpetas filas/ y corrientes/)."""
    os.makedirs(os.path.join(carpeta, "filas"), exist_ok=True)
    os.makedirs(os.path.join(carpeta, "corrientes"), exist_ok=True)
    pend = [f for f in filas if not os.path.exists(os.path.join(carpeta, "filas", f["id"] + ".json"))]
    print("Corrientes: %d en total, %d ya hechas, %d por hacer." % (len(filas), len(filas) - len(pend), len(pend)))
    t0, hechas, errores = time.time(), 0, []
    args = [(f, ruta_sis, carpeta) for f in pend]
    if procesos > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(procesos) as ex:
            it = ex.map(_trabajador, args)
            for pid, msg in it:
                hechas += 1
                errores += [(pid, msg)] if msg.startswith("error") else []
                if progreso:
                    _barra(hechas, len(pend), t0, pid)
    else:
        for a in args:
            pid, msg = _trabajador(a)
            hechas += 1
            errores += [(pid, msg)] if msg.startswith("error") else []
            if progreso:
                _barra(hechas, len(pend), t0, pid)
    if errores:
        print("\nErrores: %s" % errores[:5])
    return errores


def _barra(i, n, t0, txt=""):
    import sys
    f = i / n if n else 1
    dt = time.time() - t0
    sys.stdout.write("\r  [%-30s] %3d%% (%d/%d) %6.0f s, faltan ~%6.0f s %s   " % (
        "#" * int(30 * f), 100 * f, i, n, dt, dt / f - dt if f else 0, txt))
    sys.stdout.flush()
    if i >= n:
        sys.stdout.write("\n")


def leer_catalogo(carpeta):
    """DataFrame con una fila por corriente (lee filas/*.json)."""
    import glob
    import pandas as pd
    filas = []
    for r in sorted(glob.glob(os.path.join(carpeta, "filas", "*.json"))):
        with open(r, encoding="utf-8") as f:
            filas.append(json.load(f))
    return pd.DataFrame(filas)
