import datetime
import hmac
import json
from functools import wraps
from urllib.parse import quote

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.safestring import mark_safe
from django.utils.formats import date_format
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .crm import notificar_binn
from .forms import LeadCumpleForm, PedidoForm
from .models import Cotizacion, Estilo, LeadCumple, Receta

PASOS_NOMBRES = ["Datos", "Receta", "Forma", "Confirmar"]

FRASE_ESTILO = {
    Estilo.HUESITO: "en forma de huesito",
    Estilo.REDONDO: "en forma redonda",
}


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def es_htmx(request):
    return request.headers.get("HX-Request") == "true"


# Nombre del campo trampa: está oculto para las personas y solo lo llenan los bots.
CAMPO_TRAMPA = "sitio_web"


def es_bot(request):
    return bool(request.POST.get(CAMPO_TRAMPA, "").strip())


def _ip(request):
    """IP del visitante. Detrás de un proxy, la última de X-Forwarded-For es la que
    agregó nuestro proxy; las anteriores las puede inventar el cliente."""
    if settings.DETRAS_DE_PROXY:
        reenviada = request.headers.get("X-Forwarded-For", "")
        if reenviada:
            return reenviada.split(",")[-1].strip()
    return request.META.get("REMOTE_ADDR", "")


class LimiteEnvios:
    """Cuenta los envíos guardados por IP y formulario en una ventana fija."""

    def __init__(self, request, formulario):
        self.clave = f"envios:{formulario}:{_ip(request)}"

    def superado(self):
        return (cache.get(self.clave) or 0) >= settings.CHESTERS_LIMITE_ENVIOS

    def sumar(self):
        if cache.add(self.clave, 1, settings.CHESTERS_VENTANA_ENVIOS):
            return
        try:
            cache.incr(self.clave)
        except ValueError:  # la clave expiró entre add() e incr()
            cache.set(self.clave, 1, settings.CHESTERS_VENTANA_ENVIOS)


def _datos_pedido(request):
    """Datos del configurador que llegan en el POST (paso actual + ocultos)."""
    nombres = PedidoForm.campos_hasta(PedidoForm.TOTAL_PASOS)
    return {n: request.POST.get(n, "").strip() for n in nombres if request.POST.get(n)}


def _paso_valido(valor, por_defecto=1):
    try:
        return min(max(int(valor), 1), PedidoForm.TOTAL_PASOS)
    except (TypeError, ValueError):
        return por_defecto


def _contexto_configurador(paso, datos, form=None):
    """Arma el contexto del paso `paso`.

    Si no hay errores, se usa un formulario NO ligado con `initial` para que
    los campos aparezcan rellenos sin disparar validaciones (ni aria-invalid).
    """
    form = form or PedidoForm(initial=datos)
    visibles = set(PedidoForm.PASOS[paso])
    ocultos = [(k, v) for k, v in datos.items() if k not in visibles and k != "acepta_datos"]
    pasos = [
        {"numero": i, "nombre": nombre, "estado": "hecho" if i < paso else "actual" if i == paso else "pendiente"}
        for i, nombre in enumerate(PASOS_NOMBRES, start=1)
    ]
    resumen = None
    if paso == PedidoForm.TOTAL_PASOS:
        resumen = {
            "nombre_perro": datos.get("nombre_perro", ""),
            "fecha": _fecha_legible(datos.get("fecha_cumple")),
            "receta": dict(Receta.choices).get(datos.get("receta"), ""),
            "estilo": dict(Estilo.choices).get(datos.get("estilo"), ""),
        }
    return {
        "form": form,
        "paso": paso,
        "pasos": pasos,
        "ocultos": ocultos,
        "resumen": resumen,
        "errores": form.errors if form.is_bound else {},
        "recetas": Receta,
        "estilos": Estilo,
    }


def _fecha_legible(valor):
    """'2026-12-15' o date -> '15 de diciembre de 2026'."""
    if not valor:
        return ""
    if isinstance(valor, str):
        try:
            valor = datetime.datetime.strptime(valor, "%Y-%m-%d").date()
        except ValueError:
            return valor
    return date_format(valor, r"j \d\e F \d\e Y")


def mensaje_whatsapp(cotizacion):
    receta = cotizacion.get_receta_display().lower()
    estilo = FRASE_ESTILO[cotizacion.estilo]
    fecha = _fecha_legible(cotizacion.fecha_cumple)
    return (
        f"Hola Melloco, quiero confirmar el pastel de {receta} {estilo} "
        f"para el cumpleaños de {cotizacion.nombre_perro} el {fecha}"
    )


