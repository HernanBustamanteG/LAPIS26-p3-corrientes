"""Contenido de los notebooks 00 a 03."""

from comun import SETUP, badge, guardar_fig, salidas


def nb00():
    return [
        ("md", badge("00_entorno.ipynb") + """

# 00 · Entorno y comprobaciones

**XII LAPIS 2026 · Proyecto 3 (J. N. Garavito-Camargo): corrientes estelares como sondas de la LMC y del
movimiento reflejo de la Vía Láctea.** Hernán Bustamante Gallagher.

Este notebook prepara el entorno y corre las pruebas del paquete `p3streams` antes de confiar en cualquier
resultado. Orden de los notebooks:

| notebook | qué hace | tiempo en Colab |
|---|---|---|
| 00 | entorno, versiones, autotest | ~2 min |
| 01 | hito 1: una corriente en la MW aislada y en MW + LMC | ~2 min |
| 02 | hito 2: los cuatro potenciales validados, $\\lvert\\mathbf a_{\\rm MW}(t)\\rvert$ y distancia de la LMC | ~4 min |
| 03 | hito 3: la corriente y sus tres métricas en los cuatro modelos; corrientes corta, larga y de dos vueltas | ~3 min |
| 04 | hito 4: el catálogo (lee el incluido; puede rehacerlo) | 1 min (o ~1.5 h) |
| 05 | hito 5: clasificación reflejo / torque y tendencias | ~1 min |
| 06 | hito 5: predicciones para LSST | ~2 min |
| 07 | hito 6: corrientes observadas; masa de la LMC | ~2 min |
| 08 | figuras finales (académicas y de prensa) | ~3 min |
| 09 | videos (MP4 y GIF) | ~10 min |

**Cómo funciona en Colab.** La primera celda de cada notebook clona este repositorio, instala versiones fijas
(`requirements-colab.txt`: gala 1.12.0 y numpy 2.2.x, porque numpy 2.3 o mayor rompe numba, que viene en Colab)
y monta Google Drive para guardar las salidas en `MyDrive/lapis26_p3/salidas/`. Si numpy cambia de versión la
sesión se reinicia una sola vez: hay que volver a ejecutar la primera celda.

**Reglas de las salidas.** Cada notebook escribe en una carpeta nueva `salidas/<notebook>_<fecha>/`; nada se
pisa. Los datos de entrada (`datos_entrada/`) son de solo lectura."""),
        ("code", SETUP),
        ("md", """## Autotest

Casos con respuesta conocida: la curva de rotación de la MW del tutorial, polos y planos de un anillo,
el desalineamiento de una corriente sintética (0° y 20°), el ángulo desenrollado, $f_{\\rm reflex}$, la isócrona,
los errores de LSST, el campo uniforme contra $-\\mathbf a_{\\rm MW}$, el modelo D contra una integración en el
marco inercial, la órbita del enunciado (pericentro ~27 kpc, e ~0.6) y la reproducibilidad con la semilla."""),
        ("code", "from p3streams import autotest\nOK = autotest.correr()\nassert OK, 'alguna prueba falla: no seguir'"),
        ("md", """## Decisiones del proyecto

Todas están en `p3streams/config.py`, con su fuente. Las principales:"""),
        ("code", """from p3streams import config as C
print("MW (tutorial):  disco MN3 %.3g Msun, bulbo %.3g, nucleo %.3g, halo NFW v_c = %.1f km/s, r_s = %.2f kpc"
      % (C.MW_DISCO["m"], C.MW_BULBO["m"], C.MW_NUCLEO["m"], C.MW_HALO["v_c"], C.MW_HALO["r_s"]))
print("LMC (tutorial): Hernquist %.2g Msun, a = %.0f kpc; hoy x = %s kpc, v = %s km/s" % (C.LMC_M, C.LMC_A, C.LMC_X0, C.LMC_V0))
print("Friccion dinamica: %s" % C.DF_LNL)
print("Sistema MW + LMC integrado %.0f Gyr hacia atras, dt = %.0f Myr; potenciales interpolados cada %.0f Myr"
      % (C.T_ATRAS / 1e3, C.DT_SISTEMA, C.DT_NUDOS))
print("Corrientes: FardalStreamDF, t_start = %.0f Gyr, dt = %.0f Myr, release_every = %d, semilla %d"
      % (C.T_START / 1e3, C.DT_CORRIENTE, C.RELEASE_EVERY, C.SEMILLA))
print("Sol (astropy v4.0): R = %.3f kpc, z = %.4f kpc, v = %s km/s" % (C.SOL_R, C.SOL_Z, C.SOL_V))
print("LSST: Dec < %.0f deg, r < %.1f (10 anios), PM r < %.1f, sigma_mu %s" % (C.LSST_DEC_MAX, C.LSST_R_LIM_10A, C.LSST_PM_R_MAX, C.LSST_PM_PUNTOS))
from p3streams import ejecutar
ejecutar.main(["planes"]);"""),
    ]


