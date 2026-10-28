"""Figuras academicas (fondo blanco) de los hitos 1-6. Cada funcion devuelve la figura; guardar con estilo.guardar."""

import numpy as np

from . import config as C
from . import estilo as E


def marco_plano(n0, x0):
    """Matriz de rotacion a coordenadas del plano orbital inicial: z' = n0, x' hacia la posicion inicial."""
    from . import metricas as Me
    n = Me.unit(n0)
    e1 = Me.unit(np.asarray(x0) - np.dot(x0, n) * n)
    return np.vstack([e1, np.cross(n, e1), n])


def polo_lmc(sis):
    """Polo orbital de la LMC hoy (marco de la MW)."""
    from . import metricas as Me
    x = sis.x_lmc_rel(0.0)
    v = sis._x_lmc(0.0, 1) - sis._x_mw(0.0, 1)
    return Me.unit(np.cross(x, v))


def lb(v):
    v = np.atleast_2d(v)
    return np.arctan2(v[:, 1], v[:, 0]), np.arcsin(np.clip(v[:, 2], -1, 1))


def hito1(corr, sis, n0, x0, t_lmc=(-1500, 0), titulo=None):
    """Corriente de hoy en su plano orbital inicial (de frente y de canto), en varios modelos, con la orbita de
    la LMC. corr: {modelo: dict de corrientes.generar}."""
    import matplotlib.pyplot as plt
    Rm = marco_plano(n0, x0)
    tl = np.linspace(*t_lmc, 300)
    xl = sis.x_lmc_rel(tl) @ Rm.T
    fig, ax = plt.subplots(2, len(corr), figsize=(5.2 * len(corr), 8.4), gridspec_kw=dict(height_ratios=[2.2, 1]),
                           squeeze=False)
    lim = 1.15 * max(np.percentile(np.abs(c["pos"] @ Rm.T)[:, :2], 99.5) for c in corr.values())
    for j, (m, c) in enumerate(corr.items()):
        p = c["pos"] @ Rm.T
        col = E.COLOR_MODELO[m]
        for i, (a, b) in enumerate(((0, 1), (0, 2))):
            A = ax[i, j]
            A.scatter(p[:, a], p[:, b], s=1.5, color=col, alpha=0.6, lw=0, rasterized=True)
            A.plot(xl[:, a], xl[:, b], color=E.COLOR_LMC, lw=1.4)
            A.plot(xl[-1, a], xl[-1, b], "o", color=E.COLOR_LMC, ms=6)
            A.plot(0, 0, "+", color=E.TINTA, ms=9)
            A.set_xlim(-lim, lim)
            A.set_ylim(-lim, lim) if i == 0 else A.set_ylim(-0.45 * lim, 0.45 * lim)
            A.set_aspect("equal")
            A.set_xlabel("x' (kpc)")
            A.set_ylabel("y' (kpc)" if i == 0 else "z' (kpc)")
            E.grilla(A)
        ax[0, j].set_title(E.NOMBRE_MODELO[m], color=col, loc="left")
    ax[0, 0].text(0.02, 0.02, "LMC orbit, last %.1f Gyr (dot: today)" % (-t_lmc[0] / 1e3),
                  transform=ax[0, 0].transAxes, color=E.COLOR_LMC, fontsize=10)
    if titulo:
        fig.suptitle(titulo, x=0.01, ha="left", fontsize=14)
    fig.tight_layout()
    return fig

def hito2(sis, val=None):
    """|a_MW(t)| y distancia de la LMC; opcional: diferencia modelo D - marco inercial de una particula."""
    import matplotlib.pyplot as plt
    n = 3 if val is not None else 2
    fig, ax = plt.subplots(1, n, figsize=(5.3 * n, 4.3))
    t = sis.t / 1e3
    ax[0].plot(t, sis.d_lmc(), color=E.COLOR_LMC)
    ax[0].set_ylabel(r"$|\mathbf{x}_{\rm LMC}-\mathbf{x}_{\rm MW}|$ (kpc)")
    a = np.linalg.norm(sis.a_mw(sis.t), axis=1) * 977.792221 * 1e3     # kpc/Myr^2 -> km/s/Gyr
    ax[1].semilogy(t, a, color=E.COLOR_MODELO["B"])
    ax[1].set_ylabel(r"$|\mathbf{a}_{\rm MW}|$ (km s$^{-1}$ Gyr$^{-1}$)")
    if val is not None:
        tt, rd, ri = val
        ax[2].semilogy(tt / 1e3, np.maximum(np.linalg.norm(rd - ri, axis=1) * 1e3, 1e-6), color=E.COLOR_MODELO["D"])
        ax[2].set_ylabel("|model D - inertial frame| (pc)")
        ax[2].set_title("test particle, r = 50 kpc polar orbit", fontsize=11, loc="left")
    for A in ax:
        A.set_xlabel("time (Gyr)")
        E.grilla(A)
    fig.tight_layout()
    return fig


