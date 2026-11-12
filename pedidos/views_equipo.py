"""Gestor de pedidos del equipo de Chester’s (spec 010).

Pensado para el celular: tarjetas de pedido que empiezan por el perrito, asignación
de cocina y reparto, y la ficha de cada perrito con lo que le encanta y sus alergias.
"""

from functools import wraps

from django import forms
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import INPUT
from .models import Cotizacion, EstadoPedido, Estilo, LeadCumple, Perrito, Receta

GRUPOS_EQUIPO = ("Atención de pedidos", "Cocina", "Reparto")

ACTIVOS = (EstadoPedido.NUEVO, EstadoPedido.CONFIRMADO, EstadoPedido.EN_PREPARACION)

# Siguiente paso de cada pedido y el texto del botón que lo dispara.
SIGUIENTE = {
    EstadoPedido.NUEVO: (EstadoPedido.CONFIRMADO, "Confirmar pedido"),
    EstadoPedido.CONFIRMADO: (EstadoPedido.EN_PREPARACION, "Pasar a cocina"),
    EstadoPedido.EN_PREPARACION: (EstadoPedido.ENTREGADO, "Marcar entregado"),
}

PESTANAS = [
    ("activos", "Activos"),
    ("mios", "Míos"),
    (EstadoPedido.NUEVO, "Nuevos"),
    (EstadoPedido.CONFIRMADO, "Confirmados"),
    (EstadoPedido.EN_PREPARACION, "En preparación"),
    (EstadoPedido.ENTREGADO, "Entregados"),
    (EstadoPedido.CANCELADO, "Cancelados"),
]


# ---------------------------------------------------------------------------
# Acceso
# ---------------------------------------------------------------------------

def es_del_equipo(user):
    return user.is_active and (user.is_superuser or user.groups.filter(name__in=GRUPOS_EQUIPO).exists())


def equipo_requerido(vista):
    """Sesión iniciada y del equipo; si no, a la pantalla de ingreso o a "sin acceso"."""

    @wraps(vista)
    @login_required(login_url=reverse_lazy("pedidos:equipo_ingresar"))
    def envoltura(request, *args, **kwargs):
        if not es_del_equipo(request.user):
            return render(request, "pedidos/equipo/sin_acceso.html", status=403)
        return vista(request, *args, **kwargs)

    return envoltura


class Ingresar(LoginView):
    template_name = "pedidos/equipo/ingresar.html"
    redirect_authenticated_user = True

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["username"].widget.attrs.update(
            {"class": INPUT, "autocomplete": "username", "autocapitalize": "none", "spellcheck": "false"})
        form.fields["password"].widget.attrs.update({"class": INPUT, "autocomplete": "current-password"})
        return form

    def get_default_redirect_url(self):
        return reverse("pedidos:equipo")


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _personas(grupo):
    return get_user_model().objects.filter(is_active=True, groups__name=grupo).order_by("first_name", "username")


def nombre_persona(user):
    return (user.get_full_name() or user.username) if user else ""


def _cuando(pedido, hoy):
    """Ayuda para la fecha de celebración: 'Hoy', 'Mañana', 'En 3 días' o 'Atrasado'."""
    dias = (pedido.fecha_cumple - hoy).days
    if pedido.estado in ACTIVOS and dias < 0:
        return {"texto": "Atrasado", "urgente": True}
    if dias == 0:
        return {"texto": "Hoy", "urgente": pedido.estado in ACTIVOS}
    if dias == 1:
        return {"texto": "Mañana", "urgente": pedido.estado in ACTIVOS}
    if dias > 1:
        return {"texto": f"En {dias} días", "urgente": False}
    return {"texto": f"Hace {-dias} días", "urgente": False}


def _registrar(request, pedido, mensaje):
    """Deja el cambio en el historial de Django (se ve en /admin/)."""
    LogEntry.objects.log_actions(
        user_id=request.user.pk, queryset=[pedido], action_flag=CHANGE,
        change_message=mensaje, single_object=True,
    )


def _contexto_tarjeta(pedido, hoy=None):
    hoy = hoy or timezone.localdate()
    return {
        "p": pedido,
        "cuando": _cuando(pedido, hoy),
        "siguiente": SIGUIENTE.get(pedido.estado),
        "cocina": _personas("Cocina"),
        "reparto": _personas("Reparto"),
    }


def _pedidos_con_perrito():
    return Cotizacion.objects.select_related("perrito", "cocinero", "repartidor")


# ---------------------------------------------------------------------------
# Pedidos
# ---------------------------------------------------------------------------

@require_GET
@equipo_requerido
def pedidos(request):
    pestana = request.GET.get("ver", "activos")
    if pestana not in dict(PESTANAS):
        pestana = "activos"
    busqueda = request.GET.get("q", "").strip()

    qs = _pedidos_con_perrito()
    mios = Q(cocinero=request.user) | Q(repartidor=request.user)
    if busqueda:
        qs = qs.filter(Q(nombre_perro__icontains=busqueda) | Q(nombre_cliente__icontains=busqueda)
                       | Q(telefono__icontains=busqueda))

    filtros = {
        "activos": Q(estado__in=ACTIVOS),
        "mios": Q(estado__in=ACTIVOS) & mios,
        **{estado: Q(estado=estado) for estado in EstadoPedido.values},
    }
    conteos = qs.aggregate(**{clave: Count("pk", filter=filtro) for clave, filtro in filtros.items()})

    lista = qs.filter(filtros[pestana])
    # Lo pendiente, por la celebración más cercana; lo cerrado, lo más reciente primero.
    lista = lista.order_by("fecha_cumple", "creado_en") if pestana in ("activos", "mios", *ACTIVOS) \
        else lista.order_by("-fecha_cumple", "-creado_en")

    hoy = timezone.localdate()
    contexto = {
        "pestanas": [{"clave": c, "nombre": n, "total": conteos[c], "actual": c == pestana} for c, n in PESTANAS],
        "pestana": pestana,
        "busqueda": busqueda,
        "tarjetas": [_contexto_tarjeta(p, hoy) for p in lista[:200]],
    }
    return render(request, "pedidos/equipo/pedidos.html", contexto)


