"""Metricas de la perturbacion (project_3_streams.md, "Metrics of the perturbation").

  1. Desalineamiento del movimiento propio, visto desde el Sol y corregido por el movimiento solar:
       dtheta = arctan(mu_phi2 / mu_phi1) - arctan(dphi2 / dphi1)
     Se calcula en un marco LOCAL de la corriente: en cada tramo, e1 es la direccion de la traza en el cielo y
     e2 = n x e1; asi dphi2/dphi1 = 0 y dtheta = arctan(mu_2 / mu_1). Es la misma definicion que en coordenadas
     (phi1, phi2) de un gran circulo, pero no se rompe cuando la corriente da mas de una vuelta o se curva.
     Tambien esta la version literal en GreatCircleICRSFrame (para corrientes de <= 1 vuelta y para figuras).
  2. Polos orbitales: L = x x v / |x x v| de cada estrella en el marco de la MW; polo medio, dispersion y cambio
     a lo largo de la corriente.
  3. Inclinacion del plano: angulo entre el polo medio de hoy y el polo inicial, y entre el polo inicial y la
     normal del plano que mejor ajusta las posiciones (SVD; el plano pasa por el centro de la MW).
Estadistica robusta (medianas), como recomienda el enunciado.
"""

import numpy as np

from . import config as C

METRICAS = ("desalineamiento_deg", "dispersion_polos_deg", "tilt_polo_deg", "tilt_plano_deg", "grosor_kpc",
            "tilt_polos_mediana_deg")
PARTES = ("todo", "lider", "cola", "vieja", "joven")


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def angulo(a, b):
    """Angulo en grados entre vectores (o filas de vectores)."""
    return np.degrees(np.arccos(np.clip(np.sum(unit(a) * unit(b), axis=-1), -1.0, 1.0)))


def mad(x):
    x = np.asarray(x, float)
    return 1.4826 * np.median(np.abs(x - np.median(x)))


def polos(pos, vel):
    return unit(np.cross(pos, vel))


def polo_medio(L):
    return unit(np.mean(L, axis=0))


def normal_svd(pos, referencia=None):
    """Normal del plano por el origen que mejor ajusta las posiciones (vector singular de menor valor)."""
    _, _, vt = np.linalg.svd(np.asarray(pos, float), full_matrices=False)
    n = vt[-1]
    if referencia is not None and np.dot(n, referencia) < 0:
        n = -n
    return n


def grosor(pos, n):
    """Espesor fuera del plano: 1.4826 MAD de la distancia al plano de normal n [kpc]."""
    return float(mad(pos @ unit(n)))


def angulo_desenrollado(pos, release_time, lead_trail, prog_pos, n_plano):
    """Angulo orbital [rad] de cada estrella respecto del progenitor, en el plano de normal n_plano (el polo
    medio: el sentido de giro es +), desenrollado con la etiqueta lead_trail como en stream_evolution.ipynb:
    las estrellas lideres van en [0, 2 pi) y las de cola en (-2 pi, 0]. Mide hasta una vuelta por brazo, es
    decir hasta dos vueltas en total (el rango del enunciado). release_time no se usa (se deja por simetria)."""
    n = unit(n_plano)
    e1 = unit(prog_pos - np.dot(prog_pos, n) * n)
    e2 = np.cross(n, e1)
    psi = np.arctan2(pos @ e2, pos @ e1)
    psi = np.where((lead_trail == 1) & (psi < 0), psi + 2 * np.pi, psi)
    psi = np.where((lead_trail == -1) & (psi > 0), psi - 2 * np.pi, psi)
    return psi


def longitud_vueltas(psi, p=(2, 98)):
    lo, hi = np.nanpercentile(psi, p)
    return float((hi - lo) / (2 * np.pi))


def marco_galactocentrico():
    import astropy.coordinates as coord
    import astropy.units as u
    return coord.Galactocentric(galcen_distance=C.SOL_R * u.kpc, z_sun=C.SOL_Z * u.kpc,
                                galcen_v_sun=coord.CartesianDifferential(list(C.SOL_V) * u.km / u.s))


def a_icrs(pos, vel_kms, corregir=True):
    """Posiciones [kpc] y velocidades [km/s] en el marco de la MW -> ICRS (ra, dec, distancia, pm, v_r),
    con el movimiento propio corregido por el movimiento del Sol (gala.coordinates.reflex_correct)."""
    import astropy.coordinates as coord
    import astropy.units as u
    gc = marco_galactocentrico()
    c = coord.SkyCoord(x=pos[:, 0] * u.kpc, y=pos[:, 1] * u.kpc, z=pos[:, 2] * u.kpc,
                       v_x=vel_kms[:, 0] * u.km / u.s, v_y=vel_kms[:, 1] * u.km / u.s,
                       v_z=vel_kms[:, 2] * u.km / u.s, frame=gc).transform_to(coord.ICRS())
    if corregir:
        import gala.coordinates as gcoord
        c = gcoord.reflex_correct(c, gc)
    return c


