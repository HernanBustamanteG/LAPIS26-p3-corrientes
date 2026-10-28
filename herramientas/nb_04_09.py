"""Contenido de los notebooks 04 a 09."""

from comun import SETUP, badge, guardar_fig, salidas

CARGA = '''from p3streams import resultados as R, analisis as An, metricas as Me, figuras as F, potenciales as P
PROPIOS = False          # True: usar la corrida propia mas reciente (salidas/) en vez de la incluida en resultados/
DF, ORIGEN = R.cargar("catalogo_principal", propios=PROPIOS)
print("Catalogo: %d corrientes, leido de %s" % (len(DF), ORIGEN))
sis = P.integrar_sistema()          # el mismo sistema MW + LMC (1.8e11 Msun) del catalogo
DF = An.agregar_geometria(DF, sis)'''


def nb04():
    return [
        ("md", badge("04_hito4_catalogo.ipynb") + """

# 04 · Hito 4: el catálogo

**Qué pide el enunciado.** Un conjunto de corrientes con la parametrización (polo, fase, apocentro, $f$), con
corrientes cortas (< media vuelta), largas (~1 vuelta) y de dos vueltas; para cada una: polo inicial, apocentro,
pericentro, excentricidad, longitud (en vueltas), acercamiento mínimo a la LMC y todas las métricas en los cuatro
modelos. Empezar chico (12 polos × 2 sentidos × 2 apocentros) antes de una grilla grande.

**Diseño.**
- *Piloto* (el "empezar chico"): 12 polos de Fibonacci × 2 sentidos × 3 familias = 72 corrientes.
- *Principal*: los 48 polos HEALPix de `nside = 2` (que ya contienen $\\hat{\\mathbf n}$ y $-\\hat{\\mathbf n}$, es decir
  los dos sentidos de giro) × 3 familias × 2 fases $\\psi \\in \\{0°, 90°\\}$ = 288 corrientes.
- Las tres familias se calibraron en la MW aislada con $t_{\\rm start} = 5$ Gyr y $f = 0.5$ (longitud en vueltas):

| $r_{\\rm apo}$ (kpc) | $10^7\\,M_\\odot$ | $5\\times10^7$ | $10^8$ |
|---|---|---|---|
| 25 | 1.59 | 1.76 | 1.80 |
| 40 | 1.26 | 1.61 | **1.72 (doble)** |
| 60 | 0.73 | **1.14 (larga)** | 1.57 |
| 100 | **0.30 (corta)** | 1.11 | 1.31 |

- Cada corriente se guarda en su archivo y cada fila en `filas/<id>.json`: si la sesión de Colab se corta, la
  corrida se **retoma** donde quedó.
- Costo medido: 17 a 50 s por progenitor (cuatro modelos); la principal tarda ~1.5 h con 2 núcleos.

El repositorio trae los catálogos ya calculados en `resultados/` (con su procedencia en `resultados/PROCEDENCIA.md`).
Para rehacerlos, poner `CORRER = True` (o usar la terminal: `python -m p3streams.ejecutar grilla --plan principal --correr`)."""),
        ("code", SETUP),
        ("code", salidas("04_hito4")),
        ("code", """CORRER = False           # True: rehacer la grilla (en Colab, ~1.5 h para 'principal'; se puede retomar)
PLAN = "principal"
from p3streams import ejecutar
ejecutar.main(["grilla", "--plan", PLAN, "--simular"])
if CORRER:
    ejecutar.main(["grilla", "--plan", PLAN, "--correr", "--procesos", str(os.cpu_count() or 1)])"""),
        ("code", CARGA + '''
PIL, _ = R.cargar("catalogo_piloto")
print("Piloto: %d corrientes" % len(PIL))'''),
        ("md", """### Las columnas que pide el hito 4

Una fila por corriente: `polo` (inicial), `apo_kpc`, `peri_kpc`, `ecc`, `longitud_vueltas_<modelo>`,
`dmin_lmc_kpc` (acercamiento mínimo del progenitor a la LMC en el modelo D) y, para cada métrica, parte y modelo,
`<metrica>_<parte>_<modelo>`; además $\\Delta M$, $f_{\\rm reflex}$ y el término no lineal."""),
        ("code", """cols = ["id", "familia", "psi_deg", "apo_kpc", "peri_kpc", "ecc", "longitud_vueltas_A", "dmin_lmc_kpc",
        "tilt_polo_deg_todo_A", "tilt_polo_deg_todo_D", "desalineamiento_deg_todo_A", "desalineamiento_deg_todo_D",
        "dpolo_B_todo", "dpolo_C_todo", "dpolo_D_todo", "dpolo_f_reflex_todo"]
print("Columnas en total:", DF.shape[1])
DF[cols].head(8).round(2)"""),
        ("code", """RES = DF.groupby("familia")[["longitud_vueltas_A", "longitud_vueltas_D", "peri_kpc", "apo_kpc", "ecc",
                               "dmin_lmc_kpc", "segundos"]].median().round(2)
RES["n"] = DF.groupby("familia").size()
RES.to_csv(os.path.join(SAL, "hito4_resumen_familias.csv"))
RES"""),
        ("md", """### El piso del modelo A

Lo que miden las métricas en la MW aislada. Las inclinaciones respecto del polo inicial **no** son cero en A: el
disco hace precesar los planos orbitales que no son polares, más cuanto más cerca pasan del centro. Por eso, para
el polo, se usa además el **cambio vectorial del polo respecto del modelo A** (`dpolo_B`, `dpolo_C`, `dpolo_D`),
que no incluye la precesión por el disco (está igual en los cuatro modelos)."""),
        ("code", """PISO = DF.groupby("familia")[["desalineamiento_deg_todo_A", "tilt_polo_deg_todo_A", "tilt_plano_deg_todo_A",
                                "dispersion_polos_deg_todo_A", "grosor_kpc_todo_A"]].median().round(2)
PISO"""),
        ("code", """fig, ax = plt.subplots(1, 3, figsize=(15, 4.3))
COLF = {"corta": E.COLOR_MODELO["B"], "larga": E.COLOR_MODELO["D"], "doble": E.COLOR_MODELO["C"]}
NOMF = {"corta": "short (r_apo 100 kpc, 1e7)", "larga": "long (60 kpc, 5e7)", "doble": "two-wrap (40 kpc, 1e8)"}
for fam in ("corta", "larga", "doble"):
    s = DF["familia"] == fam
    ax[0].hist(DF.loc[s, "longitud_vueltas_A"], bins=np.linspace(0, 2.2, 45), color=COLF[fam], alpha=0.8, label=NOMF[fam])
    ax[1].scatter(DF.loc[s, "peri_kpc"], DF.loc[s, "dmin_lmc_kpc"], s=14, color=COLF[fam], alpha=0.7, lw=0)
ax[0].set_xlabel("stream length in model A (wraps)"); ax[0].set_ylabel("number of streams"); ax[0].legend(fontsize=9)
ax[1].set_xlabel("pericentre in model A (kpc)"); ax[1].set_ylabel("closest approach to the LMC (kpc)"); ax[1].set_yscale("log")
z = np.abs(np.array(DF["polo"].tolist())[:, 2])
for fam in ("corta", "larga", "doble"):
    s = (DF["familia"] == fam).to_numpy()
    ax[2].scatter(z[s], DF.loc[s, "tilt_polo_deg_todo_A"], s=14, color=COLF[fam], alpha=0.7, lw=0)
ax[2].set_xlabel(r"$|\\hat{n}_{0,z}|$  (0: polar orbit, 1: in the disc plane)")
ax[2].set_ylabel("pole tilt in model A (deg)")
for A in ax: E.grilla(A)
fig.tight_layout()
""" + guardar_fig("fig", "hito4_catalogo.png",
                  "Milestone 4, the catalogue. Left: stream lengths in the isolated MW (model A) for the three "
                  "families. Centre: pericentre against the closest approach of the progenitor to the LMC (model "
                  "D). Right: tilt of the mean orbital pole from the initial pole in model A, against the z "
                  "component of the initial pole: the disc makes non-polar orbital planes precess, which sets the "
                  "floor of the tilt metrics.")),
        ("code", """from p3streams import resultados as R2
ruta = R2.exportar(DF.drop(columns=["sentido_lmc"]), "hito4_catalogo_con_geometria", SAL)
print("Catalogo exportado:", ruta)"""),
    ]


