"""Videos (MP4 H.264 + GIF) de la formacion de una corriente en los cuatro modelos. Fondo negro solido.

Las instantaneas salen del propio generador de gala (MockStreamGenerator con output_every, integrador DOP853,
archivo HDF5), como sugiere el enunciado; la corriente final coincide con la del catalogo (leapfrog) a ~1e-4 kpc.
  - academico: 2 x 2 paneles (A, B, C, D) en el plano orbital inicial, con la orbita de la LMC, y abajo la
    inclinacion del polo medio respecto del polo inicial en funcion del tiempo.
  - prensa: un panel, densidad 'luminosa' del modelo D sobre el fantasma del modelo A (MW aislada), sin ejes.
Nada se pisa: si el archivo existe, se detiene.
"""

import os
import shutil
import subprocess

import numpy as np

from . import config as C
from . import estilo as E

FPS = 30
TAM = (1920, 1080)


def simular(fila, sis, carpeta, modelos="ABCD", output_every=10, mods=None):
    """Corre los modelos de un progenitor guardando instantaneas. Devuelve {modelo: ruta .h5}."""
    import astropy.units as u
    import gala.dynamics as gd
    import gala.potential as gp
    from gala.dynamics import mockstream as ms
    from gala.integrate import DOPRI853Integrator
    from . import corrientes as Co, potenciales as P
    mods = mods or P.modelos(sis)
    x0, v0 = Co.condiciones_iniciales(fila["polo"], fila["r_apo"], fila["f"], fila["psi_deg"])
    t_ini = -fila["t_start"]
    os.makedirs(carpeta, exist_ok=True)
    rutas = {}
    for m in modelos:
        ruta = os.path.join(carpeta, "%s_%s.h5" % (fila["id"], m))
        rutas[m] = ruta
        if os.path.exists(ruta):
            continue
        df = ms.FardalStreamDF(gala_modified=True, random_state=np.random.RandomState(C.SEMILLA))
        gen = ms.MockStreamGenerator(df, gp.Hamiltonian(mods[m]))
        w0 = gd.PhaseSpacePosition(pos=np.asarray(x0) * u.kpc, vel=np.asarray(v0) * u.km / u.s)
        st, _ = gen.run(w0, fila["m_prog"] * u.Msun, dt=C.DT_CORRIENTE * u.Myr,
                        n_steps=int(round(-t_ini / C.DT_CORRIENTE)), t1=t_ini * u.Myr,
                        release_every=C.RELEASE_EVERY, n_particles=C.N_PARTICULAS, output_every=output_every,
                        output_filename=ruta, Integrator=DOPRI853Integrator, check_filesize=False, overwrite=False)
        import h5py
        with h5py.File(ruta, "a") as f:
            f["stream/release_time"] = np.asarray(st.release_time.to_value(u.Myr))
    return rutas


def leer(ruta):
    import h5py
    with h5py.File(ruta, "r") as f:
        return dict(t=f["stream/time"][:], pos=np.transpose(f["stream/pos"][:], (1, 2, 0)).astype(np.float32),
                    vel=np.transpose(f["stream/vel"][:], (1, 2, 0)).astype(np.float32),
                    prog=np.transpose(f["nbody/pos"][:, :, 0], (1, 0)))


def tilt_en_el_tiempo(s, n0):
    """Angulo [grados] entre el polo medio de las estrellas ya liberadas y el polo inicial, en cada instantanea."""
    from . import metricas as Me
    out = np.full(len(s["t"]), np.nan)
    for i in range(len(s["t"])):
        p, v = s["pos"][i], s["vel"][i]
        ok = np.isfinite(p[:, 0])
        if ok.sum() >= 30:
            out[i] = Me.angulo(Me.polo_medio(Me.polos(p[ok].astype(float), v[ok].astype(float))), n0)
    return out


class EscritorMP4:
    """Recibe figuras de matplotlib y las manda a ffmpeg (H.264, yuv420p, crf 16). No pisa archivos."""

    def __init__(self, ruta, fps=FPS, titulo="", comentario=""):
        if os.path.exists(ruta):
            raise FileExistsError(ruta)
        if not shutil.which("ffmpeg"):
            raise RuntimeError("ffmpeg no esta instalado")
        self.ruta, self.fps, self.p = ruta, fps, None
        self.meta = ["-metadata", "title=%s" % titulo, "-metadata", "comment=%s" % comentario]

    def agregar(self, fig):
        fig.canvas.draw()
        w, h = fig.canvas.get_width_height(physical=True)
        buf = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
        if self.p is None:
            self.p = subprocess.Popen(["ffmpeg", "-n", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                       "-s", "%dx%d" % (w, h), "-r", str(self.fps), "-i", "-", "-c:v", "libx264",
                                       "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
                                       "-movflags", "+faststart"] + self.meta + [self.ruta], stdin=subprocess.PIPE)
        self.p.stdin.write(np.ascontiguousarray(buf).tobytes())

    def cerrar(self):
        if self.p:
            self.p.stdin.close()
            if self.p.wait():
                raise RuntimeError("ffmpeg fallo")


