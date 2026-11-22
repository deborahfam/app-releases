# App releases · deborahfam

Repositorio público de distribución para las aplicaciones de deborahfam. Contiene instaladores firmados, instrucciones y herramientas de publicación; **no contiene el código ni el historial de los repositorios privados de las aplicaciones**.

## Aplicaciones

- **[Keepr](apps/keepr/README.md)** — [descargar versión estable](https://github.com/deborahfam/app-releases/releases/tag/keepr-stable).
- **[SIMple](apps/simple/README.md)** — [descargar versión estable](https://github.com/deborahfam/app-releases/releases/tag/simple-stable).

Cada aplicación tiene su propio identificador y canal. No uses `/releases/latest`: devuelve la última publicación del repositorio entero y puede pertenecer a otra aplicación.

## Integrar otra aplicación

Pasa esta guía a la persona o agente que desarrolle tu siguiente app:

**[docs/INTEGRATION.md](docs/INTEGRATION.md)**

Ejemplo: `simple-stable` para SIMple y `otra-app-stable` para otra aplicación. Las versiones históricas se publican como `simple-v0.6.21` y `otra-app-v1.0.0`.

El cliente consulta su canal público sin tokens. La credencial de publicación se guarda únicamente en el equipo del desarrollador o en los secretos del CI privado. Los APK y demás instaladores son públicos y pueden inspeccionarse: no deben contener claves privadas, tokens, datos personales ni configuraciones confidenciales.

Las aplicaciones conservan sus propias licencias. Los ZIP automáticos de “Source code” que muestra GitHub corresponden solo a los archivos públicos de este repositorio de distribución.
