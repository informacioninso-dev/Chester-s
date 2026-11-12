# MEMORY.md · Chester's

Decisiones y contexto que no se deducen del código. Lo más importante va primero.
Formato: `- AAAA-MM-DD · decisión — por qué`.

## Reglas del equipo

- 2026-11-11 · **Claude (o cualquier agente de IA) NO va como coautor.** No agregar `Co-Authored-By` ni firmas de IA en commits ni en PRs — decisión del dueño del repo.

- 2026-11-12 · **Melloco es el Director de Calidad de Chester’s** (hermano perruno de Chester). Todo texto nuevo debe dejarlo claro: la primera vez que aparece en cada pantalla o sección va con su cargo ("Melloco, nuestro Director de Calidad"), y en descripciones para buscadores y redes también. Las respuestas y la venta las hace "la familia de Chester" — decisión del dueño del repo: el copy no lo dejaba claro.

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

- 2026-11-12 · Melloco tiene cara: dibujo vectorial hecho a mano (`pedidos/static/pedidos/img/melloco.svg`, se edita directo) en el estilo de Chester, en la insignia "Aprobado por Melloco", el sello del paso 4, el chat y la confirmación. Rasgos confirmados por el dueño con fotos (`assets/melloco-original.png`, `assets/melloco-frente.png`): **mestizo, no terrier**, blanco, cabeza redondeada con hocico blanco de largo medio y un copete pequeño al centro, **pecas café claro agrupadas en la coronilla y una mancha sobre el puente del hocico**, orejas que se doblan hacia abajo (blancas en la base, crema-café en el borde), ojos grandes oscuros y brillantes, nariz café oscura con la parte de abajo rosada. Lleva **corbata larga de ejecutivo** (azul marino, rayas discretas) bajo un collar granate — nada de moños ni lunares: "ejecutivo, no payaso de circo". Es provisional: conviene que un ilustrador haga la versión final. En "Nuestra historia" no va por ahora.

- 2026-11-12 · Voz humana, nada que suene a app o IA — pedido del dueño: "transmitir humanidad". Melloco habla como el perrito de la familia (sin "te ayudo", "en un minuto" ni "¡Buena elección!"), y se dice que del otro lado de WhatsApp responde la familia. Melloco figura como Director de Calidad que revisa cada pastel: insignia de la portada, sello en el paso 4 y resumen del chat.

- 2026-11-12 · **Estrategia de marketing: todo pastel está aprobado por Melloco, Director de Calidad.** En la portada manda el sello redondo "APROBADO POR MELLOCO · DIRECTOR DE CALIDAD" junto a la lista "Control de calidad Melloco", **nunca sobre el logo de Chester**: el perrito original es el protagonista de la marca. La lista dice: recetas caseras aprobadas por Melloco, hecho a pedido, revisado por él antes de salir de la cocina. Melloco se dibuja contento (boca abierta, lengua, cabeza ladeada): con la boca cerrada se veía triste. Decisión del dueño.

- 2026-11-12 · Portada sin patrones de "landing hecha por IA" — pedido del dueño. Evitar: etiqueta en cápsula con puntito sobre el título, título partido en dos con la segunda frase en cursiva de color, pares de adjetivos genéricos ("saludables y artesanales"), frases en espejo ("inspirados por…, aprobados por…") y emoji al final de la frase. Escribir como la familia: quiénes somos, qué hacemos y cómo. Título actual: "Su cumpleaños también merece pastel."

- 2026-11-12 · WhatsApp **nunca se abre solo** (spec 007): confirmar guarda el pedido y muestra la pantalla de Melloco con "Enviar por WhatsApp" en otra pestaña y qué sigue. La redirección automática ocultaba esa pantalla y cambiaba la página sin aviso. Un solo verbo para pedir: "Pedir" / "Pedir su pastel"; el chat es el camino secundario (botón azul marino). Decisión del dueño tras la revisión de impeccable (26/40).