@require_POST
@equipo_requerido
def cambiar_estado(request, pk):
    pedido = get_object_or_404(_pedidos_con_perrito(), pk=pk)
    nuevo = request.POST.get("estado")
    permitido = (nuevo == EstadoPedido.CANCELADO and pedido.estado in ACTIVOS) or \
                (pedido.estado in SIGUIENTE and SIGUIENTE[pedido.estado][0] == nuevo)
    if permitido:
        anterior = pedido.get_estado_display()
        pedido.estado = nuevo
        pedido.save(update_fields=["estado"])
        _registrar(request, pedido, f"Estado: {anterior} → {pedido.get_estado_display()} (gestor)")
    return _responder_tarjeta(request, pedido)


@require_POST
@equipo_requerido
def asignar(request, pk):
    pedido = get_object_or_404(_pedidos_con_perrito(), pk=pk)
    for campo, grupo, rol in (("cocinero", "Cocina", "Cocina"), ("repartidor", "Reparto", "Reparto")):
        if campo not in request.POST:
            continue
        valor = request.POST.get(campo)
        persona = _personas(grupo).filter(pk=valor).first() if valor else None
        if valor and persona is None:
            continue  # alguien que no está en el grupo: se ignora
        if getattr(pedido, f"{campo}_id") != (persona.pk if persona else None):
            setattr(pedido, campo, persona)
            pedido.save(update_fields=[campo])
            _registrar(request, pedido, f"{rol}: {nombre_persona(persona) or 'sin asignar'} (gestor)")
    return _responder_tarjeta(request, pedido, guardado=True)


def _responder_tarjeta(request, pedido, guardado=False):
    if request.headers.get("HX-Request") != "true":
        # Sin JavaScript se vuelve a la lista; solo a una dirección del propio gestor.
        volver = request.POST.get("volver", "")
        seguro = url_has_allowed_host_and_scheme(volver, allowed_hosts={request.get_host()})             and volver.startswith(reverse("pedidos:equipo")) and "/pedido/" not in volver
        return HttpResponseRedirect(volver if seguro else reverse("pedidos:equipo"))
    contexto = _contexto_tarjeta(pedido)
    contexto["guardado"] = guardado
    return render(request, "pedidos/equipo/tarjeta_pedido.html", contexto)


# ---------------------------------------------------------------------------
# Ficha del perrito
# ---------------------------------------------------------------------------

class FichaForm(forms.ModelForm):
    class Meta:
        model = Perrito
        fields = ["raza", "tamano", "le_encanta", "no_le_gusta", "notas"]
        widgets = {
            "raza": forms.TextInput(attrs={"class": INPUT, "placeholder": "Ej.: Schnauzer", "autocomplete": "off"}),
            "tamano": forms.Select(attrs={"class": INPUT}),
            "le_encanta": forms.Textarea(attrs={"class": INPUT, "rows": 2, "placeholder": "Ej.: La zanahoria y el huesito de carne"}),
            "no_le_gusta": forms.Textarea(attrs={"class": INPUT, "rows": 2, "placeholder": "Ej.: Alérgico al pollo. No tolera la lactosa."}),
            "notas": forms.Textarea(attrs={"class": INPUT, "rows": 3, "placeholder": "Lo que convenga recordar para la próxima"}),
        }
        labels = {"tamano": "Tamaño", "le_encanta": "Le encanta", "no_le_gusta": "No le gusta / alergias"}


def _favorita(pedidos, campo, opciones):
    fila = (pedidos.exclude(estado=EstadoPedido.CANCELADO).values(campo)
            .annotate(veces=Count("pk")).order_by("-veces", campo).first())
    return {"nombre": dict(opciones)[fila[campo]], "veces": fila["veces"]} if fila else None


@require_http_methods(["GET", "POST"])
@equipo_requerido
def ficha(request, pk):
    perrito = get_object_or_404(Perrito, pk=pk)
    guardado = False
    if request.method == "POST":
        form = FichaForm(request.POST, instance=perrito)
        if form.is_valid():
            form.save()
            LogEntry.objects.log_actions(user_id=request.user.pk, queryset=[perrito], action_flag=CHANGE,
                                         change_message="Ficha actualizada (gestor)", single_object=True)
            guardado = True
            form = FichaForm(instance=perrito)
        if request.headers.get("HX-Request") == "true":
            return render(request, "pedidos/equipo/ficha_form.html",
                          {"perrito": perrito, "form": form, "guardado": guardado})
    else:
        form = FichaForm(instance=perrito)

    pedidos_perrito = Cotizacion.objects.filter(perrito=perrito).select_related("cocinero", "repartidor")
    cumple = LeadCumple.objects.filter(perrito=perrito).order_by("-creado_en").first()
    return render(request, "pedidos/equipo/ficha.html", {
        "perrito": perrito,
        "form": form,
        "guardado": guardado,
        "pedidos": pedidos_perrito.order_by("-fecha_cumple", "-creado_en"),
        "receta_favorita": _favorita(pedidos_perrito, "receta", Receta.choices),
        "forma_favorita": _favorita(pedidos_perrito, "estilo", Estilo.choices),
        "cumple": cumple,
        "proximo_cumple": cumple.proximo_cumple() if cumple else None,
        "notas_familia": [p for p in pedidos_perrito.order_by("-creado_en") if p.nota_familia],
    })