def perfil_tilt(L, psi, n0, ancho_deg=6.0, n_min=15):
    from . import metricas as Me
    b = np.arange(np.nanmin(psi), np.nanmax(psi) + np.radians(ancho_deg), np.radians(ancho_deg))
    k = np.digitize(psi, b) - 1
    c, v = [], []
    for i in range(len(b) - 1):
        s = k == i
        if s.sum() >= n_min:
            c.append(0.5 * (b[i] + b[i + 1]))
            v.append(np.median(Me.angulo(L[s], n0)))
    return np.degrees(c), np.array(v)


def perfil_altura(pos, psi, n0, ancho_deg=6.0, n_min=15):
    from . import metricas as Me
    z = pos @ Me.unit(n0)
    b = np.arange(np.nanmin(psi), np.nanmax(psi) + np.radians(ancho_deg), np.radians(ancho_deg))
    k = np.digitize(psi, b) - 1
    c, v = [], []
    for i in range(len(b) - 1):
        s = k == i
        if s.sum() >= n_min:
            c.append(0.5 * (b[i] + b[i + 1]))
            v.append(np.median(z[s]))
    return np.degrees(c), np.array(v)


def hito3(corr, perfiles, n0, x0, sis, titulo=None):
    """La corriente y sus tres metricas a lo largo de la corriente, en los cuatro modelos."""
    import matplotlib.pyplot as plt
    Rm = marco_plano(n0, x0)
    fig = plt.figure(figsize=(15, 10.5))
    gs = fig.add_gridspec(3, 4, height_ratios=[1.35, 1, 1], hspace=0.38, wspace=0.28)
    lim = 1.15 * max(np.percentile(np.abs(c["pos"] @ Rm.T)[:, :2], 99.5) for c in corr.values())
    tl = np.linspace(-1500, 0, 300)
    xl = sis.x_lmc_rel(tl) @ Rm.T
    for j, m in enumerate("ABCD"):
        A = fig.add_subplot(gs[0, j])
        p = corr[m]["pos"] @ Rm.T
        A.scatter(p[:, 0], p[:, 1], s=1, color=E.COLOR_MODELO[m], alpha=0.6, lw=0, rasterized=True)
        A.plot(xl[:, 0], xl[:, 1], color=E.COLOR_LMC, lw=1.2)
        A.set_xlim(-lim, lim)
        A.set_ylim(-lim, lim)
        A.set_aspect("equal")
        A.set_title(E.NOMBRE_MODELO[m], color=E.COLOR_MODELO[m], loc="left", fontsize=12)
        A.set_xlabel("x' (kpc)")
        if j == 0:
            A.set_ylabel("y' (kpc)")
        E.grilla(A)
    ax1, ax2 = fig.add_subplot(gs[1, :2]), fig.add_subplot(gs[1, 2:])
    ax3 = fig.add_subplot(gs[2, :2])
    ax4 = fig.add_subplot(gs[2, 2:])
    for m in "ABCD":
        col = E.COLOR_MODELO[m]
        d = perfiles[m]["desal"]
        ax1.plot(np.degrees(d["centro"]), d["dtheta"], color=col, lw=1.6, label=m)
        cx, v = perfil_tilt(perfiles[m]["polos"], perfiles[m]["psi"], n0)
        ax2.plot(cx, v, color=col, lw=1.6)
        cx, v = perfil_altura(corr[m]["pos"], perfiles[m]["psi"], n0)
        ax3.plot(cx, v, color=col, lw=1.6)
    ax1.axhline(0, color=E.TINTA_SUAVE, lw=0.7)
    ax1.set_ylabel(r"PM misalignment $\Delta\theta$ (deg)")
    ax2.set_ylabel(r"pole tilt from initial pole (deg)")
    ax3.set_ylabel(r"height above initial plane (kpc)")
    for A in (ax1, ax2, ax3):
        A.set_xlabel(r"angle along the stream from the progenitor (deg)")
        E.grilla(A)
    ax1.legend(ncol=4, loc="upper left")
    ax4.axis("off")
    if titulo:
        fig.suptitle(titulo, x=0.01, ha="left", fontsize=14)
    return fig, ax4