def nb05():
    return [
        ("md", badge("05_hito5_clasificacion.ipynb") + """

# 05 · Hito 5: ¿qué corrientes sienten qué?

Preguntas del enunciado: qué corrientes están dominadas por el **reflejo** ($f_{\\rm reflex} > 0.6$) y cuáles por el
**torque** o tirón directo ($< 0.4$); mapa de $f_{\\rm reflex}$ sobre los polos iniciales; dependencia con la distancia,
la orientación del plano (respecto de la órbita de la LMC y de $\\mathbf a_{\\rm MW}$), el acercamiento a la LMC, el
sentido de giro, la longitud y la edad de los restos; qué métrica es más sensible a cada efecto; y si hay órbitas
en que los dos efectos se cancelan."""),
        ("code", SETUP),
        ("code", salidas("05_hito5")),
        ("code", CARGA),
        ("md", """### Sensibilidad de cada métrica

Piso = mediana en el modelo A. Para el cambio del polo, el piso de referencia es la dispersión intrínseca de los
polos en A (cuánto se puede definir un polo medio en la práctica)."""),
        ("code", """SENS = An.tabla_sensibilidad(DF).round(2)
SENS.to_csv(os.path.join(SAL, "hito5_sensibilidad.csv"), index=False)
SENS"""),
        ("code", """for met in ("dpolo", "desalineamiento_deg"):
    fig = F.mapas_clasificacion(DF, met, sis=sis)
    E.guardar(fig, os.path.join(SAL, "hito5_mapa_%s.png" % met),
              "Milestone 5. Initial orbital poles of the %d streams (Mollweide, Galactocentric frame of the MW; "
              "longitude increases to the left) coloured by the reflex perturbation |B - A|, the direct-pull "
              "perturbation |C - A| and the reflex fraction f_reflex of the %s. Filled star: orbital pole of the "
              "LMC today; open star: the opposite pole. Each pole hosts six streams (3 families x 2 phases): "
              "the colours overlap." % (len(DF), An.METRICAS[met]), FUENTE, pdf=True)
    plt.show()"""),
        ("md", """Cada polo tiene seis corrientes (tres familias y dos fases) que se superponen en el mapa. Por familia:"""),
        ("code", """for fam in ("corta", "larga", "doble"):
    d = DF[DF["familia"] == fam]
    fig = F.mapa_polos(d, ["dpolo_f_reflex_todo"], ["f_reflex (pole change), %s streams" % fam], sis=sis,
                       cmaps={"dpolo_f_reflex_todo": F.cmap_f_reflex()}, rangos={"dpolo_f_reflex_todo": (0, 1)})
    E.guardar(fig, os.path.join(SAL, "hito5_mapa_f_%s.png" % fam), "Reflex fraction of the pole change for the "
              "%s family (median of the two phases overlaps: both are plotted)." % fam, FUENTE)
    plt.show()
CL = pd.crosstab(DF["familia"], An.clases(DF, "dpolo"))
CL.to_csv(os.path.join(SAL, "hito5_clases_por_familia.csv"))
CL"""),
        ("md", """### Distancia, acercamiento a la LMC y longitud"""),
        ("code", """for met in ("dpolo", "desalineamiento_deg"):
    fig = F.tendencias(DF, met, ylabel="|perturbation| of the " + An.METRICAS[met])
    E.guardar(fig, os.path.join(SAL, "hito5_tendencias_%s.png" % met), "Milestone 5. Perturbation of the %s by "
              "the reflex motion alone (B - A), the direct pull alone (C - A) and both (D - A), against "
              "pericentre, apocentre, closest approach to the LMC and stream length. Lines: medians in bins."
              % An.METRICAS[met], FUENTE, pdf=True)
    plt.show()"""),
        ("md", """### Distancia y longitud por separado

En la grilla principal cada familia fija a la vez la distancia y la masa del progenitor (y con ellas la longitud),
así que las tendencias de arriba mezclan los dos factores. Dos catálogos más los separan (12 polos HEALPix cada uno):
*distancia* ($r_{\\rm apo}$ = 30, 45, 70, 100, 150 kpc con $10^7\\,M_\\odot$) y *longitud* ($r_{\\rm apo}$ = 60 kpc con
$M_{\\rm prog} = 10^6, 10^7, 10^8\\,M_\\odot$)."""),
        ("code", """DIS, _ = R.cargar("catalogo_distancia", propios=PROPIOS)
LON, _ = R.cargar("catalogo_longitud", propios=PROPIOS)
fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.3))
for k, m, nom in (("dpolo_B_todo", "B", "reflex only"), ("dpolo_C_todo", "C", "direct pull only"), ("dpolo_D_todo", "D", "full")):
    g = DIS.groupby("r_apo")[k]
    ax[0].fill_between(g.median().index, g.quantile(0.16), g.quantile(0.84), color=E.COLOR_MODELO[m], alpha=0.12, lw=0)
    ax[0].plot(g.median().index, g.median().values, "-o", color=E.COLOR_MODELO[m], lw=2, label=nom)
    g = LON.groupby("m_prog")
    ax[1].errorbar(g["longitud_vueltas_A"].median(), g[k].median(), yerr=[g[k].median() - g[k].quantile(0.16), g[k].quantile(0.84) - g[k].median()],
                   fmt="-o", color=E.COLOR_MODELO[m], lw=2, capsize=3, label=nom)
ax[0].set_xlabel("apocentre (kpc), progenitor 1e7 Msun"); ax[0].set_xscale("log")
ax[1].set_xlabel("stream length in model A (wraps), r_apo = 60 kpc, M_prog = 1e6, 1e7, 1e8 Msun")
for A in ax:
    A.set_ylabel("pole change (deg)"); E.grilla(A)
ax[0].legend(fontsize=9)
fig.tight_layout()
""" + guardar_fig("fig", "hito5_distancia_longitud.png",
                  "Milestone 5, distance and length separated. Left: median (and 16-84 per cent range) pole change "
                  "against apocentre for 1e7 Msun progenitors on 12 HEALPix poles. Right: against stream length in "
                  "model A, changing only the progenitor mass at a fixed apocentre of 60 kpc.") + """
print(DIS.groupby("r_apo")[["peri_kpc", "longitud_vueltas_A", "dpolo_B_todo", "dpolo_C_todo", "dpolo_D_todo", "dpolo_f_reflex_todo"]].median().round(2))
print(LON.groupby("m_prog")[["longitud_vueltas_A", "dpolo_B_todo", "dpolo_C_todo", "dpolo_D_todo", "dpolo_f_reflex_todo"]].median().round(2))"""),
        ("md", """### Estrella a estrella: ¿dónde se cancelan los dos efectos?

Como los cuatro modelos usan la misma semilla, la estrella *i* es la misma en A, B, C y D. Para cada estrella de las
corrientes del catálogo principal: el ángulo entre su polo orbital en B (o C, D) y en A, en función de su radio hoy."""),
        ("code", """RAD, _ = R.cargar("por_radio_principal")
fig = F.por_radio(RAD)
""" + guardar_fig("fig", "hito5_por_radio.png",
                  "Milestone 5, star by star. Change of each star's orbital pole relative to the same star in the "
                  "isolated MW (same seed in the four models), against the star's galactocentric radius today, for "
                  "all streams of the main catalogue: medians and 16-84 per cent ranges. Reflex only (B), direct "
                  "pull only (C) and both (D).") + """
RAD.round(2)"""),
        ("md", """### Orientación y sentido de giro

¿Una fuerza uniforme perpendicular al plano de la corriente la inclina más? Se mide con
$|\\hat{\\mathbf n}_0\\cdot\\hat{\\mathbf a}_{\\rm MW}|$, con $\\hat{\\mathbf a}_{\\rm MW}$ la dirección media de la aceleración de la MW
en el último Gyr (pesada por su módulo; apunta hacia la LMC). El sentido de giro: prógrada si el polo inicial
está del mismo lado que el polo orbital de la LMC."""),
        ("code", """fig = F.orientacion(DF)
""" + guardar_fig("fig", "hito5_orientacion.png",
                  "Milestone 5. Left: pole change caused by the reflex motion alone against |n0 . a_MW|, where "
                  "a_MW is the |a|-weighted mean direction of the MW acceleration over the last Gyr (1: the uniform "
                  "force is perpendicular to the stream plane). Right: pole change caused by the direct pull alone "
                  "against the closest approach to the LMC, for streams rotating in the same sense as the LMC "
                  "orbit (prograde) or opposite (retrograde).") + '''
from scipy.stats import spearmanr
r = spearmanr(DF["perp_aMW"], DF["dpolo_B_todo"])
print("Spearman (|n0.a_MW|, cambio del polo por reflejo): rho = %.2f, p = %.1e" % (r.statistic, r.pvalue))
print(DF.groupby("sentido_lmc")[["dpolo_B_todo", "dpolo_C_todo", "dpolo_D_todo", "dmin_lmc_kpc"]].median().round(2))
from scipy.stats import mannwhitneyu
a, b = (DF.loc[DF["sentido_lmc"] == s, "dpolo_C_todo"] for s in ("prograde", "retrograde"))
print("Tiron directo, prograda vs retrograda: Mann-Whitney p = %.1e" % mannwhitneyu(a, b).pvalue)'''),
        ("md", """### Restos viejos y jóvenes"""),
        ("code", """fig = F.viejo_joven(DF, "dpolo")
""" + guardar_fig("fig", "hito5_viejo_joven.png",
                  "Milestone 5. Pole change of the old debris (released before the median release time) against "
                  "the young debris, for the long and two-wrap streams, for each effect. Line: one to one.")),
        ("md", """### No linealidad y cancelaciones

No linealidad: $|\\Delta M_{\\rm full} - (\\Delta M_{\\rm reflex} + \\Delta M_{\\rm direct})| / (|\\Delta M_{\\rm reflex}| + |\\Delta M_{\\rm direct}|)$.
Cancelación (cambio vectorial del polo): el efecto total es menor que la mitad del mayor de los dos efectos
separados (y este supera 1°)."""),
        ("code", """filas = []
for met in ("desalineamiento_deg", "tilt_polo_deg", "tilt_plano_deg", "dispersion_polos_deg"):
    nl = An.no_linealidad(DF, met)
    filas.append(dict(metric=An.METRICAS[met], median_nonlinear=np.nanmedian(nl), frac_above_0_5=np.nanmean(nl > 0.5)))
NL = pd.DataFrame(filas).round(2)
canc = An.cancelaciones(DF)
print("Cancelaciones: %d de %d corrientes (%.0f %%)" % (canc.sum(), len(DF), 100 * canc.mean()))
print(DF.loc[canc].groupby("familia").size().rename("n con cancelacion"))
print(DF.loc[canc, ["perp_aMW", "cos_polo_lmc", "dmin_lmc_kpc"]].median().round(2).rename("mediana (cancelan)"))
print(DF.loc[~canc, ["perp_aMW", "cos_polo_lmc", "dmin_lmc_kpc"]].median().round(2).rename("mediana (resto)"))
NL"""),
        ("md", """## Discusión del hito 5

Números de la corrida incluida en `resultados/` (si se rehace con `PROPIOS = True`, mirar las salidas de arriba).
Entre corchetes, el estatus de cada afirmación.

**1. Lo que decide quién domina es la distancia.** Con el cambio vectorial del polo, 66 de las 96 corrientes
cortas ($r_{\\rm apo}$ = 100 kpc) están dominadas por el reflejo y 72 de las 96 de dos vueltas (40 kpc) por el
torque; las largas (60 kpc) quedan repartidas [comprobado]. El catálogo *distancia*, con la misma masa, lo aísla:
la mediana de $f_{\\rm reflex}$ sube de forma monótona de 0.30 (30 kpc) a 0.80 (150 kpc) [comprobado].
Una explicación [deducido]: la fuerza ficticia $-\\mathbf a_{\\rm MW}$ es casi la misma en todo el halo, pero una
órbita interna da muchas vueltas mientras la LMC pasa y su torque se promedia (respuesta adiabática), mientras
que una órbita externa, de período largo, no alcanza a promediarlo.

**2. Cerca del centro los dos efectos se cancelan.** Estrella por estrella, el reflejo solo y el tirón solo inclinan
cada uno las órbitas ~8–10° a cualquier radio. Juntos (D) quedan en ~4° dentro de ~40 kpc; más allá de ~80 kpc,
D se acerca a B (12–16°) y el tirón solo baja a ~6° [comprobado]. Es lo que anticipa el enunciado: en el centro
queda solo el campo de marea de la LMC.

**3. Orientación.** El cambio del polo por el reflejo crece con $|\\hat{\\mathbf n}_0\\cdot\\hat{\\mathbf a}_{\\rm MW}|$
(Spearman ρ ≈ 0.33, p ~ 10⁻⁸): sí, una fuerza uniforme perpendicular al plano lo inclina más [comprobado]. El
**sentido de giro** respecto de la LMC no da una diferencia significativa en la grilla principal (p ≈ 0.4), aunque
en el piloto sí parecía haberla: con 72 corrientes era una fluctuación. No es un resultado robusto [comprobado].

**4. Acercamiento a la LMC.** La correlación con el tirón directo es débil (ρ ≈ −0.12): en esta grilla casi ninguna
corriente pasa a menos de ~20 kpc de la LMC [comprobado].

**5. Longitud y edad de los restos.** A distancia fija, las corrientes más largas cambian menos su polo medio
(reflejo: de ~10° con 0.6 vueltas a ~5° con 1.5 vueltas), pero $f_{\\rm reflex}$ no cambia (~0.53) [comprobado]: la
longitud cambia la amplitud, no la clase. En las corrientes largas y de dos vueltas, los restos jóvenes se
perturban más que los viejos en ~70–76 % de los casos [comprobado]. Una posible razón [deducido, sin verificar]:
el polo medio de los restos viejos promedia estrellas en fases muy distintas de la órbita, y sus perturbaciones
se compensan en parte.

**6. Qué métrica.** El cambio del polo (vectorial) y la dispersión de los polos son las más sensibles (superan el
piso en 66–95 % de las corrientes, según el efecto); la inclinación del plano por SVD es la menos sensible (~25–40 %), porque la
precesión por el disco la contamina [comprobado]. Con datos reales, la primera que se mediría es el
**desalineamiento**: es intrínseco (no necesita el polo inicial) y no necesita velocidades radiales (notebook 06).

**7. No linealidad y cancelaciones.** $\\Delta M_{\\rm full}$ difiere de $\\Delta M_{\\rm reflex} + \\Delta M_{\\rm direct}$
en ~45–75 % de su tamaño (mediana) [comprobado]: la descomposición sirve para clasificar, no para sumar. En ~1 de
cada 4 corrientes los dos efectos se compensan; esas corrientes tienen el plano más perpendicular a
$\\mathbf a_{\\rm MW}$ (mediana 0.65 contra 0.43) [comprobado].

**Límites.** Potenciales rígidos (sin la estela de materia oscura ni la deformación del halo de la MW,
Garavito-Camargo et al. 2019); una sola MW; la LMC del tutorial, que en este modelo tuvo un pericentro anterior
(notebook 02); progenitores sin autogravedad en la integración (`FardalStreamDF`); grilla de polos de ~30°; tres
familias que acoplan distancia, masa y longitud (los catálogos *distancia* y *longitud* las separan solo en parte)."""),
        ("code", """U.escribir_texto("Hito 5 (%s): %d corrientes; clases (cambio del polo): %s; cancelaciones %d."
                 % (U.ahora(), len(DF), pd.Series(An.clases(DF, "dpolo")).value_counts().to_dict(), canc.sum()),
                 os.path.join(SAL, "registro.txt"))"""),
    ]


