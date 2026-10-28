"""Pruebas automaticas del paquete (no escriben nada). Uso: python -m p3streams.autotest [--rapido]

Cubren la fisica de cada pieza con casos de respuesta conocida, antes de confiar en una corrida larga.
"""

import sys
import time

import numpy as np


def correr(rapido=False):
    from . import config as C, corrientes as Co, metricas as Me, observar as O, potenciales as P, util as U
    t = U.Pruebas("p3streams")
    t0 = time.time()
    # 1. MW del tutorial
    import astropy.units as u
    mw = P.potencial_mw()
    vc = mw.circular_velocity([8.1, 0, 0] * u.kpc).to_value(u.km / u.s)[0]
    t(200 < vc < 260, "MW del tutorial: v_c(8.1 kpc) = %.1f km/s" % vc)
    # 2. polos y plano
    rng = np.random.default_rng(0)
    phi = rng.uniform(0, 2 * np.pi, 2000)
    pos = np.column_stack([20 * np.cos(phi), 20 * np.sin(phi), 0.1 * rng.normal(size=2000)])
    vel = np.column_stack([-200 * np.sin(phi), 200 * np.cos(phi), np.zeros(2000)])
    t(Me.angulo(Me.polo_medio(Me.polos(pos, vel)), [0, 0, 1]) < 0.5, "polo medio de un anillo en z = 0 es +z")
    n = Me.normal_svd(pos, referencia=[0, 0, 1])
    t(Me.angulo(n, [0, 0, 1]) < 0.5 and abs(Me.grosor(pos, n) - 0.1) < 0.01, "normal SVD y espesor (0.1 kpc)")
    # 3. desalineamiento: corriente sintetica en un gran circulo moviendose a lo largo -> ~0; con PM girado 20 grados -> 20
    ang = np.linspace(-0.6, 0.6, 3000)
    nc = np.column_stack([np.cos(ang), np.sin(ang), np.zeros_like(ang)])
    tg = np.column_stack([-np.sin(ang), np.cos(ang), np.zeros_like(ang)])
    perp = np.cross(nc, tg)
    for gir in (0.0, 20.0):
        pm = np.cos(np.radians(gir)) * tg + np.sin(np.radians(gir)) * perp
        d = Me.desalineamiento_local(nc, pm, ang)
        t(abs(np.nanmedian(np.abs(d["dtheta"])) - gir) < 0.3, "desalineamiento local de una corriente sintetica = %.0f deg" % gir)
    # 4. angulo desenrollado con lead_trail
    lt = np.where(rng.uniform(size=200) < 0.5, 1, -1)
    ps = np.where(lt > 0, rng.uniform(0.1, 5.5, 200), -rng.uniform(0.1, 5.5, 200))
    pos2 = np.column_stack([np.cos(ps), np.sin(ps), np.zeros(200)]) * 30
    psi = Me.angulo_desenrollado(pos2, np.zeros(200), lt, np.array([30.0, 0, 0]), [0, 0, 1])
    t(np.allclose(psi, ps, atol=1e-9), "angulo desenrollado hasta una vuelta por brazo")
    # 5. f_reflex
    res = {m: {"todo": {"x": v}} for m, v in zip("ABCD", (1.0, 4.0, 2.0, 3.5))}
    p = Me.perturbaciones(res, "x")
    t(abs(p["f_reflex"] - 0.75) < 1e-12 and Me.clase(p["f_reflex"]) == "reflex", "f_reflex = 3/(3+1) = 0.75 -> reflex")
    # 6. LSST
    fl = O.FuncionLuminosidad()
    t(1.0 < fl.cw[-1] < 2.5 and -4 < fl.Ms.min() < -2, "isocrona PARSEC: %.2f estrellas por Msun, M_r min %.1f"
      % (fl.cw[-1], fl.Ms.min()))
    t(abs(O.sigma_pm_lsst(21.0) - 0.2) < 1e-9 and abs(O.sigma_pm_lsst(24.0) - 1.0) < 1e-9
      and abs(O.sigma_pm_lsst(24.0, 3.0) / O.sigma_pm_lsst(24.0) - (10 / 3) ** 1.5) < 1e-9,
      "sigma_mu LSST: 0.2 (r=21), 1.0 (r=24) mas/yr a 10 anios y escala t^-1.5")
    # 7. sistema MW + LMC, campo uniforme y modelo D contra el marco inercial
    if not rapido:
        s = P.integrar_sistema(t_atras=3000.0)
        e = P.validar_campo(s, radios=(10, 100, 200), n_t=10)
        t(e < 1e-3, "campo uniforme = -a_MW (error relativo %.1e a <= 200 kpc)" % e)
        dx, *_ = P.validar_inercial(s, t0=-1000.0)
        t(dx < 0.01, "modelo D = marco inercial para una particula de prueba (|dx| max %.1e kpc en 1 Gyr)" % dx)
        mods = P.modelos(s)
        x0, v0 = Co.condiciones_iniciales([0, -1, 0], 100, 0.5, 0, mw)
        o = Co.resumen_orbita(Co.orbita(mods["A"], x0, v0, -3000))
        t(abs(o["peri_kpc"] - 27) < 2 and abs(o["ecc"] - 0.6) < 0.05, "f = 0.5 a 100 kpc: peri %.1f kpc, e = %.2f "
          "(enunciado: ~27 kpc, ~0.6)" % (o["peri_kpc"], o["ecc"]))
        ca = Co.generar(mods["A"], x0, v0, m_prog=1e6, t_inicio=-1000, release_every=4)
        cb = Co.generar(mods["A"], x0, v0, m_prog=1e6, t_inicio=-1000, release_every=4)
        t(np.array_equal(ca["pos"], cb["pos"]), "misma semilla -> misma corriente")
        r, _ = Me.medir(ca, [0, -1, 0])
        t(r["todo"]["tilt_polo_deg"] < 2 and r["todo"]["desalineamiento_deg"] < 3,
          "modelo A: polo e inclinacion ~0 (%.2f y %.2f deg)" % (r["todo"]["tilt_polo_deg"],
                                                              r["todo"]["desalineamiento_deg"]))
    print("Tiempo: %.0f s" % (time.time() - t0))
    return t.fin()


if __name__ == "__main__":
    sys.exit(0 if correr("--rapido" in sys.argv) else 1)