def a_gif(mp4, gif, ancho=960, fps=15):
    """GIF con paleta optimizada (dos pasadas de ffmpeg). No pisa."""
    if os.path.exists(gif):
        raise FileExistsError(gif)
    filtro = "fps=%d,scale=%d:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=192[p];[b][p]paletteuse=dither=sierra2_4a" \
        % (fps, ancho)
    subprocess.run(["ffmpeg", "-n", "-loglevel", "error", "-i", mp4, "-vf", filtro, gif], check=True)


def academico(snaps, sis, n0, x0, ruta, titulo="", paso=1, procedencia=""):
    """snaps: {modelo: dict de leer()}. Un cuadro por instantanea (cada `paso`)."""
    import matplotlib.pyplot as plt
    from . import figuras as F
    E.usar(oscuro=True, agg=True)
    Rm = F.marco_plano(n0, x0)
    t = snaps["A"]["t"]
    tilts = {m: tilt_en_el_tiempo(s, n0) for m, s in snaps.items()}
    fin = {m: s["pos"][-1] @ Rm.T for m, s in snaps.items()}
    lim = 1.12 * max(np.nanpercentile(np.abs(p[:, :2]), 99.5) for p in fin.values())
    xl = sis.x_lmc_rel(t) @ Rm.T
    fig = plt.figure(figsize=(TAM[0] / 100, TAM[1] / 100), dpi=100)
    gs = fig.add_gridspec(2, 3, width_ratios=[1, 1, 1.35], height_ratios=[1, 1], left=0.035, right=0.975,
                          bottom=0.09, top=0.9, wspace=0.12, hspace=0.16)
    ejes = {m: fig.add_subplot(gs[i // 2, i % 2]) for i, m in enumerate("ABCD")}
    ax_t = fig.add_subplot(gs[:, 2])
    col = E.COLOR_MODELO_OSCURO
    arts = {}
    for m, A in ejes.items():
        A.set_xlim(-lim, lim)
        A.set_ylim(-lim, lim)
        A.set_aspect("equal")
        E.sin_ejes(A)
        A.set_title(E.NOMBRE_MODELO[m], color=col[m], loc="left", fontsize=15)
        A.plot(0, 0, "+", color="#8A8F98", ms=10)
        arts[m] = dict(sc=A.scatter([], [], s=1.3, color=col[m], alpha=0.75, lw=0),
                       pr=A.plot([], [], "o", ms=5, color="#F2F2F2")[0])
        if m in "CD":
            arts[m]["lmc"] = A.plot([], [], color=E.COLOR_LMC, lw=1.5, alpha=0.9)[0]
            arts[m]["lmcp"] = A.plot([], [], "o", ms=9, color=E.COLOR_LMC)[0]
    barra = 0.2 * lim
    nb = 10 ** np.floor(np.log10(barra))
    barra = nb * np.round(barra / nb)
    A = ejes["A"]
    A.plot([-lim * 0.92, -lim * 0.92 + barra], [-lim * 0.9] * 2, color="#F2F2F2", lw=2)
    A.text(-lim * 0.92, -lim * 0.84, "%g kpc" % barra, color="#F2F2F2", fontsize=12)
    ax_t.set_xlim(t[0] / 1e3, 0)
    tmax = np.nanmax([np.nanmax(v) for v in tilts.values()])
    ax_t.set_ylim(0, 1.15 * tmax)
    ax_t.set_xlabel("time (Gyr)", fontsize=14)
    ax_t.set_ylabel("tilt of the mean orbital pole (deg)", fontsize=14)
    ax_t.grid(True, color="#2A2F38", lw=0.7)
    lin = {m: ax_t.plot([], [], color=col[m], lw=2.2, label=m)[0] for m in "ABCD"}
    ax_t.legend(loc="upper left", fontsize=13)
    rel = fig.text(0.035, 0.035, "", color="#F2F2F2", fontsize=16)
    fig.text(0.035, 0.94, titulo, color="#F2F2F2", fontsize=18)
    E.numeros_rectos(fig)
    w = EscritorMP4(ruta, titulo=titulo, comentario=procedencia)
    try:
        for i in range(0, len(t), paso):
            for m, s in snaps.items():
                p = s["pos"][i] @ Rm.T
                ok = np.isfinite(p[:, 0])
                arts[m]["sc"].set_offsets(p[ok][:, :2])
                pg = s["prog"][i] @ Rm.T
                arts[m]["pr"].set_data([pg[0]], [pg[1]])
                if "lmc" in arts[m]:
                    j0 = max(0, i - 60)
                    arts[m]["lmc"].set_data(xl[j0:i + 1, 0], xl[j0:i + 1, 1])
                    arts[m]["lmcp"].set_data([xl[i, 0]], [xl[i, 1]])
            for m in "ABCD":
                lin[m].set_data(t[:i + 1] / 1e3, tilts[m][:i + 1])
            rel.set_text("t = %+.2f Gyr" % (t[i] / 1e3))
            w.agregar(fig)
    finally:
        w.cerrar()
        plt.close(fig)
    return ruta


def _densidad(p2, ext, res, sig):
    from scipy.ndimage import gaussian_filter
    H, _, _ = np.histogram2d(p2[:, 1], p2[:, 0], bins=res, range=[[-ext[1], ext[1]], [-ext[0], ext[0]]])
    return gaussian_filter(H, sig[0]) + 0.35 * gaussian_filter(H, sig[1])


def prensa(snapD, snapA, sis, n0, x0, ruta, titulo="", paso=1, procedencia="", inclinacion=62.0):
    """Densidad luminosa del modelo D (violeta-blanco) sobre el modelo A (gris azulado), vista oblicua del plano
    orbital inicial, con la LMC y su estela. Sin ejes."""
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    from . import figuras as F
    E.usar(oscuro=True, agg=True)
    Rm = F.marco_plano(n0, x0)
    c, s_ = np.cos(np.radians(inclinacion)), np.sin(np.radians(inclinacion))
    Rv = np.array([[1, 0, 0], [0, c, -s_], [0, s_, c]]) @ Rm
    t = snapD["t"]
    fin = snapD["pos"][-1] @ Rv.T
    lim = 1.1 * max(np.nanpercentile(np.abs(fin[:, :2]), 99.5), np.nanpercentile(np.abs(snapA["pos"][-1] @ Rv.T)[:, :2], 99.5))
    ext = (lim * TAM[0] / TAM[1], lim)
    res = (540, 960)
    cmD = LinearSegmentedColormap.from_list("d", ["#000000", "#2B1150", "#6E3FB0", "#B98CF0", "#FFFFFF"])
    cmA = LinearSegmentedColormap.from_list("a", ["#000000", "#16202C", "#3C5470", "#8FA6C4"])
    xl = sis.x_lmc_rel(t) @ Rv.T
    fig = plt.figure(figsize=(TAM[0] / 100, TAM[1] / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(-ext[0], ext[0])
    ax.set_ylim(-ext[1], ext[1])
    E.sin_ejes(ax)
    im = ax.imshow(np.zeros(res + (3,)), extent=[-ext[0], ext[0], -ext[1], ext[1]], origin="lower",
                   interpolation="bilinear")
    # disco de la MW: muestra del disco exponencial (h_R, h_z del modelo) proyectada, como brillo calido tenue
    rgd = np.random.default_rng(0)
    R = rgd.gamma(2.0, C.MW_DISCO["h_R"], 60000)
    ph = rgd.uniform(0, 2 * np.pi, 60000)
    z = rgd.laplace(0, C.MW_DISCO["h_z"], 60000)
    dsk = np.column_stack([R * np.cos(ph), R * np.sin(ph), z]) @ Rv.T
    Hd = _densidad(dsk, ext, res, (1.5, 5.0))
    cmW = LinearSegmentedColormap.from_list("w", ["#000000", "#2A2216", "#7A6640", "#F2E6C8"])
    capa_disco = cmW(np.clip(np.arcsinh(Hd / np.percentile(Hd[Hd > 0], 99.5) * 4) / np.arcsinh(4), 0, 1))[:, :, :3] * 0.55
    lmc_l, = ax.plot([], [], color=E.COLOR_LMC, lw=1.6, alpha=0.75)
    lmc_p, = ax.plot([], [], "o", ms=11, color="#FF5C9A", mec="#FFFFFF", mew=0.6)
    txt_t = fig.text(0.03, 0.05, "", color="#F2F2F2", fontsize=22)
    fig.text(0.03, 0.92, titulo, color="#F2F2F2", fontsize=26)
    fig.text(0.97, 0.05, "violet: Milky Way + LMC    blue-grey: Milky Way alone", color="#B8BEC8", fontsize=15,
             ha="right")
    w = EscritorMP4(ruta, titulo=titulo, comentario=procedencia)
    norma = None
    try:
        for i in range(0, len(t), paso):
            capas = []
            for s, cm in ((snapA, cmA), (snapD, cmD)):
                p = s["pos"][i] @ Rv.T
                ok = np.isfinite(p[:, 0])
                H = _densidad(p[ok], ext, res, (1.2, 6.0)) if ok.sum() else np.zeros(res)
                capas.append((H, cm))
            if norma is None or i % 20 == 0:
                norma = max(np.percentile(capas[1][0][capas[1][0] > 0], 99.7) if (capas[1][0] > 0).any() else 1,
                            norma or 0)
            rgb = capa_disco.copy()
            for H, cm in capas:
                rgb += cm(np.clip(np.arcsinh(H / norma * 6) / np.arcsinh(6), 0, 1))[:, :, :3]
            im.set_data(np.clip(rgb, 0, 1))
            j0 = max(0, i - 35)          # estela de la LMC: ultimos ~350 Myr
            lmc_l.set_data(xl[j0:i + 1, 0], xl[j0:i + 1, 1])
            lmc_p.set_data([xl[i, 0]], [xl[i, 1]])
            txt_t.set_text("%.1f billion years ago" % (-t[i] / 1e3) if t[i] < -50 else "today")
            w.agregar(fig)
    finally:
        w.cerrar()
        plt.close(fig)
    return ruta