def nb06():
    return [
        ("md", badge("06_hito5_lsst.ipynb") + """

# 06 · Hito 5: predicciones para LSST

**Qué pide el enunciado.** "Observar" las corrientes simuladas como lo haría LSST (footprint, profundidad,
errores de movimiento propio, distancias fotométricas, sin velocidades radiales), recalcular las métricas solo con
las estrellas observadas y responder: qué corrientes (y qué partes) podría detectar LSST y a qué distancias; para
cuáles la señal del reflejo supera los errores, y en qué métrica; cuántas corrientes harían falta para distinguir
el reflejo del tirón directo.

**Supuestos** (todos en `p3streams/config.py` y `p3streams/observar.py`):
- Población: isócrona PARSEC 12 Gyr, Z = 0.0002, bandas LSST, IMF de Chabrier. Masa estelar formada
  $M_* = 10^{-2}\\,M_{\\rm prog}$ (supuesto: los progenitores son enanas dominadas por materia oscura; se varía abajo).
- Cada partícula representa $M_*/N$; el número de estrellas sobre el límite se sortea con Poisson.
- Footprint Dec < +5°; profundidad r < 27 (10 años); movimientos propios para 16 < r < 24.5 con
  $\\sigma_\\mu$ = 0.2 mas/yr (r = 21) a 1.0 mas/yr (r = 24), interpolado en log (Ivezić et al. 2019);
  distancias fotométricas con 7 % de error; sin velocidades radiales.
- Seguimiento espectroscópico opcional (4MOST, DESI, PFS): r < 21, $\\sigma_v$ = 2 km/s. Solo con él se calculan
  los polos orbitales (necesitan la velocidad completa).
- Gaia DR3 para comparar: G < 21 con G ≈ r y sus errores de movimiento propio (Lindegren et al. 2021, aproximados).
- Errores de las métricas: bootstrap (remuestreo de estrellas + nuevas realizaciones de los errores).
  Con más de 20 000 estrellas se usa un subconjunto al azar, así que esos errores son una **cota superior** y la
  señal/ruido `snr` es **conservadora**. La columna `snrx` reescala los errores por $\\sqrt{N_{\\rm usadas}/N_{\\rm obs}}$
  [deducido: supone errores puramente estadísticos]; la verdad está entre las dos.

**Qué es observable de verdad.** El desalineamiento y la dispersión de los polos son *intrínsecos*: se miden en la
corriente sin saber cuál era su órbita inicial. Las inclinaciones (del polo y del plano) se miden **respecto del
polo inicial**, que no se observa: solo sirven comparando con modelos ajustados. Por eso el criterio de detección
compara modelos con las mismas condiciones iniciales ($|M_D - M_C|$ para el reflejo y $|M_D - M_B|$ para el tirón
directo, en unidades de su error, > 3σ), y el número de corrientes necesario es una **cota optimista**: supone
conocidos la MW, la LMC y los progenitores."""),
        ("code", SETUP),
        ("code", salidas("06_hito5_lsst")),
        ("code", CARGA + """
from p3streams import lsst as L, observar as O, corrientes as Co, catalogo as Ca
LS, ORIGEN_L = R.cargar("lsst_principal", propios=PROPIOS)
print("Pasada LSST: %d corrientes, leida de %s" % (len(LS), ORIGEN_L))
M = L.agregar_snr_escalada(DF.merge(LS, on="id", how="inner"))"""),
        ("md", """### Una corriente vista por LSST

Se rehace una corriente larga del catálogo (las corrientes no vienen en el repositorio, solo su tabla) y se
observa en los modelos C y D."""),
        ("code", """FILA = DF[(DF["familia"] == "larga") & (DF["psi_deg"] == 0)].sort_values("dpolo_B_todo").iloc[-1].to_dict()
print("Corriente:", FILA["id"], "polo", np.round(FILA["polo"], 2))
CAT = os.path.join(SAL, "catalogo_local")
os.makedirs(os.path.join(CAT, "filas")); os.makedirs(os.path.join(CAT, "corrientes"))
base = {k: FILA[k] for k in ("id", "polo", "polo_idx", "sentido", "familia", "psi_deg", "f", "t_start", "r_apo", "m_prog")}
fila_local = Ca.correr_corriente(base, sis, CAT)
import json
with open(os.path.join(CAT, "filas", FILA["id"] + ".json"), "x") as f:
    json.dump(fila_local, f, default=float)
FL = O.FuncionLuminosidad()
CORR = {m: Co.cargar(os.path.join(CAT, "corrientes", "%s_%s.npz" % (FILA["id"], m))) for m in "CD"}
OBS = {m: O.observar(CORR[m], 1e-2 * FILA["m_prog"], np.random.default_rng(1), espectro=True, fl=FL) for m in "CD"}
lmc = Me.a_icrs(sis.x_lmc_rel(0.0)[None, :], ((sis._x_lmc(0.0, 1) - sis._x_mw(0.0, 1)) / P.KMS())[None, :], corregir=False)
LMC_RADEC = (lmc.ra.deg[0], lmc.dec.deg[0])
print("LMC hoy (modelo): RA %.1f, Dec %.1f deg" % LMC_RADEC)"""),
        ("code", """fig = F.lsst_cielo(CORR, OBS, LMC_RADEC)
""" + guardar_fig("fig", "hito5_lsst_cielo.png",
                  "Milestone 5, LSST view of one long stream of the catalogue (models C and D). Grey: all stream "
                  "particles; coloured: stars LSST would detect after 10 years (r < 27, Dec < +5 deg, dashed line), "
                  "drawn from a 12 Gyr, Z = 0.0002 PARSEC isochrone with M_* = 0.01 M_prog. Star: the LMC today in "
                  "the model. Equatorial coordinates, Mollweide, RA increasing to the left.")),
        ("md", """### ¿Qué se ve y a qué distancias?"""),
        ("code", """T = M.groupby("familia").agg(frac_en_footprint=("frac_footprint_D", "median"), parte_del_largo=("psi_footprint_D", "median"),
                               estrellas_LSST=("n_obs_D", "median"), con_PM=("n_pm_D", "median"), Gaia_G21=("n_gaia_D", "median"),
                               d_mediana_kpc=("d_med_obs_D", "median"), d_max_kpc=("d_max_obs_D", "median"),
                               n_corrientes=("id", "size")).round(2)
T.to_csv(os.path.join(SAL, "hito5_lsst_visibilidad.csv"))
print("Corrientes sin ninguna estrella observada (modelo D):", int((M["n_obs_D"] == 0).sum()))
T"""),
        ("md", """### ¿Supera la señal a los errores?

Fracción de corrientes con señal > 3σ, por métrica y por variante: toda la corriente con LSST, cada brazo con
LSST, y toda la corriente con Gaia (G < 21, sin espectroscopía)."""),
        ("code", """MET = {"desalineamiento_deg": "PM misalignment", "dispersion_polos_deg": "pole spread (needs RVs)",
       "tilt_polo_deg": "pole tilt (needs RVs; model comparison)", "tilt_plano_deg": "plane tilt (model comparison)"}
filas = []
for var in ("", "lider", "cola", "gaia"):
    pre = var + "_" if var else ""
    for met, nom in MET.items():
        r = M["snr_%sreflejo_%s" % (pre, met)].to_numpy(float)
        d = M["snr_%sdirecto_%s" % (pre, met)].to_numpy(float)
        rx = M["snrx_%sreflejo_%s" % (pre, met)].to_numpy(float)
        dx = M["snrx_%sdirecto_%s" % (pre, met)].to_numpy(float)
        filas.append(dict(variant={"": "LSST, whole stream", "lider": "LSST, leading arm", "cola": "LSST, trailing arm",
                                   "gaia": "Gaia (G < 21)"}[var], metric=nom,
                          measurable=np.mean(np.isfinite(r)), reflex_gt_3sigma=np.nanmean(r > 3) if np.isfinite(r).any() else np.nan,
                          direct_gt_3sigma=np.nanmean(d > 3) if np.isfinite(d).any() else np.nan,
                          reflex_gt_3sigma_scaled=np.nanmean(rx > 3) if np.isfinite(rx).any() else np.nan,
                          direct_gt_3sigma_scaled=np.nanmean(dx > 3) if np.isfinite(dx).any() else np.nan,
                          median_snr_reflex=np.nanmedian(r) if np.isfinite(r).any() else np.nan))
DET = pd.DataFrame(filas).round(2)
DET.to_csv(os.path.join(SAL, "hito5_lsst_deteccion.csv"), index=False)
DET"""),
        ("code", """fig = F.lsst_snr(M, list(MET), [MET[k] for k in MET], col="snrx")
""" + guardar_fig("fig", "hito5_lsst_snr.png",
                  "Milestone 5. Reflex signal in the metrics recomputed from the stars LSST would observe: |M_D - "
                  "M_C| (with and without the reflex motion, same initial conditions) divided by its bootstrap "
                  "uncertainty (bootstrap on at most 20 000 stars, rescaled by sqrt(N_used/N_observed) to all observed stars, "
                  "assuming purely statistical errors), against the median distance of the observed stars. Dashed: 3 sigma. Metrics marked "
                  "'needs RVs' use spectroscopic follow-up for r < 21; 'model comparison' metrics are measured "
                  "relative to the unobservable initial pole.")),
        ("md", """### Lista de corrientes y regiones con reflejo detectable en una métrica intrínseca"""),
        ("code", """filas = []
for _, f in M.iterrows():
    for var, reg in (("", "whole"), ("lider", "leading arm"), ("cola", "trailing arm")):
        pre = var + "_" if var else ""
        for met in ("desalineamiento_deg", "dispersion_polos_deg"):
            v = f.get("snr_%sreflejo_%s" % (pre, met), np.nan)
            vx = f.get("snrx_%sreflejo_%s" % (pre, met), np.nan)
            if np.isfinite(vx) and vx > 3:
                filas.append(dict(id=f["id"], family=f["familia"], region=reg, metric=MET[met], snr_reflex=round(v, 1),
                                  snr_reflex_scaled=round(vx, 1),
                                  d_med_kpc=round(f["d_med_obs_D"], 1), peri_kpc=round(f["peri_kpc"], 1)))
LISTA = pd.DataFrame(filas)
LISTA.to_csv(os.path.join(SAL, "hito5_lsst_lista_reflejo_detectable.csv"), index=False)
print("Corrientes con al menos una region/metrica intrinseca > 3 sigma (snr reescalada): %d de %d"
      % (LISTA["id"].nunique() if len(LISTA) else 0, len(M)))
if len(LISTA):
    print("  solo con el desalineamiento (sin velocidades radiales): %d"
          % LISTA.loc[LISTA["metric"] == MET["desalineamiento_deg"], "id"].nunique())
    print("  con la version conservadora: %d" % LISTA.loc[LISTA["snr_reflex"] > 3, "id"].nunique())
LISTA.sort_values("snr_reflex_scaled", ascending=False).head(25) if len(LISTA) else LISTA"""),
        ("md", """### ¿Cuántas corrientes harían falta?

Corrientes tomadas al azar del catálogo (en el footprint) hasta que su señal combinada en cuadratura supera
3σ; mediana y rango 16-84 % de 4000 sorteos. Cota optimista (ver arriba)."""),
        ("code", """filas = []
for var in ("", "gaia"):
    pre = var + "_" if var else ""
    for met, nom in MET.items():
        for efecto in ("reflejo", "directo"):
            n50, n16, n84 = L.n_necesarias(M["snr_%s%s_%s" % (pre, efecto, met)])
            x50, _, _ = L.n_necesarias(M["snrx_%s%s_%s" % (pre, efecto, met)])
            filas.append(dict(survey="Gaia" if var else "LSST", metric=nom, effect={"reflejo": "reflex", "directo": "direct pull"}[efecto],
                              n_streams_median=n50, n16=n16, n84=n84, n_streams_scaled=x50))
NN = pd.DataFrame(filas)
NN.to_csv(os.path.join(SAL, "hito5_lsst_n_necesarias.csv"), index=False)
NN"""),
        ("md", """### Sensibilidad a la masa estelar supuesta

Con $M_*/M_{\\rm prog}$ diez veces menor hay diez veces menos estrellas. Se observa de nuevo la corriente de arriba,
esta vez **con todas las estrellas** (sin el tope de 20 000), para que la comparación sea justa."""),
        ("code", """filas = []
for frac in (1e-2, 1e-3):
    r = L.observar_corriente(FILA["id"], CAT, fl=FL, frac=frac, n_boot=10, variantes=("lsst",), n_max=10**7)   # sin tope
    filas.append(dict(M_star_over_M_prog=frac, n_obs_D=r["n_obs_D"], n_pm_D=r.get("n_pm_D"),
                      **{"snr_reflex_" + k: r.get("snr_reflejo_" + k) for k in MET}))
pd.DataFrame(filas).round(2)"""),
        ("md", """## Discusión: predicciones para LSST

Números de la corrida incluida (288 corrientes, $M_* = 10^{-2}\\,M_{\\rm prog}$, 10 años). `snr`: conservadora
(como mucho 20 000 estrellas); `snrx`: errores reescalados a todas las estrellas observadas [deducido].

**¿Qué ve LSST y a qué distancia?** [comprobado] Todas las corrientes tienen estrellas sobre el límite. Las de
dos vueltas (40 kpc) y las largas (60 kpc) caen en ~60 % dentro del footprint y LSST cubre toda su extensión en
ángulo, con mediana de ~27 y ~37 kpc y estrellas hasta ~80–120 kpc. Las cortas (100 kpc) son el caso difícil:
solo ~10 % de sus estrellas cae en el footprint, con ~2800 estrellas observadas y ~560 con movimiento propio
(mediana a ~66 kpc, hasta ~140 kpc).

**¿Supera la señal del reflejo a los errores?** [comprobado, salvo donde se indica]
- *Desalineamiento* (solo posiciones, distancias y movimientos propios): >3σ en ~8 % de las corrientes con la
  versión conservadora y en ~46 % con la reescalada [deducido]. Por familia, con la reescalada: ~78 % de las de
  dos vueltas, ~53 % de las largas y solo ~7 % de las cortas.
- *Dispersión de los polos* (necesita velocidades radiales, r < 21): >3σ en ~44–67 %.
- *Inclinaciones* (comparan con el polo inicial, que no se observa): 34–97 %. Sirven solo dentro de un ajuste de
  modelos.
- *Gaia* (G < 21): el desalineamiento se mide en ~la mitad de las corrientes y casi nunca supera 3σ (~1 %).
  **LSST es lo que hace observable esta señal** a estas distancias.

**La tensión principal** [deducido de lo anterior y del notebook 05]: las corrientes **dominadas por el reflejo**
son las lejanas, y son justo las que LSST ve peor (pocas estrellas, casi todas fuera del footprint del sur). Donde
LSST mide bien (corrientes internas, largas) la señal del reflejo existe (D ≠ C), pero ahí domina el tirón
directo. Separar los dos efectos va a depender de pocas corrientes externas bien medidas, o de seguimiento
espectroscópico.

**¿Cuántas corrientes?** Combinando corrientes al azar, el desalineamiento llega a 3σ con ~2–4 corrientes y la
dispersión de los polos con 1–2 [comprobado]. Son cotas **optimistas**: suponen conocidos la MW, la LMC y los
progenitores. En un análisis real hay que marginalizar sobre ellos, y el número crece [deducido, sin cuantificar].

**Cuidado con el desalineamiento observado** [comprobado en la última tabla]: con diez veces menos estrellas, la
dispersión de los polos y las inclinaciones pierden señal/ruido como se espera (~×3), pero la del desalineamiento
*sube* (2.3 → 3.9). Eso indica que la medición fluctúa entre realizaciones del muestreo más de lo que dice su error
de bootstrap: además, la mediana de $|\\Delta\\theta|$ está sesgada hacia arriba por el ruido. Hay que leer la
señal/ruido del desalineamiento como incierta en un factor ~2 [deducido]. Para un análisis real convendría repetir
la observación con varias semillas.

**Límites del modelo de observación.** Un solo valor de $M_*/M_{\\rm prog}$ (se prueba ×0.1 en una corriente); sin
polvo ni contaminación de campo; errores de LSST interpolados entre dos puntos de Ivezić et al. (2019); el ángulo
a lo largo de la corriente viene de la simulación (en datos reales hay que ajustar la traza); Gaia aproximada con
G ≈ r."""),
        ("code", """U.escribir_texto("Hito 5 LSST (%s): %d corrientes; deteccion por metrica en hito5_lsst_deteccion.csv."
                 % (U.ahora(), len(M)), os.path.join(SAL, "registro.txt"))"""),
    ]


