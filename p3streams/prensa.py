"""Figuras de prensa (fondo negro solido, sin jerga, 4K). Los datos son los mismos de las figuras academicas;
solo cambia la presentacion. La procedencia va en los metadatos del PNG, como en las demas figuras."""

import numpy as np

from . import config as C
from . import estilo as E

ANCHO, ALTO = 3840, 2160
VIOLETA = ["#000000", "#2B1150", "#6E3FB0", "#B98CF0", "#FFFFFF"]
GRIS_AZUL = ["#000000", "#16202C", "#3C5470", "#8FA6C4"]
CALIDO = ["#000000", "#2A2216", "#7A6640", "#F2E6C8"]


def _cmap(colores, nombre="c"):
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list(nombre, colores)


def _capa(p2, ext, res, sig, cm, norma=None, k=6.0, peso=1.0):
    from .videos import _densidad
    H = _densidad(p2, ext, res, sig)
    norma = norma or (np.percentile(H[H > 0], 99.7) if (H > 0).any() else 1.0)
    return cm(np.clip(np.arcsinh(H / norma * k) / np.arcsinh(k), 0, 1))[:, :, :3] * peso


def disco(Rv, ext, res, n=120000):
    """Brillo del disco exponencial del modelo (h_R, h_z) proyectado."""
    rgd = np.random.default_rng(0)
    R = rgd.gamma(2.0, C.MW_DISCO["h_R"], n)
    ph = rgd.uniform(0, 2 * np.pi, n)
    z = rgd.laplace(0, C.MW_DISCO["h_z"], n)
    return _capa(np.column_stack([R * np.cos(ph), R * np.sin(ph), z]) @ Rv.T, ext, res, (2.0, 7.0), _cmap(CALIDO),
                 k=4.0, peso=0.6)


def heroe(corrD, corrA, sis, n0, x0, titulo, subtitulo, inclinacion=62.0, t_lmc=(-700.0, 0.0)):
    """La corriente en la MW + LMC (violeta) sobre la misma corriente en la MW sola (gris azulado), con el disco y
    la orbita reciente de la LMC. Vista oblicua del plano orbital inicial."""
    import matplotlib.pyplot as plt
    from . import figuras as F
    E.usar(oscuro=True, agg=False)
    Rm = F.marco_plano(n0, x0)
    c, s = np.cos(np.radians(inclinacion)), np.sin(np.radians(inclinacion))
    Rv = np.array([[1, 0, 0], [0, c, -s], [0, s, c]]) @ Rm
    pD, pA = (np.asarray(x["pos"], float) @ Rv.T for x in (corrD, corrA))
    lim = 1.12 * max(np.nanpercentile(np.abs(pD[:, :2]), 99.5), np.nanpercentile(np.abs(pA[:, :2]), 99.5))
    ext = (lim * ANCHO / ALTO, lim)
    res = (1080, 1920)
    rgb = disco(Rv, ext, res)
    rgb += _capa(pA, ext, res, (1.6, 8.0), _cmap(GRIS_AZUL))
    rgb += _capa(pD, ext, res, (1.6, 8.0), _cmap(VIOLETA))
    fig = plt.figure(figsize=(ANCHO / 200, ALTO / 200), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(np.clip(rgb, 0, 1), extent=[-ext[0], ext[0], -ext[1], ext[1]], origin="lower", interpolation="bilinear")
    tl = np.linspace(*t_lmc, 400)
    xl = sis.x_lmc_rel(tl) @ Rv.T
    ax.plot(xl[:, 0], xl[:, 1], color=E.COLOR_LMC, lw=1.4, alpha=0.8)
    ax.plot(xl[-1, 0], xl[-1, 1], "o", ms=10, color="#FF5C9A", mec="#FFFFFF", mew=0.6)
    ax.annotate("Large Magellanic Cloud", (xl[-1, 0], xl[-1, 1]), xytext=(14, -6), textcoords="offset points",
                color="#FF8FB8", fontsize=13)
    ax.set_xlim(-ext[0], ext[0])
    ax.set_ylim(-ext[1], ext[1])
    E.sin_ejes(ax)
    fig.text(0.03, 0.93, titulo, color="#F2F2F2", fontsize=26)
    fig.text(0.03, 0.885, subtitulo, color="#B8BEC8", fontsize=15)
    fig.text(0.97, 0.04, "violet: stream with the LMC     blue-grey: the same stream without it", color="#B8BEC8",
             fontsize=13, ha="right")
    barra = 10 ** np.floor(np.log10(0.2 * lim))
    barra *= 5 if 5 * barra < 0.3 * lim else (2 if 2 * barra < 0.3 * lim else 1)
    ax.plot([-ext[0] * 0.94, -ext[0] * 0.94 + barra], [-ext[1] * 0.9] * 2, color="#F2F2F2", lw=2)
    ax.text(-ext[0] * 0.94, -ext[1] * 0.85, "%g kpc  (%g thousand light-years)" % (barra, round(barra * 3.2616)),
            color="#F2F2F2", fontsize=12)
    return fig


def radio(tab, titulo, subtitulo):
    """Cambio del polo estrella a estrella contra el radio, en lenguaje simple."""
    import matplotlib.pyplot as plt
    E.usar(oscuro=True, agg=False)
    fig, ax = plt.subplots(figsize=(ANCHO / 300, ALTO / 300), dpi=300)
    fig.subplots_adjust(left=0.1, right=0.95, top=0.78, bottom=0.15)
    col = E.COLOR_MODELO_OSCURO
    for m, nom in (("B", "the Milky Way's wobble alone"), ("C", "the LMC's pull alone"), ("D", "both together")):
        ax.plot(tab["r_med"], tab["med_%s" % m], "-", lw=3 if m == "D" else 2, color=col[m] if m != "D" else "#FFFFFF")
        ax.text(tab["r_med"].iloc[-1] * 1.04, tab["med_%s" % m].iloc[-1], nom, color=col[m] if m != "D" else "#FFFFFF",
                fontsize=12, va="center")
    ax.set_xscale("log")
    ax.set_xlim(tab["r_med"].min() * 0.9, tab["r_med"].max() * 2.6)
    ax.set_xlabel("distance from the centre of the Milky Way (kpc)", fontsize=13)
    ax.set_ylabel("how much the orbits are tilted (degrees)", fontsize=13)
    ax.grid(True, color="#22262E", lw=0.7)
    E.log_plano(ax)
    fig.text(0.1, 0.9, titulo, color="#F2F2F2", fontsize=20)
    fig.text(0.1, 0.84, subtitulo, color="#B8BEC8", fontsize=12)
    return fig


def guardar(fig, ruta, pie, fuente):
    E.guardar(fig, ruta, pie, fuente, pdf=False, exacto=True)
