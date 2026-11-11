# MEMORY.md · Chester's

Decisiones y contexto que no se deducen del código. Lo más importante va primero.
Formato: `- AAAA-MM-DD · decisión — por qué`.

## Reglas del equipo

- 2026-11-11 · **Claude (o cualquier agente de IA) NO va como coautor.** No agregar `Co-Authored-By` ni firmas de IA en commits ni en PRs — decisión del dueño del repo.

## Decisiones

- 2026-11-11 · Sin build de frontend: Tailwind por CDN y HTMX — se mantiene simple hasta salir a producción (ver README).
- 2026-11-11 · El pedido termina en WhatsApp de Melloco, no hay pago en línea — Melloco cierra la venta a mano.
- 2026-11-11 · El regalo de la Ruleta se envía `CHESTERS_DIAS_REGALO` (15) días antes del próximo cumpleaños; el 29/02 se trata como 28/02.
- 2026-11-11 · Binn se integra en dos modos (webhook push + API pull) para que la API sirva de reintento si falla el webhook.
- 2026-11-11 · Política de privacidad propia en `/privacidad/`, enlazada desde ambas autorizaciones y el footer (spec 001).

## Pendientes conocidos

- Compilar Tailwind en lugar del CDN.
- Revisar con un abogado el texto de `/privacidad/` (spec 001) y agregar razón social/RUC del responsable.
- Mover el webhook a una cola (Celery/RQ) si sube el volumen.
