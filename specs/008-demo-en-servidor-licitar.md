# 008 · Demo en el servidor de Licitar

**Estado:** en curso
**Fecha:** 2026-11-12

## Qué y por qué

El dueño de Chester’s necesita ver el sitio funcionando en internet antes de salir a producción. Para no pagar otro servidor, la demo corre en el droplet de Licitar (DigitalOcean, 1 GB) en `chesters.binnso.com`, separada de Licitar: su propia carpeta, su propio contenedor y su propia base.

## Criterios de aceptación

- [ ] `https://chesters.binnso.com/` responde 200 con certificado válido y `http://` redirige a `https://`.
- [ ] La demo no se indexa: todas las respuestas llevan `X-Robots-Tag: noindex, nofollow`.
- [ ] Los pedidos y cumpleaños se guardan en un volumen de Docker y sobreviven a un nuevo despliegue (`DJANGO_DB_PATH`).
- [ ] El freno anti-spam ve la IP real del visitante, no la de Caddy (`DJANGO_BEHIND_PROXY=1`).
- [ ] Licitar sigue respondiendo 200 después del despliegue.
- [ ] Ningún secreto queda en el repo: la clave y el número de WhatsApp viven en `/opt/chesters/.env.production`.

Los criterios de infraestructura se verifican en el servidor (curl) y el resultado se anota abajo; `DJANGO_DB_PATH` tiene test.

## Fuera de alcance

- Dominio propio de Chester’s, PostgreSQL y respaldos automáticos: llegan con la salida a producción.
- Revisión legal de `/privacidad/` (pendiente de la spec 001).

## Notas técnicas

- **Dependencia nueva: `gunicorn`.** `runserver` no sirve para internet (un hilo, sin reinicio de procesos, Django lo desaconseja). Gunicorn es el servidor WSGI que ya usa Licitar en el mismo droplet.
- `Dockerfile` (python:3.13-slim) y `docker-compose.yml` con un solo servicio, `chesters-web`, con 1 worker y 4 hilos, y límite de 200 MB de memoria. El droplet tiene unos 280 MB libres.
- El contenedor se une a la red `licitar_default` para que el Caddy de Licitar le pase el tráfico. El bloque `chesters.binnso.com` va en `deploy/Caddyfile` **del repo de Licitar**. Si no va ahí, el siguiente despliegue de Licitar lo borraría.
- Al arrancar, el contenedor corre `migrate`. `collectstatic` se hace al construir la imagen.
- Despliegue: `git archive HEAD` → `/opt/chesters` → `docker compose up -d --build`. Ver README.

## Resultado

Pendiente.
