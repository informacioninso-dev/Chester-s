# 011 · Gestor por día y por rol

**Estado:** hecha
**Fecha:** 2026-11-12

## Qué y por qué

El dueño probó el gestor de la spec 010 y la experiencia del equipo es mala. Tiene seis problemas:

- No se ve el día de un vistazo: las pestañas van por estado y la cocina pregunta *qué sale hoy*.
- Las tarjetas son enormes, con dos selectores y cuatro botones cada una. Diez pedidos obligan a bajar muchísimo.
- En computador queda una sola columna angosta.
- Todos ven lo mismo: quien cocina no necesita asignar, y quien reparte necesita saber a dónde y a qué hora.
- Asignar con menús desplegables es lento.
- La pantalla vacía no orienta a nadie.

El gestor sigue limitado a estados, cocina, reparto y ficha (decisión del dueño). Esta spec reemplaza la **interfaz** de pedidos de la 010. La ficha del perrito no cambia.

## Criterios de aceptación

### Vista del día

- [x] La pantalla principal dice qué día es y resume lo urgente, por ejemplo "2 para hoy · 1 atrasado".
- [x] Los pedidos activos se agrupan por día: **Atrasados**, **Hoy**, **Mañana**, **Esta semana** y **Más adelante**.
- [x] Cada pedido es **una fila compacta**:
  - el nombre del perrito y su estado;
  - la receta, la forma y la hora de entrega si la hay;
  - un aviso rojo si tiene alergias en su ficha, y uno crema si la familia contó algo;
  - quién lo cocina y quién lo reparte.
- [x] Al tocar la fila se abre el detalle del pedido.
- [x] Cada fila tiene **una sola acción rápida**: la que toca en esa vista.
- [x] En computador (desde 1024 px), la vista "Todo" es un **tablero de tres columnas**: Nuevos → Confirmados → En cocina.

### Una vista por rol

- [x] Un selector arriba ofrece cinco vistas, con contador: **Todo · Cocina · Reparto · Asignados · Historial**.
- [x] Cada persona entra por defecto a la vista de su grupo. Atención de pedidos y el superusuario entran a "Todo".
- [x] **Cocina** muestra los pedidos confirmados o en cocina que son suyos o que nadie ha tomado. Su acción rápida es **"Lo tomo yo"** si nadie lo tiene, y si no, **"Pasar a cocina"**.
- [x] **Reparto** muestra los pedidos en cocina que son suyos o que nadie lleva. Su acción rápida es **"Lo llevo yo"**, y luego **"Marcar entregado"**.
- [x] **Todo** muestra todos los activos, con la acción del siguiente estado.
- [x] **Asignados** agrupa los pedidos activos por persona y rol ("Carla · Cocina") y cuenta los que no tienen quién los cocine o quién los reparta. Lo pidió el dueño durante la implementación.
- [x] **Historial** muestra los entregados y cancelados, del más reciente al más antiguo.
- [x] El buscador sigue funcionando dentro de cada vista.

### Detalle del pedido

- [x] Cada pedido tiene su página `/equipo/pedido/<n>/`. Muestra, en este orden:
  1. para quién es y cuándo se celebra;
  2. las alergias, en rojo;
  3. lo que contó la familia;
  4. lo que le encanta;
  5. la receta y la forma;
  6. la familia, con su botón de WhatsApp;
  7. el enlace a la ficha.
- [x] Desde el detalle:
  - se avanza o se cancela el pedido (cancelar pide confirmación);
  - quien está en Cocina o Reparto lo toma con un botón;
  - Atención y el superusuario pueden asignarlo a cualquier persona del grupo.
- [x] **Entrega:** el equipo anota la **dirección** (con referencias) y la **hora** de entrega. La hora se ve en la fila.
- [x] El detalle muestra los últimos cambios del pedido: quién lo hizo y cuándo.

### Perritos

- [x] El gestor tiene dos secciones en la cabecera: **Pedidos** y **Perritos**. Lo pidió el dueño durante la implementación.
- [x] Perritos lista todas las fichas con buscador. Cada fila muestra el nombre, la familia, la raza, cuántos pasteles lleva, su próximo cumpleaños y sus alergias, y al tocarla abre la ficha.

### Pantalla vacía

- [x] Si no hay pedidos en una vista, la pantalla explica qué esperar. Al superusuario además le dice cómo crear al equipo y cómo hacer un pedido de prueba.

### Calidad

- [x] En 375 px no hay scroll lateral, los botones miden 44 px o más y los campos tienen 16 px. Se verifica en Chrome emulando el celular y el computador.
- [x] La política de privacidad menciona la dirección y la hora de entrega.

## Fuera de alcance

- Que el cliente escriba la dirección al pedir. Se coordina por WhatsApp.
- Mapas, rutas, avisos de pedido nuevo y arrastrar tarjetas en el tablero.

## Notas técnicas

- `Cotizacion` gana `direccion_entrega` (texto) y `hora_entrega` (hora), ambos opcionales y solo internos.
- Un único endpoint de acciones, `POST /equipo/pedido/<n>/accion/`, para estado, tomar, asignar y entrega. Todas se registran en el historial de Django.
- Las acciones rápidas de la lista usan HTMX y vuelven a pintar la vista entera; así el pedido cambia de grupo o de columna. Las del detalle son formularios normales que vuelven al detalle con un aviso.
- Se elimina `tarjeta_pedido.html` y se reemplazan las rutas `equipo_estado` y `equipo_asignar`.

## Resultado

- **104 tests.** Los de la interfaz de la spec 010 se reemplazaron por 18 nuevos: `GestorVistaDelDiaTests`, `GestorDetalleTests` y `GestorPerritosTests`.
- **Probado en Chrome** emulando un celular de 375 px y un computador de 1280 px, con una base de prueba:
  - la vista del día por grupos y el tablero de tres columnas;
  - la vista Cocina por defecto para quien está en ese grupo, y "Lo tomo yo" ("Tomaste el pedido de Max.");
  - la vista Asignados, el detalle con su entrega y la sección Perritos.
  - Sin scroll lateral, sin textos de menos de 12 px y sin errores de JavaScript.
- **Ajuste durante la prueba:** en el celular, el botón de la acción rápida va debajo de la fila, a todo el ancho; al lado recortaba el nombre y la receta.