def url_whatsapp(cotizacion):
    return f"https://wa.me/{settings.CHESTERS_WHATSAPP}?text={quote(mensaje_whatsapp(cotizacion))}"


def _render_parcial_o_pagina(request, parcial, contexto, status=200):
    """Con HTMX devuelve solo el fragmento; sin JavaScript, la página completa."""
    if es_htmx(request):
        return render(request, parcial, contexto, status=status)
    pagina = _contexto_index()
    pagina.update(contexto)
    return render(request, "pedidos/index.html", pagina, status=status)


def _contexto_index():
    ctx = _contexto_configurador(1, {})
    ctx.update(
        {
            "lead_form": LeadCumpleForm(),
            "lead_ok": None,
            "whatsapp": settings.CHESTERS_WHATSAPP,
            "dias_regalo": settings.CHESTERS_DIAS_REGALO,
            **contexto_chat_inicial(),
            "hoy": timezone.localdate(),
        }
    )
    return ctx


# ---------------------------------------------------------------------------
# Páginas y fragmentos HTMX
# ---------------------------------------------------------------------------

@require_GET
def index(request):
    ctx = _contexto_index()
    ctx["datos_estructurados"] = _datos_estructurados(request)
    return render(request, "pedidos/index.html", ctx)


def _datos_estructurados(request):
    """JSON-LD de la portada (schema.org/Bakery), escapado para ir dentro de <script>."""
    datos = {
        "@context": "https://schema.org",
        "@type": "Bakery",
        "name": "Chester’s",
        "description": "Pasteles para el cumpleaños de tu perrito, horneados en casa por la familia de Chester y aprobados por Melloco, su Director de Calidad.",
        "url": request.build_absolute_uri(reverse("pedidos:index")),
        "logo": request.build_absolute_uri(static("pedidos/img/logo.jpg")),
        "image": request.build_absolute_uri(static("pedidos/img/logo.jpg")),
        "telephone": f"+{settings.CHESTERS_WHATSAPP}",
        "servesCuisine": "Pasteles para perritos",
        "areaServed": {"@type": "Country", "name": "Ecuador"},
    }
    texto = json.dumps(datos, ensure_ascii=False)
    for caracter, escape in (("<", r"\u003C"), (">", r"\u003E"), ("&", r"\u0026")):
        texto = texto.replace(caracter, escape)
    return mark_safe(texto)


@require_GET
def robots_txt(request):
    lineas = [
        "User-agent: *",
        # Fragmentos de HTMX y la API: no son páginas para buscadores.
        "Disallow: /api/",
        "Disallow: /configurador/",
        "Disallow: /ruleta/",
        "Disallow: /chat/",
        "",
        f"Sitemap: {request.build_absolute_uri(reverse('sitemap'))}",
    ]
    return HttpResponse("\n".join(lineas) + "\n", content_type="text/plain; charset=utf-8")


@require_GET
def privacidad(request):
    return render(request, "pedidos/privacidad.html", {
        "titulo": "Política de privacidad | Chester’s",
        "descripcion": "Qué datos guarda Chester’s, para qué los usa, con quién los comparte "
                       "y cómo pedir que los corrijan o los borren (LOPDP, Ecuador).",
        "og_descripcion": "Qué datos guardamos y cómo ejercer tus derechos.",
        "whatsapp": settings.CHESTERS_WHATSAPP,
    })


@require_http_methods(["GET", "POST"])
def configurador(request):
    """Navegación entre pasos.

    - GET: reinicia el configurador en el paso 1.
    - POST: `paso` = paso actual, `ir_a` = paso destino (botón pulsado).
      Para avanzar se validan todos los campos hasta el paso actual; si algo
      falla se muestra el primer paso con error. Retroceder no valida.
    """
    if request.method == "GET":
        ctx = _contexto_configurador(1, {})
        return _render_parcial_o_pagina(request, "pedidos/partials/configurador.html", ctx)

    datos = _datos_pedido(request)
    paso = _paso_valido(request.POST.get("paso"))
    destino = _paso_valido(request.POST.get("ir_a"), por_defecto=paso)

    if destino > paso:
        form = PedidoForm(request.POST)
        form.is_valid()  # dispara la validación; solo miramos los pasos ya completados
        paso_error = form.primer_paso_con_error(paso)
        if paso_error:
            ctx = _contexto_configurador(paso_error, datos, form=form)
            return _render_parcial_o_pagina(request, "pedidos/partials/configurador.html", ctx)

    ctx = _contexto_configurador(destino, datos)
    return _render_parcial_o_pagina(request, "pedidos/partials/configurador.html", ctx)


