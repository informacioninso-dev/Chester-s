# AGENTS.md · Chester's

Guía para agentes de IA que trabajan en este repo. Léela junto con [MEMORY.md](MEMORY.md).

## Qué es

Landing + configurador de pedidos de pasteles para perritos (Django 5 + HTMX + Tailwind CDN).
Una sola app: `pedidos`. Idioma del código, UI y commits: **español**. Zona: `America/Guayaquil`.

## Comandos

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
python manage.py test pedidos      # debe pasar antes de cada commit
```

## Mapa rápido

- `pedidos/models.py` — `Cotizacion`, `LeadCumple` (heredan `SincronizableCRM`)
- `pedidos/forms.py` — `PedidoForm` (por pasos), `LeadCumpleForm`
- `pedidos/views.py` — landing, pasos HTMX del configurador, ruleta, API Binn
- `pedidos/crm.py` — webhook a Binn en hilo aparte
- `pedidos/templates/pedidos/partials/` — fragmentos que devuelve HTMX

## Reglas

- Las vistas HTMX devuelven el parcial si llega `HX-Request`; si no, la página completa (`_render_parcial_o_pagina`).
- Todo formulario que guarde datos personales exige consentimiento (LOPDP) y llena `consentimiento_en`.
- La integración con Binn nunca debe bloquear ni romper la respuesta al cliente.
- Configuración sensible solo por variables de entorno (ver README).
- No agregar dependencias sin justificarlo en la spec.

## Flujo: Spec Driven Development (mínimo)

Ningún cambio de comportamiento se programa sin spec.

1. **Spec**: copia [specs/_plantilla.md](specs/_plantilla.md) a `specs/NNN-nombre-corto.md` (NNN correlativo) y llena *Qué y por qué* y *Criterios de aceptación*. Estado: `borrador`.
2. **Aprobar**: el usuario revisa la spec y la aprueba. Estado: `aprobada`.
3. **Implementar**: un test por cada criterio de aceptación y luego el código. Estado: `en curso`.
4. **Cerrar**: los tests pasan, se marcan los criterios y se apunta en MEMORY.md cualquier decisión que no se deduzca del código. Estado: `hecha`.

Los arreglos triviales (texto, estilos, typos) no necesitan spec.
