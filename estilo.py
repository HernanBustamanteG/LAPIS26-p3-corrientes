"""Estilo de las figuras (mismas decisiones que el proyecto de F. Gomez):
graficos con fondo blanco solido, imagenes y version de prensa con fondo negro solido, Inter Light Italic
(licencia OFL, incluida) con los numeros de los ejes sin cursiva, rotulos en ingles, y la procedencia
(script, fecha, datos de entrada) en los metadatos del PNG, no dibujada.
"""

import os

FUENTES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fuentes")
TINTA, TINTA_SUAVE, GRILLA = "#15233B", "#5B6472", "#E6E8EB"
# Modelos: A referencia gris; B reflejo azul; C tiron directo naranja; D completo violeta
# (B, C, D validados: banda de luminosidad, croma, separacion CVD y contraste sobre blanco)
COLOR_MODELO = {"A": "#8A8F98", "B": "#1F5E99", "C": "#D0663F", "D": "#7A4BA8"}
COLOR_MODELO_OSCURO = {"A": "#B8BEC8", "B": "#4F9AD6", "C": "#E8834F", "D": "#A47FD6"}
NOMBRE_MODELO = {"A": "A  MW isolated", "B": "B  reflex only", "C": "C  direct pull only", "D": "D  MW + LMC"}
COLOR_CLASE = {"reflex": "#1F5E99", "torque": "#D0663F", "mixed": "#8A8F98", "undetermined": "#D9DCE1"}
COLOR_LMC = "#C2185B"


def usar(oscuro=False, agg=False):
    """Configura matplotlib. agg=True solo en scripts sin pantalla (en Colab/Jupyter se deja el backend)."""
    import logging
    import matplotlib
    # matplotlib avisa cuando una fuente de respaldo (cm, STIX) no tiene peso 300: es cosmetico
    logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
    if agg:
        matplotlib.use("Agg")
    from matplotlib import font_manager, rcParams
    for f in ("Inter-Light.otf", "Inter-LightItalic.otf", "Inter-Regular.otf"):
        ruta = os.path.join(FUENTES, f)
        if os.path.exists(ruta):
            font_manager.fontManager.addfont(ruta)
    font_manager.fontManager.ttflist = [x for x in font_manager.fontManager.ttflist
                                        if x.name != "Inter" or os.path.dirname(x.fname) == FUENTES]
    if hasattr(font_manager.fontManager, "_findfont_cached"):
        font_manager.fontManager._findfont_cached.cache_clear()
    fondo, tinta, suave = ("#000000", "#F2F2F2", "#B8BEC8") if oscuro else ("#FFFFFF", TINTA, TINTA_SUAVE)
    rcParams.update({
        "font.family": "Inter", "font.weight": 300, "font.style": "italic", "font.size": 12,
        "mathtext.fontset": "custom", "mathtext.rm": "Inter:weight=300", "mathtext.it": "Inter:italic:weight=300",
        "mathtext.bf": "Inter:weight=400", "mathtext.sf": "Inter:weight=300", "mathtext.cal": "Inter:italic:weight=300",
        "mathtext.tt": "DejaVu Sans Mono", "mathtext.fallback": "cm",
        "figure.facecolor": fondo, "axes.facecolor": fondo, "savefig.facecolor": fondo,
        "text.color": tinta, "axes.labelcolor": tinta, "axes.edgecolor": suave, "xtick.color": suave,
        "ytick.color": suave, "axes.titlecolor": tinta, "axes.titlesize": 13, "axes.labelsize": 12,
        "axes.titleweight": 300, "axes.labelweight": 300, "axes.linewidth": 0.8,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.prop_cycle": matplotlib.cycler(color=[COLOR_MODELO[k] for k in "BCDA"]),
        "xtick.labelsize": 11, "ytick.labelsize": 11, "legend.frameon": False, "legend.fontsize": 11,
        "lines.linewidth": 1.8, "figure.dpi": 100, "savefig.dpi": 200, "savefig.bbox": "tight",
        "savefig.pad_inches": 0.12, "image.origin": "lower"})


def numeros_rectos(fig):
    for ax in fig.axes:
        if ax.name == "rectilinear":
            log_plano(ax)
        for t in ax.get_xticklabels() + ax.get_yticklabels():
            t.set_fontstyle("normal")


def grilla(ax, eje="both"):
    ax.grid(True, axis=eje, color=GRILLA, lw=0.7)
    ax.set_axisbelow(True)


def guardar(fig, ruta, pie, fuente, cerrar=False, pdf=False, exacto=False):
    """PNG (y PDF opcional) con pie y procedencia en los metadatos. No pisa archivos existentes.
    exacto=True: el lienzo completo al tamano y dpi de la figura (prensa 4K), sin recorte."""
    import matplotlib.pyplot as plt
    numeros_rectos(fig)
    if os.path.exists(ruta):
        raise FileExistsError(ruta)
    kw = dict(bbox_inches=fig.bbox_inches, dpi="figure", pad_inches=0) if exacto else {}
    fig.savefig(ruta, metadata={"Title": os.path.basename(ruta), "Description": pie, "Source": fuente,
                                "Software": "p3streams (XII LAPIS 2026) + gala + matplotlib"}, **kw)
    if pdf:
        fig.savefig(os.path.splitext(ruta)[0] + ".pdf", metadata={"Title": os.path.basename(ruta),
                                                                   "Subject": pie, "Creator": fuente})
    if cerrar:
        plt.close(fig)


def sin_ejes(ax):
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def log_plano(ax, eje="both"):
    """Numeros planos (20, 50, 100) en ejes logaritmicos en vez de 2x10^1."""
    from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter
    fmt = FuncFormatter(lambda v, _: ("%g" % v))
    for nombre in (("x", "y") if eje == "both" else (eje,)):
        a = getattr(ax, nombre + "axis")
        if a.get_scale() == "log":
            a.set_major_locator(LogLocator(base=10, subs=(1.0, 2.0, 5.0)))
            a.set_major_formatter(fmt)
            a.set_minor_formatter(NullFormatter())
