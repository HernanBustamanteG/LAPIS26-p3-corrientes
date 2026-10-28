"""Observaciones simuladas de las corrientes con LSST (y Gaia como comparacion), para el hito 5.

Supuestos (todos en config.py y en el notebook 06):
  - Poblacion: isocrona PARSEC v1.2S (Bressan+2012; Marigo+2017), 12 Gyr, Z = 0.0002 ([M/H] = -1.89), bandas
    LSST (AB), IMF de Chabrier (2001); archivo de la libreria de ugali (release v1.9.0). Sin polvo.
  - Cada particula de la corriente representa M_* / N_part de masa estelar formada; el numero de estrellas
    que pasan el limite de magnitud se sortea con Poisson y sus magnitudes con la funcion de luminosidad.
  - Footprint: Dec < +5 grados. Profundidad: r < 27 (10 anios). Movimientos propios: r < 24.5, con
    sigma_mu(r) interpolado en log entre 0.2 mas/yr (r = 21) y 1.0 mas/yr (r = 24) a 10 anios, que escala
    como (10 / anios)^1.5. Gaia DR3 para comparar: G < 21 con G ~ r (aproximacion, +-0.3 mag).
  - Distancias fotometricas con error relativo de 7 %. Sin velocidades radiales (LSST no las mide); los polos
    orbitales necesitan un seguimiento espectroscopico (opcion espectro=True: r < 21, sigma_v = 2 km/s).
"""

import os

import numpy as np

from . import config as C


def cargar_isocrona(ruta=None):
    """Tabla de la isocrona: Mini, int_IMF, label y magnitudes absolutas ugrizy."""
    ruta = ruta or os.path.join(C.RAIZ, C.ISOCRONA)
    with open(ruta, encoding="utf-8") as f:
        cab = [ln for ln in f if ln.startswith("#") and "Mini" in ln][0].lstrip("#").split()
    d = np.loadtxt(ruta, comments="#")
    col = {k: i for i, k in enumerate(cab)}
    return {k: d[:, col[k]] for k in ("Mini", "int_IMF", "label", "umag", "gmag", "rmag", "imag", "zmag", "ymag")}


class FuncionLuminosidad:
    """Estrellas por Msun formada con M_r < x, y sorteo de magnitudes, a partir de los pesos de la isocrona."""

    def __init__(self, iso=None, banda="rmag"):
        iso = iso or cargar_isocrona()
        w = np.diff(iso["int_IMF"])                # estrellas por Msun formada en cada tramo de masa
        self.M = 0.5 * (iso[banda][1:] + iso[banda][:-1])
        self.gr = 0.5 * ((iso["gmag"] - iso["rmag"])[1:] + (iso["gmag"] - iso["rmag"])[:-1])
        ok = w > 0
        self.w, self.M, self.gr = w[ok], self.M[ok], self.gr[ok]
        o = np.argsort(self.M)
        self.Ms, self.cw = self.M[o], np.cumsum(self.w[o])
        self._o = o

    def n_mas_brillantes(self, M_lim):
        """Numero de estrellas por Msun formada con M_r < M_lim."""
        return np.interp(M_lim, self.Ms, self.cw, left=0.0, right=self.cw[-1])

    def sortear(self, M_lim, rng):
        """Magnitudes absolutas sorteadas entre las estrellas con M_r < M_lim (una por elemento de M_lim)."""
        tope = self.n_mas_brillantes(M_lim)
        u = rng.uniform(0, 1, len(M_lim)) * tope
        j = np.clip(np.searchsorted(self.cw, u), 0, len(self.Ms) - 1)
        return self.Ms[j], self.gr[self._o][j]


def sigma_pm_lsst(r, anios=10.0):
    """sigma_mu [mas/yr]: interpolacion log-lineal entre los dos puntos de Ivezic+2019 (extrapolada hacia
    r > 24) y piso de 0.2 mas/yr para r < 21 (no se extrapola hacia estrellas brillantes)."""
    (r1, s1), (r2, s2) = C.LSST_PM_PUNTOS
    r = np.maximum(r, r1)
    ls = np.interp(r, [r1, r2], [np.log10(s1), np.log10(s2)], left=np.nan, right=np.nan)
    ext = np.log10(s1) + (np.log10(s2) - np.log10(s1)) * (r - r1) / (r2 - r1)   # extrapolacion lineal en log
    ls = np.where(np.isfinite(ls), ls, ext)
    return 10 ** ls * (10.0 / anios) ** 1.5


def sigma_pm_gaia(G):
    g, s = np.array(C.GAIA_PM_PUNTOS).T
    return 10 ** np.interp(G, g, np.log10(s))


