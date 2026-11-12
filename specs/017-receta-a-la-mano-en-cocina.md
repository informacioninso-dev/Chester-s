# 017 · La receta a la mano en Cocina

**Estado:** hecha
**Fecha:** 2026-11-12

## Qué y por qué

En la cocina lo primero que se necesita de un pedido es **cómo se hace**. En la vista Cocina había que abrir el pedido y bajar hasta encontrar la receta. El dueño pidió que, al tocar un pedido en Cocina, la receta se vea enseguida.

## Criterios de aceptación

- [x] En la vista **Cocina**, cada pedido tiene **"Ver receta"**, que se despliega ahí mismo, sin cambiar de pantalla. Muestra:
  - las alergias del perrito, lo que contó la familia y lo que contiene la receta, juntos y en rojo;
  - los ingredientes;
  - los pasos numerados;
  - cómo armar la forma;
  - las notas.
- [x] Si la receta aún no tiene ingredientes ni pasos, lo dice y explica quién puede completarla.
- [x] En Cocina, tocar el pedido abre el detalle **directo en "Cómo se hace"**.
- [x] Las otras vistas no cambian.

## Notas técnicas

- `<details>` nativo, sin JavaScript (`receta_en_fila.html`). El detalle tiene el ancla `#como-se-hace` con `scroll-margin` para que no quede debajo de la cabecera fija.
