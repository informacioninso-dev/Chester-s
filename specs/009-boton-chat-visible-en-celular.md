# 009 · "Pedir con Melloco" visible en el celular

**Estado:** hecha
**Fecha:** 2026-11-12

## Qué y por qué

En el celular el botón flotante "Pedir con Melloco" casi nunca se veía. Se escondía en la portada, en el configurador y en la Ruleta, que juntos son casi toda la página. El dueño quiere que en el celular sí se vea, porque el chat es justamente la forma más cómoda de pedir desde el teléfono (spec 005).

Desde la spec 007 el título y "Pedir su pastel" van arriba en la portada y el botón flotante queda abajo, así que ya no se tapan. Esta spec reemplaza, **solo en el celular**, el criterio de la 007 que escondía el botón en la portada.

## Criterios de aceptación

- [x] En el celular (menos de 640 px), el botón "Pedir con Melloco" se ve completo en la portada y en la historia.
- [x] En el celular, sobre el configurador y la Ruleta se reduce a la carita de Melloco (un círculo). Sigue diciendo "Pedir con Melloco" para lectores de pantalla y para el toque.
- [x] En el celular, mientras la persona escribe en un campo de texto, fecha o teléfono, el botón se esconde y vuelve al salir del campo.
- [x] Con el chat abierto, el botón dice "Cerrar" completo en cualquier zona.
- [x] En tablet y computador no cambia nada: se esconde sobre el configurador y la Ruleta, como en la 005.

## Fuera de alcance

- Cambiar el diseño del panel del chat.

## Notas técnicas

- Solo cambia el script de `index.html`. El texto del botón pasa a `sr-only` en el modo compacto, y por eso el botón conserva su nombre accesible.
- Los criterios de comportamiento se verifican con Chrome emulando un celular (CDP). El test revisa que el script tenga las piezas.

## Resultado

- Verificado en Chrome con emulación de iPhone SE (375 px) y de iPad (1024 px):
  - iPhone SE: el botón se ve completo en la portada y en la historia (207×52); compacto sobre el configurador y la Ruleta (52×52); oculto mientras se escribe y de vuelta al salir del campo. Con el chat abierto dice "Cerrar".
  - iPad: sin cambios, oculto sobre el configurador y la Ruleta.
- 72 tests (1 nuevo: `test_boton_del_chat_visible_en_celular`).
