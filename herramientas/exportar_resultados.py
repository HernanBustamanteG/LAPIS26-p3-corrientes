"""Copia las tablas de las corridas a resultados/ (CSV) y escribe resultados/PROCEDENCIA.md con las carpetas de
origen, los metadatos de cada corrida y el sha256 de cada CSV. No pisa nada: si un CSV ya existe, se detiene.

  python herramientas/exportar_resultados.py --salidas RUTA_DE_SALIDAS [--simular]
"""

import argparse
import glob
import hashlib
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)


def ultima(base, prefijo):
    hay = sorted(glob.glob(os.path.join(base, prefijo + "_2*")))
    return hay[-1] if hay else None


def main():
    from p3streams import analisis as An, catalogo as Ca, lsst as L, resultados as R, util as U
    ap = argparse.ArgumentParser()
    ap.add_argument("--salidas", required=True)
    ap.add_argument("--simular", action="store_true")
    a = ap.parse_args()
    dest = os.path.join(RAIZ, "resultados")
    tareas = []
    for plan in ("piloto", "principal", "distancia", "longitud", "masa_1.0", "masa_1.5", "masa_1.8", "masa_2.5"):
        car = ultima(a.salidas, plan) or (ultima(a.salidas, "catalogo_piloto_M1.8") if plan == "piloto" else None)
        if car:
            tareas.append(("catalogo_" + plan, car, "catalogo"))
    car_l = ultima(a.salidas, "lsst_f1e-02_10a")
    if car_l:
        tareas.append(("lsst_principal", car_l, "lsst"))
    car_p = ultima(a.salidas, "principal")
    if car_p:
        tareas.append(("por_radio_principal", car_p, "por_radio"))
    lineas = ["# Procedencia de las tablas de resultados/", "",
              "Generadas con `herramientas/exportar_resultados.py` el %s." % U.ahora(), "",
              "| archivo | filas | carpeta de origen (corrida) | sha256 |", "|---|---|---|---|"]
    for nombre, car, tipo in tareas:
        ruta = os.path.join(dest, nombre + ".csv")
        print("%-26s <- %s%s" % (nombre, car, "  (YA EXISTE: se omite)" if os.path.exists(ruta) else ""))
        if a.simular or os.path.exists(ruta):
            continue
        if tipo == "catalogo":
            df = Ca.leer_catalogo(car)
        elif tipo == "lsst":
            df = L.leer(car)
        else:
            df = An.por_radio(car)
        R.exportar(df, nombre, dest)
    if a.simular:
        print("SIMULACION: no se escribio nada.")
        return
    for nombre, car, tipo in tareas:
        ruta = os.path.join(dest, nombre + ".csv")
        h = hashlib.sha256(open(ruta, "rb").read()).hexdigest()
        n = sum(1 for _ in open(ruta, encoding="utf-8")) - 1
        lineas.append("| %s.csv | %d | `%s` | `%s` |" % (nombre, n, os.path.basename(car), h[:16]))
    lineas += ["", "## Metadatos de cada corrida", ""]
    for nombre, car, tipo in tareas:
        m = os.path.join(car, "metadatos.json")
        if os.path.exists(m) and tipo != "por_radio":
            meta = json.load(open(m, encoding="utf-8"))
            meta.pop("filas", None)
            lineas += ["### %s" % nombre, "```json", json.dumps(meta, indent=1, ensure_ascii=False)[:3000], "```", ""]
    lineas += ["`por_radio_principal.csv`: `p3streams.analisis.por_radio` sobre las corrientes guardadas de la corrida "
               "principal (cambio del polo estrella a estrella respecto de la misma estrella en el modelo A)."]
    ruta = os.path.join(dest, "PROCEDENCIA.md")
    if os.path.exists(ruta):
        os.rename(ruta, ruta.replace(".md", "_anterior_%s.md" % U.ahora().replace(":", "")))
    with open(ruta, "x", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")
    print("Escrito", ruta)


if __name__ == "__main__":
    main()
