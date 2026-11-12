# 015 · Entregado y cobrado

**Estado:** hecha
**Fecha:** 2026-11-12

## Qué y por qué

El dueño notó dos huecos en el gestor:

- **Entregado.** Un pedido entregado desaparece de la vista principal y solo queda en el Historial. Ahí se pierde lo que falta: cobrarlo.
- **Cobrado.** No hay dónde anotar que un pedido ya se pagó, ni cuánto ni cómo.

El cobro no es un paso más del estado: a veces se paga antes, con un anticipo por transferencia, y a veces al entregar, en efectivo. Por eso va **aparte**, como una marca del pedido.

## Criterios de aceptación

- [x] Cada pedido puede marcarse **cobrado**, con la fecha y hora, quién lo marcó y, de forma opcional, el **monto** y la **forma de pago** (Efectivo, Transferencia u Otro).
- [x] Un pedido **entregado y sin cobrar** sigue a la vista:
  - en **Todo** aparece en un grupo **"Por cobrar"** (en computador, una cuarta columna del tablero);
  - hay una vista nueva **"Por cobrar"**, con contador;
  - el resumen de arriba dice "N por cobrar".
- [x] Su acción rápida es **"Marcar cobrado"**. Al tocarla sale del grupo, y el aviso flotante ofrece **"Deshacer"**.
- [x] En el **detalle** hay una sección **Cobro**:
  - si no está cobrado: monto (opcional), forma de pago (opcional) y "Marcar cobrado". Se puede cobrar en cualquier estado menos Cancelado, para los anticipos;
  - si está cobrado: "Cobrado el 12 de noviembre · $25,00 · Transferencia", quién lo marcó y "Deshacer cobro".
- [x] Las filas de entregados muestran "Por cobrar" en rojo o "Cobrado" en azul marino. El **Historial** muestra lo mismo.
- [x] Todo queda en el historial de cambios del pedido.
- [x] Binn recibe `cobrado`, `monto_cobrado` y `forma_pago`.

## Fuera de alcance

- Precios por receta o forma, facturas, abonos parciales y reportes de caja.

## Notas técnicas

- `Cotizacion` gana `cobrado` (bool), `cobrado_en`, `cobrado_por` (FK a User), `monto_cobrado` (Decimal 8,2, opcional) y `forma_pago` (opciones, opcional).
- Acciones nuevas en el endpoint de siempre: `cobrar` y `descobrar` (esta última es el "Deshacer").

## Resultado

- **135 tests:** 5 nuevos en `CobroTests`. El tablero tiene ahora cuatro columnas.
- **Probado en Chrome:**
  - en el celular, el grupo "Por cobrar" aparece en Todo y la sección Cobro del detalle avisa "Ya se entregó: falta cobrarlo";
  - en el computador, el tablero muestra Nuevos · Confirmados · En cocina · Por cobrar;
  - sin scroll lateral y sin errores de JavaScript.
- **Ajustes durante la prueba:**
  - el resumen "N por cobrar" es texto y no un enlace pequeño, porque ya está la pestaña;
  - dice "Hace 1 día", no "Hace 1 días".
