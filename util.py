"""Salidas que nunca pisan, metadatos de procedencia y pruebas automaticas."""

import datetime
import json
import os
import platform
import sys

from . import config as C


def ahora():
    return datetime.datetime.now().isoformat(timespec="seconds")


def carpeta_nueva(prefijo, base=None):
    """salidas/<prefijo>_<FECHA_HORA>/, creada de cero (falla si existe)."""
    base = base or C.carpeta_salidas()
    os.makedirs(base, exist_ok=True)
    ruta = os.path.join(base, "%s_%s" % (prefijo, datetime.datetime.now().strftime("%Y%m%d_%H%M%S")))
    os.makedirs(ruta, exist_ok=False)
    return ruta


def ultima(prefijo, base=None):
    """La carpeta salidas/<prefijo>_<FECHA> mas reciente, o None."""
    import glob
    base = base or C.carpeta_salidas()
    hay = sorted(glob.glob(os.path.join(base, prefijo + "_2*")))
    return hay[-1] if hay else None


def versiones():
    out = {"python": sys.version.split()[0], "plataforma": platform.platform(), "p3streams": C.VERSION}
    for m in ("numpy", "scipy", "astropy", "gala", "matplotlib", "pandas", "healpy"):
        try:
            out[m] = __import__(m).__version__
        except Exception:  # noqa: BLE001
            out[m] = None
    return out


def escribir_json(obj, ruta):
    with open(ruta, "x", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, default=str, ensure_ascii=False)


def escribir_texto(texto, ruta):
    with open(ruta, "x", encoding="utf-8") as f:
        f.write(texto if texto.endswith("\n") else texto + "\n")


def metadatos(ruta_carpeta, **extra):
    escribir_json(dict(fecha=ahora(), versiones=versiones(), **extra), os.path.join(ruta_carpeta, "metadatos.json"))


class Pruebas:
    """Lista de comprobaciones con PASA / FALLA y un resumen final."""

    def __init__(self, titulo):
        print("AUTOTEST %s (p3streams %s): no escribe nada." % (titulo, C.VERSION))
        self.ok = []

    def __call__(self, cond, texto, aviso=False):
        if aviso and not cond:
            print("  [AVISO] " + texto)
            return bool(cond)
        self.ok.append(bool(cond))
        print("  [%s] %s" % ("PASA" if cond else "FALLA", texto))
        return bool(cond)

    def fin(self):
        print("Autotest: %d de %d pruebas pasan." % (sum(self.ok), len(self.ok)))
        return all(self.ok)