- 2026-11-12 · La demo vive en el droplet de Licitar (spec 008). Desde la spec 018 está en su propia red, `chesters_proxy`, que comparte solo con Caddy; antes estaba en `licitar_default`. El servicio de Docker se llama `chesters`, **nunca `web`**: ese es el nombre del de Licitar en la misma red, y con dos `web` Caddy le mandaba a Chester’s parte del tráfico de licitar.binnso.com (Licitar dio 400 a ratos entre las 08:59 y las 09:40 del 12-nov).
- 2026-11-12 · El botón "Pedir con Melloco" se ve **siempre** (spec 009, reemplaza lo de la 005 y la 007 que lo escondían): completo en la portada y la historia, compacto (solo la carita) sobre los formularios — decisión del dueño: el chat es la forma más cómoda de pedir desde el teléfono.
- 2026-11-12 · Gestor del equipo en `/equipo/` (spec 010). Cada tarjeta empieza por el perrito y sus alergias, no por el trámite: "cada pastel se hace con cariño para alguien" es la parte humana del negocio (dueño). La gestión interna se limita a estados, cocina y reparto; el dueño pidió no agregar más por ahora. `/admin/` queda para el administrador.
- 2026-11-12 · La ficha del perrito se identifica por WhatsApp (formato 593…) + nombre sin tildes ni mayúsculas. Se aceptó que una familia con dos perritos del mismo nombre comparta ficha.

- 2026-11-12 · El gestor se organiza **por día y por rol** (spec 011), no por estado: al dueño la primera versión, en tarjetas grandes con pestañas por estado, le pareció mala para el equipo. Una sola acción rápida por fila; el resto, en el detalle. La dirección y la hora de entrega las anota el equipo, no el cliente.

- 2026-11-12 · En el gestor, "En preparación" se muestra como **"En cocina"**: así lo dice el equipo. El modelo conserva el valor `en_preparacion`.

- 2026-11-12 · Recetas y formas viven en el **Recetario** (spec 013), no en el código. Cada una tiene una `clave` fija que no cambia aunque se renombre: la usan el formulario, el chat y Binn. Las claves originales (`carne_pure`, `manzana_zanahoria_yogur`, `huesito`, `redondo`) se conservaron.

- 2026-11-12 · El equipo de Chester’s no es muy tecnológico: los usuarios se crean desde la pestaña **Equipo** del gestor (spec 014), con contraseñas de palabras fáciles de dictar que se muestran una sola vez. A las personas nuevas no se les marca staff. Lo administra solo el superusuario.

- 2026-11-12 · **Cobrado va aparte del estado** (spec 015): a veces pagan un anticipo antes de entregar. Un pedido entregado y sin cobrar no se va al Historial; queda en "Por cobrar".

- 2026-11-12 · Freno de ingreso (spec 016): 10 fallos por IP o 20 por usuario en 15 min bloquean 15 min. Usa la caché local: si gunicorn pasa a más de un proceso, hay que mover la caché a Redis o a la base, o el freno se reparte entre procesos.

- 2026-11-12 · En la vista Cocina la receta está a la mano (spec 017): "Ver receta" se despliega en la misma fila y tocar el pedido abre el detalle en "Cómo se hace". Pedido del dueño: en la cocina lo primero es cómo se hace.

- 2026-11-12 · El WhatsApp de Melloco se configura en **Ajustes** del gestor (spec 019, modelo `Ajustes` con pk=1). `CHESTERS_WHATSAPP` queda solo como respaldo si nadie lo configuró. Confirmar y cancelar pedidos es solo de Atención y del administrador.

## Pendientes conocidos

- **Respaldo diario automático de la base de Chester’s (spec 018, hallazgo 2): hoy no hay ningún respaldo.**
- Revisar con un abogado el texto de `/privacidad/` (spec 001) y agregar razón social/RUC del responsable.
- Mover el webhook a una cola (Celery/RQ) si sube el volumen.
- Dar de alta el dominio en Google Search Console y crear el perfil de Google Business (dirección y horario también irían al JSON-LD).
- Mostrar precio desde, porciones, zona de entrega y días de anticipación (esperando los datos del dueño); poner la anticipación como fecha mínima.
- P2 de la revisión de impeccable: etiquetas en mayúsculas sobre los títulos, historia de Chester, nombre de la Ruleta, emoji 🐾, enlaces de 20 px.
- Content-Security-Policy: después de compilar Tailwind (spec 003) y sacar los `hx-on` en línea.
