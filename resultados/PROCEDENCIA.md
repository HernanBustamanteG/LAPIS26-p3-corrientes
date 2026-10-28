# Procedencia de las tablas de resultados/

| archivo | filas | carpeta de origen (corrida) | sha256 |
|---|---|---|---|
| catalogo_piloto.csv | 72 | `catalogo_piloto_M1.8_20261027_155034` | `39b4d57e53a702ba` |
| catalogo_principal.csv | 288 | `principal_20261027_161540` | `9ebd94b7b6cb968f` |
| catalogo_distancia.csv | 60 | `distancia_20261027_175727` | `7acaec56f9c7cf6d` |
| catalogo_longitud.csv | 36 | `longitud_20261027_181504` | `3c3caae1cd6917d0` |
| catalogo_masa_1.0.csv | 36 | `masa_1.0_20261027_202451` | `fb9c160910fdb707` |
| catalogo_masa_1.5.csv | 36 | `masa_1.5_20261027_203353` | `a1ef1e76d3d9b65b` |
| catalogo_masa_1.8.csv | 36 | `masa_1.8_20261027_204541` | `53f35328026d46fa` |
| catalogo_masa_2.5.csv | 36 | `masa_2.5_20261027_205423` | `c03b4ca2b0fbf4ba` |
| lsst_principal.csv | 288 | `lsst_f1e-02_10a_20261027_200046` | `7f7ee69970e2ed46` |
| por_radio_principal.csv | 9 | `principal_20261027_161540` | `1969a31310c2c214` |

## Metadatos de cada corrida

### catalogo_principal
```json
{
 "fecha": "2026-10-27T16:15:40",
 "versiones": {
  "python": "3.13.16",
  "plataforma": "Linux-6.18.44-fc-v165-x86_64-with-glibc2.39",
  "p3streams": "1.0",
  "numpy": "2.2.6",
  "scipy": "1.18.1",
  "astropy": "8.0.2",
  "gala": "1.12.0",
  "matplotlib": "3.11.2",
  "pandas": "3.1.0",
  "healpy": "1.20.1"
 },
 "plan": "principal",
 "parametros": {
  "n_polos": 2,
  "polos": "healpy",
  "sentidos": false,
  "fases": [
   0.0,
   90.0
  ],
  "m_lmc": 180000000000.0,
  "nota": "48 polos HEALPix x 3 familias x 2 fases"
 },
 "n_corrientes": 288
}
```

### catalogo_distancia
```json
{
 "fecha": "2026-10-27T17:57:27",
 "versiones": {
  "python": "3.13.16",
  "plataforma": "Linux-6.18.44-fc-v165-x86_64-with-glibc2.39",
  "p3streams": "1.0",
  "numpy": "2.2.6",
  "scipy": "1.18.1",
  "astropy": "8.0.2",
  "gala": "1.12.0",
  "matplotlib": "3.11.2",
  "pandas": "3.1.0",
  "healpy": "1.20.1"
 },
 "plan": "distancia",
 "parametros": {
  "n_polos": 1,
  "polos": "healpy",
  "sentidos": false,
  "fases": [
   0.0
  ],
  "m_lmc": 180000000000.0,
  "familias": {
   "r030": {
    "r_apo": 30.0,
    "m_prog": 10000000.0
   },
   "r045": {
    "r_apo": 45.0,
    "m_prog": 10000000.0
   },
   "r070": {
    "r_apo": 70.0,
    "m_prog": 10000000.0
   },
   "r100": {
    "r_apo": 100.0,
    "m_prog": 10000000.0
   },
   "r150": {
    "r_apo": 150.0,
    "m_prog": 10000000.0
   }
  },
  "nota": "12 polos HEALPix x r_apo 30, 45, 70, 100, 150 kpc, 1e7 Msun"
 },
 "n_corrientes": 60
}
```

### catalogo_longitud
```json
{
 "fecha": "2026-10-27T18:15:04",
 "versiones": {
  "python": "3.13.16",
  "plataforma": "Linux-6.18.44-fc-v165-x86_64-with-glibc2.39",
  "p3streams": "1.0",
  "numpy": "2.2.6",
  "scipy": "1.18.1",
  "astropy": "8.0.2",
  "gala": "1.12.0",
  "matplotlib": "3.11.2",
  "pandas": "3.1.0",
  "healpy": "1.20.1"
 },
 "plan": "longitud",
 "parametros": {
  "n_polos": 1,
  "polos": "healpy",
  "sentidos": false,
  "fases": [
   0.0
  ],
  "m_lmc": 180000000000.0,
  "familias": {
   "m1e6": {
    "r_apo": 60.0,
    "m_prog": 1000000.0
   },
   "m1e7": {
    "r_apo": 60.0,
    "m_prog": 10000000.0
   },
   "m1e8": {
    "r_apo": 60.0,
    "m_prog": 100000000.0
   }
  },
  "nota": "12 polos HEALPix x M_prog 1e6, 1e7, 1e8 Msun a r_apo = 60 kpc"
 },
 "n_corrientes": 36
}
```