def observar(c, m_estelar, rng, anios=10.0, r_lim=C.LSST_R_LIM_10A, espectro=False, sigma_v=2.0,
             r_espectro=21.0, fl=None, error_dist=C.ERROR_DIST_FOTOMETRICA):
    """Estrellas que LSST veria de una corriente (dict de corrientes.generar). Devuelve dict de arrays."""
    import astropy.units as u
    from . import metricas as Me
    fl = fl or FuncionLuminosidad()
    pos, vel = np.asarray(c["pos"], float), np.asarray(c["vel"], float)
    sky = Me.a_icrs(pos, vel, corregir=False)
    dist = sky.distance.to_value(u.kpc)
    mu = 5 * np.log10(dist * 1e3) - 5
    pie = sky.dec.deg < C.LSST_DEC_MAX
    m_part = m_estelar / len(pos)
    lam = m_part * fl.n_mas_brillantes(r_lim - mu) * pie
    k = rng.poisson(lam)
    idx = np.repeat(np.arange(len(pos)), k)
    out = {"n_particulas": len(pos), "n_en_footprint": int(pie.sum()), "idx": idx}
    if not len(idx):
        out["n"] = 0
        return out
    Mr, gr = fl.sortear(r_lim - mu[idx], rng)
    r = Mr + mu[idx]
    s_l = sigma_pm_lsst(r, anios)
    ok_pm = (r < C.LSST_PM_R_MAX) & (r > C.LSST_R_SATURACION)
    s_g = np.where(r < C.GAIA_G_LIM, sigma_pm_gaia(r), np.nan)
    pmra = sky.pm_ra_cosdec.to_value(u.mas / u.yr)[idx]
    pmde = sky.pm_dec.to_value(u.mas / u.yr)[idx]
    d_obs = dist[idx] * (1 + error_dist * rng.normal(size=len(idx)))
    out.update(n=len(idx), r=r, g=r + gr, ra=sky.ra.deg[idx], dec=sky.dec.deg[idx], dist_true=dist[idx],
               dist_obs=d_obs, pm_ok=ok_pm, sigma_pm=s_l, sigma_pm_gaia=s_g,
               pmra_obs=pmra + s_l * rng.normal(size=len(idx)), pmdec_obs=pmde + s_l * rng.normal(size=len(idx)),
               pmra_true=pmra, pmdec_true=pmde,
               vr_true=sky.radial_velocity.to_value(u.km / u.s)[idx])
    if espectro:
        ok = r < r_espectro
        out["vr_ok"] = ok
        out["vr_obs"] = out["vr_true"] + sigma_v * rng.normal(size=len(idx))
    return out


def a_marco_mw(ra, dec, d, pmra, pmdec, vr):
    """Observables heliocentricos -> posiciones y velocidades en el marco de la MW (Galactocentric v4.0)."""
    import astropy.coordinates as coord
    import astropy.units as u
    from . import metricas as Me
    c = coord.SkyCoord(ra=ra * u.deg, dec=dec * u.deg, distance=d * u.kpc, pm_ra_cosdec=pmra * u.mas / u.yr,
                       pm_dec=pmdec * u.mas / u.yr, radial_velocity=vr * u.km / u.s, frame="icrs")
    g = c.transform_to(Me.marco_galactocentrico())
    return (np.column_stack([g.x.to_value(u.kpc), g.y.to_value(u.kpc), g.z.to_value(u.kpc)]),
            np.column_stack([g.v_x.to_value(u.km / u.s), g.v_y.to_value(u.km / u.s), g.v_z.to_value(u.km / u.s)]))


def metricas_observadas(obs, c, n_inicial, psi_particula, rng, n_boot=30, n_min_pm=30):
    """Metricas desde las estrellas observadas, con su incertidumbre por bootstrap (re-muestreo de estrellas y
    nuevas realizaciones de los errores). Devuelve dict metrica -> (valor, sigma)."""
    from . import metricas as Me
    if obs.get("n", 0) < n_min_pm:
        return {}
    n0 = Me.unit(n_inicial)
    idx = obs["idx"]
    psi = psi_particula[idx]
    res = {}

    def una(sel, pert):
        """sel: indices de estrellas (con repeticion en el bootstrap)."""
        out = {}
        d = obs["dist_true"][sel] * (1 + C.ERROR_DIST_FOTOMETRICA * rng.normal(size=len(sel))) if pert \
            else obs["dist_obs"][sel]
        pmra = obs["pmra_true"][sel] + obs["sigma_pm"][sel] * rng.normal(size=len(sel)) if pert \
            else obs["pmra_obs"][sel]
        pmde = obs["pmdec_true"][sel] + obs["sigma_pm"][sel] * rng.normal(size=len(sel)) if pert \
            else obs["pmdec_obs"][sel]
        vr = obs["vr_true"][sel]
        pos, vel = a_marco_mw(obs["ra"][sel], obs["dec"][sel], d, pmra, pmde, vr)
        nsvd = Me.normal_svd(pos)
        t = Me.angulo(nsvd, n0)
        out["tilt_plano_deg"] = float(min(t, 180 - t))
        okp = obs["pm_ok"][sel]
        if okp.sum() >= n_min_pm:
            cie = Me.a_icrs(pos[okp], vel[okp])
            ncie, pm = Me.vectores_cielo(cie)
            dl = Me.desalineamiento_local(ncie, pm, psi[sel][okp], n_min=10)
            out["desalineamiento_deg"] = float(np.nanmedian(np.abs(dl["dtheta"]))) if np.isfinite(
                dl["dtheta"]).any() else np.nan
        if "vr_ok" in obs:
            oks = obs["vr_ok"][sel] & okp
            if oks.sum() >= n_min_pm:
                vrs = obs["vr_true"][sel][oks] + 2.0 * rng.normal(size=oks.sum()) if pert else obs["vr_obs"][sel][oks]
                p2, v2 = a_marco_mw(obs["ra"][sel][oks], obs["dec"][sel][oks], d[oks], pmra[oks], pmde[oks], vrs)
                L = Me.polos(p2, v2)
                out["tilt_polo_deg"] = float(Me.angulo(Me.polo_medio(L), n0))
                out["dispersion_polos_deg"] = float(np.median(Me.angulo(L, Me.polo_medio(L))))
        return out

    base = una(np.arange(obs["n"]), False)
    boots = [una(rng.integers(0, obs["n"], obs["n"]), True) for _ in range(n_boot)]
    for k, v in base.items():
        b = np.array([x.get(k, np.nan) for x in boots], float)
        res[k] = (v, float(np.nanstd(b)))
    res["n_obs"] = (int(obs["n"]), 0)
    res["n_pm"] = (int(obs["pm_ok"].sum()), 0)
    return res