def vectores_cielo(c):
    """Vector unitario de cada estrella (ICRS) y su movimiento propio como vector 3D tangente [mas/yr]."""
    import astropy.units as u
    ra, dec = c.ra.to_value(u.rad), c.dec.to_value(u.rad)
    n = np.column_stack([np.cos(dec) * np.cos(ra), np.cos(dec) * np.sin(ra), np.sin(dec)])
    e_ra = np.column_stack([-np.sin(ra), np.cos(ra), np.zeros_like(ra)])
    e_dec = np.column_stack([-np.sin(dec) * np.cos(ra), -np.sin(dec) * np.sin(ra), np.cos(dec)])
    pm = c.pm_ra_cosdec.to_value(u.mas / u.yr)[:, None] * e_ra + c.pm_dec.to_value(u.mas / u.yr)[:, None] * e_dec
    return n, pm


def desalineamiento_local(n_cielo, pm, orden, ancho_deg=4.0, n_min=15):
    """Desalineamiento en tramos a lo largo de la corriente.
    n_cielo, pm: vectores (N, 3); orden: coordenada a lo largo de la corriente (p. ej. angulo desenrollado, rad).
    Devuelve dict con el centro de cada tramo (en 'orden'), dtheta [grados, con signo] y numero de estrellas."""
    ok = np.isfinite(orden)
    o = np.radians(ancho_deg)
    bordes = np.arange(np.nanmin(orden[ok]), np.nanmax(orden[ok]) + o, o)
    k = np.digitize(orden, bordes) - 1
    centros, cielo, mov, nn = [], [], [], []
    for i in range(len(bordes) - 1):
        s = ok & (k == i)
        if s.sum() < n_min:
            continue
        centros.append(0.5 * (bordes[i] + bordes[i + 1]))
        cielo.append(unit(np.median(n_cielo[s], axis=0)))
        mov.append(np.median(pm[s], axis=0))
        nn.append(int(s.sum()))
    centros, cielo, mov = np.array(centros), np.array(cielo), np.array(mov)
    dth = np.full(len(centros), np.nan)
    for i in range(len(centros)):
        a, b = max(i - 1, 0), min(i + 1, len(centros) - 1)
        if b == a or abs(centros[b] - centros[a]) > 2.5 * o:
            continue
        t = cielo[b] - cielo[a]
        t = unit(t - np.dot(t, cielo[i]) * cielo[i])
        e2 = np.cross(cielo[i], t)
        m = mov[i] - np.dot(mov[i], cielo[i]) * cielo[i]
        m1, m2 = np.dot(m, t), np.dot(m, e2)
        dth[i] = np.degrees(np.arctan(m2 / m1)) if m1 != 0 else np.nan
    return dict(centro=centros, dtheta=dth, n=np.array(nn))


def desalineamiento_gran_circulo(c, polo_icrs, ancho_deg=4.0, n_min=15):
    """Version literal del enunciado en coordenadas (phi1, phi2) de gala.coordinates.GreatCircleICRSFrame."""
    import astropy.coordinates as coord
    import astropy.units as u
    import gala.coordinates as gcoord
    polo = coord.SkyCoord(*unit(polo_icrs), representation_type="cartesian", frame="icrs").spherical
    fr = gcoord.GreatCircleICRSFrame.from_pole_ra0(coord.SkyCoord(ra=polo.lon, dec=polo.lat, frame="icrs"),
                                                   ra0=np.median(c.ra.deg) * u.deg)
    s = c.transform_to(fr)
    p1, p2 = s.phi1.wrap_at(180 * u.deg).deg, s.phi2.deg
    # origen de phi1 en el centro (circular) de la corriente: una rotacion alrededor del polo no cambia mu_phi1,2
    c0 = np.degrees(np.arctan2(np.mean(np.sin(np.radians(p1))), np.mean(np.cos(np.radians(p1)))))
    p1 = (p1 - c0 + 180.0) % 360.0 - 180.0
    m1, m2 = s.pm_phi1_cosphi2.to_value(u.mas / u.yr), s.pm_phi2.to_value(u.mas / u.yr)
    b = np.arange(np.min(p1), np.max(p1) + ancho_deg, ancho_deg)
    k = np.digitize(p1, b) - 1
    cen, tr, mm1, mm2, nn = [], [], [], [], []
    for i in range(len(b) - 1):
        q = k == i
        if q.sum() >= n_min:
            cen.append(0.5 * (b[i] + b[i + 1]))
            tr.append(np.median(p2[q]))
            mm1.append(np.median(m1[q]))
            mm2.append(np.median(m2[q]))
            nn.append(int(q.sum()))
    cen, tr = np.array(cen), np.array(tr)
    # traza suavizada (mediana movil de 5 tramos) antes de derivar: la pendiente de una traza ruidosa domina dtheta
    if len(cen) > 4:
        from scipy.ndimage import median_filter
        tr_s = median_filter(tr, size=5, mode="nearest")
        pend = np.gradient(tr_s, cen)
    else:
        tr_s, pend = tr, np.full(len(cen), np.nan)
    dth = np.degrees(np.arctan(np.array(mm2) / np.array(mm1)) - np.arctan(pend))
    return dict(phi1=p1, phi2=p2, pm1=m1, pm2=m2, centro=cen, traza=tr_s, dtheta=dth, n=np.array(nn))


