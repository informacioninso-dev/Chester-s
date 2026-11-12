# 010 · Gestor de pedidos y ficha del perrito

**Estado:** hecha
**Fecha:** 2026-11-12

## Qué y por qué

Hoy los pedidos se gestionan en el panel de Django (`/admin/`, spec 006). Funciona, pero es genérico, incómodo en el celular y no dice nada de cada perrito.

En Chester’s cada pastel se hace con cariño para alguien con nombre, gustos y alergias: esa es la parte humana del negocio, y el equipo tiene que verla en cada pedido. Por eso hacemos un **gestor propio en `/equipo/`**, pensado para el celular y con la marca, con tres partes:

1. **Pedidos:** qué hay que preparar, ordenado por fecha de celebración. Cada pedido se avanza con un toque y **cada tarjeta empieza por el perrito**, no por el trámite.
2. **Cocina y reparto:** cada pedido se asigna a una persona de cocina y luego a una de reparto. Cada quien ve "sus" pedidos.
3. **Ficha del perrito:** una por perrito. Junta sus pedidos y su cumpleaños de la Ruleta, y guarda lo que le encanta, lo que no le gusta y sus alergias.

Es toda la gestión interna por ahora (decisión del dueño, 12-nov-2026).

## Criterios de aceptación

### Acceso

- [x] `/equipo/` pide iniciar sesión en una pantalla con la marca de Chester’s.
- [x] Pueden entrar el superusuario y quienes estén en los grupos "Atención de pedidos", "Cocina" o "Reparto". Cualquier otro usuario ve "No tienes acceso al gestor". Los grupos "Cocina" y "Reparto" los crea una migración.
- [x] Hay un botón "Salir".

### Pedidos

- [x] Por defecto se ven los pedidos **activos** (Nuevo, Confirmado y En preparación) en tarjetas, con la celebración más cercana primero.
- [x] Hay pestañas con contador: Activos, Míos (asignados a mí en cocina o reparto), Nuevos, Confirmados, En preparación, Entregados y Cancelados.
- [x] Cada tarjeta empieza por el perrito: su nombre en grande, lo que le encanta y, **destacado en rojo, sus alergias o lo que no puede comer**. Esto sale de su ficha y de lo que contó la familia al pedir.
- [x] Debajo del perrito, la tarjeta muestra:
  - el día de la celebración, con una ayuda: "Hoy", "Mañana", "En 3 días" o "Atrasado" si pasó y no se entregó;
  - la receta y la forma;
  - el nombre de la familia;
  - quién lo cocina y quién lo reparte.
- [x] Cada tarjeta tiene botones de al menos 44 px:
  - **avanzar al siguiente estado:** "Confirmar pedido" → "Pasar a cocina" → "Marcar entregado";
  - **Escribir por WhatsApp:** abre el chat con el cliente;
  - **Ver ficha**.
- [x] Cancelar un pedido pide confirmación.
- [x] El cambio de estado se guarda al instante, sin recargar (HTMX), y queda registrado quién lo hizo y cuándo en el historial de Django, que se ve en `/admin/`.
- [x] Un buscador encuentra pedidos por el nombre del perrito, de la familia o por teléfono.

### Cocina y reparto

- [x] En cada tarjeta se elige **quién lo cocina** entre las personas del grupo "Cocina" y **quién lo reparte** entre las de "Reparto". Se guarda al instante y queda en el historial.
- [x] La pestaña "Míos" muestra a cada persona los pedidos activos que tiene asignados.

### Ficha del perrito

- [x] Cada perrito tiene **una sola ficha**. Mismo WhatsApp y mismo nombre, sin importar mayúsculas, tildes ni espacios, es el mismo perrito: "Rocky" y "rocky " del 0991234567 (o del 593991234567) comparten ficha.
- [x] Los pedidos (del configurador y del chat) y los registros de la Ruleta se enlazan solos a su ficha, también los que ya existen hoy (migración).
- [x] La ficha muestra:
  - el nombre del perrito, el de su familia y su WhatsApp;
  - su cumpleaños, si se registró en la Ruleta, y si ya se le envió el regalo;
  - todos sus pedidos, con su estado y con lo que contó la familia en cada uno;
  - su **receta favorita** y su **forma favorita**, que son las que más ha pedido sin contar los cancelados.
