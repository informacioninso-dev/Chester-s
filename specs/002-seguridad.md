# 002 · Seguridad para producción

**Estado:** hecha
**Fecha:** 2026-11-11

## Qué y por qué

El sitio está listo para correr en local, pero no para internet. `check --deploy` da 4 advertencias (HTTPS, HSTS, cookies), con `DJANGO_DEBUG=0` arranca igual con la `SECRET_KEY` de ejemplo y los formularios públicos no tienen ningún freno contra spam: un bot puede llenar la base y disparar miles de webhooks a Binn. Además, `?limite=-1` en la API devuelve un error 500.

## Criterios de aceptación

- [x] Con `DJANGO_DEBUG=0` y sin `DJANGO_SECRET_KEY`, el arranque falla con un mensaje claro en vez de usar la clave de ejemplo.
- [x] Con `DJANGO_DEBUG=0`, `manage.py check --deploy` no da advertencias: redirección a HTTPS, cookies `Secure` y HSTS (30 días por defecto, configurable con `DJANGO_HSTS_SECONDS`; subdominios y preload se activan a mano y, mientras estén apagados, sus dos advertencias quedan silenciadas a propósito).
- [x] Detrás de un proxy (`DJANGO_BEHIND_PROXY=1`) se respeta `X-Forwarded-Proto`, y `DJANGO_CSRF_TRUSTED_ORIGINS` permite declarar el dominio.
- [x] Confirmar pedido y la Ruleta aceptan como máximo 10 envíos cada 10 minutos por IP; al pasarse responden 429 con un mensaje amable en el mismo panel.
- [x] Ambos formularios tienen un campo trampa oculto: si llega lleno, no se guarda nada ni se avisa a Binn, pero se responde como si todo hubiera salido bien.
- [x] La API de Binn acepta `limite` entre 1 y 1000; un valor negativo, cero o no numérico no da error 500.
- [x] La ruta del admin se puede cambiar con `DJANGO_ADMIN_URL` (por defecto `admin/`).
- [x] htmx se sirve desde los estáticos propios, no desde unpkg.

## Fuera de alcance

- Content-Security-Policy: hay que compilar Tailwind primero (spec 003) y sacar los `hx-on` en línea.
- Límite de envíos compartido entre varios procesos (usa la caché en memoria; sirve para un solo servidor).

## Notas técnicas

- Todo en `settings.py` con variables de entorno, sin dependencias nuevas.
- El límite usa el framework de caché de Django; la IP sale de `REMOTE_ADDR`, o de `X-Forwarded-For` solo si `DJANGO_BEHIND_PROXY=1`.
- `DEBUG` sigue en `1` por defecto para desarrollo: un despliegue sin variables ya falla por `ALLOWED_HOSTS`.
