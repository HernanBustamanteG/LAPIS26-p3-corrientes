"""Preparacion del entorno en Google Colab (y comprobacion en cualquier maquina).

Por que asi: gala 1.12 necesita numpy >= 2.2 y numba (preinstalado en Colab) necesita numpy < 2.3. Instalar sin
restriccion trae numpy 2.5 y rompe numba (lo que se vio en el primer intento). Aqui todo se instala con
versiones fijas (requirements-colab.txt). Si numpy cambia de version, la sesion se reinicia una vez: hay que
volver a ejecutar la primera celda del notebook.
"""

import importlib
import os
import subprocess
import sys

REQUISITOS = {"gala": "1.12.0"}
NUMPY_RANGO = ((2, 2), (2, 3))


def _version(mod):
    try:
        return importlib.import_module(mod).__version__
    except Exception:  # noqa: BLE001
        return None


def _numpy_ok(v):
    if v is None:
        return False
    t = tuple(int(x) for x in v.split(".")[:2])
    return NUMPY_RANGO[0] <= t < NUMPY_RANGO[1]


def en_colab():
    return "google.colab" in sys.modules


def instalar(raiz):
    req = os.path.join(raiz, "requirements-colab.txt")
    print("Instalando versiones fijas (%s) ..." % os.path.basename(req))
    r = subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", req], capture_output=True, text=True)
    if r.returncode:
        print(r.stdout[-2000:], r.stderr[-2000:])
        raise RuntimeError("pip fallo; ver arriba")


def preparar_colab(raiz, montar_drive=True):
    """Instala lo necesario (una vez por sesion), monta Google Drive y fija la carpeta de salidas."""
    np_antes = _version("numpy")
    gala_v = _version("gala")
    if not (_numpy_ok(np_antes) and gala_v == REQUISITOS["gala"] and _version("healpy")):
        instalar(raiz)
        importlib.invalidate_caches()
        if "numpy" in sys.modules and not _numpy_ok(np_antes):
            print("\nnumpy cambio de version: la sesion se REINICIA ahora. Cuando vuelva, ejecuta de nuevo "
                  "esta misma celda (ya no instalara nada).")
            os.kill(os.getpid(), 9)
    if montar_drive:
        from google.colab import drive
        drive.mount("/content/drive")
        os.makedirs("/content/drive/MyDrive/lapis26_p3/salidas", exist_ok=True)
        os.environ["P3_SALIDAS"] = "/content/drive/MyDrive/lapis26_p3/salidas"


def resumen():
    """Versiones, carpeta de salidas, ffmpeg y CPU disponibles."""
    import shutil
    from . import config as C
    print("Python %s" % sys.version.split()[0])
    for m in ("numpy", "scipy", "astropy", "gala", "matplotlib", "pandas", "healpy", "galstreams"):
        v = _version(m)
        print("  %-11s %s" % (m, v if v else "(no instalado%s)" % (", opcional" if m == "galstreams" else "")))
    ok = _numpy_ok(_version("numpy")) and _version("gala") == REQUISITOS["gala"]
    print("Salidas en: %s" % C.carpeta_salidas())
    print("ffmpeg: %s | CPU: %d" % (shutil.which("ffmpeg") or "no", os.cpu_count() or 1))
    print("Entorno %s" % ("OK" if ok else "con versiones distintas a las probadas (gala 1.12.0, numpy 2.2.x)"))
    return ok