def _guardar_cotizacion(request, form):
    """Guarda un pedido válido (configurador o chat) y avisa a Binn.

    Devuelve None si esta conexión superó el límite de envíos. Si llenó el campo
    trampa, devuelve la cotización sin guardarla: al bot se le responde igual.
    """
    limite = LimiteEnvios(request, "pedido")
    if limite.superado():
        return None
    limite.sumar()
    if es_bot(request):
        return form.save(commit=False)
    with transaction.atomic():
        cotizacion = form.save()
        notificar_binn(cotizacion)
    return cotizacion


@require_POST
def confirmar_pedido(request):
    """Paso 4: guarda la cotización en silencio y manda al cliente a WhatsApp."""
    datos = _datos_pedido(request)
    form = PedidoForm(request.POST)
    if not form.is_valid():
        paso_error = form.primer_paso_con_error(PedidoForm.TOTAL_PASOS)
        ctx = _contexto_configurador(paso_error, datos, form=form)
        return _render_parcial_o_pagina(request, "pedidos/partials/configurador.html", ctx)

    cotizacion = _guardar_cotizacion(request, form)
    if cotizacion is None:
        ctx = _contexto_configurador(PedidoForm.TOTAL_PASOS, datos)
        ctx.update(limite_envios="configurador", whatsapp=settings.CHESTERS_WHATSAPP)
        return _render_parcial_o_pagina(request, "pedidos/partials/configurador.html", ctx, status=429)

    wa_url = url_whatsapp(cotizacion)
    if not es_htmx(request):
        return HttpResponseRedirect(wa_url)

    respuesta = render(
        request,
        "pedidos/partials/pedido_confirmado.html",
        {"cotizacion": cotizacion, "wa_url": wa_url},
    )
    return respuesta


@require_http_methods(["GET", "POST"])
def registrar_lead(request):
    """La Ruleta de Melloco: guarda la fecha y avisa a Binn.

    GET devuelve el formulario vacío (botón "Registrar otro perrito").
    """
    form = LeadCumpleForm(request.POST if request.method == "POST" else None)
    lead = None
    if request.method == "POST" and form.is_valid():
        limite = LimiteEnvios(request, "ruleta")
        if limite.superado():
            ctx = {"lead_form": form, "lead_ok": None, "limite_envios": "ruleta",
                   "whatsapp": settings.CHESTERS_WHATSAPP, "hoy": timezone.localdate()}
            return _render_parcial_o_pagina(request, "pedidos/partials/ruleta.html", ctx, status=429)
        limite.sumar()

        if es_bot(request):
            lead = form.save(commit=False)  # se responde igual, pero no se guarda ni se avisa a Binn
        else:
            with transaction.atomic():
                lead = form.save()
                notificar_binn(lead)
        form = LeadCumpleForm()

    ctx = {
        "lead_form": form,
        "lead_ok": lead,
        "fecha_regalo": _fecha_legible(lead.fecha_regalo()) if lead else "",
        "hoy": timezone.localdate(),
    }
    return _render_parcial_o_pagina(request, "pedidos/partials/ruleta.html", ctx)


# ---------------------------------------------------------------------------
# Chat de pedidos con Melloco (spec 005)
#
# Conversación guiada, sin IA. No hay sesión: las respuestas ya dadas viajan
# como campos ocultos, igual que en el configurador, y se validan con PedidoForm.
# ---------------------------------------------------------------------------

# Orden de las preguntas y tipo de respuesta que espera cada una.
PREGUNTAS_CHAT = {
    "nombre_perro": "texto",
    "fecha_cumple": "fecha",
    "receta": "opciones",
    "estilo": "opciones",
    "nombre_cliente": "texto",
    "telefono": "telefono",
    "acepta_datos": "confirmar",
}

ETIQUETAS_CHAT = {
    "nombre_perro": "Nombre de tu perrito",
    "fecha_cumple": "Día de la celebración",
    "nombre_cliente": "Tu nombre",
    "telefono": "Tu WhatsApp",
}