def nb01():
    return [
        ("md", badge("01_hito1_una_corriente.ipynb") + """

# 01 · Hito 1: una corriente en la MW aislada y en MW + LMC

**Qué pide el enunciado.** Un progenitor en el apocentro a ~100 kpc, hace 4 Gyr, con la mitad de la velocidad
circular local; su corriente en la MW aislada (modelo A) y en el sistema completo MW + LMC (modelo D).

**Cómo se hace aquí.**
- El sistema MW + LMC se integra hacia atrás 7 Gyr como dos cuerpos con fricción dinámica (tutorial de
  Garavito-Camargo). De ahí salen la posición de la LMC relativa a la MW, $\\mathbf x_{\\rm LMC}(t)$, y la
  aceleración del centro de la MW, $\\mathbf a_{\\rm MW}(t)$.
- Todo se escribe en el **marco de la MW** (centro de la MW fijo en el origen). Los cuatro modelos:
  A = MW; B = MW + campo uniforme $-\\mathbf a_{\\rm MW}(t)$ (masa puntual muy lejana, `TimeInterpolatedPotential`);
  C = MW + LMC móvil; D = MW + LMC móvil + campo uniforme.
- La corriente: `MockStreamGenerator` + `FardalStreamDF`, con las **mismas condiciones iniciales en el pasado y la
  misma semilla** en los cuatro modelos."""),
        ("code", SETUP),
        ("code", salidas("01_hito1")),
        ("code", """import time
from p3streams import potenciales as P, corrientes as Co, metricas as Me, figuras as F
t0 = time.time()
sis = P.integrar_sistema()           # MW + LMC hacia atras, con friccion dinamica
mods = P.modelos(sis)                # A, B, C, D
d = sis.d_lmc()
i = np.argmin(d[sis.t > -3000] if (sis.t > -3000).any() else d)
print("Sistema integrado en %.0f s" % (time.time() - t0))
print("LMC hoy a %.1f kpc del centro de la MW; pericentro reciente %.1f kpc hace %.0f Myr"
      % (d[np.argmin(np.abs(sis.t))], d[sis.t > -3000].min(), -sis.t[sis.t > -3000][np.argmin(d[sis.t > -3000])]))"""),
        ("md", """### El progenitor

Polo inicial $\\hat{\\mathbf n} = -\\hat{\\mathbf y}$ (órbita polar en el plano $x$–$z$ de la MW), apocentro 100 kpc,
$f = 0.5$, $t_{\\rm start} = 4$ Gyr, $10^7\\,M_\\odot$. Primero se comprueba en la MW aislada que la órbita sea la del
enunciado (pericentro ~27 kpc, excentricidad ~0.6)."""),
        ("code", """N0 = np.array([0.0, -1.0, 0.0])
x0, v0 = Co.condiciones_iniciales(N0, r_apo=100.0, f=0.5, psi_deg=0.0)
orb = Co.orbita(mods["A"], x0, v0, t_inicio=-4000.0)
r = Co.resumen_orbita(orb)
print("x0 = %s kpc, v0 = %s km/s" % (np.round(x0, 2), np.round(v0, 1)))
print("MW aislada: pericentro %.1f kpc, apocentro %.1f kpc, e = %.2f, periodo radial %.2f Gyr"
      % (r["peri_kpc"], r["apo_kpc"], r["ecc"], r["periodo_radial_Myr"] / 1e3))"""),
        ("code", """t0 = time.time()
CORR = {m: Co.generar(mods[m], x0, v0, m_prog=1e7, t_inicio=-4000.0) for m in "ABCD"}
print("4 corrientes en %.0f s; %d particulas cada una" % (time.time() - t0, len(CORR["A"]["pos"])))
RES, PERF = {}, {}
for m in "ABCD":
    RES[m], PERF[m] = Me.medir(CORR[m], N0)"""),
        ("code", """fig = F.hito1({m: CORR[m] for m in "AD"}, sis, N0, x0)
""" + guardar_fig("fig", "hito1_corriente_A_D.png",
                  "Milestone 1. Mock stream today (4 Gyr of disruption, 1e7 Msun progenitor starting at apocentre "
                  "100 kpc with f = 0.5) in the isolated Milky Way (A) and in the full MW + LMC system (D), in the "
                  "frame of the initial orbital plane: face-on (top) and edge-on (bottom). Magenta: LMC orbit over "
                  "the last 1.5 Gyr (dot: today). Cross: MW centre.")),
        ("md", """### Las métricas en A y D

`tilt_polo`: ángulo entre el polo medio de hoy y el polo inicial. `tilt_plano`: ángulo entre el polo inicial y
la normal del plano SVD. `desalineamiento`: mediana de $|\\Delta\\theta|$ a lo largo de la corriente, vista desde el
Sol con el movimiento propio corregido por el movimiento solar. `dispersion_polos`: mediana del ángulo de
cada polo al polo medio. `grosor`: espesor fuera del plano (1.4826 MAD)."""),
        ("code", """filas = []
for m in "AD":
    for parte in ("todo", "lider", "cola", "vieja", "joven"):
        d = RES[m].get(parte)
        if d:
            filas.append(dict(modelo=m, parte=parte, **{k: round(d[k], 2) for k in Me.METRICAS}))
TAB = pd.DataFrame(filas)
TAB.to_csv(os.path.join(SAL, "hito1_metricas.csv"), index=False)
TAB"""),
        ("md", """### La definición literal: coordenadas $(\\phi_1, \\phi_2)$ de un gran círculo

El paquete mide el desalineamiento en un marco local que sigue la traza (sirve también para corrientes de más de
una vuelta). Aquí está la versión literal del enunciado, con `GreatCircleICRSFrame` ajustado a la corriente
vista desde el Sol: las flechas son la dirección del movimiento propio (corregido por el Sol) en cada tramo."""),
        ("code", """fig = F.cielo_gran_circulo(CORR, ("A", "D"))
""" + guardar_fig("fig", "hito1_cielo_phi1_phi2.png",
                  "Milestone 1, sky view. The same streams as seen from the Sun in great-circle coordinates "
                  "(phi1, phi2) fitted to each stream. Arrows: direction of the median solar-reflex-corrected "
                  "proper motion in 4-degree bins; line: stream track (running median of 5 bins). phi1 = 0 at the circular mean of the stream. Bottom: misalignment Delta theta = "
                  "arctan(mu_phi2/mu_phi1) - arctan(dphi2/dphi1) per bin.")),
        ("code", """for m in "AD":
    d = RES[m]["todo"]
    print("%s: tilt del polo %.1f deg, tilt del plano %.1f deg, desalineamiento %.1f deg, longitud %.2f vueltas"
          % (m, d["tilt_polo_deg"], d["tilt_plano_deg"], d["desalineamiento_deg"], RES[m]["longitud_vueltas"]))
U.escribir_texto("Hito 1 (%s): progenitor polo -y, r_apo 100, f 0.5, 4 Gyr, 1e7 Msun. Peri %.1f kpc, e %.2f. "
                 "Tilt del polo A %.2f, D %.2f deg. Figuras y tabla en esta carpeta."
                 % (U.ahora(), r["peri_kpc"], r["ecc"], RES["A"]["todo"]["tilt_polo_deg"], RES["D"]["todo"]["tilt_polo_deg"]),
                 os.path.join(SAL, "registro.txt"))"""),
    ]


