# 005 · Chat para pedir el pastel

**Estado:** hecha
**Fecha:** 2026-11-11

## Qué y por qué

Hay gente que prefiere conversar a llenar un formulario, sobre todo en el celular. Un botón flotante abre un chat con "Melloco" que pide los datos del pedido uno por uno, con botones para la receta y la forma, y al final abre WhatsApp con el pedido ya escrito, igual que el configurador.

Es un chat **guiado**, sin inteligencia artificial: no necesita claves ni tiene costo por mensaje, responde al instante y no envía datos personales a otro proveedor (eso obligaría a cambiar la política de privacidad).

## Criterios de aceptación

- [x] La portada tiene un botón flotante "Pedir por chat" que abre y cierra el chat; también se cierra con Esc y el foco va al campo de respuesta.
- [x] El chat pregunta en orden: nombre del perrito, día de la celebración, receta (botones), forma (botones), nombre de la persona y WhatsApp.
- [x] Cada respuesta se valida con las mismas reglas del configurador (`PedidoForm`). Si algo está mal, Melloco explica qué corregir y vuelve a preguntar lo mismo.
- [x] Antes de confirmar, muestra el resumen del pedido y pide la autorización de datos con enlace a la política de privacidad.
- [x] Al confirmar, guarda la cotización, avisa a Binn y abre WhatsApp con el mismo mensaje que el configurador.
- [x] Aplican las mismas protecciones de la spec 002: límite de envíos (compartido con el configurador) y campo trampa.
- [x] "Empezar de nuevo" reinicia la conversación.
- [x] Accesible: el historial se anuncia a lectores de pantalla (`role="log"`) y todo se puede usar con teclado.

## Fuera de alcance

- Respuestas libres con IA (por ejemplo, Claude con una clave de API). Puede ser una spec futura que también actualice la política de privacidad.
- Guardar la conversación al recargar la página.
- Registrar cumpleaños de la Ruleta desde el chat.

## Notas técnicas

- Endpoint `POST /chat/` con HTMX. Sin sesión: las respuestas ya dadas viajan como campos ocultos, igual que en el configurador.
- Cada respuesta agrega las burbujas al historial (`beforeend`) y reemplaza el campo de respuesta con `hx-swap-oob`.
- El guardado se comparte con `confirmar_pedido` para no duplicar el límite, el campo trampa ni el aviso a Binn.

## Resultado

- 10 tests en `ChatTests` y una prueba de punta a punta en Chrome (390 px y 1280 px): conversación completa, error de fecha pasada, autorización obligatoria, Esc y foco. WhatsApp se abre con el mismo mensaje que el configurador y no hay errores de JavaScript.
- El chat usa `novalidate`, igual que los otros formularios: los errores los explica Melloco en la conversación, no el navegador.