LIMITE_CHAT = (
    "Recibí varios pedidos seguidos desde tu conexión. Espera unos minutos y vuelve "
    "a intentarlo, o escríbeme directo por WhatsApp."
)


def _textos_pregunta(campo, datos):
    perro = datos.get("nombre_perro") or "tu perrito"
    if campo == "nombre_perro":
        return ["¡Hola! Soy Melloco, el Director de Calidad de Chester’s 🐾",
                "Reviso cada pastel antes de que salga de la cocina. Cuéntame, ¿cómo se llama tu perrito?"]
    if campo == "fecha_cumple":
        return [f"¡Qué lindo nombre! ¿Qué día celebran a {perro}?"]
    if campo == "receta":
        return [f"Tenemos dos recetas caseras y las dos llevan mi aprobación. ¿Cuál crees que le gustará a {perro}?"]
    if campo == "estilo":
        return ["¡Esa me encanta! ¿Y qué forma le hacemos?"]
    if campo == "nombre_cliente":
        return ["¿Y tú cómo te llamas?"]
    if campo == "telefono":
        nombre = datos.get("nombre_cliente", "")
        return [f"Gracias, {nombre}. ¿A qué WhatsApp te escribimos?"]
    return []  # acepta_datos: se muestra el resumen


def _respuesta_legible(campo, valor):
    if campo == "receta":
        return dict(Receta.choices).get(valor, valor)
    if campo == "estilo":
        return dict(Estilo.choices).get(valor, valor)
    if campo == "fecha_cumple":
        return _fecha_legible(valor)
    if campo == "acepta_datos":
        return "Confirmo el pedido"
    return valor


def _contexto_chat(campo, datos, mensajes, preguntar=True):
    """Contexto para pintar las burbujas nuevas y el campo de respuesta de `campo`."""
    mensajes = list(mensajes)
    if preguntar:
        mensajes += [{"de": "melloco", "texto": t} for t in _textos_pregunta(campo, datos)]
    if preguntar and campo == "acepta_datos":
        mensajes += [
            {"de": "melloco", "texto": f"Así queda el pedido de {datos.get('nombre_perro', 'tu perrito')}:"},
            {"de": "melloco", "resumen": {
                "Para": datos.get("nombre_perro", ""),
                "Fecha": _fecha_legible(datos.get("fecha_cumple")),
                "Receta": dict(Receta.choices).get(datos.get("receta"), ""),
                "Forma": dict(Estilo.choices).get(datos.get("estilo"), ""),
                "WhatsApp": datos.get("telefono", ""),
            }},
            {"de": "melloco", "texto": "Antes de que salga, yo mismo lo reviso. Si está todo bien, marca la autorización y confírmalo."},
        ]
    opciones = {"receta": Receta.choices, "estilo": Estilo.choices}.get(campo, [])
    return {
        "chat_mensajes": mensajes,
        "chat_campo": campo,
        "chat_tipo": PREGUNTAS_CHAT.get(campo, "fin"),
        "chat_etiqueta": ETIQUETAS_CHAT.get(campo, ""),
        "chat_opciones": opciones,
        "chat_ocultos": [(k, v) for k, v in datos.items() if k not in (campo, "acepta_datos")],
        "chat_inicio": campo == "nombre_perro" and not datos,
        "hoy": timezone.localdate(),
    }


def contexto_chat_inicial():
    return _contexto_chat("nombre_perro", {}, [])


