"""Corridas largas desde la terminal (o desde un notebook con !python -m ...).

  python -m p3streams.ejecutar --autotest
  python -m p3streams.ejecutar grilla --plan principal --simular
  python -m p3streams.ejecutar grilla --plan principal --correr [--procesos 2] [--carpeta RUTA_PARA_RETOMAR]
  python -m p3streams.ejecutar lsst --catalogo RUTA --simular | --correr
  python -m p3streams.ejecutar planes

Todo se escribe en una carpeta nueva salidas/<plan>_<FECHA>/ (o se retoma la indicada con --carpeta); nada se
pisa. --simular no escribe nada: dice que se haria, cuanto disco y cuanto tiempo.
"""

import argparse
import os
import sys
import time

from . import config as C

# Planes de corrida. La grilla principal usa HEALPix nside = 2 (48 polos, que ya incluyen n y -n: los dos
# sentidos de giro), tres familias de longitud y dos fases en la orbita (0 y 90 grados).
PLANES = {
    "piloto": dict(n_polos=12, polos="fibonacci", sentidos=True, fases=(0.0,), m_lmc=1.8e11,
                   nota="12 polos x 2 sentidos x 3 familias (el 'empezar chico' del enunciado)"),
    "principal": dict(n_polos=2, polos="healpy", sentidos=False, fases=(0.0, 90.0), m_lmc=1.8e11,
                      nota="48 polos HEALPix x 3 familias x 2 fases"),
}
for _m in C.LMC_MASAS:
    PLANES["masa_%.1f" % (_m / 1e11)] = dict(n_polos=1, polos="healpy", sentidos=False, fases=(0.0,), m_lmc=_m,
                                             nota="12 polos HEALPix x 3 familias, M_LMC = %.1e Msun" % _m)

# Planes que separan distancia y longitud (en la grilla principal van juntas: cada familia fija las dos)
PLANES["distancia"] = dict(n_polos=1, polos="healpy", sentidos=False, fases=(0.0,), m_lmc=1.8e11,
                           familias={"r%03d" % r: dict(r_apo=float(r), m_prog=1e7) for r in (30, 45, 70, 100, 150)},
                           nota="12 polos HEALPix x r_apo 30, 45, 70, 100, 150 kpc, 1e7 Msun")
PLANES["longitud"] = dict(n_polos=1, polos="healpy", sentidos=False, fases=(0.0,), m_lmc=1.8e11,
                          familias={"m%s" % k: dict(r_apo=60.0, m_prog=v) for k, v in
                                    (("1e6", 1e6), ("1e7", 1e7), ("1e8", 1e8))},
                          nota="12 polos HEALPix x M_prog 1e6, 1e7, 1e8 Msun a r_apo = 60 kpc")

SEG_POR_CORRIENTE = 35.0     # medido: 17-50 s por progenitor (4 modelos) en un nucleo de Colab / de prueba
MB_POR_CORRIENTE = 0.55


def filas_plan(nombre):
    from . import catalogo as Ca
    p = PLANES[nombre]
    kw = {"familias": p["familias"]} if "familias" in p else {}
    return Ca.grilla(n_polos=p["n_polos"], sentidos=p["sentidos"], fases=p["fases"], polos=p["polos"], **kw)


def cmd_planes(_):
    for k, p in PLANES.items():
        print("%-10s %4d corrientes  %s" % (k, len(filas_plan(k)), p["nota"]))