def nb02():
    return [
        ("md", badge("02_hito2_potenciales.ipynb") + """

# 02 · Hito 2: cuatro potenciales validados

**Qué pide el enunciado.** Los cuatro modelos validados y un gráfico de $|\\mathbf a_{\\rm MW}(t)|$ y de la
distancia de la LMC en función del tiempo.

**Las dos piezas que hay que validar.**
1. *El campo uniforme* $-\\mathbf a_{\\rm MW}(t)$ (modelos B y D). `gala` no tiene un potencial de campo uniforme:
   se imita con una masa puntual de Kepler a $d = 10^6$ kpc en la dirección $-\\hat{\\mathbf a}_{\\rm MW}(t)$, con
   $m(t) = |\\mathbf a_{\\rm MW}(t)|\\,d^2/G$ (`TimeInterpolatedPotential` con `origin` y `m` dependientes del tiempo).
   Su aceleración en la región de las corrientes debe ser $-\\mathbf a_{\\rm MW}$, con errores del orden de $r/d$.
2. *El modelo D completo.* Una partícula de prueba integrada en el modelo D (marco de la MW) tiene que seguir
   la misma trayectoria que la misma partícula integrada en el marco inercial, con la MW y la LMC moviéndose,
   cuando se resta la posición del centro de la MW."""),
        ("code", SETUP),
        ("code", salidas("02_hito2")),
        ("code", """import time
from p3streams import potenciales as P, figuras as F
sis = P.integrar_sistema()
print("Cobertura de los potenciales interpolados para t_start = 5 Gyr:", P.cobertura(sis, -5000.0))
t0 = time.time()
err = P.validar_campo(sis)
print("Campo uniforme: error relativo maximo %.1e entre 10 y 200 kpc (%.0f s)" % (err, time.time() - t0))"""),
        ("code", """t0 = time.time()
VAL = P.validar_inercial(sis)      # particula de prueba, orbita polar a 50 kpc, 4 Gyr: modelo D vs marco inercial
dx, tt, rd, ri = VAL
print("Modelo D vs marco inercial: |dx| maximo = %.2f pc en 4 Gyr (%.0f s)" % (dx * 1e3, time.time() - t0))"""),
        ("code", """fig = F.hito2(sis, val=(tt, rd, ri))
""" + guardar_fig("fig", "hito2_aMW_dLMC_validacion.png",
                  "Milestone 2. Left: distance between the LMC and the MW centre from the two-body integration "
                  "with dynamical friction (MW and LMC models of the LAPIS26 tutorial). Centre: magnitude of the "
                  "acceleration of the MW centre caused by the LMC, |a_MW(t)|; models B and D add the uniform "
                  "field -a_MW(t). Right: difference between a test particle integrated in model D (MW frame) "
                  "and the same particle integrated in the inertial frame, after subtracting the MW centre.")),
        ("md", """**Ojo con la historia orbital de la LMC en este modelo.** Con la MW y la LMC del tutorial
($1.8\\times10^{11}\\,M_\\odot$) y la fricción dinámica de van der Marel et al. (2012), la integración hacia atrás da
una LMC **ligada**, con un pericentro anterior hace ~6 Gyr (valores exactos abajo). Es una propiedad del modelo
(la masa de la MW y la fricción la determinan), no una conclusión sobre la LMC real: buena parte de la
literatura favorece una primera caída [conocimiento general, ver Vasiliev 2023]. Para las corrientes que empiezan
a formarse hace 4 a 5 Gyr, ese pericentro antiguo queda fuera; lo que las perturba es el pericentro actual."""),
        ("code", """a = np.linalg.norm(sis.a_mw(sis.t), axis=1) * 977.792221 * 1e3   # kpc/Myr^2 -> km/s/Gyr
i = np.argmax(a)
print("|a_MW| maximo = %.0f km/s/Gyr a t = %.0f Myr (LMC a %.1f kpc); hoy %.0f km/s/Gyr"
      % (a[i], sis.t[i], sis.d_lmc()[i], a[np.argmin(np.abs(sis.t))]))
print("Hace 2 Gyr: %.1f km/s/Gyr (LMC a %.0f kpc)" % (a[np.argmin(np.abs(sis.t + 2000))], sis.d_lmc()[np.argmin(np.abs(sis.t + 2000))]))
d = sis.d_lmc()
mins = np.where((d[1:-1] < d[:-2]) & (d[1:-1] <= d[2:]))[0] + 1
maxs = np.where((d[1:-1] > d[:-2]) & (d[1:-1] >= d[2:]))[0] + 1
for j in mins:
    print("Pericentro de la LMC: %.1f kpc a t = %.2f Gyr" % (d[j], sis.t[j] / 1e3))
for j in maxs:
    print("Apocentro de la LMC: %.0f kpc a t = %.2f Gyr" % (d[j], sis.t[j] / 1e3))
U.escribir_texto("Hito 2 (%s): campo uniforme error %.1e; D vs inercial %.2f pc; |a_MW| max %.0f km/s/Gyr a t = %.0f Myr."
                 % (U.ahora(), err, dx * 1e3, a[i], sis.t[i]), os.path.join(SAL, "registro.txt"))"""),
    ]


