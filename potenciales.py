"""Potenciales de la MW y la LMC, el sistema MW + LMC vivo con friccion dinamica, y los cuatro modelos A-D.

La MW, la LMC y la friccion dinamica siguen al pie de la letra dynamical_friction_MWLMC_tutorial.ipynb
(J. N. Garavito-Camargo, LAPIS26, licencia MIT). Los cuatro modelos siguen project_3_streams.md:

  A  MW aislada                    MW
  B  solo reflejo                  MW + campo uniforme -a_MW(t)
  C  solo tiron directo            MW + LMC movil
  D  MW + LMC                      MW + LMC movil + campo uniforme -a_MW(t)

todos escritos en el marco de la MW (centro de la MW en el origen). gala no tiene un potencial de campo
uniforme: como sugiere el enunciado, se usa una masa puntual (Kepler) muy lejana y muy masiva cuya posicion y
masa dependen del tiempo, de modo que su aceleracion en la region de interes es -a_MW(t).
"""

import numpy as np

from . import config as C

_G = None


def G():
    """G en unidades galactic (kpc^3 / Msun / Myr^2)."""
    global _G
    if _G is None:
        import astropy.units as u
        from astropy.constants import G as Gc
        _G = Gc.to_value(u.kpc ** 3 / u.Msun / u.Myr ** 2)
    return _G


def KMS():
    """1 km/s en kpc/Myr."""
    return 1.0 / 977.792221


def componentes_mw():
    """dict nombre -> potencial de gala (se agregan uno a uno a cada CCompositePotential)."""
    import astropy.units as u
    import gala.potential as gp
    from gala.units import galactic
    return {
        "disco": gp.MN3ExponentialDiskPotential(units=galactic, m=C.MW_DISCO["m"] * u.Msun,
                                                h_R=C.MW_DISCO["h_R"] * u.kpc, h_z=C.MW_DISCO["h_z"] * u.kpc),
        "bulbo": gp.HernquistPotential(units=galactic, m=C.MW_BULBO["m"] * u.Msun, c=C.MW_BULBO["c"] * u.kpc),
        "nucleo": gp.HernquistPotential(units=galactic, m=C.MW_NUCLEO["m"] * u.Msun, c=C.MW_NUCLEO["c"] * u.kpc),
        "halo": gp.LeeSutoTriaxialNFWPotential(units=galactic, v_c=C.MW_HALO["v_c"] * u.km / u.s,
                                               r_s=C.MW_HALO["r_s"] * u.kpc, a=C.MW_HALO["a"],
                                               b=C.MW_HALO["b"], c=C.MW_HALO["c"]),
    }


def potencial_mw():
    import gala.potential as gp
    p = gp.CCompositePotential()
    for k, v in componentes_mw().items():
        p[k] = v
    return p


def potencial_lmc(m=C.LMC_M, a=C.LMC_A):
    import astropy.units as u
    import gala.potential as gp
    from gala.units import galactic
    return gp.HernquistPotential(units=galactic, m=m * u.Msun, c=a * u.kpc)


def sigma_nfw(vmax, rs, r):
    """Zentner & Bullock (2003): dispersion isotropa de un NFW, en las unidades de vmax."""
    x = r / rs
    return vmax * 1.4393 * x ** 0.354 / (1.0 + 1.1756 * x ** 0.725)


def ln_lambda(r, L=0.0, C=1.22, a=20.0, alpha=1.0, form="VdM"):
    if form == "Hashimoto":
        return np.maximum(0.0, alpha * np.log(r / (1.4 * a)))
    arg = np.log(r / (C * a))
    return np.maximum(L, np.where(arg > 0, np.abs(arg) ** alpha, 0.0))


def factor_velocidad(X):
    from scipy.special import erf
    return erf(X) - 2 * X / np.sqrt(np.pi) * np.exp(-X ** 2)


def aceleracion_df(x_rel, v_rel, m_sat, mw, vmax, rs, lnl):
    """Chandrasekhar (Binney & Tremaine 2008, ec. 8.7); x_rel [kpc], v_rel [kpc/Myr] -> kpc/Myr^2."""
    import astropy.units as u
    r, v = np.linalg.norm(x_rel), np.linalg.norm(v_rel)
    rho = mw.density(x_rel * u.kpc).to_value(u.Msun / u.kpc ** 3)[0]
    X = v / (np.sqrt(2) * sigma_nfw(vmax, rs, r))
    return -4 * np.pi * G() ** 2 * m_sat * rho * ln_lambda(r, **lnl) * factor_velocidad(X) / v ** 3 * v_rel


