# 001 · Política de privacidad (LOPDP)

**Estado:** hecha
**Fecha:** 2026-11-11

## Qué y por qué

Los formularios del configurador y de la Ruleta piden autorización "conforme a la LOPDP", pero no hay ninguna política que la persona pueda leer. Hace falta una página pública que explique qué datos se guardan, para qué, con quién se comparten y cómo ejercer los derechos, y que esté enlazada desde los dos textos de autorización.

## Criterios de aceptación

- [x] `GET /privacidad/` responde 200 y muestra la política: responsable, datos, finalidad, base legal, destinatarios (Binn y WhatsApp), conservación, derechos y cómo ejercerlos.
- [x] El texto de autorización del configurador (paso 4) enlaza a `/privacidad/`.
- [x] El texto de autorización de la Ruleta enlaza a `/privacidad/`.
- [x] El footer de la landing enlaza a `/privacidad/`.
- [x] La página usa el mismo `<head>` (Tailwind, fuentes, colores) que la landing, sin duplicarlo.

## Fuera de alcance

- Revisión legal del texto (la hace el dueño o su abogado).
- Banner de cookies: el sitio no usa cookies de seguimiento.

## Notas técnicas

- El `<head>` común pasa a `partials/head.html`; la landing y la política lo incluyen.
- Los enlaces desde los formularios abren en una pestaña nueva para no perder lo que la persona ya escribió.
