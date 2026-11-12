# 006 · Equipo y gestión de pedidos en el panel

**Estado:** hecha
**Fecha:** 2026-11-11

## Qué y por qué

El panel solo sirve hoy para el superusuario y no permite darle seguimiento a un pedido: no se sabe cuáles ya se confirmaron, cuáles están en el horno o cuáles se entregaron, ni a qué perritos ya se les mandó el regalo de la Ruleta. Para sumar gente que atienda pedidos sin darle acceso total, hacen falta perfiles con permisos limitados.

## Criterios de aceptación

- [x] Existe el grupo **"Atención de pedidos"**, creado por una migración: puede ver y editar cotizaciones y cumpleaños, pero no borrarlos ni gestionar usuarios.
- [x] El administrador crea a cada persona del equipo desde el panel (Usuarios → Añadir), marca "Es staff" y la asigna al grupo; el README explica los pasos.
- [x] Cada cotización tiene un **estado**: Nuevo → Confirmado → En preparación → Entregado, o Cancelado. Los pedidos nuevos entran como "Nuevo".
- [x] En la lista de cotizaciones el estado se cambia directamente desde la tabla y se puede filtrar por estado; los pedidos del chat y del configurador se ven igual.
- [x] Cada fila tiene un enlace **"Escribir por WhatsApp"** que abre el chat con el número del cliente.
- [x] Cada cumpleaños de la Ruleta tiene la casilla **"Regalo enviado"**, editable desde la lista y filtrable, para saber a quién le falta.
- [x] El estado y el regalo enviado viajan a Binn en `to_crm()` y en la API.

## Fuera de alcance

- Avisos automáticos al cliente cuando cambia el estado.
- Historial de quién cambió qué (Django ya registra las acciones del admin en "Acciones recientes").
- Un panel propio fuera del admin de Django.

## Notas técnicas

- Migración de esquema (`estado`, `regalo_enviado`) y migración de datos para el grupo y sus permisos.
- Los pedidos que ya existen quedan como "Nuevo".
