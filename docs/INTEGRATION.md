# Integrar cualquier aplicación en app-releases

Repositorio de distribución: **deborahfam/app-releases**.

## Instrucción para pasar a otra app o agente

> Integra las actualizaciones de esta aplicación con `deborahfam/app-releases`. Mantén el código en su repositorio actual. Elige un ID exclusivo en minúsculas (por ejemplo `mi-app`) y usa el canal `mi-app-stable`. Consulta `https://api.github.com/repos/deborahfam/app-releases/releases/tags/mi-app-stable` sin autenticación. No uses el endpoint global `/releases/latest`. Publica versiones históricas como `mi-app-v1.0.0` y usa un código de compilación entero creciente. Cada instalador debe tener un nombre único por código. Verifica el identificador de la app, la versión y la firma antes de instalar; rechaza retrocesos y URLs de otra app. Conserva los datos al actualizar. No incluyas tokens en la app, código privado, archivos de firma o datos personales en este repositorio. Usa el publicador y las instrucciones que siguen, y documenta la nueva app en `apps/<id>/README.md`.

## Contrato del canal

- ID de app: 2–40 caracteres, minúsculas, números y guiones; comienza por letra.
- Canal estable: `<id>-stable`.
- Versión histórica: `<id>-v<major>.<minor>.<patch>`.
- Código: entero positivo creciente **por app**, nunca reutilizado para un binario distinto.
- Archivos: nombres que incluyen el código, por ejemplo `MiApp-12.apk`, y `SHA256SUMS.txt`.
- Endpoint: `https://api.github.com/repos/deborahfam/app-releases/releases/tags/<id>-stable`.
- Metadatos de la API: `tag_name` debe coincidir; rechaza borradores y preversiones. Selecciona solo assets con `state=uploaded` y el patrón de nombre de tu app; ignora los demás.
- URL permitida del binario: `https://github.com/deborahfam/app-releases/releases/download/<id>-stable/<archivo>`.
- GitHub puede redirigir el binario a sus hosts de assets. Usa HTTPS, una lista explícita de hosts, límites de tamaño/tiempo y un máximo de redirecciones. Nunca envíes credenciales desde el cliente.
- El hash detecta corrupción, pero no sustituye verificar la firma de la app. Android: comprueba package ID, versionCode y certificado/rotación autorizada antes de abrir el instalador. Para otras plataformas usa su firma de código equivalente.
- Si falla la consulta o descarga, conserva la instalación y permite reintentar. No desinstales para actualizar.

## Publicación desde el equipo

Requisitos: Python 3.11+, GitHub CLI autenticado y permiso de escritura sobre este repositorio. Firma y prueba el instalador en el repositorio privado antes de publicarlo.

```bash
git clone https://github.com/deborahfam/app-releases.git
python3 app-releases/scripts/publish.py \
  --app mi-app --version 1.0.0 --code 1 \
  --asset /ruta/MiApp-1.apk \
  --asset /ruta/SHA256SUMS.txt
```

Pasa archivos concretos; nunca una carpeta completa del proyecto ni comodines. Para formatos ZIP, revisa su contenido antes: el publicador no puede determinar si un archivo contiene información privada. `--notes /ruta/notas-publicas.md` permite añadir novedades; no copies notas con rutas locales, correos privados o referencias confidenciales.

El publicador crea primero la versión histórica y después actualiza el canal estable. Rechaza retrocesos y reutilizar un código con otros archivos. No modifica el código de ninguna aplicación. Los reintentos con exactamente los mismos archivos son idempotentes. No ejecutes publicaciones concurrentes de la misma app; serialízalas en el CI. Diferentes apps pueden publicarse independientemente.

## Publicación automática desde un repositorio privado

1. Crea un token **fine-grained**, propietario `deborahfam`, acceso únicamente a **app-releases**, permiso **Contents: Read and write** y caducidad apropiada.
2. Guárdalo en el repositorio privado como secreto de Actions **APP_RELEASES_TOKEN**. Nunca lo pegues en código, conversaciones o logs.
3. Copia una versión revisada de `scripts/publish.py` a tu repositorio privado. Si prefieres descargarlo en CI, fija un commit completo; no ejecutes scripts remotos flotantes.
4. Después de compilar, probar y firmar, llama al publicador con `GH_TOKEN` definido solo en ese paso:

```yaml
- name: Publish public application channel
  env:
    GH_TOKEN: ${{ secrets.APP_RELEASES_TOKEN }}
  run: |
    test -n "$GH_TOKEN"
    python3 scripts/publish_public.py \
      --app mi-app --version 1.0.0 --code 1 \
      --asset "$RUNNER_TEMP/release/MiApp-1.apk" \
      --asset "$RUNNER_TEMP/release/SHA256SUMS.txt"
```

Sustituye los números por las salidas de tu flujo de versionado y usa `concurrency` por app. El `GITHUB_TOKEN` normal del repositorio privado no puede publicar en este otro repositorio. Las claves de firma permanecen en los secretos del proyecto privado; solo se transfieren los instaladores firmados y checksums. Si el token caduca, renueva el secreto. El publicador muestra errores de red/permisos como errores, no como ausencia de versiones.

## Migrar una app ya instalada

Publica una nueva versión firmada con la misma identidad de instalación y un código mayor, apuntando al nuevo canal. Si el canal antiguo ya es privado, entrega el enlace público de esa nueva versión: el usuario la instala **sobre la anterior**, sin desinstalar. Desde esa versión, las actualizaciones vuelven a descargarse dentro de la app.
