# 012 · Gestor pulido: avisos con deshacer, refresco y pulgar

**Estado:** hecha
**Fecha:** 2026-11-12

## Qué y por qué

Esta es la última pasada de UX/UI al gestor, pedida por el dueño. La spec 011 dejó la estructura bien; faltan detalles que se notan en el día a día:

- El aviso de cada acción aparece arriba de la lista. Si la acción se hizo más abajo, no se ve.
- Un toque por error, como "Marcar entregado", no tiene vuelta atrás desde la lista.
- La lista no se actualiza sola, y en la cocina nadie recarga la página.
- En el celular, la acción principal del detalle queda lejos del pulgar.
- No se puede soltar un pedido tomado por error.
- Al pasar la vista rápido, las filas no se distinguen por estado.

## Criterios de aceptación

- [x] Tras una acción rápida aparece un **aviso flotante abajo** que se oculta solo a los pocos segundos. Si la acción fue avanzar el estado o tomar un pedido, el aviso trae **"Deshacer"**, que lo devuelve a como estaba.
- [x] "Deshacer" de un estado solo retrocede un paso (por ejemplo, de Entregado a En cocina) y queda en el historial. Cancelar no se deshace desde ahí, porque ya pide confirmación.
- [x] La vista de pedidos **se refresca sola cada 60 segundos** mientras la pestaña está visible, salvo si alguien está escribiendo en un campo. Muestra la hora de la última actualización.
- [x] En el detalle, en el celular, la acción principal ("Confirmar pedido", "Pasar a cocina" o "Marcar entregado") va en una **barra fija abajo**, sin tapar el contenido.
- [x] Quien tomó un pedido puede **soltarlo** desde el detalle ("Soltar"), y queda en el historial.
- [x] Cada fila tiene una **franja de color a la izquierda según su estado**: rojo para Nuevo, azul marino para Confirmado y crema para En cocina.
- [x] La pantalla vacía muestra a Melloco.
- [x] Todo sigue cumpliendo lo de la spec 011: 375 px sin scroll lateral, botones de 44 px y textos de 12 px o más.

## Fuera de alcance

- Notificaciones push o sonido de pedido nuevo.

## Notas técnicas

- Acciones nuevas en el mismo endpoint: `deshacer` (retrocede un paso) y `soltar_cocina` / `soltar_reparto`.
- `GET /equipo/` con HTMX devuelve solo la vista, para el refresco (`hx-trigger="every 60s [...]"`).
- El aviso flotante se oculta con una animación CSS de opacidad, sin JavaScript propio.

## Resultado

- **113 tests.** Hay 9 nuevos en `GestorPulidoTests`.
- **Probado en Chrome** emulando un celular de 375 px:
  - el aviso de una acción hecha al final de la lista se ve abajo y "Deshacer" devuelve el pedido ("Listo, Toby volvió a confirmado.");
  - a los 8 segundos el aviso ya no está;
  - las franjas de color se ven en cada fila;
  - en el detalle, "Marcar entregado" queda fijo abajo;
  - sin scroll lateral, sin textos de menos de 12 px y sin errores de JavaScript.
- **Ajuste:** los avisos y el historial dicen "En cocina", igual que el resto del gestor, en lugar de "En preparación".