@require_http_methods(["GET", "POST"])
def chat(request):
    """GET: conversación nueva. POST: una respuesta (`campo` = pregunta respondida)."""
    if request.method == "GET":
        return render(request, "pedidos/partials/chat_inicio.html", contexto_chat_inicial())
    if not es_htmx(request):
        return HttpResponseRedirect(reverse("pedidos:index"))

    datos = {c: request.POST.get(c, "").strip() for c in PREGUNTAS_CHAT if request.POST.get(c, "").strip()}
    campo = request.POST.get("campo")
    if campo not in PREGUNTAS_CHAT:
        campo = "nombre_perro"

    mensajes = []
    if datos.get(campo):
        mensajes.append({"de": "cliente", "texto": _respuesta_legible(campo, datos[campo])})

    form = PedidoForm(datos)
    form.is_valid()

    # La respuesta recién dada no pasa la validación: se explica y se vuelve a preguntar.
    if campo in form.errors:
        mensajes.append({"de": "melloco", "texto": form.errors[campo][0], "error": True})
        datos.pop(campo, None)
        return render(request, "pedidos/partials/chat_paso.html",
                      _contexto_chat(campo, datos, mensajes, preguntar=False))

    siguiente = next((c for c in PREGUNTAS_CHAT if c in form.errors), None)
    if siguiente:
        if datos.get(siguiente):  # ya respondida pero dejó de ser válida (p. ej. pasó la fecha)
            mensajes.append({"de": "melloco", "texto": form.errors[siguiente][0], "error": True})
            datos.pop(siguiente)
        return render(request, "pedidos/partials/chat_paso.html", _contexto_chat(siguiente, datos, mensajes))

    # Todo válido, incluida la autorización: se guarda igual que en el configurador.
    cotizacion = _guardar_cotizacion(request, form)
    if cotizacion is None:
        mensajes.append({"de": "melloco", "texto": LIMITE_CHAT, "error": True})
        datos.pop("acepta_datos", None)
        return render(request, "pedidos/partials/chat_paso.html",
                      _contexto_chat("acepta_datos", datos, mensajes, preguntar=False), status=429)

    wa_url = url_whatsapp(cotizacion)
    mensajes.append({"de": "melloco", "texto": "¡Listo! Tu pedido quedó guardado. Toca «Enviar por WhatsApp» para mandármelo con el mensaje ya escrito; mi familia te responde por ahí para confirmar precio, fecha y entrega."})
    ctx = _contexto_chat("fin", {}, mensajes, preguntar=False)
    ctx["chat_wa_url"] = wa_url
    return render(request, "pedidos/partials/chat_paso.html", ctx)


# ---------------------------------------------------------------------------
# API para el CRM Binn (pull)
#
#   GET  /api/binn/leads/?pendientes=1&desde=2026-11-01T00:00:00-05:00
#   GET  /api/binn/cotizaciones/?pendientes=1
#   POST /api/binn/sincronizados/   {"leads": [1, 2], "cotizaciones": [5]}
#
# Autenticación: header  X-Binn-Token: <BINN_API_TOKEN>
# ---------------------------------------------------------------------------

def token_binn_requerido(vista):
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        esperado = settings.BINN_API_TOKEN
        if not esperado:
            return JsonResponse({"error": "API de Binn no configurada (BINN_API_TOKEN)."}, status=503)
        recibido = request.headers.get("X-Binn-Token", "")
        if not hmac.compare_digest(recibido.encode(), esperado.encode()):
            return JsonResponse({"error": "Token inválido."}, status=401)
        return vista(request, *args, **kwargs)

    return envoltura


def _listar(request, modelo):
    qs = modelo.objects.all()
    if request.GET.get("pendientes") in ("1", "true"):
        qs = qs.filter(sincronizado_crm=False)
    if desde := request.GET.get("desde"):
        fecha = parse_datetime(desde.replace(" ", "+"))
        if fecha is None:
            return JsonResponse({"error": "Parámetro 'desde' inválido (usa ISO 8601)."}, status=400)
        qs = qs.filter(creado_en__gte=fecha)
    try:
        limite = min(max(int(request.GET.get("limite", 200)), 1), 1000)
    except ValueError:
        limite = 200
    return JsonResponse({"resultados": [obj.to_crm() for obj in qs.order_by("creado_en")[:limite]]})


@require_GET
@token_binn_requerido
def api_leads(request):
    return _listar(request, LeadCumple)


@require_GET
@token_binn_requerido
def api_cotizaciones(request):
    return _listar(request, Cotizacion)


@csrf_exempt
@require_POST
@token_binn_requerido
def api_marcar_sincronizados(request):
    try:
        cuerpo = json.loads(request.body or b"{}")
        ids_leads = [int(i) for i in cuerpo.get("leads", [])]
        ids_cot = [int(i) for i in cuerpo.get("cotizaciones", [])]
    except (ValueError, TypeError, AttributeError):
        return JsonResponse({"error": "JSON inválido."}, status=400)

    ahora = timezone.now()
    n_leads = LeadCumple.objects.filter(pk__in=ids_leads).update(sincronizado_crm=True, sincronizado_en=ahora)
    n_cot = Cotizacion.objects.filter(pk__in=ids_cot).update(sincronizado_crm=True, sincronizado_en=ahora)
    return JsonResponse({"leads": n_leads, "cotizaciones": n_cot})
