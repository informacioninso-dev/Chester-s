# 009 · "Pedir con Melloco" siempre visible

**Estado:** hecha
**Fecha:** 2026-11-12

## Qué y por qué

El botón flotante "Pedir con Melloco" casi nunca se veía en el celular: se escondía en la portada, en el configurador y en la Ruleta, que juntos son casi toda la página. El dueño quiere que se vea **siempre**, porque el chat es la forma más cómoda de pedir desde el teléfono (spec 005).

Desde la spec 007 el título y "Pedir su pastel" van arriba en la portada y el botón flotante queda abajo, así que ya no se tapan. Esta spec reemplaza los criterios de la 005 y la 007 que escondían el botón.

## Criterios de aceptación

- [x] El botón se ve en toda la página, en celular, tablet y computador. Nunca se esconde, tampoco mientras se escribe.
- [x] En la portada y en la historia se ve completo: "Pedir con Melloco".
- [x] Sobre el configurador y la Ruleta se reduce a la carita de Melloco (un círculo) para no tapar campos. Para lectores de pantalla sigue llamándose "Pedir con Melloco".
- [x] Con el chat abierto dice "Cerrar" completo en cualquier zona.

## Fuera de alcance

- Cambiar el diseño del panel del chat.

## Notas técnicas

- Solo cambia el script de `index.html`. En el modo compacto el texto pasa a `sr-only`, y así el botón conserva su nombre accesible.
- En Android, con el teclado abierto, el botón sube junto al teclado (el viewport se achica). Se aceptó a cambio de que esté siempre a mano.
- Los criterios se verifican con Chrome emulando cada pantalla (CDP). El test revisa que el script no esconda el botón.

## Resultado

- Verificado en Chrome emulando iPhone SE (375 px), iPad (768 px) y computador (1280 px). En los tres el botón se ve completo (207×52) en la portada y la historia, compacto (52×52) sobre el configurador y la Ruleta, también mientras se escribe, y dice "Cerrar" con el chat abierto. Nunca se esconde.
- 72 tests (1 nuevo: `test_boton_del_chat_siempre_visible`).
