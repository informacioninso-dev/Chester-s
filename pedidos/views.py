import datetime
import hmac
import json
from functools import wraps
from urllib.parse import quote

from django.conf import settings
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
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


def _render_parcial_o_pagina(request, parcial, contexto):
    """Con HTMX devuelve solo el fragmento; sin JavaScript, la página completa."""
    if es_htmx(request):
        return render(request, parcial, contexto)
    pagina = _contexto_index()
    pagina.update(contexto)
    return render(request, "pedidos/index.html", pagina)


def _contexto_index():
    ctx = _contexto_configurador(1, {})
    ctx.update(
        {
            "lead_form": LeadCumpleForm(),
            "lead_ok": None,
            "whatsapp": settings.CHESTERS_WHATSAPP,
            "dias_regalo": settings.CHESTERS_DIAS_REGALO,
            "hoy": timezone.localdate(),
        }
    )
    return ctx


# ---------------------------------------------------------------------------
# Páginas y fragmentos HTMX
# ---------------------------------------------------------------------------

@require_GET
def index(request):
    return render(request, "pedidos/index.html", _contexto_index())


@require_GET
def privacidad(request):
    return render(request, "pedidos/privacidad.html", {
        "titulo": "Política de privacidad | Chester's",
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


@require_POST
def confirmar_pedido(request):
    """Paso 4: guarda la cotización en silencio y manda al cliente a WhatsApp."""
    datos = _datos_pedido(request)
    form = PedidoForm(request.POST)
    if not form.is_valid():
        paso_error = form.primer_paso_con_error(PedidoForm.TOTAL_PASOS)
        ctx = _contexto_configurador(paso_error, datos, form=form)
        return _render_parcial_o_pagina(request, "pedidos/partials/configurador.html", ctx)

    with transaction.atomic():
        cotizacion = form.save()
        notificar_binn(cotizacion)

    wa_url = url_whatsapp(cotizacion)
    if not es_htmx(request):
        return HttpResponseRedirect(wa_url)

    respuesta = render(
        request,
        "pedidos/partials/pedido_confirmado.html",
        {"cotizacion": cotizacion, "wa_url": wa_url},
    )
    # Tras pintar el mensaje de éxito, el JS de la página abre WhatsApp.
    respuesta["HX-Trigger-After-Settle"] = json.dumps({"abrirWhatsapp": {"url": wa_url}})
    return respuesta


@require_http_methods(["GET", "POST"])
def registrar_lead(request):
    """La Ruleta de Melloco: guarda la fecha y avisa a Binn.

    GET devuelve el formulario vacío (botón "Registrar otro perrito").
    """
    form = LeadCumpleForm(request.POST if request.method == "POST" else None)
    lead = None
    if request.method == "POST" and form.is_valid():
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
        limite = min(int(request.GET.get("limite", 200)), 1000)
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
