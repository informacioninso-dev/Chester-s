# 003 · Rendimiento

**Estado:** aprobada
**Fecha:** 2026-11-11

## Qué y por qué

La portada carga el CDN de prueba de Tailwind: unos 400 KB de JavaScript que bloquean la página y generan los estilos en el navegador de cada visitante, lo que provoca un parpadeo sin estilos en celulares lentos. Las imágenes van en JPG a tamaño completo (el avatar de 480 px se usa también a 40 px en el menú) y los estáticos no tienen caché de larga duración.

## Criterios de aceptación

- [ ] La página ya no carga `cdn.tailwindcss.com`: usa un CSS compilado y minificado de `pedidos/static/`, que se versiona en el repo (no hace falta Node para desplegar, solo para regenerarlo).
- [ ] El README explica cómo regenerar el CSS (`npx tailwindcss@3.4.17 …`) después de tocar plantillas.
- [ ] Las imágenes tienen versión WebP con JPG de respaldo (`<picture>`), y el menú usa un avatar pequeño.
- [ ] En producción los estáticos llevan un hash en el nombre y se sirven comprimidos con caché de 1 año (WhiteNoise).
- [ ] Todos los tests siguen pasando y la página se ve igual que antes.

## Fuera de alcance

- Alojar las fuentes en el propio servidor (Google Fonts ya usa `display=swap` y `preconnect`).
- CDN propio para los estáticos.

## Notas técnicas

- Revierte la decisión "Sin build de frontend" de MEMORY.md: el build es local y su resultado se versiona.
- Nueva dependencia: `whitenoise`. Sirve los estáticos desde Django en cualquier hosting sin configurar Nginx.
- La conversión a WebP se hace una sola vez con Pillow en el entorno local; Pillow no entra en `requirements.txt`.
