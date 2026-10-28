"""Progenitores (polo, fase, apocentro, excentricidad) y corrientes simuladas con gala (FardalStreamDF).

Parametrizacion de project_3_streams.md, "How to explore different stream orbits":
  x0 = r_apo u(psi),   v0 = f v_c(r_apo) (n x u(psi)),   con n el polo orbital inicial.
Las condiciones iniciales se fijan en el pasado (t_start) y son las mismas en los cuatro modelos, igual que la
semilla: las diferencias entre modelos vienen solo del potencial.
"""

import numpy as np

from . import config as C


def polos_fibonacci(n):
    """n vectores unitarios casi uniformes sobre la esfera (espiral de Fibonacci)."""
    i = np.arange(n) + 0.5
    z = 1 - 2 * i / n
    phi = np.pi * (1 + 5 ** 0.5) * i
    r = np.sqrt(1 - z * z)
    return np.column_stack([r * np.cos(phi), r * np.sin(phi), z])


def polos_healpy(nside=2):
    """Centros de los pixeles HEALPix (nside = 2 -> 48 direcciones, que incluyen n y -n)."""
    import healpy as hp
    return np.array(hp.pix2vec(nside, np.arange(hp.nside2npix(nside)))).T


def base_plano(n):
    """(u0, w0): base ortonormal del plano perpendicular a n (u0 en la direccion de z x n, o x si n ~ z)."""
    n = np.asarray(n, float) / np.linalg.norm(n)
    ref = np.array([0.0, 0.0, 1.0]) if abs(n[2]) < 0.95 else np.array([1.0, 0.0, 0.0])
    u0 = np.cross(ref, n)
    u0 /= np.linalg.norm(u0)
    return u0, np.cross(n, u0)


def condiciones_iniciales(n, r_apo, f=C.F_TANG, psi_deg=0.0, mw=None):
    """x0 [kpc] y v0 [km/s] de un progenitor en el apocentro, con velocidad tangencial f v_c(r_apo)."""
    import astropy.units as u
    from . import potenciales as P
    mw = mw or P.potencial_mw()
    n = np.asarray(n, float) / np.linalg.norm(n)
    u0, w0 = base_plano(n)
    psi = np.radians(psi_deg)
    uh = np.cos(psi) * u0 + np.sin(psi) * w0
    x0 = r_apo * uh
    vc = mw.circular_velocity(x0[:, None] * u.kpc).to_value(u.km / u.s)[0]
    return x0, f * vc * np.cross(n, uh)


def orbita(potencial, x0, v0_kms, t_inicio=-C.T_START, dt=C.DT_CORRIENTE):
    """Orbita del progenitor de t_inicio a 0 en un potencial (DOP853)."""
    import astropy.units as u
    import gala.dynamics as gd
    import gala.integrate as gi
    import gala.potential as gp
    w0 = gd.PhaseSpacePosition(pos=np.asarray(x0) * u.kpc, vel=np.asarray(v0_kms) * u.km / u.s)
    return gp.Hamiltonian(potencial).integrate_orbit(w0, dt=dt * u.Myr, n_steps=int(round(-t_inicio / dt)),
                                                    t1=t_inicio * u.Myr, Integrator=gi.DOPRI853Integrator)


def resumen_orbita(orb):
    """pericentro, apocentro, excentricidad (de la orbita completa) y periodo radial estimado."""
    import astropy.units as u
    r = np.linalg.norm(orb.xyz.to_value(u.kpc), axis=0).ravel()
    t = orb.t.to_value(u.Myr)
    peri, apo = float(r.min()), float(r.max())
    # periodo radial: tiempo medio entre maximos locales de r (apocentros)
    i = np.where((r[1:-1] > r[:-2]) & (r[1:-1] >= r[2:]))[0] + 1
    per = float(np.mean(np.diff(t[i]))) if len(i) >= 2 else np.nan
    return dict(peri_kpc=peri, apo_kpc=apo, ecc=(apo - peri) / (apo + peri), periodo_radial_Myr=per)


def acercamiento_lmc(orb, sis):
    """Distancia minima progenitor - LMC [kpc] y su tiempo [Myr], en el marco de la MW."""
    import astropy.units as u
    t = orb.t.to_value(u.Myr)
    x = orb.xyz.to_value(u.kpc).T
    d = np.linalg.norm(x - sis.x_lmc_rel(t), axis=1)
    i = int(np.argmin(d))
    return float(d[i]), float(t[i])


def generar(potencial, x0, v0_kms, m_prog=C.M_PROG, t_inicio=-C.T_START, dt=C.DT_CORRIENTE,
            release_every=C.RELEASE_EVERY, n_particles=C.N_PARTICULAS, semilla=C.SEMILLA):
    """Corriente de hoy formada desde t_inicio con FardalStreamDF (gala_modified). Devuelve dict con arrays
    float32: pos [kpc], vel [km/s], release_time [Myr], lead_trail (+1 lider, -1 de cola), y el progenitor hoy."""
    import astropy.units as u
    import gala.dynamics as gd
    import gala.potential as gp
    from gala.dynamics import mockstream as ms
    df = ms.FardalStreamDF(gala_modified=True, random_state=np.random.RandomState(semilla))
    gen = ms.MockStreamGenerator(df, gp.Hamiltonian(potencial))
    w0 = gd.PhaseSpacePosition(pos=np.asarray(x0) * u.kpc, vel=np.asarray(v0_kms) * u.km / u.s)
    st, prog = gen.run(w0, m_prog * u.Msun, dt=dt * u.Myr, n_steps=int(round(-t_inicio / dt)),
                       t1=t_inicio * u.Myr, release_every=release_every, n_particles=n_particles)
    lt = np.asarray(st.lead_trail)
    lt = np.where(np.char.lower(lt.astype(str)) == "l", 1, -1).astype(np.int8) if lt.dtype.kind in "US" \
        else np.where(lt > 0, 1, -1).astype(np.int8)
    return dict(pos=st.xyz.to_value(u.kpc).T.astype(np.float32),
                vel=st.v_xyz.to_value(u.km / u.s).T.astype(np.float32),
                release_time=np.asarray(st.release_time.to_value(u.Myr), np.float32),
                lead_trail=lt,
                prog_pos=prog.xyz.to_value(u.kpc).reshape(3).astype(np.float64),
                prog_vel=prog.v_xyz.to_value(u.km / u.s).reshape(3).astype(np.float64))


def guardar(c, ruta, **meta):
    with open(ruta, "xb") as f:
        np.savez_compressed(f, **c, **{k: np.asarray(v) for k, v in meta.items()})


def cargar(ruta):
    d = np.load(ruta, allow_pickle=False)
    return {k: d[k] for k in d.files}
