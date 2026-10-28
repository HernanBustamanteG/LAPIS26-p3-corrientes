# Créditos y referencias

## Proyecto
- Enunciado: *Project 3: Stellar streams as probes of the LMC and the Milky Way's reflex motion*,
  J. N. Garavito-Camargo, XII LAPIS 2026 (repositorio LAPIS26, licencia MIT).
- Modelos de la Vía Láctea y de la LMC, fricción dinámica de Chandrasekhar y condiciones de la LMC hoy:
  `dynamical_friction_MWLMC_tutorial.ipynb` del mismo repositorio (adaptados en `p3streams/potenciales.py`).

## Software
- gala (Price-Whelan 2017, JOSS 2, 388; Price-Whelan et al., Zenodo): potenciales, integración,
  `MockStreamGenerator`, `FardalStreamDF` (Fardal, Huang & Weinberg 2015, MNRAS 452, 301), `reflex_correct`,
  `GreatCircleICRSFrame`.
- Astropy (Astropy Collaboration 2013, 2018, 2022), NumPy (Harris et al. 2020), SciPy (Virtanen et al. 2020),
  Matplotlib (Hunter 2007), pandas (McKinney 2010), h5py, healpy (Zonca et al. 2019) y HEALPix (Górski et al. 2005).
- galstreams (Mateu 2023, MNRAS 520, 5225): trazas de las corrientes observadas (cada traza con su referencia).
- FFmpeg (H.264 con x264) para los videos.
- Tipografía Inter (The Inter Project Authors, SIL OFL 1.1).

## Datos y supuestos con fuente
- Isócrona PARSEC v1.2S + COLIBRI S_35 (Bressan et al. 2012; Chen et al. 2014, 2015; Tang et al. 2014;
  Marigo et al. 2017; Pastorelli et al. 2019), 12 Gyr, Z = 0.0002, bandas LSST ugrizy (AB), IMF de
  Chabrier (2001); generada con CMD 3.8 y distribuida con ugali (release v1.9.0).
- Movimiento y posición del Sol: `astropy.coordinates.Galactocentric` v4.0 (GRAVITY Collaboration 2018;
  Bennett & Bovy 2019; Drimmel & Poggio 2018; Reid & Brunthaler 2004).
- LSST: Ivezić et al. 2019, ApJ 873, 111 (profundidad de 10 años y errores de movimiento propio).
- Gaia DR3: Lindegren et al. 2021, A&A 649, A2 (errores de movimiento propio, aproximados).

## Literatura del enunciado
Gómez et al. 2015; Vasiliev, Belokurov & Erkal 2021; Garavito-Camargo et al. 2019; Petersen & Peñarrubia 2021;
Vasiliev 2023; Koposov et al. 2019; Erkal et al. 2019; Shipp et al. 2021; Ivezić et al. 2019; Fardal et al. 2015;
Mateu 2023 (lista completa con arXiv en `project_3_streams.md`).
