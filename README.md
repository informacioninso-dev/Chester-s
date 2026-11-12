# Chester's · Pasteles para perritos

Landing page + configurador de pedidos y chat con Melloco en una sola página (Django + HTMX + Tailwind).

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

## Gestor del equipo y panel

**El equipo trabaja en `/equipo/`** (spec 010), pensado para el celular:

- **Pedidos** (spec 011): la vista del día agrupa los pedidos en Atrasados, Hoy, Mañana, Esta semana y Más adelante, en filas compactas que muestran las alergias en rojo y lo que contó la familia. En computador, la vista *Todo* es un tablero: Nuevos → Confirmados → En cocina. Hay cinco vistas:
  - *Todo:* todos los pedidos activos.
  - *Cocina:* "Lo tomo yo" y "Pasar a cocina".
  - *Reparto:* "Lo llevo yo" y "Marcar entregado".
  - *Asignados:* los pedidos agrupados por persona.
  - *Historial:* los entregados y cancelados.

  Cada persona entra a la vista de su grupo. Al tocar un pedido se abre su detalle: avanzar o cancelar, asignar (solo Atención), la dirección y hora de entrega, WhatsApp, la ficha y los últimos cambios.
- **Cobro** (spec 015): cada pedido puede marcarse cobrado, con monto y forma de pago opcionales, también antes de entregar si dejan un anticipo. Los entregados sin cobrar siguen a la vista en "Por cobrar" hasta que se cobran.
- **Recetario** (spec 013): las recetas y formas que se ofrecen a las familias, con lo que sigue la cocina (ingredientes, pasos, alérgenos y cómo armar cada forma). Solo lo marcado «Disponible» aparece en la página y en el chat. Lo que ya tiene pedidos no se borra, se pausa. Editan Atención de pedidos y el administrador; Cocina y Reparto solo leen.
- **Perritos:** todas las fichas, con buscador. Cada ficha junta los pedidos y el cumpleaños de la Ruleta y muestra las favoritas. El equipo anota raza, tamaño, lo que le encanta, alergias y notas.

**Usuarios:** el administrador los crea en la pestaña **Equipo** del gestor (spec 014), sin pasar por el panel. Escribe el nombre y marca qué hace la persona (Atiende pedidos, Cocina o Reparte). El usuario y una contraseña fácil de dictar se crean solos y salen en un mensaje listo para mandar por WhatsApp. Desde la ficha de cada persona se genera una **nueva contraseña** o se **quita el acceso**. Al ingresar no importan las mayúsculas ni los espacios del usuario.

Lo que sigue explica cómo hacerlo desde el panel de Django, por si hace falta:

1. **Administrador** (una sola vez): `python manage.py createsuperuser`. Tiene acceso total en `/admin/` y en `/equipo/`.
2. **Cada persona:** en `/admin/` → *Usuarios* → *Añadir usuario* se pone su usuario y contraseña, y en la pantalla siguiente se escribe su nombre (es el que aparece en el gestor) y se le asigna un grupo:
   - **Atención de pedidos:** gestor completo. Si además se marca **Es staff**, entra también a `/admin/` para ver y editar pedidos, cumpleaños y fichas, sin poder borrar ni gestionar usuarios.
   - **Cocina:** aparece en "Lo cocina".
   - **Reparto:** aparece en "Lo reparte".

`/admin/` queda para el administrador: usuarios, correcciones y el historial de cambios. Ahí se ve quién avanzó o asignó cada pedido desde el gestor.

## Variables de entorno

| Variable | Para qué |
|---|---|
| `CHESTERS_WHATSAPP` | Número de Melloco, solo dígitos con código de país (ej. `593991234567`). **Obligatorio cambiarlo.** |
| `DJANGO_DEBUG=0` | Producción. Activa HTTPS obligatorio, cookies seguras y HSTS. |
| `DJANGO_SECRET_KEY` | Obligatoria con `DJANGO_DEBUG=0`: sin ella el sitio no arranca. |
| `DJANGO_ALLOWED_HOSTS` | Dominios del sitio, separados por coma (ej. `chesters.ec,www.chesters.ec`). |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Los mismos dominios con esquema (ej. `https://chesters.ec`). |
| `DJANGO_BEHIND_PROXY=1` | Si un proxy o PaaS termina el HTTPS (Render, Railway, Nginx). |
| `DJANGO_ADMIN_URL` | Ruta del panel (por defecto `admin/`). Conviene cambiarla en producción. |
| `DJANGO_HSTS_SECONDS` | Duración de HSTS (por defecto 30 días). `DJANGO_HSTS_SUBDOMAINS=1` y `DJANGO_HSTS_PRELOAD=1` solo cuando el dominio esté 100 % en HTTPS. |
| `DJANGO_SSL_REDIRECT=0` | Solo si el proxy ya redirige a HTTPS por su cuenta. |
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
  views.py       index, configurador (pasos HTMX), confirmar_pedido, chat, registrar_lead, robots.txt, API Binn
  crm.py         webhook a Binn (no bloquea la respuesta)
  templates/pedidos/index.html · privacidad.html
  templates/pedidos/partials/  head.html · configurador.html · pedido_confirmado.html · ruleta.html
specs/           specs del flujo spec driven (ver AGENTS.md)
```

## Estilos (Tailwind)

El CSS ya compilado está en `pedidos/static/pedidos/css/chesters.css` y se versiona, así que para desplegar no hace falta Node. Si cambias clases en las plantillas o en `forms.py`, regenéralo:

```bash
npx tailwindcss@3.4.17 -i assets/tailwind.css -o pedidos/static/pedidos/css/chesters.css --minify
```

Los colores y las fuentes están en `tailwind.config.js`; los estilos propios (animaciones de la ruleta, estados de carga) en `assets/tailwind.css`.

## Demo en el servidor de Licitar (spec 008)

`https://chesters.binnso.com` corre en el droplet de Licitar (`root@167.99.2.102`), en `/opt/chesters`, con su propio contenedor (`chesters-web`) y su base SQLite en el volumen `chesters_datos`. El HTTPS lo da el Caddy de Licitar: el bloque `chesters.binnso.com` está en `deploy/Caddyfile` **del repo de Licitar**.

- **Secretos:** `/opt/chesters/.env.production` en el servidor, nunca en el repo. Lleva `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` y `CHESTERS_WHATSAPP`.
- **Publicar lo último** (desde Git Bash, con todo en commit):
  ```bash
  git archive --format=tar -o /tmp/chesters.tar HEAD
  scp /tmp/chesters.tar root@167.99.2.102:/tmp/
  ssh root@167.99.2.102 'tar -x -f /tmp/chesters.tar -C /opt/chesters && cd /opt/chesters && docker compose up -d --build && docker builder prune -f --keep-storage 1500MB >/dev/null'
  ```
- **Crear el administrador:** `ssh -t root@167.99.2.102 'docker exec -it chesters-web python manage.py createsuperuser'`
- **Ver errores:** `ssh root@167.99.2.102 'docker logs --tail 100 chesters-web'`

## Antes de producción

- Al desplegar: `pip install -r requirements.txt`, `python manage.py migrate` y `python manage.py collectstatic --noinput`.
- Revisar con un abogado el texto de la política de privacidad (`/privacidad/`) y agregar razón social/RUC.
- Para muchos envíos al webhook, mover `crm.py` a una cola (Celery/RQ) en lugar de hilos.