def nb03():
    return [
        ("md", badge("03_hito3_metricas.ipynb") + """

# 03 · Hito 3: la corriente y sus tres métricas en los cuatro modelos

**Qué pide el enunciado.** Una sola figura con la corriente y sus tres métricas en los cuatro modelos, y una tabla
con $\\Delta M_{\\rm reflex} = M_B - M_A$, $\\Delta M_{\\rm direct} = M_C - M_A$, $\\Delta M_{\\rm full} = M_D - M_A$ y
$f_{\\rm reflex} = |\\Delta M_{\\rm reflex}| / (|\\Delta M_{\\rm reflex}| + |\\Delta M_{\\rm direct}|)$.
También: las corrientes y las métricas a lo largo de la corriente para una corriente **corta**, una **larga** y
una de **dos vueltas** (resultados esperados del enunciado).

**El piso del modelo A.** Lo que se mide en A no viene de la LMC: viene del disco (que hace precesar los planos
orbitales que no son polares), de la dispersión de las estrellas liberadas y del propio método. Es el piso
contra el que se comparan B, C y D."""),
        ("code", SETUP),
        ("code", salidas("03_hito3")),
        ("code", """import time
from p3streams import potenciales as P, corrientes as Co, metricas as Me, figuras as F, catalogo as Ca
sis = P.integrar_sistema()
mods = P.modelos(sis)

def cuatro(polo, r_apo, m_prog, t_start, f=0.5, psi=0.0):
    x0, v0 = Co.condiciones_iniciales(polo, r_apo, f, psi)
    corr = {m: Co.generar(mods[m], x0, v0, m_prog=m_prog, t_inicio=-t_start) for m in "ABCD"}
    res, perf = {}, {}
    for m in "ABCD":
        res[m], perf[m] = Me.medir(corr[m], polo)
    return x0, corr, res, perf

def tabla(res, parte="todo"):
    filas = []
    for met, nombre in (("desalineamiento_deg", "PM misalignment (deg)"), ("tilt_polo_deg", "pole tilt (deg)"),
                        ("tilt_plano_deg", "plane tilt, SVD (deg)"), ("dispersion_polos_deg", "pole spread (deg)")):
        p = Me.perturbaciones(res, met, parte)
        filas.append([nombre, "%.2f" % res["A"][parte][met], "%+.2f" % p["dM_reflex"], "%+.2f" % p["dM_direct"],
                      "%+.2f" % p["dM_full"], "%.2f" % p["f_reflex"], Me.clase(p["f_reflex"])])
    cp = Me.cambio_polo(res, parte)
    filas.append(["pole change vs A (deg)", "0", "%.2f" % cp["B"], "%.2f" % cp["C"], "%.2f" % cp["D"],
                  "%.2f" % cp["f_reflex"], Me.clase(cp["f_reflex"])])
    return filas

COLS = ["metric", "M_A", "dM_reflex", "dM_direct", "dM_full", "f_reflex", "class"]
N0 = np.array([0.0, -1.0, 0.0])
t0 = time.time()
x0, CORR, RES, PERF = cuatro(N0, 100.0, 1e7, 4000.0)
print("Progenitor del hito 1: 4 modelos en %.0f s" % (time.time() - t0))
pd.DataFrame(tabla(RES), columns=COLS)"""),
        ("code", """fig, ax_tabla = F.hito3(CORR, PERF, N0, x0, sis)
F.tabla_en_eje(ax_tabla, tabla(RES), COLS, titulo="Perturbations (whole stream)")
""" + guardar_fig("fig", "hito3_figura_unica.png",
                  "Milestone 3. Top: the milestone-1 stream today in the four models (A isolated MW, B reflex "
                  "only, C direct LMC pull only, D full MW + LMC), face-on in the initial orbital plane; magenta: "
                  "LMC orbit over the last 1.5 Gyr. Middle and bottom: the three metrics along the stream (angle "
                  "from the progenitor in the plane of the mean pole; leading arm > 0): proper-motion "
                  "misalignment seen from the Sun, tilt of the stars' orbital poles from the initial pole, and "
                  "height above the initial orbital plane. Table: perturbations relative to model A and reflex "
                  "fraction f_reflex = |dM_reflex| / (|dM_reflex| + |dM_direct|).")),
        ("md", """### Corrientes corta, larga y de dos vueltas

Las tres familias del catálogo (notebook 04), con el mismo polo $-\\hat{\\mathbf y}$ y $t_{\\rm start} = 5$ Gyr:

| familia | $r_{\\rm apo}$ | $M_{\\rm prog}$ | longitud en la MW aislada |
|---|---|---|---|
| corta | 100 kpc | $10^7\\,M_\\odot$ | ~0.3 vueltas |
| larga | 60 kpc | $5\\times10^7\\,M_\\odot$ | ~1.1 vueltas |
| doble | 40 kpc | $10^8\\,M_\\odot$ | ~1.7 vueltas |"""),
        ("code", """REPR = {}
for fam in ("corta", "larga", "doble"):
    p = Ca.FAMILIAS[fam]
    t0 = time.time()
    REPR[fam] = cuatro(N0, p["r_apo"], p["m_prog"], C.T_START)
    print("%s: %.2f vueltas en A, %.0f s" % (fam, REPR[fam][2]["A"]["longitud_vueltas"], time.time() - t0))"""),
        ("code", """NOMBRE = {"corta": "short stream (r_apo = 100 kpc, 1e7 Msun)", "larga": "long stream (r_apo = 60 kpc, 5e7 Msun)",
          "doble": "two-wrap stream (r_apo = 40 kpc, 1e8 Msun)"}
for fam, (x0f, cf, rf, pf) in REPR.items():
    fig, axt = F.hito3(cf, pf, N0, x0f, sis, titulo=NOMBRE[fam] + ", 5 Gyr")
    F.tabla_en_eje(axt, tabla(rf), COLS, titulo="Perturbations (whole stream)")
    E.guardar(fig, os.path.join(SAL, "hito3_%s.png" % fam), "Stream and metrics in the four models: " + NOMBRE[fam]
              + ", initial pole -y, t_start = 5 Gyr. Panels as in the milestone-3 figure.", FUENTE, pdf=True)
    plt.show()"""),
        ("md", """### Viejo contra joven

La corriente de dos vueltas se separa por la mediana del tiempo de liberación: la parte **vieja** (liberada
antes) y la **joven**."""),
        ("code", """filas = []
for fam, (x0f, cf, rf, pf) in REPR.items():
    for parte in ("vieja", "joven", "lider", "cola"):
        for met in ("tilt_polo_deg", "desalineamiento_deg"):
            p = Me.perturbaciones(rf, met, parte)
            filas.append(dict(familia=fam, parte=parte, metrica=met, M_A=rf["A"][parte][met],
                              dM_reflex=p["dM_reflex"], dM_direct=p["dM_direct"], dM_full=p["dM_full"],
                              f_reflex=p["f_reflex"]))
PARTES = pd.DataFrame(filas).round(2)
PARTES.to_csv(os.path.join(SAL, "hito3_partes.csv"), index=False)
PARTES"""),
        ("md", """## Qué muestra el hito 3

- En la corriente del hito 1, el reflejo solo inclina el polo medio ~20°, el tirón solo ~5° y el sistema completo
  ~10° [comprobado, tabla de arriba]: los dos efectos se oponen en parte, como dice el enunciado (~20° contra ~10°).
  Por el cambio del polo es una corriente dominada por el reflejo ($f_{\\rm reflex}$ ≈ 0.8). Por el desalineamiento
  queda mixta (~0.4): **la clase depende de la métrica** [comprobado].
- En el modelo A todo es casi cero para esta órbita polar (piso ~0.02° en el polo y ~0.8° en el desalineamiento).
  En las órbitas no polares el disco hace precesar el plano y el piso crece (notebook 04).
- $\\Delta M_{\\rm full}$ no es $\\Delta M_{\\rm reflex} + \\Delta M_{\\rm direct}$: la respuesta no es lineal [comprobado].
- Las tres corrientes representativas y la comparación entre restos viejos y jóvenes se generalizan con el
  catálogo en los notebooks 04 y 05."""),
    ]
