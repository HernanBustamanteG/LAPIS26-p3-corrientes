# Subir este repositorio a GitHub (una vez)

El repositorio tiene que llamarse `lapis26-p3-corrientes` y estar en la cuenta `HernanBustamanteG`: los botones
"Open in Colab" y la primera celda de cada notebook apuntan a
`https://github.com/HernanBustamanteG/lapis26-p3-corrientes`.

**Público o privado.** Colab abre sin más un repositorio público. Si se deja privado, Colab pide autorizar GitHub
al abrir el notebook y la celda 1 no puede clonarlo sin un token: para compartirlo con compañeros conviene público
(son resultados propios; no incluye datos ni código no publicado de nadie más).

## Opción A: desde la VM (terminal)

1. En github.com: **New repository** → nombre `lapis26-p3-corrientes`, público, **sin** README ni licencia (ya
   vienen en la carpeta).
2. En la VM:

```
conda activate lapis26 && cd ~/lapis2026/p3_corrientes/lapis26-p3-corrientes && git init -b main && git add . && git commit -m "Proyecto 3 LAPIS 2026: corrientes, LMC y movimiento reflejo" && git remote add origin https://github.com/HernanBustamanteG/lapis26-p3-corrientes.git && git push -u origin main
```

GitHub pide usuario y un *personal access token* (Settings → Developer settings → Tokens) como contraseña.
El token no se comparte con nadie ni se pega en el chat.

## Opción B: desde el navegador

En el repositorio vacío: **uploading an existing file** → arrastrar el contenido de la carpeta (no la carpeta
misma) → **Commit changes**. GitHub web acepta hasta 100 archivos por vez: subir primero `p3streams/` y
`notebooks/`, después el resto.

## Comprobar

Abrir el botón "Open in Colab" de `notebooks/00_entorno.ipynb` en el README y ejecutar todo: el autotest debe
terminar con "14 de 14 pruebas pasan".
