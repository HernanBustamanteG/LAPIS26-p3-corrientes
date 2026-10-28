"""Construye los notebooks (sin ejecutar) en herramientas/build/ y, con --ejecutar, los ejecuta con nbclient y
escribe la version ejecutada (con salidas visibles en GitHub) en notebooks/.

  python herramientas/construir_notebooks.py [--ejecutar] [--solo 00,01] [--forzar]

--forzar reemplaza el notebook ejecutado anterior de notebooks/ (es codigo fuente del repositorio, no una salida
de datos; las salidas de datos de cada ejecucion van siempre a carpetas nuevas en salidas/).
"""

import argparse
import os
import sys
import time

import nbformat

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from comun import notebook  # noqa: E402
import nb_00_03  # noqa: E402

NOTEBOOKS = {
    "00": ("00_entorno.ipynb", nb_00_03.nb00),
    "01": ("01_hito1_una_corriente.ipynb", nb_00_03.nb01),
    "02": ("02_hito2_potenciales.ipynb", nb_00_03.nb02),
    "03": ("03_hito3_metricas.ipynb", nb_00_03.nb03),
}
try:
    import nb_04_09  # noqa: E402
    NOTEBOOKS.update(nb_04_09.NOTEBOOKS)
except ImportError:
    pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ejecutar", action="store_true")
    ap.add_argument("--solo")
    ap.add_argument("--forzar", action="store_true")
    ap.add_argument("--timeout", type=int, default=7200)
    a = ap.parse_args()
    raiz = os.path.dirname(AQUI)
    build = os.path.join(AQUI, "build")
    os.makedirs(build, exist_ok=True)
    claves = a.solo.split(",") if a.solo else sorted(NOTEBOOKS)
    for k in claves:
        nombre, f = NOTEBOOKS[k]
        nb = notebook(f(), nombre)
        ruta = os.path.join(build, nombre)
        nbformat.write(nb, ruta)
        print("construido", ruta)
        if a.ejecutar:
            from nbclient import NotebookClient
            dest = os.path.join(os.environ.get("NB_DESTINO", os.path.join(raiz, "notebooks")), nombre)
            if os.path.exists(dest) and not a.forzar:
                print("  ya existe %s (usar --forzar)" % dest)
                continue
            t0 = time.time()
            NotebookClient(nb, timeout=a.timeout, kernel_name="python3",
                           resources={"metadata": {"path": os.path.join(raiz, "notebooks")}}).execute()
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            nbformat.write(nb, dest)
            print("  ejecutado en %.0f s -> %s" % (time.time() - t0, dest))


if __name__ == "__main__":
    main()
