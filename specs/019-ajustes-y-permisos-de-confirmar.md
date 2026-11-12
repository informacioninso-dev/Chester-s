# 019 · Ajustes desde el gestor y quién confirma o cancela

**Estado:** hecha
**Fecha:** 2026-11-12

## Qué y por qué

- **El WhatsApp de Melloco vive en una variable del servidor.** Hoy los pedidos van a un número de prueba y cambiarlo exige entrar al servidor. El dueño quiere configurarlo él mismo desde el gestor, sin ayuda técnica.
- **Cocina y Reparto pueden confirmar y cancelar pedidos.** Confirmar es acordar el pedido con la familia y cancelar no tiene vuelta atrás: lo deciden Atención de pedidos y el administrador (hallazgo 4 de la spec 018, aprobado por el dueño).

## Criterios de aceptación

### Ajustes

- [x] El gestor tiene una pestaña **Ajustes** que solo ve el administrador.
- [x] **WhatsApp de Melloco:** se escribe como en el celular (`0991234567`, `099 123 4567` o `+593 99 123 4567`) y se guarda en formato internacional (`593991234567`). Si no es válido, se explica cómo escribirlo. Hay un botón **"Probar en WhatsApp"**.
- [x] El número guardado se usa en todo el sitio: el mensaje del pedido (configurador y chat), el enlace del pie, la política de privacidad, el aviso de límite de envíos y los datos para Google. Si nadie lo ha configurado, se usa el del servidor (`CHESTERS_WHATSAPP`).
- [x] Mientras siga el número de prueba, el administrador ve en **Pedidos** un aviso rojo: "Los pedidos todavía van a un número de prueba", con un enlace a Ajustes.
- [x] **Ajustes** muestra una **lista para empezar**:
  - si el WhatsApp ya está configurado;
  - qué recetas disponibles no tienen pasos y qué formas no tienen cómo armarlas, con enlaces al Recetario;
  - cuántas personas hay en el equipo.
- [x] El cambio queda en el historial y se ve quién lo hizo y cuándo.

### Quién confirma y cancela

- [x] Solo **Atención de pedidos** y el **administrador** pueden **confirmar** un pedido nuevo y **cancelar** un pedido. También solo ellos pueden deshacer una confirmación.
- [x] Cocina y Reparto no ven esos botones: ni en la acción rápida de la lista ni en el detalle. En un pedido nuevo, el detalle les dice "Este pedido lo confirma Atención de pedidos con la familia".
- [x] El servidor rechaza esas acciones aunque alguien las fuerce.
- [x] Cocina sigue pudiendo "Pasar a cocina" y Reparto "Marcar entregado".

## Notas técnicas

- Modelo `Ajustes`, con una sola fila (`pk=1`), y la función `whatsapp_melloco()`. Los 8 usos de `settings.CHESTERS_WHATSAPP` en `views.py` pasan a esa función.
- `_accion_rapida` y el detalle reciben si la persona puede confirmar o cancelar. `_aplicar` lo vuelve a comprobar.

## Resultado

- **153 tests:** 6 nuevos en `AjustesYConfirmarTests`.
- **Probado en Chrome** emulando un celular de 375 px:
  - el administrador ve el aviso rojo del número de prueba y la pestaña Ajustes;
  - Ajustes muestra la lista para empezar;
  - sin scroll lateral, sin bloqueos de la CSP y sin errores de JavaScript.
- **Ajustes durante la prueba:**
  - las etiquetas de pendientes miden 44 px;
  - con el número de prueba, el campo empieza vacío.
