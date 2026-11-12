# MEMORY.md · Chester's

Decisiones y contexto que no se deducen del código. Lo más importante va primero.
Formato: `- AAAA-MM-DD · decisión — por qué`.

## Reglas del equipo

- 2026-11-11 · **Claude (o cualquier agente de IA) NO va como coautor.** No agregar `Co-Authored-By` ni firmas de IA en commits ni en PRs — decisión del dueño del repo.

## Decisiones

- 2026-11-11 · Tailwind compilado en local y **el CSS resultante se versiona** (spec 003): el servidor no necesita Node. Reemplaza la decisión anterior de usar el CDN. Hay que regenerarlo al tocar clases (ver README) — si no, la clase nueva no tendrá estilo.
- 2026-11-11 · WhiteNoise sirve los estáticos con hash y caché de 1 año solo con `DJANGO_DEBUG=0`; en desarrollo y tests se usa el almacenamiento normal para no exigir `collectstatic`.
- 2026-11-11 · El pedido termina en WhatsApp de Melloco, no hay pago en línea — Melloco cierra la venta a mano.
- 2026-11-11 · El regalo de la Ruleta se envía `CHESTERS_DIAS_REGALO` (15) días antes del próximo cumpleaños; el 29/02 se trata como 28/02.
- 2026-11-11 · Binn se integra en dos modos (webhook push + API pull) para que la API sirva de reintento si falla el webhook.
- 2026-11-11 · Política de privacidad propia en `/privacidad/`, enlazada desde ambas autorizaciones y el footer (spec 001).
- 2026-11-11 · La fecha del configurador es el **día de la celebración** ("¿Cuándo lo celebran?", solo hoy en adelante); la de la Ruleta es el **cumpleaños** (cualquier año). Se separaron las etiquetas porque con la misma etiqueta la gente ponía la fecha de nacimiento en el pedido y el formulario la rechazaba.
- 2026-11-11 · Textos en español con mayúscula solo inicial ("Carne y puré", "Huesito"), siempre "perrito" y "Tu WhatsApp", y "Chester’s" con apóstrofo curvo como en el logo. La regla de *Title Case* de `web-design-guidelines` no aplica en español.
- 2026-11-11 · El botón de la Ruleta dice "Guardar su cumpleaños", no "Girar la ruleta": no hay premio al azar y el texto no debe prometerlo. La ruleta solo gira al pasar el cursor o al enviar (pauta de accesibilidad de animaciones).
- 2026-11-11 · El formulario de la Ruleta usa ids `ruleta_*`: convive en la página con el configurador, que tiene campos con el mismo nombre.
- 2026-11-11 · Skills de revisión del proyecto en `.claude/skills/`: `web-design-guidelines` (Vercel, interfaz) y `ux-copy` (Anthropic, textos).
- 2026-11-11 · Freno anti-spam sin dependencias (spec 002): 10 envíos guardados por IP cada 10 min con la caché de Django, más un campo trampa `sitio_web`. Los errores de validación no cuentan, para no castigar a quien se equivoca. Con varios procesos o servidores hay que pasar a una caché compartida (Redis).
- 2026-11-11 · Al bot que llena el campo trampa se le responde como si todo saliera bien, para que no aprenda a esquivarlo.
- 2026-11-11 · HSTS arranca en 30 días, sin subdominios ni preload (difícil de revertir); sus advertencias de `check --deploy` están silenciadas a propósito mientras sigan apagados.
- 2026-11-11 · htmx se sirve desde `pedidos/static/pedidos/js/` (2.0.4, hash igual al SRI publicado), no desde unpkg.
- 2026-11-11 · SEO (spec 004): las URL absolutas (canónica, og:image, sitemap) salen del dominio de la petición, así que dependen de `DJANGO_ALLOWED_HOSTS` y, detrás de un proxy, de `DJANGO_BEHIND_PROXY=1` para que salgan con https. `robots.txt` no menciona el admin a propósito.
- 2026-11-11 · Chat de pedidos (spec 005) **guiado y sin IA**: sin claves, sin costo por mensaje y sin enviar datos personales a otro proveedor. Valida con el mismo `PedidoForm` y guarda con `_guardar_cotizacion`, que también usa el configurador (mismo límite, campo trampa y aviso a Binn). Si algún día se le agrega IA, hay que actualizar la política de privacidad.
- 2026-11-11 · Equipo (spec 006): el grupo "Atención de pedidos" lo crea una migración con permisos de ver y editar, sin borrar; el superusuario es el único que gestiona usuarios. `sincronizado_crm` es de solo lectura en el panel: solo lo cambian el webhook y la API de Binn.

## Pendientes conocidos

- Revisar con un abogado el texto de `/privacidad/` (spec 001) y agregar razón social/RUC del responsable.
- Mover el webhook a una cola (Celery/RQ) si sube el volumen.
- Dar de alta el dominio en Google Search Console y crear el perfil de Google Business (dirección y horario también irían al JSON-LD).
- Content-Security-Policy: después de compilar Tailwind (spec 003) y sacar los `hx-on` en línea.
