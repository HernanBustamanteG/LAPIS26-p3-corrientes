"""Piezas comunes para construir los notebooks (nbformat). Uso: python herramientas/construir_notebooks.py"""

import nbformat as nbf

USUARIO = "HernanBustamanteG"
REPO = "lapis26-p3-corrientes"


def badge(nombre):
    url = "https://colab.research.google.com/github/%s/%s/blob/main/notebooks/%s" % (USUARIO, REPO, nombre)
    return "[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](%s)" % url


SETUP = '''# Celda 1: entorno. En Colab clona el repositorio, instala versiones fijas y monta Google Drive (las salidas
# quedan en MyDrive/lapis26_p3/salidas). Si numpy cambia de version, la sesion se reinicia UNA vez:
# vuelve a ejecutar esta celda. En una maquina propia solo comprueba versiones.
import os, sys, subprocess
REPO_URL = "https://github.com/%s/%s.git"
USAR_DRIVE = True
if "google.colab" in sys.modules:
    RAIZ = "/content/%s"
    if not os.path.isdir(RAIZ):
        subprocess.run(["git", "clone", "-q", REPO_URL, RAIZ], check=True)
else:
    RAIZ = os.path.abspath("..") if os.path.basename(os.getcwd()) == "notebooks" else os.getcwd()
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
from p3streams import entorno
if entorno.en_colab():
    entorno.preparar_colab(RAIZ, montar_drive=USAR_DRIVE)
entorno.resumen();''' % (USUARIO, REPO, REPO)


def salidas(prefijo):
    return '''import warnings
warnings.filterwarnings("ignore", category=UserWarning)
import numpy as np, pandas as pd
warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)
import matplotlib.pyplot as plt
from p3streams import config as C, util as U, estilo as E
E.usar()
SAL = U.carpeta_nueva("%s")          # carpeta nueva de este notebook (nada se pisa)
FUENTE = "notebooks/%s.ipynb, p3streams " + C.VERSION + ", " + U.ahora()
print("Salidas de este notebook:", SAL)''' % (prefijo, prefijo)


def guardar_fig(var, archivo, pie, pdf=True):
    return '''PIE = %r
E.guardar(%s, os.path.join(SAL, %r), PIE, FUENTE, pdf=%s)
plt.show()
print("Figura:", %r, "\\n" + PIE)''' % (pie, var, archivo, pdf, archivo)


def notebook(celdas, nombre):
    nb = nbf.v4.new_notebook()
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nb.metadata["language_info"] = {"name": "python"}
    nb.metadata["colab"] = {"provenance": [], "name": nombre}
    for tipo, txt in celdas:
        nb.cells.append(nbf.v4.new_markdown_cell(txt) if tipo == "md" else nbf.v4.new_code_cell(txt))
    return nb