### catalogo_masa_1.0
```json
{
 "fecha": "2026-10-27T20:24:51",
 "versiones": {
  "python": "3.13.16",
  "plataforma": "Linux-6.18.44-fc-v165-x86_64-with-glibc2.39",
  "p3streams": "1.0",
  "numpy": "2.2.6",
  "scipy": "1.18.1",
  "astropy": "8.0.2",
  "gala": "1.12.0",
  "matplotlib": "3.11.2",
  "pandas": "3.1.0",
  "healpy": "1.20.1"
 },
 "plan": "masa_1.0",
 "parametros": {
  "n_polos": 1,
  "polos": "healpy",
  "sentidos": false,
  "fases": [
   0.0
  ],
  "m_lmc": 100000000000.0,
  "nota": "12 polos HEALPix x 3 familias, M_LMC = 1.0e+11 Msun"
 },
 "n_corrientes": 36
}
```

### catalogo_masa_1.5
```json
{
 "fecha": "2026-10-27T20:33:53",
 "versiones": {
  "python": "3.13.16",
  "plataforma": "Linux-6.18.44-fc-v165-x86_64-with-glibc2.39",
  "p3streams": "1.0",
  "numpy": "2.2.6",
  "scipy": "1.18.1",
  "astropy": "8.0.2",
  "gala": "1.12.0",
  "matplotlib": "3.11.2",
  "pandas": "3.1.0",
  "healpy": "1.20.1"
 },
 "plan": "masa_1.5",
 "parametros": {
  "n_polos": 1,
  "polos": "healpy",
  "sentidos": false,
  "fases": [
   0.0
  ],
  "m_lmc": 150000000000.0,
  "nota": "12 polos HEALPix x 3 familias, M_LMC = 1.5e+11 Msun"
 },
 "n_corrientes": 36
}
```

### catalogo_masa_1.8
```json
{
 "fecha": "2026-10-27T20:45:41",
 "versiones": {
  "python": "3.13.16",
  "plataforma": "Linux-6.18.44-fc-v165-x86_64-with-glibc2.39",
  "p3streams": "1.0",
  "numpy": "2.2.6",
  "scipy": "1.18.1",
  "astropy": "8.0.2",
  "gala": "1.12.0",
  "matplotlib": "3.11.2",
  "pandas": "3.1.0",
  "healpy": "1.20.1"
 },
 "plan": "masa_1.8",
 "parametros": {
  "n_polos": 1,
  "polos": "healpy",
  "sentidos": false,
  "fases": [
   0.0
  ],
  "m_lmc": 180000000000.0,
  "nota": "12 polos HEALPix x 3 familias, M_LMC = 1.8e+11 Msun"
 },
 "n_corrientes": 36
}
```

### catalogo_masa_2.5
```json
{
 "fecha": "2026-10-27T20:54:23",
 "versiones": {
  "python": "3.13.16",
  "plataforma": "Linux-6.18.44-fc-v165-x86_64-with-glibc2.39",
  "p3streams": "1.0",
  "numpy": "2.2.6",
  "scipy": "1.18.1",
  "astropy": "8.0.2",
  "gala": "1.12.0",
  "matplotlib": "3.11.2",
  "pandas": "3.1.0",
  "healpy": "1.20.1"
 },
 "plan": "masa_2.5",
 "parametros": {
  "n_polos": 1,
  "polos": "healpy",
  "sentidos": false,
  "fases": [
   0.0
  ],
  "m_lmc": 250000000000.0,
  "nota": "12 polos HEALPix x 3 familias, M_LMC = 2.5e+11 Msun"
 },
 "n_corrientes": 36
}
```

### lsst_principal
```json
{
 "fecha": "2026-10-27T20:00:46",
 "versiones": {
  "python": "3.13.16",
  "plataforma": "Linux-6.18.44-fc-v165-x86_64-with-glibc2.39",
  "p3streams": "1.0",
  "numpy": "2.2.6",
  "scipy": "1.18.1",
  "astropy": "8.0.2",
  "gala": "1.12.0",
  "matplotlib": "3.11.2",
  "pandas": "3.1.0",
  "healpy": "1.20.1"
 },
 "catalogo": "salidas/principal_20261027_161540",
 "frac": 0.01,
 "anios": 10.0,
 "n_boot": 20
}
```

`por_radio_principal.csv`: `p3streams.analisis.por_radio` sobre las corrientes guardadas de la corrida principal (cambio del polo estrella a estrella respecto de la misma estrella en el modelo A).

## Incidencias

- `catalogo_masa_2.5`: el contenedor se reinició durante la corrida (6 de 36 filas hechas). Los archivos de las dos
  corrientes que estaban a medio escribir se apartaron a `_incompletos_reinicio_contenedor/` dentro de la carpeta de
  la corrida y la corrida se retomó con `--carpeta`; esas dos corrientes se recalcularon desde cero.
- `catalogo_piloto`: corrido con un script previo a `p3streams.ejecutar` (mismo código del paquete; sin
  `metadatos.json`). Sus parámetros son los del plan `piloto`.
