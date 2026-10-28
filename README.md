# Corrientes estelares como sondas de la LMC y del movimiento reflejo de la Vía Láctea

**XII LAPIS 2026, Proyecto 3** (enunciado de J. N. Garavito-Camargo, repositorio
[LAPIS26](https://github.com/jngaravitoc/LAPIS26)). Hernán Bustamante, Universidad Central de Chile.

*Stellar streams as probes of the LMC and the Milky Way's reflex motion.* Mock streams of different lengths
(up to two wraps) on 288 orbits, each one in four rigid potentials written in the Milky Way frame: isolated MW
(A), reflex motion only (B), direct LMC pull only (C) and the full MW + LMC system (D). Three metrics
(proper-motion misalignment, orbital poles, plane tilt), a reflex / torque classification, predictions for LSST,
and a comparison with observed streams (galstreams). Everything runs in Google Colab.

## Abrir en Colab

| notebook | contenido |
|---|---|
| [00 · entorno](notebooks/00_entorno.ipynb) [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HernanBustamanteG/lapis26-p3-corrientes/blob/main/notebooks/00_entorno.ipynb) | versiones fijas, autotest (14 pruebas con respuesta conocida) |
| [01 · hito 1](notebooks/01_hito1_una_corriente.ipynb) [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HernanBustamanteG/lapis26-p3-corrientes/blob/main/notebooks/01_hito1_una_corriente.ipynb) | una corriente en la MW aislada y en MW + LMC; versión literal en $(\phi_1,\phi_2)$ |
| [02 · hito 2](notebooks/02_hito2_potenciales.ipynb) [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HernanBustamanteG/lapis26-p3-corrientes/blob/main/notebooks/02_hito2_potenciales.ipynb) | los cuatro potenciales validados; $\lvert\mathbf a_{\rm MW}(t)\rvert$ y distancia de la LMC |
| [03 · hito 3](notebooks/03_hito3_metricas.ipynb) [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HernanBustamanteG/lapis26-p3-corrientes/blob/main/notebooks/03_hito3_metricas.ipynb) | la figura única con las tres métricas; corrientes corta, larga y de dos vueltas |
| [04 · hito 4](notebooks/04_hito4_catalogo.ipynb) [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HernanBustamanteG/lapis26-p3-corrientes/blob/main/notebooks/04_hito4_catalogo.ipynb) | el catálogo (incluido; se puede rehacer y retomar) |
| [05 · hito 5](notebooks/05_hito5_clasificacion.ipynb) [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HernanBustamanteG/lapis26-p3-corrientes/blob/main/notebooks/05_hito5_clasificacion.ipynb) | reflejo contra torque: mapas, tendencias, cancelaciones |
| [06 · hito 5, LSST](notebooks/06_hito5_lsst.ipynb) [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HernanBustamanteG/lapis26-p3-corrientes/blob/main/notebooks/06_hito5_lsst.ipynb) | qué vería LSST y con qué error |
| [07 · hito 6](notebooks/07_hito6_interpretacion.ipynb) [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HernanBustamanteG/lapis26-p3-corrientes/blob/main/notebooks/07_hito6_interpretacion.ipynb) | Sgr, Orphan–Chenab, S5; masa de la LMC; halo achatado |
| [08 · figuras finales](notebooks/08_figuras_finales.ipynb) [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HernanBustamanteG/lapis26-p3-corrientes/blob/main/notebooks/08_figuras_finales.ipynb) | resumen académico y figuras de prensa (4K) |
| [09 · videos](notebooks/09_videos.ipynb) [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HernanBustamanteG/lapis26-p3-corrientes/blob/main/notebooks/09_videos.ipynb) | MP4 y GIF, académico y de prensa |

La primera celda de cada notebook clona este repositorio, instala versiones fijas (`requirements-colab.txt`) y
monta Google Drive: las salidas quedan en `MyDrive/lapis26_p3/salidas/<notebook>_<fecha>/`. Si numpy cambia de
versión, la sesión se reinicia **una vez** y hay que volver a ejecutar esa celda.

## Resultados principales

Con la MW y la LMC ($1.8\times10^{11}\,M_\odot$) del tutorial y 288 corrientes en la grilla principal (detalles,
números y límites en los notebooks 05 a 07):

1. **Quién domina depende sobre todo de la distancia.** Con la misma masa de progenitor, la fracción de reflejo del
   cambio del polo sube de 0.30 (apocentro 30 kpc) a 0.80 (150 kpc). Las corrientes cortas a 100 kpc están dominadas
   por el reflejo (66 de 96); las de dos vueltas a 40 kpc, por el torque (72 de 96).
2. **Cerca del centro los dos efectos se cancelan.** Estrella por estrella, el reflejo solo y el tirón solo inclinan
   las órbitas ~8–10° a todo radio; juntos, ~4° dentro de ~40 kpc.
3. **La orientación importa:** el reflejo inclina más los planos perpendiculares a $\mathbf a_{\rm MW}$. En ~1 de cada 4
   corrientes los dos efectos se compensan.
4. **LSST** ve bien las corrientes internas y largas: la señal del reflejo en el desalineamiento supera 3σ en ~5–10 %
   de ellas con errores conservadores y en ~50–80 % con los errores reescalados a todas las estrellas. Pero las corrientes dominadas por el reflejo son las lejanas, que LSST ve peor. Gaia casi
   nunca detecta el desalineamiento.
5. **Orphan–Chenab y las corrientes de S5** caen en la zona de torque o mixta. La clasificación es robusta a la masa de
   la LMC entre 1 y 2.5 × 10¹¹ M☉; la amplitud de las perturbaciones no lo es.
6. En un halo achatado ($c/a = 0.8$), las órbitas no polares precesan mucho más de lo que las inclina la LMC.

## Terminal (Colab o máquina propia)

```bash
python -m p3streams.ejecutar --autotest
python -m p3streams.ejecutar planes
python -m p3streams.ejecutar grilla --plan principal --simular
python -m p3streams.ejecutar grilla --plan principal --correr --procesos 2
python -m p3streams.ejecutar grilla --plan principal --correr --carpeta salidas/principal_<FECHA>   # retomar
python -m p3streams.ejecutar lsst --catalogo salidas/principal_<FECHA> --correr
```

## Estructura

```
p3streams/        el paquete: config (todas las decisiones, con fuente), potenciales, corrientes, metricas,
                  catalogo, observar y lsst, analisis, interpretar, figuras, prensa, videos, estilo, entorno,
                  autotest, ejecutar
notebooks/        00 a 09, ejecutados (las salidas se ven en GitHub)
resultados/       tablas de las corridas largas (CSV) y su procedencia (PROCEDENCIA.md)
datos_entrada/    isócrona PARSEC (solo lectura)
herramientas/     construcción y ejecución de los notebooks; exportación de resultados
```

## Reglas del proyecto

Los datos de entrada son de solo lectura; cada corrida y cada notebook escribe en una carpeta nueva y nunca pisa
un archivo; todo se puede retomar; las figuras llevan rótulos en inglés, unidades y su procedencia en los
metadatos del PNG. Los supuestos (y sus límites) están escritos en `p3streams/config.py` y en cada notebook.

## Créditos

Ver [CREDITOS.md](CREDITOS.md) (enunciado y tutorial de J. N. Garavito-Camargo; gala, astropy, galstreams,
PARSEC, healpy y demás). Licencia MIT
([LICENSE](LICENSE)).