def nb07():
    return [
        ("md", badge("07_hito6_interpretacion.ipynb") + """

# 07 · Hito 6: corrientes observadas y temas avanzados

**Qué pide el enunciado.** Comparar con Sagitario (dos vueltas, ~20–100 kpc), Orphan–Chenab y las corrientes de
S5: ¿dónde caerían en la clasificación? Y, como temas avanzados: variar la masa de la LMC, separar la precesión de
un halo achatado de la perturbación de la LMC, y la no linealidad (notebook 05).

**Cómo se ubica una corriente real.** Con las trazas de `galstreams` (Mateu 2023): se pasan las posiciones de la
traza al marco de la MW (el mismo Sol que el resto del proyecto) y se ajusta el plano por el centro de la MW (SVD);
si la traza tiene movimientos propios **y** velocidad radial, el sentido de giro sale de $\\mathbf L = \\mathbf x \\times \\mathbf v$.
Se buscan en el catálogo las corrientes con el **polo de hoy** (modelo D) a menos de 30° y con radios que se solapan.
Es una ubicación aproximada (la grilla tiene polos cada ~30°), no un ajuste de cada corriente."""),
        ("code", SETUP),
        ("code", salidas("07_hito6")),
        ("code", CARGA + """
from p3streams import interpretar as I
MWS = I.cargar_galstreams()
REALES = [I.corriente_real(MWS, n) for n in I.REALES]
TR = pd.DataFrame([{k: (np.round(v, 3).tolist() if isinstance(v, np.ndarray) else v) for k, v in r.items()} for r in REALES])
TR"""),
        ("code", """TAB = I.resumen(REALES, DF, metrica="desalineamiento_deg").round(2)
TAB.to_csv(os.path.join(SAL, "hito6_corrientes_reales.csv"), index=False)
TAB"""),
        ("code", """fig = F.mapa_polos(DF.assign(_f=DF["dpolo_f_reflex_todo"]), ["_f"], [r"$f_{\\rm reflex}$ (pole change) and observed streams"],
                   sis=sis, cmaps={"_f": F.cmap_f_reflex()}, rangos={"_f": (0, 1)},
                   etiquetas={"_f": "0: torque-dominated    1: reflex-dominated"})
A = fig.axes[0]
fig.set_size_inches(9.5, 5.6)
for j, r in enumerate(REALES):
    for sg in ((1,) if r["sentido_conocido"] else (1, -1)):
        lo, la = F.lb(sg * r["normal"])
        A.plot(-lo, la, "D" if r["sentido_conocido"] else "d", ms=8, mfc="none", mec=E.TINTA, mew=1.3, zorder=5)
        A.annotate(r["nombre"].split("-")[0] if not r["nombre"].startswith("AAU") else r["nombre"].split("-")[1],
                   (-lo[0], la[0]), xytext=(6, 4 if j % 2 else -11), textcoords="offset points", fontsize=8, color=E.TINTA)
""" + guardar_fig("fig", "hito6_mapa_reales.png",
                  "Milestone 6. Reflex fraction of the pole change for the catalogue streams (colour, at their "
                  "initial poles) and the orbital-plane normals of observed streams from galstreams tracks "
                  "(diamonds; open thin diamonds: both orientations, when the track has no radial velocities to "
                  "fix the sense of rotation). Star: LMC orbital pole. Galactocentric frame, Mollweide.")),
        ("md", """### Masa de la LMC

Cuatro catálogos iguales (12 polos HEALPix × 3 familias) con $M_{\\rm LMC}$ = 1.0, 1.5, 1.8 y 2.5 × 10¹¹ M☉: el sistema
MW + LMC se integra de nuevo para cada masa (la órbita pasada de la LMC cambia con su masa)."""),
        ("code", """filas = []
for m in ("1.0", "1.5", "1.8", "2.5"):
    d, _ = R.cargar("catalogo_masa_" + m, propios=PROPIOS)
    for fam, g in d.groupby("familia"):
        filas.append(dict(M_LMC=float(m), familia=fam, reflex=g["dpolo_B_todo"].median(), direct=g["dpolo_C_todo"].median(),
                          full=g["dpolo_D_todo"].median(), f_reflex=g["dpolo_f_reflex_todo"].median(),
                          desal_full=g["dM_full_desalineamiento_deg_todo"].abs().median(), n=len(g)))
MAS = pd.DataFrame(filas).round(2)
MAS.to_csv(os.path.join(SAL, "hito6_masa_lmc.csv"), index=False)
fig, ax = plt.subplots(1, 3, figsize=(14, 4.2), sharex=True)
for fam in ("corta", "larga", "doble"):
    g = MAS[MAS["familia"] == fam]
    col = F.COLOR_FAMILIA[fam]
    ax[0].plot(g["M_LMC"], g["reflex"], "-o", color=col, label=F.NOMBRE_FAMILIA[fam])
    ax[1].plot(g["M_LMC"], g["direct"], "-o", color=col)
    ax[2].plot(g["M_LMC"], g["f_reflex"], "-o", color=col)
ax[0].set_ylabel("median pole change, reflex only (deg)")
ax[1].set_ylabel("median pole change, direct pull only (deg)")
ax[2].set_ylabel(r"median $f_{\\rm reflex}$ (pole change)")
ax[2].axhspan(0.4, 0.6, color=E.GRILLA, alpha=0.6, lw=0)
for A in ax:
    A.set_xlabel(r"LMC mass ($10^{11}\\,M_\\odot$)"); E.grilla(A)
ax[0].legend(fontsize=9)
fig.tight_layout()
""" + guardar_fig("fig", "hito6_masa_lmc.png",
                  "Advanced topic: LMC mass. Median pole change caused by the reflex motion alone and by the direct "
                  "pull alone, and median reflex fraction, for 12 HEALPix poles x 3 stream families, re-integrating "
                  "the MW + LMC system for each LMC mass. Grey band: mixed (0.4 < f_reflex < 0.6).") + """
MAS"""),
        ("md", """### Halo achatado contra LMC

Un halo achatado también hace precesar los polos orbitales, salvo en órbitas polares (enunciado). Se compara el
cambio del polo que produce un halo con $c/a = 0.8$ (sin LMC) con el que produce la LMC (modelo D), para una
órbita polar y una inclinada 45°, en la familia larga."""),
        ("code", """import time
import gala.potential as gp, astropy.units as u
from gala.units import galactic
from p3streams import potenciales as P, corrientes as Co, catalogo as Ca
def mw_achatada(c=0.8):
    p = gp.CCompositePotential()
    for k, v in P.componentes_mw().items():
        p[k] = v
    p["halo"] = gp.LeeSutoTriaxialNFWPotential(units=galactic, v_c=C.MW_HALO["v_c"] * u.km / u.s,
                                               r_s=C.MW_HALO["r_s"] * u.kpc, a=1.0, b=1.0, c=c)
    return p
MODS = P.modelos(sis)
POT = {"A": MODS["A"], "D": MODS["D"], "A_flat": mw_achatada(0.8)}
fam = Ca.FAMILIAS["larga"]
filas = []
for nombre, polo in (("polar", [0.0, -1.0, 0.0]), ("inclined 45 deg", [0.0, -np.sqrt(0.5), np.sqrt(0.5)])):
    x0, v0 = Co.condiciones_iniciales(polo, fam["r_apo"], 0.5, 0.0)
    t0 = time.time()
    pol = {k: Me.polo_medio(Me.polos(*(np.asarray(Co.generar(p, x0, v0, m_prog=fam["m_prog"], t_inicio=-C.T_START)[q], float)
                                        for q in ("pos", "vel")))) for k, p in POT.items()}
    filas.append({"orbit": nombre, "pole change, flattened halo c/a = 0.8 (deg)": Me.angulo(pol["A_flat"], pol["A"]),
                  "pole change, LMC (D vs A) (deg)": Me.angulo(pol["D"], pol["A"]),
                  "pole tilt from initial, spherical A (deg)": Me.angulo(pol["A"], polo), "s": round(time.time() - t0)})
HALO = pd.DataFrame(filas).round(2)
HALO.to_csv(os.path.join(SAL, "hito6_halo_achatado.csv"), index=False)
HALO"""),
        ("md", """## Discusión del hito 6 y de los temas avanzados

**Dónde caen las corrientes observadas** (tabla de arriba; ubicación aproximada, no un ajuste):
- **Orphan–Chenab** (15–59 kpc, sentido conocido): sus vecinas del catálogo están dominadas por el **torque**
  ($f_{\\rm reflex}$ ≈ 0.3 en las dos métricas) [comprobado en el catálogo]. Es coherente con la literatura, que
  atribuye su desalineamiento a la LMC (Koposov et al. 2019; Erkal et al. 2019) [conocimiento general: verificar
  los detalles en los artículos].
- **Corrientes de S5** (ATLAS, Aliqa Uma, Elqui, Indus, Jhelum, Phoenix, Turranburra, Tucana III; 9–50 kpc): mixtas
  por el desalineamiento y casi todas **torque** por el cambio del polo; Indus (13–15 kpc) es la más claramente de
  torque [comprobado en el catálogo]. Están en el rango de radios donde, estrella por estrella, los dos efectos se
  cancelan en parte (notebook 05).
- **Sagitario**: queda **mixta**, pero con tres advertencias. La traza de galstreams usada cubre 19–48 kpc, no los
  ~100 kpc del brazo lejano. Sin velocidades radiales en esa traza, el sentido de giro queda indeterminado. Y Sgr es
  masiva y su propia dinámica no está en estos modelos [deducido].
- Ninguna corriente observada de la lista cae entre las claramente dominadas por el reflejo: esas son las que
  están más allá de ~70–100 kpc (notebook 05).

**Masa de la LMC** [comprobado]: las perturbaciones crecen con la masa (el cambio del polo por reflejo en las
cortas: ~9° con $10^{11}\\,M_\\odot$, ~17° con $2.5\\times10^{11}$). En cambio, $f_{\\rm reflex}$ apenas se mueve: las
cortas siguen dominadas por el reflejo (0.69 → 0.57) y las de dos vueltas por el torque (0.27 → 0.33). La
clasificación es robusta a la masa de la LMC en este rango. La amplitud no lo es: por eso la amplitud sirve
para pesar la LMC (Shipp et al. 2021; Erkal et al. 2019).

**Halo achatado contra LMC** [comprobado]: con $c/a = 0.8$, la órbita polar casi no precesa (~0.04°), pero la inclinada
45° cambia su polo ~60° en 5 Gyr, contra ~2.6° por la LMC. **Fuera de las órbitas polares, la forma del halo
domina sobre la LMC**, y hay que modelarla junto con la LMC. Las corrientes polares son las sondas más limpias.

**Qué mediría primero con datos reales** [opinión, fundada en los notebooks 05 y 06]: el desalineamiento del movimiento
propio a lo largo de corrientes largas del sur con LSST. Es intrínseco, no necesita velocidades radiales y LSST lo
mide bien hasta ~40 kpc. Después vendría la dispersión de los polos con seguimiento espectroscópico, en las
corrientes externas, que son las que llevan la señal del reflejo."""),
    ]