def partes(c):
    """Mascaras de cada parte: todo, lider, cola, vieja / joven (liberadas antes / despues de la mediana)."""
    rt, lt = c["release_time"], c["lead_trail"]
    med = np.median(rt)
    return {"todo": np.ones(len(rt), bool), "lider": lt == 1, "cola": lt == -1, "vieja": rt <= med,
            "joven": rt > med}


def medir(c, n_inicial, n_min=50, con_cielo=True):
    """Todas las metricas de una corriente (dict de arrays de gala.corrientes.generar).
    n_inicial: polo inicial del progenitor. Devuelve (escalares por parte, perfiles a lo largo de la corriente)."""
    pos, vel = np.asarray(c["pos"], float), np.asarray(c["vel"], float)
    n0 = unit(n_inicial)
    L = polos(pos, vel)
    Lm = polo_medio(L)
    psi = angulo_desenrollado(pos, c["release_time"], c["lead_trail"], c["prog_pos"], Lm)
    if con_cielo:
        cie = a_icrs(pos, vel)
        ncie, pm = vectores_cielo(cie)
        dis = desalineamiento_local(ncie, pm, psi)
    res = {"longitud_vueltas": longitud_vueltas(psi), "n_estrellas": int(len(pos))}
    for nombre, s in partes(c).items():
        if s.sum() < n_min:
            continue
        Lp = polo_medio(L[s])
        nsvd = normal_svd(pos[s], referencia=Lp)
        d = {"tilt_polo_deg": float(angulo(Lp, n0)),
             "tilt_plano_deg": float(min(angulo(nsvd, n0), 180 - angulo(nsvd, n0))),
             "dispersion_polos_deg": float(np.median(angulo(L[s], Lp))),
             "tilt_polos_mediana_deg": float(np.median(angulo(L[s], n0))),
             "grosor_kpc": grosor(pos[s], nsvd), "polo": Lp, "normal": nsvd}
        if con_cielo:
            dl = desalineamiento_local(ncie[s], pm[s], psi[s])
            d["desalineamiento_deg"] = float(np.nanmedian(np.abs(dl["dtheta"]))) if np.isfinite(dl["dtheta"]).any() \
                else np.nan
        res[nombre] = d
    perfiles = {"psi": psi, "polos": L}
    if con_cielo:
        perfiles.update(desal=dis, cielo=ncie, pm=pm)
    return res, perfiles


def perturbaciones(m_por_modelo, metrica, parte="todo"):
    """dM_reflex = M_B - M_A, dM_direct = M_C - M_A, dM_full = M_D - M_A y f_reflex (enunciado)."""
    v = {k: m_por_modelo[k].get(parte, {}).get(metrica, np.nan) for k in "ABCD"}
    dr, dd, df = v["B"] - v["A"], v["C"] - v["A"], v["D"] - v["A"]
    f = abs(dr) / (abs(dr) + abs(dd)) if np.isfinite(dr) and np.isfinite(dd) and (abs(dr) + abs(dd)) > 0 else np.nan
    return dict(dM_reflex=dr, dM_direct=dd, dM_full=df, f_reflex=f, no_lineal=df - (dr + dd))


def cambio_polo(m_por_modelo, parte="todo"):
    """Version vectorial: angulo entre el polo medio de cada modelo y el del modelo A (no se cancela por signo)."""
    pa = m_por_modelo["A"].get(parte, {}).get("polo")
    out = {}
    for k in "BCD":
        pk = m_por_modelo[k].get(parte, {}).get("polo")
        out[k] = float(angulo(pk, pa)) if pa is not None and pk is not None else np.nan
    r, d = out["B"], out["C"]
    out["f_reflex"] = r / (r + d) if np.isfinite(r) and np.isfinite(d) and (r + d) > 0 else np.nan
    return out


def clase(f):
    if not np.isfinite(f):
        return "undetermined"
    return "reflex" if f > C.F_REFLEJO_ALTO else "torque" if f < C.F_REFLEJO_BAJO else "mixed"