- [x] El equipo puede editar en la ficha la **raza**, el **tamaño** (pequeño, mediano o grande), **"Le encanta"**, **"No le gusta / alergias"** y **"Notas"**. Se guarda sin recargar.

### Lo que cuenta la familia al pedir

- [x] El configurador (paso de la receta) y el chat preguntan, de forma **opcional**: "¿Algo que debamos saber? Alergias, algo que no pueda comer o algo que le encante".
- [x] En el chat se puede responder o tocar "Nada que agregar".
- [x] La respuesta se guarda en el pedido, aparece en el resumen antes de confirmar y se ve en la tarjeta y en la ficha.

### Celular y privacidad

- [x] Todo el gestor se usa cómodo en un celular de 375 px: sin scroll lateral, botones de 44 px o más y campos de 16 px.
- [x] La política de privacidad dice que guardamos lo que la familia nos cuenta de su perrito y una ficha con su historial y sus gustos, solo para preparar sus pasteles con cuidado, y que se borra junto con los demás datos.
- [x] `/equipo/` no se indexa: `noindex` en la página y `Disallow: /equipo/` en robots.txt.

## Fuera de alcance

- Avisos de pedido nuevo, lista de regalos de la Ruleta por enviar, inventario, precios, cobros y rutas de reparto.
- Editar receta, forma o fecha de un pedido: sigue en `/admin/`.
- La foto del perrito.
- Enviar la ficha a Binn. Lo que cuenta la familia sí viaja con el pedido.

## Decisiones (12-nov-2026)

1. Se pregunta al cliente por gustos y alergias, como campo opcional.
2. En la ficha van la raza y el tamaño; la foto queda para después.
3. `/admin/` sigue existiendo, para el administrador: usuarios y correcciones. El equipo trabaja en `/equipo/`.

## Notas técnicas

- **Modelo nuevo `Perrito`:**
  - Campos: `nombre`, `nombre_clave`, `telefono`, `telefono_clave`, `familia`, `raza`, `tamano`, `le_encanta`, `no_le_gusta`, `notas`, `creado_en` y `actualizado_en`.
  - `telefono_clave` va en formato internacional, para que `0991…` y `593991…` sean el mismo número.
  - Único por (`telefono_clave`, `nombre_clave`).
- **Cambios en los modelos existentes:**
  - `Cotizacion` gana `perrito`, `nota_familia`, `cocinero` y `repartidor` (FK a `User`, opcionales).
  - `LeadCumple` gana `perrito`.
  - El perrito se asigna en `save()`.
- **Migraciones:** una de esquema y una de datos. La de datos crea las fichas de los registros existentes, los grupos "Cocina" y "Reparto", y los permisos de `perrito` para "Atención de pedidos".
- **Código:** vistas en `pedidos/views_equipo.py`, plantillas en `pedidos/templates/pedidos/equipo/` y rutas bajo `/equipo/`. Sin dependencias nuevas.
- **Riesgo aceptado:** una familia con dos perritos del mismo nombre comparte ficha.

## Resultado

- **95 tests** en total, 23 nuevos (`GestorAccesoTests`, `GestorPedidosTests`, `GestorAsignacionTests`, `FichaPerritoTests` y `NotaFamiliaTests`). Se actualizaron 5 del chat y del grupo de la spec 006: ahora el chat hace la pregunta opcional y el grupo tiene permisos sobre las fichas.
- **Probado de punta a punta** en Chrome emulando un celular de 375 px y un iPad de 768 px, con una base de prueba: ingresar, ver la lista, avanzar un pedido, asignar cocina y guardar la ficha. No hay scroll lateral, todos los campos son de 16 px y no hay errores de JavaScript.
- **Migración de datos de las fichas:** se verifica en el servidor al desplegar. Ningún pedido ni cumpleaños debe quedar sin ficha.
- **Seguridad:** el regreso sin JavaScript (`volver`) solo acepta direcciones del propio gestor, para evitar redirecciones abiertas.
