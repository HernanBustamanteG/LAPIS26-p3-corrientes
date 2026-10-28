"""Todas las decisiones del proyecto, con fuente.

Unidades internas: kpc, Myr, Msun, kpc/Myr (sistema `galactic` de gala). Velocidades de entrada en km/s.
Marco: el de la MW (centro de la MW en el origen, ejes galactocentricos de astropy; el Sol en x < 0).
"""

import os

VERSION = "1.0"

# dynamical_friction_MWLMC_tutorial.ipynb, seccion 1a (LAPIS26, J. N. Garavito-Camargo)
MW_DISCO = dict(m=4.7717e10, h_R=2.6, h_z=0.3)            # MN3ExponentialDiskPotential
MW_BULBO = dict(m=5e9, c=1.0)                              # Hernquist
MW_NUCLEO = dict(m=1.8142e9, c=0.0688867)                  # Hernquist
MW_HALO = dict(v_c=171.6, r_s=15.626, a=1.0, b=1.0, c=1.0)  # LeeSutoTriaxialNFW (esferico)

LMC_M = 1.8e11            # Msun, Hernquist
LMC_A = 20.0              # kpc
LMC_MASAS = (1.0e11, 1.5e11, 1.8e11, 2.5e11)   # tema avanzado del enunciado (1, 1.5, 2.5) + la del tutorial
LMC_X0 = (-1.1, -41.1, -27.9)       # kpc, hoy (Kallivayalil+2013 via Garavito-Camargo+2019)
LMC_V0 = (-57.0, -226.0, 221.0)     # km/s
# Friccion dinamica: van der Marel+2012 para cociente de masas 1:10 (forma 'VdM' del tutorial)
DF_LNL = dict(L=0.0, C=1.22, alpha=1.0, form="VdM")

T_ATRAS = 7000.0          # Myr: el sistema MW + LMC se integra hasta 7 Gyr atras (cubre t_start <= 6 Gyr)
DT_SISTEMA = 1.0          # Myr
DT_NUDOS = 5.0            # Myr entre nudos de los potenciales interpolados en el tiempo
D_CAMPO = 1.0e6           # kpc: distancia de la masa puntual que imita el campo uniforme -a_MW

T_START = 5000.0          # Myr atras
DT_CORRIENTE = 1.0        # Myr
RELEASE_EVERY = 2
N_PARTICULAS = 1          # por brazo y por liberacion
M_PROG = 1e7              # Msun (enunciado: 1e7-1e8 para corrientes largas)
F_TANG = 0.5              # v0 = f v_c(r_apo); enunciado: f = 0.5 a 100 kpc -> peri ~27 kpc
SEMILLA = 2026

SOL_R = 8.122             # kpc (GRAVITY 2018)
SOL_Z = 0.0208            # kpc (Bennett & Bovy 2019)
SOL_V = (12.9, 245.6, 7.78)   # km/s (Drimmel & Poggio 2018; Reid & Brunthaler 2004; GRAVITY 2018)

F_REFLEJO_ALTO = 0.6
F_REFLEJO_BAJO = 0.4

LSST_DEC_MAX = 5.0                     # grados, footprint aproximado (enunciado: Dec <~ +5)
LSST_R_LIM_10A = 27.0                  # coadd 10 anios (enunciado; Ivezic+2019 da r ~ 27.5)
LSST_R_LIM_VISITA = 24.5
# sigma_mu(r) para 10 anios: 0.2 mas/yr a r = 21 y 1.0 mas/yr a r = 24 (Ivezic+2019, Tabla 1 / sec. 3.2.3)
LSST_PM_PUNTOS = ((21.0, 0.2), (24.0, 1.0))
LSST_PM_R_MAX = 24.5                   # mas alla no se usa el movimiento propio
LSST_R_SATURACION = 16.0               # r < 16 satura (streamobs, config/surveys/lsst_yr*.yaml)
# Gaia DR3 (Lindegren+2021): sigma_mu ~ 0.02-0.03 (G<15), 0.07 (G=17), 0.5 (G=20), 1.4 mas/yr (G=21)
GAIA_PM_PUNTOS = ((15.0, 0.025), (17.0, 0.07), (20.0, 0.5), (21.0, 1.4))
GAIA_G_LIM = 21.0
ERROR_DIST_FOTOMETRICA = 0.07          # 5-10 % (enunciado, tema avanzado)
FRACCION_ESTELAR = 1.0e-2              # M_* / M_prog para progenitores enanos (supuesto; se varia en el notebook 06)
ISOCRONA = "datos_entrada/isocrona_parsec_lsst_a12.0_z0.00020.dat"

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def carpeta_salidas():
    """En Colab con Drive montado: MyDrive/lapis26_p3/salidas; si no, <repo>/salidas."""
    drive = "/content/drive/MyDrive"
    base = os.path.join(drive, "lapis26_p3") if os.path.isdir(drive) else RAIZ
    return os.environ.get("P3_SALIDAS", os.path.join(base, "salidas"))
