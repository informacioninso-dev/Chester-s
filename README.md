# Chester's · Pasteles para perritos

Landing page + configurador de pedidos en una sola página (Django + HTMX + Tailwind).

## Arrancar en local

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser   # para ver pedidos y leads en /admin
python manage.py runserver
```

Abrir http://127.0.0.1:8000 · Panel de Melloco: http://127.0.0.1:8000/admin

Tests: `python manage.py test pedidos`

## Variables de entorno

| Variable | Para qué |
|---|---|
| `CHESTERS_WHATSAPP` | Número de Melloco, solo dígitos con código de país (ej. `593991234567`). **Obligatorio cambiarlo.** |
| `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS` | Producción. |
| `BINN_API_TOKEN` | Activa la API de lectura para Binn (header `X-Binn-Token`). |
| `BINN_WEBHOOK_URL` | Si se define, cada lead/cotización nueva se envía a Binn al instante. |
| `BINN_WEBHOOK_SECRET` | Firma HMAC-SHA256 del webhook (header `X-Chesters-Signature: sha256=…`). |

## Integración con el CRM Binn

**Push (webhook):** al crearse un registro se hace `POST` a `BINN_WEBHOOK_URL` en segundo plano:

```json
{"evento": "lead_cumple.creado", "datos": {"id": 1, "nombre_humano": "Ana", "nombre_perro": "Luna",
 "telefono": "0991234567", "fecha_cumple": "2021-03-10", "proximo_cumple": "2027-03-10",
 "fecha_regalo": "2027-02-23", "creado_en": "…"}}
```

Eventos: `lead_cumple.creado` y `cotizacion.creado`. Si Binn responde 2xx, el registro queda como sincronizado; si falla, queda pendiente para la API.

**Pull (API):** con el header `X-Binn-Token: <BINN_API_TOKEN>`

- `GET /api/binn/leads/?pendientes=1&desde=2026-11-01T00:00:00-05:00&limite=200`
- `GET /api/binn/cotizaciones/?pendientes=1`
- `POST /api/binn/sincronizados/` con `{"leads": [1, 2], "cotizaciones": [5]}`

## Estructura

```
pedidos/
  models.py      Cotizacion, LeadCumple (+ campos de sincronización y consentimiento LOPDP)
  forms.py       PedidoForm (validación por pasos), LeadCumpleForm
  views.py       index, configurador (pasos HTMX), confirmar_pedido, registrar_lead, API Binn
  crm.py         webhook a Binn (no bloquea la respuesta)
  templates/pedidos/index.html · privacidad.html
  templates/pedidos/partials/  head.html · configurador.html · pedido_confirmado.html · ruleta.html
specs/           specs del flujo spec driven (ver AGENTS.md)
```

## Antes de producción

- Tailwind se carga desde el CDN de prueba: compilarlo con `django-tailwind` o el CLI standalone.
- Revisar con un abogado el texto de la política de privacidad (`/privacidad/`) y agregar razón social/RUC.
- Para muchos envíos al webhook, mover `crm.py` a una cola (Celery/RQ) en lugar de hilos.