def nb08():
    return [
        ("md", badge("08_figuras_finales.ipynb") + """

# 08 · Figuras finales: académicas y de prensa

Las figuras académicas (fondo blanco, PNG + PDF) resumen los resultados para la presentación; las de prensa
(fondo negro, 4K, sin jerga) cuentan lo mismo para todo público. Todas salen de los mismos datos y llevan su
procedencia en los metadatos del PNG."""),
        ("code", SETUP),
        ("code", salidas("08_figuras")),
        ("code", CARGA + """
from p3streams import prensa as Pr, corrientes as Co, catalogo as Ca
RAD, _ = R.cargar("por_radio_principal")
MAS = pd.concat([R.cargar("catalogo_masa_" + m)[0].assign(M_LMC=float(m)) for m in ("1.0", "1.5", "1.8", "2.5")])"""),
        ("md", """### Figura académica de resumen"""),
        ("code", """fig = plt.figure(figsize=(15, 9.5))
gs = fig.add_gridspec(2, 3, hspace=0.42, wspace=0.32)
ax = fig.add_subplot(gs[0, :2])
for m, nom in (("B", "reflex only (B)"), ("C", "direct pull only (C)"), ("D", "full MW + LMC (D)")):
    ax.fill_between(RAD["r_med"], RAD["p16_" + m], RAD["p84_" + m], color=E.COLOR_MODELO[m], alpha=0.12, lw=0)
    ax.plot(RAD["r_med"], RAD["med_" + m], "-o", ms=4, lw=2, color=E.COLOR_MODELO[m], label=nom)
ax.set_xscale("log"); ax.set_xlabel("galactocentric radius of the star today (kpc)")
ax.set_ylabel("change of the orbital pole\\nvs the same star in A (deg)"); ax.legend(fontsize=10, loc="upper left"); E.grilla(ax)
ax.set_title("(a) star by star: the two effects cancel near the centre", loc="left", fontsize=12)
ax = fig.add_subplot(gs[0, 2])
for i, fam in enumerate(("corta", "larga", "doble")):
    v = DF.loc[DF["familia"] == fam, "dpolo_f_reflex_todo"].to_numpy(float)
    x = i + np.random.default_rng(i).uniform(-0.18, 0.18, len(v))
    ax.scatter(x, v, s=10, color=F.COLOR_FAMILIA[fam], alpha=0.55, lw=0)
    ax.plot([i - 0.25, i + 0.25], [np.median(v)] * 2, color=E.TINTA, lw=2)
ax.axhspan(0.4, 0.6, color=E.GRILLA, alpha=0.7, lw=0)
ax.set_xticks([0, 1, 2], ["short\\n100 kpc", "long\\n60 kpc", "two-wrap\\n40 kpc"])
ax.set_ylabel(r"$f_{\\rm reflex}$ (pole change)"); ax.set_ylim(0, 1); E.grilla(ax, "y")
ax.set_title("(b) reflex fraction by family", loc="left", fontsize=12)
ax = fig.add_subplot(gs[1, :2])
for k, m, nom in (("dpolo_B_todo", "B", "reflex only"), ("dpolo_C_todo", "C", "direct pull only"), ("dpolo_D_todo", "D", "full")):
    x = DF["perp_aMW"].to_numpy(float); y = DF[k].to_numpy(float)
    c, med, lo, hi = An.medianas_por_tramo(x, y, np.linspace(0, 1.0001, 6))
    ax.fill_between(c, lo, hi, color=E.COLOR_MODELO[m], alpha=0.12, lw=0)
    ax.plot(c, med, "-o", ms=4, lw=2, color=E.COLOR_MODELO[m], label=nom)
ax.set_xlabel(r"$|\\hat{\\mathbf{n}}_0\\cdot\\hat{\\mathbf{a}}_{\\rm MW}|$  (1: uniform force perpendicular to the stream plane)")
ax.set_ylabel("pole change (deg)"); ax.legend(fontsize=10, loc="upper left"); E.grilla(ax)
ax.set_title("(c) orientation of the stream plane relative to the MW acceleration", loc="left", fontsize=12)
ax = fig.add_subplot(gs[1, 2])
for fam in ("corta", "larga", "doble"):
    g = MAS[MAS["familia"] == fam].groupby("M_LMC")["dpolo_f_reflex_todo"].median()
    ax.plot(g.index, g.values, "-o", color=F.COLOR_FAMILIA[fam], label=F.NOMBRE_FAMILIA[fam])
ax.axhspan(0.4, 0.6, color=E.GRILLA, alpha=0.7, lw=0)
ax.set_xlabel(r"LMC mass ($10^{11}\\,M_\\odot$)"); ax.set_ylabel(r"median $f_{\\rm reflex}$"); ax.set_ylim(0, 1)
ax.legend(fontsize=9); E.grilla(ax)
ax.set_title("(d) LMC mass", loc="left", fontsize=12)
""" + guardar_fig("fig", "final_resumen_academico.png",
                  "Summary. (a) Change of each star's orbital pole relative to the same star in the isolated MW, "
                  "against its radius today (all streams of the main catalogue; medians and 16-84 per cent ranges): "
                  "the reflex motion alone (B) and the direct pull alone (C) each tilt orbits by ~10 deg at all "
                  "radii, but together (D) they largely cancel in the inner halo. (b) Reflex fraction of the mean "
                  "pole change per stream family (lines: medians; grey band: mixed). (c) Pole change against the "
                  "orientation of the stream plane relative to the mean MW acceleration over the last Gyr. (d) "
                  "Median reflex fraction against LMC mass (12 poles x 3 families per mass).")),
        ("md", """### Figuras de prensa (4K, fondo negro)"""),
        ("code", """fam = Ca.FAMILIAS["larga"]; N0 = np.array([0.0, -1.0, 0.0])
x0, v0 = Co.condiciones_iniciales(N0, fam["r_apo"], 0.5, 0.0)
MODS = P.modelos(sis)
CORR = {m: Co.generar(MODS[m], x0, v0, m_prog=fam["m_prog"], t_inicio=-C.T_START) for m in "AD"}
fig = Pr.heroe(CORR["D"], CORR["A"], sis, N0, x0, "How the Large Magellanic Cloud bends a stellar stream",
               "A simulated stream of stars torn from a small galaxy, after 5 billion years around the Milky Way")
Pr.guardar(fig, os.path.join(SAL, "prensa_corriente_4k.png"),
           "Press image. Simulated stellar stream (5e7 Msun progenitor, apocentre 60 kpc, 5 Gyr) in the Milky Way "
           "with the Large Magellanic Cloud (violet) and the same stream in the Milky Way alone (blue-grey), seen "
           "obliquely; warm glow: exponential disc of the model; magenta: LMC orbit over the last 0.7 Gyr.", FUENTE)
plt.show()"""),
        ("code", """fig = Pr.radio(RAD, "Near the centre of the Milky Way, two effects of the LMC cancel",
               "How much the LMC tilts the orbits of stream stars, star by star, at each distance")
Pr.guardar(fig, os.path.join(SAL, "prensa_cancelacion_4k.png"),
           "Press chart. Median change of the orbital pole of stream stars caused by the LMC, against distance "
           "from the Milky Way centre: the Milky Way's own acceleration towards the LMC ('wobble', reflex motion) "
           "and the LMC's direct pull each tilt orbits, but near the centre they largely cancel.", FUENTE)
plt.show()"""),
    ]