def tabla_en_eje(ax, filas, columnas, titulo=None):
    t = ax.table(cellText=filas, colLabels=columnas, loc="center", cellLoc="right", colLoc="right")
    t.auto_set_font_size(False)
    t.set_fontsize(10)
    t.scale(1, 1.4)
    for (r, c), cell in t.get_celld().items():
        cell.set_edgecolor(E.GRILLA)
        if r == 0:
            cell.set_text_props(color=E.TINTA_SUAVE)
    if titulo:
        ax.set_title(titulo, loc="left", fontsize=12)


def mapa_polos(df, columnas, titulos, sis=None, cmaps=None, rangos=None, titulo=None, etiquetas=None):
    """Mollweide de los polos iniciales (l, b del polo en el marco de la MW), coloreados por columnas del catalogo."""
    import matplotlib.pyplot as plt
    polos = np.array(df["polo"].tolist())
    lon, lat = lb(polos)
    n = len(columnas)
    fig = plt.figure(figsize=(6.2 * n, 4.4))
    for i, col in enumerate(columnas):
        A = fig.add_subplot(1, n, i + 1, projection="mollweide")
        v = df[col].to_numpy(float)
        cm = (cmaps or {}).get(col, "viridis")
        vmin, vmax = (rangos or {}).get(col, (np.nanpercentile(v, 2), np.nanpercentile(v, 98)))
        h = A.scatter(-lon, lat, c=v, cmap=cm, vmin=vmin, vmax=vmax, s=60, edgecolor="#FFFFFF", lw=0.5, zorder=3)
        if sis is not None:
            pl = polo_lmc(sis)
            lo, la = lb(pl)
            A.plot(-lo, la, "*", ms=15, color=E.COLOR_LMC, mec="#FFFFFF", zorder=4)
            lo, la = lb(-pl)
            A.plot(-lo, la, "*", ms=15, mfc="none", mec=E.COLOR_LMC, zorder=4)
        A.grid(True, color=E.GRILLA, lw=0.6)
        A.set_xticklabels([])
        A.set_title(titulos[i], fontsize=12, pad=12)
        cb = fig.colorbar(h, ax=A, orientation="horizontal", fraction=0.05, pad=0.06)
        cb.outline.set_visible(False)
        if etiquetas and col in etiquetas:
            cb.set_label(etiquetas[col])
        A.tick_params(axis="y", labelsize=8)
    if titulo:
        fig.suptitle(titulo, x=0.01, ha="left", fontsize=14)
    return fig


def dispersiones(df, metrica, parte="todo", ejes=("peri_kpc", "apo_kpc", "dmin_lmc_kpc", "longitud_vueltas_A"),
                 etiquetas=("pericentre (kpc)", "apocentre (kpc)", "closest approach to the LMC (kpc)",
                            "stream length (wraps)"), ylabel=None):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, len(ejes), figsize=(4.4 * len(ejes), 4.0), sharey=True)
    for A, x, lab in zip(ax, ejes, etiquetas):
        for k, m in (("dM_reflex", "B"), ("dM_direct", "C"), ("dM_full", "D")):
            A.scatter(df[x], np.abs(df["%s_%s_%s" % (k, metrica, parte)]), s=14, color=E.COLOR_MODELO[m],
                      alpha=0.75, lw=0, label={"B": "reflex (B-A)", "C": "direct (C-A)", "D": "full (D-A)"}[m])
        A.set_xlabel(lab)
        A.set_yscale("log")
        E.grilla(A)
    ax[0].set_ylabel(ylabel or "|perturbation| of %s" % metrica)
    ax[0].legend(loc="lower left", fontsize=10)
    fig.tight_layout()
    return fig