def cmd_grilla(a):
    from . import catalogo as Ca, potenciales as P, util as U
    filas = filas_plan(a.plan)
    p = PLANES[a.plan]
    car = a.carpeta
    hechas = 0
    if car and os.path.isdir(os.path.join(car, "filas")):
        hechas = len([f for f in filas if os.path.exists(os.path.join(car, "filas", f["id"] + ".json"))])
    falta = len(filas) - hechas
    t_est = falta * SEG_POR_CORRIENTE / max(a.procesos, 1)
    print("Plan %s: %s" % (a.plan, p["nota"]))
    print("  corrientes: %d (hechas %d, por hacer %d); M_LMC = %.2e Msun" % (len(filas), hechas, falta, p["m_lmc"]))
    print("  carpeta: %s" % (car or os.path.join(C.carpeta_salidas(), "%s_<FECHA>" % a.plan)))
    print("  disco ~%.0f MB, memoria < 1 GB por proceso, tiempo ~%.0f min con %d procesos"
          % (falta * MB_POR_CORRIENTE, t_est / 60, a.procesos))
    if not a.correr:
        print("SIMULACION: no se escribio nada. Para correr: --correr")
        return 0
    if not car:
        car = U.carpeta_nueva(a.plan)
        U.metadatos(car, plan=a.plan, parametros={k: v for k, v in p.items()}, n_corrientes=len(filas),
                    filas=filas)
    ruta_sis = os.path.join(car, "sistema.npz")
    if not os.path.exists(ruta_sis):
        t0 = time.time()
        s = P.integrar_sistema(m_lmc=p["m_lmc"])
        s.guardar(ruta_sis)
        print("  sistema MW + LMC integrado en %.0f s" % (time.time() - t0))
    err = Ca.correr_grilla(filas, ruta_sis, car, procesos=a.procesos)
    df = Ca.leer_catalogo(car)
    ruta_csv = os.path.join(car, "catalogo.csv")
    if len(df) == len(filas) and not os.path.exists(ruta_csv):
        df.to_csv(ruta_csv, index=False)
        print("Catalogo completo: %s" % ruta_csv)
    print("FIN %s (%d errores)" % (car, len(err)))
    return 1 if err else 0


def cmd_lsst(a):
    from . import catalogo as Ca, lsst as L, util as U
    df = Ca.leer_catalogo(a.catalogo)
    ids = df["id"].tolist()
    print("Pasada LSST sobre %d corrientes de %s" % (len(ids), a.catalogo))
    print("  M_*/M_prog = %.3g, %s anios, bootstrap %d; ~%.0f min con %d procesos"
          % (a.frac, a.anios, a.n_boot, len(ids) * 7 / max(a.procesos, 1) / 60, a.procesos))
    if not a.correr:
        print("SIMULACION: no se escribio nada. Para correr: --correr")
        return 0
    car = a.carpeta or U.carpeta_nueva("lsst_f%.0e_%da" % (a.frac, a.anios))
    if not a.carpeta:
        U.metadatos(car, catalogo=a.catalogo, frac=a.frac, anios=a.anios, n_boot=a.n_boot)
    err = L.correr(ids, a.catalogo, car, procesos=a.procesos, frac=a.frac, anios=a.anios, n_boot=a.n_boot)
    print("FIN %s (%d errores)" % (car, len(err)))
    return 1 if err else 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m p3streams.ejecutar", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--autotest", action="store_true", help="pruebas del paquete (no escribe nada)")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("planes")
    g = sub.add_parser("grilla")
    g.add_argument("--plan", choices=sorted(PLANES), required=True)
    g.add_argument("--procesos", type=int, default=os.cpu_count() or 1)
    g.add_argument("--carpeta", help="carpeta de una corrida anterior, para retomarla")
    m = g.add_mutually_exclusive_group(required=True)
    m.add_argument("--simular", action="store_true")
    m.add_argument("--correr", action="store_true")
    s = sub.add_parser("lsst")
    s.add_argument("--catalogo", required=True)
    s.add_argument("--frac", type=float, default=C.FRACCION_ESTELAR)
    s.add_argument("--anios", type=float, default=10.0)
    s.add_argument("--n_boot", type=int, default=20)
    s.add_argument("--procesos", type=int, default=os.cpu_count() or 1)
    s.add_argument("--carpeta")
    m = s.add_mutually_exclusive_group(required=True)
    m.add_argument("--simular", action="store_true")
    m.add_argument("--correr", action="store_true")
    a = ap.parse_args(argv)
    if a.autotest:
        from . import autotest
        return 0 if autotest.correr() else 1
    if a.cmd is None:
        ap.print_help()
        return 0
    return {"planes": cmd_planes, "grilla": cmd_grilla, "lsst": cmd_lsst}[a.cmd](a) or 0


if __name__ == "__main__":
    sys.exit(main())