def nb09():
    return [
        ("md", badge("09_videos.ipynb") + """

# 09 · Videos

La formación de una corriente larga durante 5 Gyr en los cuatro modelos. Las instantáneas salen del propio
generador de `gala` (`output_every`, integrador DOP853, archivo HDF5), como sugiere el enunciado; la corriente
final coincide con la del catálogo (integrador por defecto) a ~10⁻⁴ kpc.

- **Académico** (1920×1080, 30 cuadros/s, H.264): 2×2 paneles en el plano orbital inicial con la órbita de la LMC, y
  la inclinación del polo medio respecto del polo inicial en función del tiempo.
- **Prensa** (1920×1080): densidad luminosa de la corriente con la LMC sobre la misma corriente sin ella, el disco
  y la LMC.
- GIF de cada uno (960 px, 15 cuadros/s) para diapositivas.

Tiempo en Colab: ~5 min de simulación y ~5 min de video."""),
        ("code", SETUP),
        ("code", salidas("09_videos")),
        ("code", """import time
from p3streams import potenciales as P, videos as V, catalogo as Ca
sis = P.integrar_sistema()
FAM = Ca.FAMILIAS["larga"]
FILA = dict(id="video_larga_polo_y", polo=[0.0, -1.0, 0.0], r_apo=FAM["r_apo"], m_prog=FAM["m_prog"], f=0.5,
            psi_deg=0.0, t_start=C.T_START)
t0 = time.time()
RUTAS = V.simular(FILA, sis, os.path.join(SAL, "instantaneas"), output_every=10)
SN = {m: V.leer(r) for m, r in RUTAS.items()}
print("Instantaneas: %d cuadros x %d estrellas, %.0f s" % (len(SN["A"]["t"]), SN["A"]["pos"].shape[1], time.time() - t0))"""),
        ("code", """from p3streams import corrientes as Co
x0, v0 = Co.condiciones_iniciales(FILA["polo"], FILA["r_apo"], FILA["f"], FILA["psi_deg"])
PROC = "notebooks/09_videos.ipynb, p3streams %s, %s; stream r_apo 60 kpc, 5e7 Msun, 5 Gyr" % (C.VERSION, U.ahora())
t0 = time.time()
MP4A = V.academico(SN, sis, FILA["polo"], x0, os.path.join(SAL, "video_academico.mp4"),
                   titulo="Stream formation in the four models (MW frame)", procedencia=PROC)
print("academico: %.0f s" % (time.time() - t0)); t0 = time.time()
MP4P = V.prensa(SN["D"], SN["A"], sis, FILA["polo"], x0, os.path.join(SAL, "video_prensa.mp4"),
                titulo="How the Large Magellanic Cloud bends a stream of stars", procedencia=PROC)
print("prensa: %.0f s" % (time.time() - t0))
for mp4 in (MP4A, MP4P):
    V.a_gif(mp4, mp4[:-4] + ".gif")
for f in sorted(os.listdir(SAL)):
    if f.endswith((".mp4", ".gif")):
        print("%-24s %6.1f MB" % (f, os.path.getsize(os.path.join(SAL, f)) / 1e6))"""),
        ("code", """from IPython.display import Video, display
display(Video(MP4A, embed=False, width=720))
display(Video(MP4P, embed=False, width=720))"""),
    ]


NOTEBOOKS = {
    "04": ("04_hito4_catalogo.ipynb", nb04),
    "05": ("05_hito5_clasificacion.ipynb", nb05),
    "06": ("06_hito5_lsst.ipynb", nb06),
    "07": ("07_hito6_interpretacion.ipynb", nb07),
    "08": ("08_figuras_finales.ipynb", nb08),
    "09": ("09_videos.ipynb", nb09),
}