def polo_cielo(c):
    """Polo (ICRS) del gran circulo que mejor ajusta la corriente vista desde el Sol (SVD de los vectores)."""
    from . import metricas as Me
    n, _ = Me.vectores_cielo(c)
    return Me.normal_svd(n)


def cielo_gran_circulo(corr, modelos=("A", "D"), ancho_deg=4.0, titulo=None):
    """La corriente en coordenadas (phi1, phi2) de GreatCircleICRSFrame (polo del gran circulo ajustado a cada
    corriente vista desde el Sol), con el movimiento propio corregido por el Sol en tramos (flechas) y
    Delta theta(phi1) debajo. Es la definicion literal del enunciado."""
    import matplotlib.pyplot as plt
    from . import metricas as Me
    fig, ax = plt.subplots(2, len(modelos), figsize=(7.2 * len(modelos), 7.2), sharex="col",
                           gridspec_kw=dict(height_ratios=[1.5, 1]), squeeze=False)
    for j, m in enumerate(modelos):
        c = Me.a_icrs(np.asarray(corr[m]["pos"], float), np.asarray(corr[m]["vel"], float))
        g = Me.desalineamiento_gran_circulo(c, polo_cielo(c), ancho_deg=ancho_deg)
        col = E.COLOR_MODELO[m]
        A = ax[0, j]
        A.scatter(g["phi1"], g["phi2"], s=1.2, color=col, alpha=0.35, lw=0, rasterized=True)
        # flechas: mediana del movimiento propio en cada tramo, normalizada (solo la direccion importa)
        m1 = np.array([np.median(g["pm1"][np.abs(g["phi1"] - x) < ancho_deg / 2]) for x in g["centro"]])
        m2 = np.array([np.median(g["pm2"][np.abs(g["phi1"] - x) < ancho_deg / 2]) for x in g["centro"]])
        nn = np.hypot(m1, m2)
        paso = max(1, len(g["centro"]) // 18)
        A.quiver(g["centro"][::paso], g["traza"][::paso], (m1 / nn)[::paso], (m2 / nn)[::paso], color=E.TINTA,
                 angles="xy", scale_units="inches", scale=3.5, width=0.003)
        cortes = np.r_[np.diff(g["centro"]) > 2.5 * ancho_deg, False]       # no unir tramos separados por huecos
        A.plot(np.where(cortes, np.nan, g["centro"]), g["traza"], color=E.TINTA_SUAVE, lw=1)
        A.set_ylabel(r"$\phi_2$ (deg)")
        A.set_title(E.NOMBRE_MODELO[m], color=col, loc="left")
        lim = max(5, 1.3 * np.nanpercentile(np.abs(g["phi2"]), 98))
        A.set_ylim(-lim, lim)
        lo, hi = np.percentile(g["phi1"], [0.5, 99.5])
        A.set_xlim(lo - 5, hi + 5)
        E.grilla(A)
        B = ax[1, j]
        B.axhline(0, color=E.TINTA_SUAVE, lw=0.7)
        B.plot(np.where(cortes, np.nan, g["centro"]), g["dtheta"], "o-", ms=3, color=col, lw=1.4)
        B.set_xlabel(r"$\phi_1$ (deg)")
        B.set_ylabel(r"$\Delta\theta$ (deg)")
        E.grilla(B)
    if titulo:
        fig.suptitle(titulo, x=0.01, ha="left", fontsize=14)
    fig.tight_layout()
    return fig


def cmap_f_reflex():
    """Divergente: torque (naranja, f = 0) - mixto (gris claro, 0.5) - reflejo (azul, f = 1)."""
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("f_reflex", [E.COLOR_MODELO["C"], "#E9E6E1", E.COLOR_MODELO["B"]])


def cmap_secuencial(color):
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("s", ["#F4F5F7", color])


def mapas_clasificacion(df, metrica, sis=None, parte="todo", vmax=None, titulo=None):
    """Mollweide de los polos iniciales coloreados por |dM_reflex|, |dM_direct| y f_reflex de una metrica."""
    from . import analisis as An
    d = df.copy()
    cr, cd, cf = (An.col(metrica, k, parte) for k in ("reflex", "direct", "f"))
    d["_r"], d["_d"] = d[cr].abs(), d[cd].abs()
    v = vmax or float(np.nanpercentile(np.r_[d["_r"], d["_d"]], 95))
    return mapa_polos(d, ["_r", "_d", cf],
                      [r"$|\Delta M_{\rm reflex}|$", r"$|\Delta M_{\rm direct}|$", r"$f_{\rm reflex}$"], sis=sis,
                      cmaps={"_r": cmap_secuencial(E.COLOR_MODELO["B"]), "_d": cmap_secuencial(E.COLOR_MODELO["C"]),
                             cf: cmap_f_reflex()},
                      rangos={"_r": (0, v), "_d": (0, v), cf: (0, 1)}, titulo=titulo,
                      etiquetas={"_r": "deg", "_d": "deg", cf: "0: torque-dominated    1: reflex-dominated"})


def tendencias(df, metrica, parte="todo", ejes=("peri_kpc", "apo_kpc", "dmin_lmc_kpc", "longitud_vueltas_A"),
               etiquetas=("pericentre (kpc)", "apocentre (kpc)", "closest approach to the LMC (kpc)",
                          "stream length in model A (wraps)"), ylabel=None, logx=(False, False, True, False)):
    """|dM| de cada efecto contra distancia, acercamiento a la LMC y longitud; puntos y medianas por tramo."""
    import matplotlib.pyplot as plt
    from . import analisis as An
    fig, ax = plt.subplots(1, len(ejes), figsize=(4.5 * len(ejes), 4.2), sharey=True)
    for A, x, lab, lg in zip(ax, ejes, etiquetas, logx):
        xv = df[x].to_numpy(float)
        bordes = np.geomspace(np.nanmin(xv), np.nanmax(xv) * 1.001, 8) if lg else \
            np.linspace(np.nanmin(xv), np.nanmax(xv) * 1.001, 8)
        for k, m, nom in (("reflex", "B", "reflex (B - A)"), ("direct", "C", "direct pull (C - A)"),
                          ("full", "D", "full (D - A)")):
            y = np.abs(df[An.col(metrica, k, parte)].to_numpy(float))
            A.scatter(xv, y, s=10, color=E.COLOR_MODELO[m], alpha=0.35, lw=0)
            c, med, _, _ = An.medianas_por_tramo(xv, y, bordes)
            A.plot(c, med, "-o", ms=4, color=E.COLOR_MODELO[m], lw=2, label=nom)
        A.set_xlabel(lab)
        A.set_yscale("log")
        if lg:
            A.set_xscale("log")
        E.grilla(A)
    ax[0].set_ylabel(ylabel or "|perturbation|")
    ax[0].legend(loc="lower left", fontsize=10)
    fig.tight_layout()
    return fig


def orientacion(df, parte="todo"):
    """Izquierda: cambio del polo por el reflejo contra |n0 . a_MW| (fuerza perpendicular al plano = 1).
    Derecha: cambio del polo por el tiron directo contra el acercamiento a la LMC, prograda vs retrograda."""
    import matplotlib.pyplot as plt
    from . import analisis as An
    fig, ax = plt.subplots(1, 2, figsize=(10.5, 4.3))
    x = df["perp_aMW"].to_numpy(float)
    for fam, mk in (("corta", "o"), ("larga", "s"), ("doble", "^")):
        s = (df["familia"] == fam).to_numpy()
        ax[0].scatter(x[s], df[An.col("dpolo", "reflex", parte)][s], s=16, marker=mk, color=E.COLOR_MODELO["B"],
                      alpha=0.6, lw=0, label={"corta": "short", "larga": "long", "doble": "two-wrap"}[fam])
    c, med, lo, hi = An.medianas_por_tramo(x, df[An.col("dpolo", "reflex", parte)].to_numpy(float),
                                           np.linspace(0, 1.0001, 6))
    ax[0].plot(c, med, "-", color=E.TINTA, lw=2, label="median")
    ax[0].set_xlabel(r"$|\hat{\mathbf{n}}_0\cdot\hat{\mathbf{a}}_{\rm MW}|$  (1: force perpendicular to the plane)")
    ax[0].set_ylabel("pole change, reflex only (deg)")
    ax[0].set_yscale("log")
    ax[0].legend(fontsize=9, loc="lower right")
    for sen, col_ in (("prograde", E.COLOR_MODELO["C"]), ("retrograde", E.COLOR_MODELO["A"])):
        s = (df["sentido_lmc"] == sen).to_numpy()
        ax[1].scatter(df["dmin_lmc_kpc"][s], df[An.col("dpolo", "direct", parte)][s], s=16, color=col_, alpha=0.7,
                      lw=0, label="%s w.r.t. the LMC orbit" % sen)
    ax[1].set_xscale("log")
    ax[1].set_yscale("log")
    ax[1].set_xlabel("closest approach to the LMC (kpc)")
    ax[1].set_ylabel("pole change, direct pull only (deg)")
    ax[1].legend(fontsize=9, loc="lower left")
    for A in ax:
        E.grilla(A)
    fig.tight_layout()
    return fig


def viejo_joven(df, metrica="dpolo", familias=("larga", "doble")):
    """Perturbacion de la parte vieja contra la joven (cada efecto), para las corrientes largas."""
    import matplotlib.pyplot as plt
    from . import analisis as An
    s = df["familia"].isin(familias).to_numpy()
    fig, ax = plt.subplots(1, 3, figsize=(13, 4.3), sharex=True, sharey=True)
    for A, (k, m, nom) in zip(ax, (("reflex", "B", "reflex only"), ("direct", "C", "direct pull only"),
                                   ("full", "D", "full MW + LMC"))):
        xo = np.abs(df[An.col(metrica, k, "vieja")].to_numpy(float))[s]
        yo = np.abs(df[An.col(metrica, k, "joven")].to_numpy(float))[s]
        A.scatter(xo, yo, s=14, color=E.COLOR_MODELO[m], alpha=0.65, lw=0)
        lim = [max(0.05, np.nanmin(np.r_[xo, yo])), np.nanmax(np.r_[xo, yo]) * 1.2]
        A.plot(lim, lim, color=E.TINTA_SUAVE, lw=0.8)
        A.set_xscale("log")
        A.set_yscale("log")
        A.set_title(nom, loc="left", color=E.COLOR_MODELO[m])
        A.set_xlabel("old debris (deg)")
        E.grilla(A)
        A.text(0.97, 0.04, "young > old: %d of %d" % (np.sum(yo > xo), np.sum(np.isfinite(xo) & np.isfinite(yo))),
               transform=A.transAxes, ha="right", fontsize=10, color=E.TINTA_SUAVE)
    ax[0].set_ylabel("young debris (deg)")
    fig.tight_layout()
    return fig


def por_radio(tab, titulo=None):
    """Cambio del polo orbital estrella a estrella (respecto de la misma estrella en A) en funcion del radio."""
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for m, nom in (("B", "reflex only (B)"), ("C", "direct pull only (C)"), ("D", "full MW + LMC (D)")):
        ax.fill_between(tab["r_med"], tab["p16_%s" % m], tab["p84_%s" % m], color=E.COLOR_MODELO[m], alpha=0.12,
                        lw=0)
        ax.plot(tab["r_med"], tab["med_%s" % m], "-o", ms=4, lw=2, color=E.COLOR_MODELO[m], label=nom)
    ax.set_xscale("log")
    ax.set_xlabel("galactocentric radius of the star today (kpc)")
    ax.set_ylabel("change of the star's orbital pole vs model A (deg)")
    ax.legend(loc="upper left", fontsize=10)
    E.grilla(ax)
    if titulo:
        ax.set_title(titulo, loc="left", fontsize=12)
    fig.tight_layout()
    return fig


COLOR_FAMILIA = {"corta": "#1F5E99", "larga": "#7A4BA8", "doble": "#D0663F"}
NOMBRE_FAMILIA = {"corta": "short", "larga": "long", "doble": "two-wrap"}


def _moll_radec(ra_deg, dec_deg):
    ra = np.radians(((np.asarray(ra_deg) + 180.0) % 360.0) - 180.0)
    return -ra, np.radians(dec_deg)          # RA crece hacia la izquierda


def lsst_cielo(corr_por_modelo, obs_por_modelo, lmc_radec=None, titulo=None):
    """Cielo (ICRS, Mollweide) de una corriente en cada modelo: todas las particulas (gris) y las estrellas que
    LSST veria (color: magnitud r), con el borde del footprint (Dec = +5) y la LMC."""
    import matplotlib.pyplot as plt
    from . import metricas as Me
    n = len(corr_por_modelo)
    fig = plt.figure(figsize=(6.6 * n, 4.6))
    h = None
    for i, (m, c) in enumerate(corr_por_modelo.items()):
        A = fig.add_subplot(1, n, i + 1, projection="mollweide")
        sky = Me.a_icrs(np.asarray(c["pos"], float), np.asarray(c["vel"], float), corregir=False)
        x, y = _moll_radec(sky.ra.deg, sky.dec.deg)
        A.scatter(x, y, s=0.6, color="#C9CDD3", lw=0, rasterized=True)
        o = obs_por_modelo[m]
        if o.get("n", 0):
            k = np.random.default_rng(0).choice(o["n"], min(o["n"], 15000), replace=False)
            k = k[np.argsort(-o["r"][k])]              # las brillantes encima
            x, y = _moll_radec(o["ra"][k], o["dec"][k])
            h = A.scatter(x, y, c=o["r"][k], s=0.8, cmap="viridis_r", vmin=16, vmax=27, lw=0, rasterized=True)
        ra = np.linspace(-180, 180, 300)
        x, y = _moll_radec(ra, np.full_like(ra, C.LSST_DEC_MAX))
        o_ = np.argsort(x)
        A.plot(x[o_], y[o_], color=E.TINTA, lw=1.0, ls="--")
        if lmc_radec is not None:
            x, y = _moll_radec(*lmc_radec)
            A.plot(x, y, "*", ms=13, color=E.COLOR_LMC, mec="#FFFFFF")
        A.grid(True, color=E.GRILLA, lw=0.6)
        A.set_xticklabels([])
        A.tick_params(axis="y", labelsize=8)
        A.set_title("%s  (%d stars, %d with PM)" % (E.NOMBRE_MODELO[m], o.get("n", 0),
                                                    int(np.sum(o["pm_ok"])) if o.get("n", 0) else 0),
                    color=E.COLOR_MODELO[m], fontsize=11, pad=10)
    if h is not None:
        cb = fig.colorbar(h, ax=fig.axes, orientation="horizontal", fraction=0.04, pad=0.08, aspect=60)
        cb.set_label("LSST r magnitude")
        cb.outline.set_visible(False)
    if titulo:
        fig.suptitle(titulo, x=0.01, ha="left", fontsize=13)
    return fig


def lsst_snr(dfm, metricas, titulos, var="", umbral=3.0, col="snr"):
    """Senal del reflejo (D vs C) en unidades de su error, para las estrellas que LSST veria, contra la distancia
    mediana de esas estrellas. Una curva por familia; linea: el umbral de deteccion."""
    import matplotlib.pyplot as plt
    pre = var + "_" if var else ""
    fig, ax = plt.subplots(1, len(metricas), figsize=(4.6 * len(metricas), 4.3), sharey=True, squeeze=False)
    for A, met, tit in zip(ax[0], metricas, titulos):
        for fam in ("corta", "larga", "doble"):
            s = (dfm["familia"] == fam).to_numpy()
            y = np.clip(dfm["%s_%sreflejo_%s" % (col, pre, met)].to_numpy(float)[s], 0.05, None)
            A.scatter(dfm["d_med_obs_D"].to_numpy(float)[s], y, s=14, alpha=0.7, lw=0, color=COLOR_FAMILIA[fam],
                      label=NOMBRE_FAMILIA[fam])
        A.axhline(umbral, color=E.TINTA, lw=1, ls="--")
        A.set_xscale("log")
        A.set_yscale("log")
        A.set_title(tit, loc="left", fontsize=11)
        A.set_xlabel("median distance of the observed stars (kpc)")
        E.grilla(A)
    ax[0, 0].set_ylabel(r"reflex signal $|M_D - M_C|\,/\,\sigma$")
    ax[0, 0].legend(fontsize=9, loc="lower left")
    fig.tight_layout()
    return fig
