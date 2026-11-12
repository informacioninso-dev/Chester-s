# 007 · Celular primero y paso a WhatsApp sin saltos

**Estado:** hecha
**Fecha:** 2026-11-12

## Qué y por qué

La revisión de diseño (impeccable, 26/40) encontró tres problemas que cuestan pedidos:

- En el celular la primera pantalla es solo el logo. El botón principal queda cortado y el botón flotante del chat lo tapa.
- Al confirmar, la página salta sola a WhatsApp a los 0,9 s y en la misma pestaña. Nadie ve la pantalla de Melloco, al volver el configurador está vacío, y a quien usa lector de pantalla le cambia la página sin aviso.
- Hay cinco nombres para la misma acción, y el botón flotante es del mismo rojo que el principal: compiten.

## Criterios de aceptación

- [x] En el celular, el título y el botón "Pedir su pastel" aparecen en la primera pantalla; el logo va debajo y más pequeño.
- [x] El botón flotante del chat no aparece mientras se ve la portada y no tapa los enlaces del pie.
- [x] Confirmar (configurador o chat) guarda el pedido y muestra la pantalla de Melloco, **sin** redirigir solo. WhatsApp se abre únicamente al tocar "Enviar por WhatsApp", en otra pestaña.
- [x] Esa pantalla explica qué sigue: enviar el mensaje y que la familia responde por WhatsApp para confirmar precio, fecha y entrega.
- [x] Un solo verbo para pedir en todo el sitio: "Pedir" ("Pedir su pastel"). Confirmar dice "Confirmar pedido" en el configurador y en el chat.
- [x] El botón flotante es secundario (azul marino), no rojo.
- [x] Sin JavaScript, confirmar sigue llevando a WhatsApp (redirección del servidor), como hasta ahora.

## Fuera de alcance

- Precio, porciones, zona y anticipación: esperan los datos reales del negocio (siguiente spec).
- Restos de plantilla, historia de Chester y botones pequeños (P2 de la revisión).

## Resultado

- Probado en Chrome: en 390 px el botón "Pedir su pastel" queda a 440 px de 844 de alto y el botón flotante no aparece sobre la portada; al confirmar, el sitio se queda y no hay ninguna navegación a wa.me hasta tocar "Enviar por WhatsApp".
- 70 tests (5 nuevos en `PasoAWhatsAppTests`).