class Sistema:
    """Trayectorias del centro de la MW y de la LMC (marco de simulacion), con t creciente en Myr."""

    def __init__(self, t, x_mw, v_mw, x_lmc, v_lmc, m_lmc, a_lmc, info=None):
        self.t, self.x_mw, self.v_mw, self.x_lmc, self.v_lmc = map(np.asarray, (t, x_mw, v_mw, x_lmc, v_lmc))
        self.m_lmc, self.a_lmc, self.info = float(m_lmc), float(a_lmc), info or {}
        from scipy.interpolate import CubicSpline
        self._x_mw = CubicSpline(self.t, self.x_mw, axis=0)
        self._v_mw = CubicSpline(self.t, self.v_mw, axis=0)
        self._x_lmc = CubicSpline(self.t, self.x_lmc, axis=0)
        self._lmc = potencial_lmc(self.m_lmc, self.a_lmc)

    # posiciones en el marco de la MW
    def x_lmc_rel(self, t):
        return self._x_lmc(t) - self._x_mw(t)

    def a_mw(self, t):
        """Aceleracion del centro de la MW producida por la LMC [kpc/Myr^2], (n, 3)."""
        t = np.atleast_1d(t)
        d = (self._x_mw(t) - self._x_lmc(t)).T
        return self._lmc.acceleration(d).decompose(_galactic()).value.T

    def d_lmc(self, t=None):
        t = self.t if t is None else t
        return np.linalg.norm(self.x_lmc_rel(t), axis=-1)

    def guardar(self, ruta):
        with open(ruta, "xb") as f:
            np.savez_compressed(f, t=self.t, x_mw=self.x_mw, v_mw=self.v_mw, x_lmc=self.x_lmc, v_lmc=self.v_lmc,
                                m_lmc=self.m_lmc, a_lmc=self.a_lmc)

    @classmethod
    def cargar(cls, ruta):
        d = np.load(ruta)
        return cls(d["t"], d["x_mw"], d["v_mw"], d["x_lmc"], d["v_lmc"], d["m_lmc"], d["a_lmc"])


def _galactic():
    from gala.units import galactic
    return galactic


def integrar_sistema(m_lmc=C.LMC_M, a_lmc=C.LMC_A, t_atras=C.T_ATRAS, dt=C.DT_SISTEMA, friccion=True):
    """MW y LMC como dos cuerpos con sus potenciales (gd.DirectNBody) + friccion dinamica sobre la LMC,
    integrados hacia atras desde hoy con leapfrog (tutorial, sec. 4b). Devuelve un Sistema con t creciente."""
    import astropy.units as u
    import gala.dynamics as gd
    import gala.integrate as gi
    galactic = _galactic()
    mw, lmc = potencial_mw(), potencial_lmc(m_lmc, a_lmc)
    r = np.logspace(-1, np.log10(300), 400)
    vc = mw.circular_velocity(np.array([r, 0 * r, 0 * r]) * u.kpc).to_value(u.kpc / u.Myr)
    vmax, rs = vc.max(), C.MW_HALO["r_s"]
    lnl = dict(a=a_lmc, **C.DF_LNL)
    w0 = gd.combine((gd.PhaseSpacePosition(pos=[0, 0, 0] * u.kpc, vel=[0, 0, 0] * u.km / u.s),
                     gd.PhaseSpacePosition(pos=C.LMC_X0 * u.kpc, vel=C.LMC_V0 * u.km / u.s)))
    nbody = gd.DirectNBody(w0, particle_potentials=[mw, lmc], units=galactic)

    def F(t, w, nb):
        nb.w0 = gd.PhaseSpacePosition.from_w(w, units=nb.units)
        wdot = np.zeros_like(w)
        wdot[:3] = w[3:]
        wdot[3:] = nb._nbody_acceleration()
        if friccion:
            wdot[3:, 1] += aceleracion_df(w[:3, 1] - w[:3, 0], w[3:, 1] - w[3:, 0], m_lmc, mw, vmax, rs, lnl)
        return wdot

    integ = gi.LeapfrogIntegrator(F, func_args=(nbody,), func_units=galactic, progress=False)
    orb = integ(w0, dt=-dt * u.Myr, n_steps=int(round(t_atras / dt)))
    t = orb.t.to_value(u.Myr)[::-1]
    x = orb.xyz.to_value(u.kpc)[:, ::-1]
    v = orb.v_xyz.to_value(u.kpc / u.Myr)[:, ::-1]
    return Sistema(t, x[:, :, 0].T, v[:, :, 0].T, x[:, :, 1].T, v[:, :, 1].T, m_lmc, a_lmc,
                   info=dict(friccion=friccion, dt=dt, lnL=lnl, vmax_kpc_myr=vmax))


def nudos(sis, dt=C.DT_NUDOS):
    t = np.arange(sis.t[0], sis.t[-1] + 1e-9, dt)
    if t[-1] < sis.t[-1]:
        t = np.append(t, sis.t[-1])
    return t


def lmc_movil(sis, dt=C.DT_NUDOS):
    """La LMC en el marco de la MW: Hernquist con origen x_LMC(t) - x_MW(t)."""
    import astropy.units as u
    import gala.potential as gp
    tk = nudos(sis, dt)
    return gp.TimeInterpolatedPotential(gp.HernquistPotential, tk * u.Myr, m=sis.m_lmc * u.Msun,
                                        c=sis.a_lmc * u.kpc, origin=np.ascontiguousarray(sis.x_lmc_rel(tk)) * u.kpc,
                                        units=_galactic())


