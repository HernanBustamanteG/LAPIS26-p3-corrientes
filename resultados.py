"""Tablas de resultados: las incluidas en el repositorio (resultados/*.csv, con su procedencia) o las de una
corrida propia en salidas/. Los notebooks usan las incluidas por defecto para no repetir horas de calculo; con
PROPIOS = True usan la corrida propia mas reciente del mismo plan."""

import glob
import json
import os

from . import config as C

LISTAS = ("polo", "x0", "v0_kms")


def _parsear(df):
    for c in df.columns:
        if c in LISTAS or c.startswith("polo_"):
            df[c] = [json.loads(v) if isinstance(v, str) else v for v in df[c]]
    return df


def cargar(nombre, propios=False):
    """nombre: 'catalogo_principal', 'catalogo_piloto', 'catalogo_masa_1.0', 'lsst_principal', ...
    Devuelve (DataFrame, ruta de origen)."""
    import pandas as pd
    if propios:
        from . import catalogo as Ca, lsst as L
        tipo, plan = nombre.split("_", 1)
        base = C.carpeta_salidas()
        if tipo == "catalogo":
            hay = sorted(glob.glob(os.path.join(base, plan + "_2*")))
            if hay:
                return Ca.leer_catalogo(hay[-1]), hay[-1]
        else:
            hay = sorted(glob.glob(os.path.join(base, "lsst_*")))
            if hay:
                return L.leer(hay[-1]), hay[-1]
        print("No hay corrida propia de %s en %s: uso la incluida en el repositorio." % (nombre, base))
    ruta = os.path.join(os.environ.get("P3_RESULTADOS", os.path.join(C.RAIZ, "resultados")), nombre + ".csv")
    return _parsear(pd.read_csv(ruta)), ruta


def exportar(df, nombre, carpeta):
    """CSV para resultados/ (las listas como JSON). No pisa."""
    ruta = os.path.join(carpeta, nombre + ".csv")
    if os.path.exists(ruta):
        raise FileExistsError(ruta)
    d = df.copy()
    for c in d.columns:
        if d[c].map(lambda v: isinstance(v, (list, tuple))).any():
            d[c] = [json.dumps([float(x) for x in v]) if isinstance(v, (list, tuple)) else v for v in d[c]]
    d.to_csv(ruta, index=False, float_format="%.6g")
    return ruta