def campo_uniforme(sis, dt=C.DT_NUDOS, d=C.D_CAMPO):
    """Fuerza ficticia -a_MW(t): Kepler de masa |a| d^2 / G ubicada en -d a_hat (su tiron en el origen es -a_MW).
    El error relativo en |x| ~ r es ~ 2 r / d (2e-4 a 100 kpc con d = 1e6 kpc)."""
    import astropy.units as u
    import gala.potential as gp
    tk = nudos(sis, dt)
    a = sis.a_mw(tk)
    na = np.linalg.norm(a, axis=1)
    origen = np.ascontiguousarray(-d * a / na[:, None])
    return gp.TimeInterpolatedPotential(gp.KeplerPotential, tk * u.Myr, m=np.ascontiguousarray(na * d * d / G()) * u.Msun,
                                        origin=origen * u.kpc, units=_galactic())


MODELOS = {"A": "MW isolated", "B": "reflex only", "C": "direct pull only", "D": "MW + LMC"}


def modelo(nombre, sis=None, dt=C.DT_NUDOS):
    """CCompositePotential del modelo A, B, C o D."""
    import gala.potential as gp
    p = gp.CCompositePotential()
    for k, v in componentes_mw().items():
        p[k] = v
    if nombre in ("C", "D"):
        p["lmc"] = lmc_movil(sis, dt)
    if nombre in ("B", "D"):
        p["reflejo"] = campo_uniforme(sis, dt)
    return p


def modelos(sis, dt=C.DT_NUDOS):
    return {m: modelo(m, sis, dt) for m in "ABCD"}


def validar_campo(sis, radios=(10, 50, 100, 200), n_t=40):
    """Error relativo maximo entre la aceleracion de la pieza 'reflejo' y -a_MW(t), a varios radios y tiempos."""
    import astropy.units as u
    cu = campo_uniforme(sis)
    rng = np.random.default_rng(0)
    ts = np.linspace(sis.t[0] + 10, sis.t[-1] - 1, n_t)
    peor = 0.0
    for r in radios:
        dirs = rng.normal(size=(8, 3))
        dirs /= np.linalg.norm(dirs, axis=1)[:, None]
        for t in ts:
            acc = cu.acceleration((r * dirs).T * u.kpc, t=t * u.Myr).decompose(_galactic()).value.T
            obj = -sis.a_mw(t)[0]
            peor = max(peor, np.max(np.linalg.norm(acc - obj, axis=1)) / np.linalg.norm(obj))
    return peor


def validar_inercial(sis, x0=(50.0, 0.0, 0.0), v_kms=None, t0=-4000.0, dt=1.0):
    """Una particula de prueba integrada en el modelo D (marco MW) y en el marco inercial con la MW y la LMC
    en movimiento (tutorial, sec. 5). Devuelve (max |dx| kpc, orbita D relativa, orbita inercial relativa)."""
    import astropy.units as u
    import gala.dynamics as gd
    import gala.integrate as gi
    import gala.potential as gp
    galactic = _galactic()
    mw, lmc = potencial_mw(), potencial_lmc(sis.m_lmc, sis.a_lmc)
    x0 = np.asarray(x0, float)
    if v_kms is None:
        vc = mw.circular_velocity(x0[:, None] * u.kpc).to_value(u.kpc / u.Myr)[0]
        v0 = np.array([0.0, 0.0, vc])
    else:
        v0 = np.asarray(v_kms, float) * KMS()
    n = int(round(-t0 / dt))

    def F_in(t, w):
        x = w[:3]
        wd = np.zeros_like(w)
        wd[:3] = w[3:]
        wd[3:] = (mw.acceleration(x - sis._x_mw(t)[:, None]) +
                  lmc.acceleration(x - sis._x_lmc(t)[:, None])).decompose(galactic).value
        return wd

    w_in = gd.PhaseSpacePosition(pos=(x0 + sis._x_mw(t0)) * u.kpc, vel=(v0 + sis._v_mw(t0)) * u.kpc / u.Myr)
    o_in = gi.DOPRI853Integrator(F_in, func_units=galactic, progress=False)(w_in, dt=dt * u.Myr, n_steps=n,
                                                                              t1=t0 * u.Myr)
    t = o_in.t.to_value(u.Myr)
    rel_in = o_in.xyz.to_value(u.kpc).reshape(3, -1).T - sis._x_mw(t)
    H = gp.Hamiltonian(modelo("D", sis))
    o_d = H.integrate_orbit(gd.PhaseSpacePosition(pos=x0 * u.kpc, vel=v0 * u.kpc / u.Myr), dt=dt * u.Myr,
                            n_steps=n, t1=t0 * u.Myr, Integrator=gi.DOPRI853Integrator)
    rel_d = o_d.xyz.to_value(u.kpc).reshape(3, -1).T
    return float(np.max(np.linalg.norm(rel_d - rel_in, axis=1))), t, rel_d, rel_in


def cobertura(sis, t_inicio):
    """True si el rango de los potenciales interpolados cubre [t_inicio, 0] (fuera de el gala devuelve NaN)."""
    return sis.t[0] <= t_inicio and sis.t[-1] >= 0.0
