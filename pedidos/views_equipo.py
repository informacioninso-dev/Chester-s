"""Gestor del equipo de Chester’s (specs 010 y 011).

Pedidos agrupados por día, una vista por rol (Todo, Cocina, Reparto, Asignados, Historial), el
detalle de cada pedido con su entrega, y las fichas de los perritos con sus gustos y alergias.
"""

import datetime
import secrets
from decimal import Decimal, InvalidOperation
from functools import wraps

from django import forms
from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, F, Max, Q
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import INPUT
from .seguridad import FrenoDeIntentos
from .models import (NUMERO_DE_PRUEBA, Ajustes, Cotizacion, EstadoPedido, Forma, FormaPago, LeadCumple, Perrito,
                     Receta, whatsapp_internacional, whatsapp_melloco)

ATENCION, COCINA, REPARTO = "Atención de pedidos", "Cocina", "Reparto"
GRUPOS_EQUIPO = (ATENCION, COCINA, REPARTO)

ACTIVOS = (EstadoPedido.NUEVO, EstadoPedido.CONFIRMADO, EstadoPedido.EN_PREPARACION)

# Siguiente paso de cada pedido y el texto del botón que lo dispara.
SIGUIENTE = {
    EstadoPedido.NUEVO: (EstadoPedido.CONFIRMADO, "Confirmar pedido"),
    EstadoPedido.CONFIRMADO: (EstadoPedido.EN_PREPARACION, "Pasar a cocina"),
    EstadoPedido.EN_PREPARACION: (EstadoPedido.ENTREGADO, "Marcar entregado"),
}

# Un paso atrás, para "Deshacer" (spec 012). Cancelar no se deshace desde la lista.
ANTERIOR = {nuevo: anterior for anterior, (nuevo, _) in SIGUIENTE.items()}

VISTAS = [("todo", "Todo"), ("cocina", "Cocina"), ("reparto", "Reparto"), ("cobrar", "Por cobrar"),
          ("asignados", "Asignados"), ("historial", "Historial")]

# Spec 015: entregado y sin cobrar sigue a la vista hasta que se cobra.
POR_COBRAR = Q(estado=EstadoPedido.ENTREGADO, cobrado=False)

COLUMNAS_TABLERO = [
    (EstadoPedido.NUEVO, "Nuevos"),
    (EstadoPedido.CONFIRMADO, "Confirmados"),
    (EstadoPedido.EN_PREPARACION, "En cocina"),
    (EstadoPedido.ENTREGADO, "Por cobrar"),
]

GRUPOS_DIA = ["Atrasados", "Hoy", "Mañana", "Esta semana", "Más adelante", "Por cobrar"]


# ---------------------------------------------------------------------------
# Acceso y roles
# ---------------------------------------------------------------------------

def grupos_de(user):
    return set(user.groups.values_list("name", flat=True))


def es_del_equipo(user):
    return user.is_active and (user.is_superuser or bool(grupos_de(user) & set(GRUPOS_EQUIPO)))


def puede_asignar(user, grupos):
    return user.is_superuser or ATENCION in grupos


def puede_confirmar(user, grupos):
    """Spec 019: confirmar (acordarlo con la familia) y cancelar es de Atención y del administrador."""
    return user.is_superuser or ATENCION in grupos


def vista_por_defecto(user, grupos):
    if user.is_superuser or ATENCION in grupos:
        return "todo"
    if COCINA in grupos:
        return "cocina"
    if REPARTO in grupos:
        return "reparto"
    return "todo"


def equipo_requerido(vista):
    """Sesión iniciada y del equipo; si no, a la pantalla de ingreso o a "sin acceso"."""

    @wraps(vista)
    @login_required(login_url=reverse_lazy("pedidos:equipo_ingresar"))
    def envoltura(request, *args, **kwargs):
        if not es_del_equipo(request.user):
            return render(request, "pedidos/equipo/sin_acceso.html", status=403)
        request.grupos = grupos_de(request.user)
        # Spec 018 (LOPDP): teléfono y dirección de las familias solo para quien los necesita.
        request.ve_contacto = request.user.is_superuser or bool(request.grupos & {ATENCION, REPARTO})
        return vista(request, *args, **kwargs)

    return envoltura


class IngresoSinMayusculas(FrenoDeIntentos, AuthenticationForm):
    """Spec 014: "Carla " entra como "carla". Spec 016: freno de intentos fallidos."""

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Usuario o contraseña incorrectos. Revisa la contraseña y vuelve a intentarlo.",
    }

    def clean(self):
        escrito = " ".join((self.cleaned_data.get("username") or "").split())
        if escrito:
            real = get_user_model().objects.filter(username__iexact=escrito).values_list("username", flat=True)
            self.cleaned_data["username"] = real[0] if len(real) == 1 else escrito
        return super().clean()


class Ingresar(LoginView):
    template_name = "pedidos/equipo/ingresar.html"
    redirect_authenticated_user = True
    authentication_form = IngresoSinMayusculas

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


def estado_legible(pedido):
    """Para el equipo, "En preparación" se llama "En cocina" (spec 011)."""
    return "En cocina" if pedido.estado == EstadoPedido.EN_PREPARACION else pedido.get_estado_display()


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
    return {"texto": f"Hace {-dias} día{'' if dias == -1 else 's'}", "urgente": False}


def _grupo_dia(fecha, hoy):
    dias = (fecha - hoy).days
    if dias < 0:
        return "Atrasados"
    if dias == 0:
        return "Hoy"
    if dias == 1:
        return "Mañana"
    return "Esta semana" if dias <= 7 else "Más adelante"


def _registrar(request, obj, mensaje):
    """Deja el cambio en el historial de Django (se ve en el detalle y en /admin/)."""
    LogEntry.objects.log_actions(user_id=request.user.pk, queryset=[obj], action_flag=CHANGE,
                                 change_message=mensaje, single_object=True)


def _pedidos():
    return Cotizacion.objects.select_related("perrito", "cocinero", "repartidor", "receta", "estilo", "cobrado_por")


def _filtro_vista(vista, user):
    if vista == "cocina":
        return Q(estado__in=[EstadoPedido.CONFIRMADO, EstadoPedido.EN_PREPARACION]) & \
            (Q(cocinero=user) | Q(cocinero__isnull=True))
    if vista == "reparto":
        return Q(estado=EstadoPedido.EN_PREPARACION) & (Q(repartidor=user) | Q(repartidor__isnull=True))
    if vista == "asignados":
        return Q(estado__in=ACTIVOS) & (Q(cocinero__isnull=False) | Q(repartidor__isnull=False))
    if vista == "cobrar":
        return POR_COBRAR
    if vista == "historial":
        return Q(estado__in=[EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO])
    return Q(estado__in=ACTIVOS) | POR_COBRAR


def _accion_rapida(pedido, vista, grupos, confirma=True):
    """La única acción que se ofrece en la fila, según la vista: (tipo, valor, texto)."""
    if pedido.estado == EstadoPedido.ENTREGADO and not pedido.cobrado:
        return ("cobrar", "", "Marcar cobrado")
    if vista == "cocina":
        if pedido.cocinero_id is None and COCINA in grupos:
            return ("tomar_cocina", "", "Lo tomo yo")
        if pedido.estado == EstadoPedido.CONFIRMADO:
            return ("estado", EstadoPedido.EN_PREPARACION, "Pasar a cocina")
        return None
    if vista == "reparto":
        if pedido.repartidor_id is None and REPARTO in grupos:
            return ("tomar_reparto", "", "Lo llevo yo")
        return ("estado", EstadoPedido.ENTREGADO, "Marcar entregado")
    if vista in ("todo", "asignados") and pedido.estado in SIGUIENTE:
        if pedido.estado == EstadoPedido.NUEVO and not confirma:
            return None  # lo confirma Atención
        return ("estado", *SIGUIENTE[pedido.estado])
    return None


def _grupos_por_persona(filas):
    """Vista "Asignados": un grupo por persona y rol (un pedido sale con quien lo cocina y con quien lo reparte)."""
    por_persona = {}
    for f in filas:
        p = f["p"]
        for persona, rol in ((p.cocinero, "Cocina"), (p.repartidor, "Reparto")):
            if persona:
                por_persona.setdefault((nombre_persona(persona), rol), []).append(f)
    return [{"nombre": f"{n} · {rol}", "filas": fs} for (n, rol), fs in sorted(por_persona.items())]


# ---------------------------------------------------------------------------
# Pedidos: vista del día
# ---------------------------------------------------------------------------

def _contexto_vista(request, vista, busqueda):
    hoy = timezone.localdate()
    user, grupos = request.user, request.grupos
    base = _pedidos()
    if busqueda:
        base = base.filter(Q(nombre_perro__icontains=busqueda) | Q(nombre_cliente__icontains=busqueda)
                           | Q(telefono__icontains=busqueda))

    conteos = base.aggregate(**{v: Count("pk", filter=_filtro_vista(v, user)) for v, _ in VISTAS})
    lista = base.filter(_filtro_vista(vista, user))
    if vista == "historial":
        lista = lista.order_by("-fecha_cumple", "-creado_en")[:100]
    else:
        lista = lista.order_by("fecha_cumple", F("hora_entrega").asc(nulls_last=True), "creado_en")[:300]

    confirma = puede_confirmar(user, grupos)
    filas = [{"p": p, "cuando": _cuando(p, hoy), "accion": _accion_rapida(p, vista, grupos, confirma)} for p in lista]

    grupos_vista = []
    if vista == "asignados":
        grupos_vista = _grupos_por_persona(filas)
    elif vista != "historial":
        por_dia = {g: [] for g in GRUPOS_DIA}
        for f in filas:
            grupo = "Por cobrar" if f["p"].estado == EstadoPedido.ENTREGADO else _grupo_dia(f["p"].fecha_cumple, hoy)
            por_dia[grupo].append(f)
        grupos_vista = [{"nombre": g, "filas": por_dia[g]} for g in GRUPOS_DIA if por_dia[g]]

    tablero = []
    if vista == "todo":
        tablero = [{"nombre": n, "filas": [f for f in filas if f["p"].estado == e]} for e, n in COLUMNAS_TABLERO]

    activos = base.filter(estado__in=ACTIVOS)
    falta_asignar = []
    if vista == "asignados":
        falta_asignar = [
            {"nombre": "Sin quién lo cocine", "total": activos.filter(
                estado__in=[EstadoPedido.CONFIRMADO, EstadoPedido.EN_PREPARACION], cocinero__isnull=True).count()},
            {"nombre": "Sin quién lo reparta", "total": activos.filter(
                estado=EstadoPedido.EN_PREPARACION, repartidor__isnull=True).count()},
        ]
    return {
        "vista": vista,
        "vistas": [{"clave": v, "nombre": n, "total": conteos[v], "actual": v == vista} for v, n in VISTAS],
        "busqueda": busqueda,
        "hoy": hoy,
        "para_hoy": activos.filter(fecha_cumple=hoy).count(),
        "atrasados": activos.filter(fecha_cumple__lt=hoy).count(),
        "por_cobrar": base.filter(POR_COBRAR).count(),
        "filas": filas,
        "grupos_vista": grupos_vista,
        "tablero": tablero,
        "falta_asignar": falta_asignar,
        "sin_pedidos": not Cotizacion.objects.exists(),
        "actualizado": timezone.localtime(),
        "whatsapp_de_prueba": user.is_superuser and whatsapp_melloco() == NUMERO_DE_PRUEBA,
    }


@require_GET
@equipo_requerido
def pedidos(request):
    vista = request.GET.get("ver") or vista_por_defecto(request.user, request.grupos)
    if vista not in dict(VISTAS):
        vista = "todo"
    contexto = _contexto_vista(request, vista, request.GET.get("q", "").strip())
    if request.headers.get("HX-Request") == "true":  # refresco automático de la vista (spec 012)
        return render(request, "pedidos/equipo/vista.html", contexto)
    return render(request, "pedidos/equipo/pedidos.html", contexto)


# ---------------------------------------------------------------------------
# Acciones sobre un pedido (lista y detalle)
# ---------------------------------------------------------------------------

def _hacer_accion(request, pedido):
    """Aplica la acción pedida. Devuelve (ok, mensaje, deshacer): deshacer es la acción que la revierte."""
    ok, mensaje = _aplicar(request, pedido)
    deshacer = getattr(request, "_deshacer", None) if ok else None
    return ok, mensaje, deshacer


def _aplicar(request, pedido):
    tipo = request.POST.get("tipo")
    grupos = request.grupos

    if tipo == "estado":
        nuevo = request.POST.get("valor")
        permitido = (nuevo == EstadoPedido.CANCELADO and pedido.estado in ACTIVOS) or \
                    (pedido.estado in SIGUIENTE and SIGUIENTE[pedido.estado][0] == nuevo)
        if not permitido:
            return False, "Ese cambio de estado no es posible."
        es_de_atencion = nuevo == EstadoPedido.CANCELADO or pedido.estado == EstadoPedido.NUEVO
        if es_de_atencion and not puede_confirmar(request.user, grupos):
            return False, "Confirmar y cancelar pedidos lo hace Atención de pedidos."
        anterior = estado_legible(pedido)
        if nuevo != EstadoPedido.CANCELADO:
            request._deshacer = {"tipo": "deshacer", "valor": pedido.estado}
        pedido.estado = nuevo
        pedido.save(update_fields=["estado"])
        _registrar(request, pedido, f"Estado: {anterior} → {estado_legible(pedido)}")
        return True, f"Pedido de {pedido.nombre_perro}: {estado_legible(pedido).lower()}."

    if tipo == "deshacer":
        valor = request.POST.get("valor")
        if ANTERIOR.get(pedido.estado) != valor:
            return False, "Ya no se puede deshacer ese cambio."
        if valor == EstadoPedido.NUEVO and not puede_confirmar(request.user, grupos):
            return False, "Deshacer una confirmación lo hace Atención de pedidos."
        anterior = estado_legible(pedido)
        pedido.estado = valor
        pedido.save(update_fields=["estado"])
        _registrar(request, pedido, f"Estado: {anterior} → {estado_legible(pedido)} (deshecho)")
        return True, f"Listo, {pedido.nombre_perro} volvió a {estado_legible(pedido).lower()}."

    if tipo in ("soltar_cocina", "soltar_reparto"):
        campo, rol = ("cocinero", "Cocina") if tipo == "soltar_cocina" else ("repartidor", "Reparto")
        if getattr(pedido, f"{campo}_id") != request.user.pk:
            return False, "Solo puedes soltar un pedido que tienes tú."
        setattr(pedido, campo, None)
        pedido.save(update_fields=[campo])
        _registrar(request, pedido, f"{rol}: sin asignar ({nombre_persona(request.user)} lo soltó)")
        return True, f"Soltaste el pedido de {pedido.nombre_perro}."

    if tipo in ("tomar_cocina", "tomar_reparto"):
        campo, grupo, rol = ("cocinero", COCINA, "Cocina") if tipo == "tomar_cocina" else ("repartidor", REPARTO, "Reparto")
        if grupo not in grupos:
            return False, f"Solo alguien de {rol} puede tomarlo."
        if getattr(pedido, f"{campo}_id") not in (None, request.user.pk):
            return False, f"Ya lo tiene {nombre_persona(getattr(pedido, campo))}."
        if getattr(pedido, f"{campo}_id") is None:
            request._deshacer = {"tipo": tipo.replace("tomar", "soltar"), "valor": ""}
        setattr(pedido, campo, request.user)
        pedido.save(update_fields=[campo])
        _registrar(request, pedido, f"{rol}: {nombre_persona(request.user)}")
        return True, f"Tomaste el pedido de {pedido.nombre_perro}."

    if tipo == "asignar":
        if not puede_asignar(request.user, grupos):
            return False, "Solo Atención de pedidos puede asignar."
        for campo, grupo, rol in (("cocinero", COCINA, "Cocina"), ("repartidor", REPARTO, "Reparto")):
            if campo not in request.POST:
                continue
            valor = request.POST.get(campo)
            persona = _personas(grupo).filter(pk=valor).first() if valor else None
            if valor and persona is None:
                continue  # alguien que no está en el grupo: se ignora
            if getattr(pedido, f"{campo}_id") != (persona.pk if persona else None):
                setattr(pedido, campo, persona)
                pedido.save(update_fields=[campo])
                _registrar(request, pedido, f"{rol}: {nombre_persona(persona) or 'sin asignar'}")
        return True, "Asignación guardada."

    if tipo == "entrega":
        if not request.ve_contacto:
            return False, "La entrega la anotan Atención de pedidos y Reparto."
        direccion = request.POST.get("direccion_entrega", "").strip()[:300]
        hora_texto = request.POST.get("hora_entrega", "").strip()
        hora = None
        if hora_texto:
            try:
                hora = datetime.time.fromisoformat(hora_texto)
            except ValueError:
                return False, "La hora no es válida. Usa el formato 15:30."
        pedido.direccion_entrega, pedido.hora_entrega = direccion, hora
        pedido.save(update_fields=["direccion_entrega", "hora_entrega"])
        _registrar(request, pedido, "Entrega actualizada")
        return True, "Entrega guardada."

    if tipo == "cobrar":
        if pedido.estado == EstadoPedido.CANCELADO:
            return False, "Un pedido cancelado no se cobra."
        if pedido.cobrado:
            return False, "Ese pedido ya estaba cobrado."
        monto = None
        monto_texto = request.POST.get("monto_cobrado", "").strip().replace("$", "").replace(" ", "").replace(",", ".")
        if monto_texto:
            try:
                monto = Decimal(monto_texto).quantize(Decimal("0.01"))
            except InvalidOperation:
                monto = None
            if monto is None or not (0 <= monto < 1000000):
                return False, "El monto no es válido. Escríbelo así: 25,50"
        forma = request.POST.get("forma_pago", "")
        forma = forma if forma in FormaPago.values else ""
        pedido.cobrado, pedido.cobrado_en, pedido.cobrado_por = True, timezone.now(), request.user
        pedido.monto_cobrado, pedido.forma_pago = monto, forma
        pedido.save(update_fields=["cobrado", "cobrado_en", "cobrado_por", "monto_cobrado", "forma_pago"])
        detalle = " · ".join(x for x in (f"${monto}" if monto is not None else "",
                                         pedido.get_forma_pago_display() if forma else "") if x)
        _registrar(request, pedido, "Cobrado" + (f" ({detalle})" if detalle else ""))
        request._deshacer = {"tipo": "descobrar", "valor": ""}
        return True, f"Pedido de {pedido.nombre_perro}: cobrado."

    if tipo == "descobrar":
        if not pedido.cobrado:
            return False, "Ese pedido no estaba cobrado."
        pedido.cobrado, pedido.cobrado_en, pedido.cobrado_por = False, None, None
        pedido.monto_cobrado, pedido.forma_pago = None, ""
        pedido.save(update_fields=["cobrado", "cobrado_en", "cobrado_por", "monto_cobrado", "forma_pago"])
        _registrar(request, pedido, "Cobro deshecho")
        return True, f"Listo, el pedido de {pedido.nombre_perro} vuelve a estar por cobrar."

    return False, "Acción desconocida."


@require_POST
@equipo_requerido
def accion(request, pk):
    pedido = get_object_or_404(_pedidos(), pk=pk)
    ok, mensaje, deshacer = _hacer_accion(request, pedido)

    # Acción rápida desde la lista: se vuelve a pintar la vista entera (el pedido cambia de grupo).
    if request.POST.get("origen") == "lista" and request.headers.get("HX-Request") == "true":
        vista = request.POST.get("ver")
        vista = vista if vista in dict(VISTAS) else "todo"
        contexto = _contexto_vista(request, vista, request.POST.get("q", "").strip())
        contexto["aviso"] = {"ok": ok, "texto": mensaje, "deshacer": deshacer, "pk": pedido.pk}
        return render(request, "pedidos/equipo/vista.html", contexto)

    (messages.success if ok else messages.error)(request, mensaje)
    if request.POST.get("origen") == "lista":
        return HttpResponseRedirect(reverse("pedidos:equipo"))
    return HttpResponseRedirect(reverse("pedidos:equipo_pedido", args=[pedido.pk]))


@require_GET
@equipo_requerido
def pedido(request, pk):
    p = get_object_or_404(_pedidos(), pk=pk)
    grupos = request.grupos
    cambios = (LogEntry.objects.filter(content_type=ContentType.objects.get_for_model(Cotizacion), object_id=str(p.pk))
               .select_related("user").order_by("-action_time")[:10])
    confirma = puede_confirmar(request.user, grupos)
    siguiente = SIGUIENTE.get(p.estado)
    if p.estado == EstadoPedido.NUEVO and not confirma:
        siguiente = None
    return render(request, "pedidos/equipo/pedido.html", {
        "p": p,
        "cuando": _cuando(p, timezone.localdate()),
        "siguiente": siguiente,
        "puede_confirmar": confirma,
        "activo": p.estado in ACTIVOS,
        "puede_asignar": puede_asignar(request.user, grupos),
        "es_cocina": COCINA in grupos,
        "es_reparto": REPARTO in grupos,
        "cocina": _personas(COCINA),
        "reparto": _personas(REPARTO),
        "cambios": cambios,
        # Spec 013: la receta declara alérgenos y el perrito tiene alergias o una nota de la familia.
        "formas_pago": FormaPago.choices,
        "revisar_alergias": bool(p.receta.contiene and ((p.perrito and p.perrito.no_le_gusta) or p.nota_familia)),
    })


# ---------------------------------------------------------------------------
# Perritos y su ficha
# ---------------------------------------------------------------------------

@require_GET
@equipo_requerido
def perritos(request):
    busqueda = request.GET.get("q", "").strip()
    qs = Perrito.objects.annotate(
        n_pedidos=Count("cotizacion_set", filter=~Q(cotizacion_set__estado=EstadoPedido.CANCELADO), distinct=True),
    ).prefetch_related("leadcumple_set")
    if busqueda:
        qs = qs.filter(Q(nombre__icontains=busqueda) | Q(familia__icontains=busqueda) | Q(telefono__icontains=busqueda))
    hoy = timezone.localdate()
    filas = []
    for perrito in qs.order_by("nombre")[:300]:
        cumple = max(perrito.leadcumple_set.all(), key=lambda c: c.creado_en, default=None)
        filas.append({"perrito": perrito, "proximo_cumple": cumple.proximo_cumple(hoy) if cumple else None})
    return render(request, "pedidos/equipo/perritos.html", {"filas": filas, "busqueda": busqueda})


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


def _favorita(pedidos_perrito, campo):
    nombre = f"{campo}__nombre"
    fila = (pedidos_perrito.exclude(estado=EstadoPedido.CANCELADO).values(nombre)
            .annotate(veces=Count("pk")).order_by("-veces", nombre).first())
    return {"nombre": fila[nombre], "veces": fila["veces"]} if fila else None


@require_http_methods(["GET", "POST"])
@equipo_requerido
def ficha(request, pk):
    perrito = get_object_or_404(Perrito, pk=pk)
    guardado = False
    if request.method == "POST":
        form = FichaForm(request.POST, instance=perrito)
        if form.is_valid():
            form.save()
            _registrar(request, perrito, "Ficha actualizada")
            guardado = True
            form = FichaForm(instance=perrito)
        if request.headers.get("HX-Request") == "true":
            return render(request, "pedidos/equipo/ficha_form.html",
                          {"perrito": perrito, "form": form, "guardado": guardado})
    else:
        form = FichaForm(instance=perrito)

    pedidos_perrito = Cotizacion.objects.filter(perrito=perrito).select_related("cocinero", "repartidor", "receta", "estilo")
    cumple = LeadCumple.objects.filter(perrito=perrito).order_by("-creado_en").first()
    return render(request, "pedidos/equipo/ficha.html", {
        "perrito": perrito,
        "form": form,
        "guardado": guardado,
        "pedidos": pedidos_perrito.order_by("-fecha_cumple", "-creado_en"),
        "receta_favorita": _favorita(pedidos_perrito, "receta"),
        "forma_favorita": _favorita(pedidos_perrito, "estilo"),
        "cumple": cumple,
        "notas_familia": [p for p in pedidos_perrito.order_by("-creado_en") if p.nota_familia],
    })


# ---------------------------------------------------------------------------
# Recetario (spec 013): recetas y formas, lo que ve el cliente y lo que sigue la cocina
# ---------------------------------------------------------------------------

def puede_editar_recetario(user, grupos):
    return user.is_superuser or ATENCION in grupos


def _campo(widget=forms.TextInput, **attrs):
    return widget(attrs={"class": INPUT, **attrs})


class RecetaForm(forms.ModelForm):
    class Meta:
        model = Receta
        fields = ["nombre", "descripcion", "disponible", "orden", "contiene", "ingredientes", "pasos", "notas"]
        widgets = {
            "nombre": _campo(placeholder="Ej.: Pollo y arroz", autocomplete="off"),
            "descripcion": _campo(placeholder="Ej.: Suave y ligera, ideal para estómagos sensibles."),
            "orden": _campo(forms.NumberInput, min=0, inputmode="numeric"),
            "contiene": _campo(placeholder="Ej.: Pollo, lácteos (yogur)"),
            "ingredientes": _campo(forms.Textarea, rows=6, placeholder="200 g de carne molida\n1 papa mediana\n1 huevo"),
            "pasos": _campo(forms.Textarea, rows=8, placeholder="Cocinar la carne sin sal\nHacer puré con la papa\nHornear 25 min a 180 °C"),
            "notas": _campo(forms.Textarea, rows=3, placeholder="Sin sal, sin cebolla, sin ajo."),
        }


class FormaForm(forms.ModelForm):
    class Meta:
        model = Forma
        fields = ["nombre", "descripcion", "frase_mensaje", "disponible", "orden", "como_armarla", "notas"]
        widgets = {
            "nombre": _campo(placeholder="Ej.: Corazón", autocomplete="off"),
            "descripcion": _campo(placeholder="Ej.: Para los más cariñosos."),
            "frase_mensaje": _campo(placeholder="Ej.: en forma de corazón"),
            "orden": _campo(forms.NumberInput, min=0, inputmode="numeric"),
            "como_armarla": _campo(forms.Textarea, rows=6, placeholder="Molde de corazón de 15 cm\nDesmoldar en frío\nDecorar el borde con puré"),
            "notas": _campo(forms.Textarea, rows=3),
        }


TIPOS_RECETARIO = {
    "receta": {"modelo": Receta, "form": RecetaForm, "nombre": "receta", "nueva": "Nueva receta"},
    "forma": {"modelo": Forma, "form": FormaForm, "nombre": "forma", "nueva": "Nueva forma"},
}


@require_GET
@equipo_requerido
def recetario(request):
    return render(request, "pedidos/equipo/recetario.html", {
        "recetas": Receta.objects.annotate(n_pedidos=Count("pedidos")),
        "formas": Forma.objects.annotate(n_pedidos=Count("pedidos")),
        "puede_editar": puede_editar_recetario(request.user, request.grupos),
    })


@require_http_methods(["GET", "POST"])
@equipo_requerido
def recetario_item(request, tipo, pk=None):
    conf = TIPOS_RECETARIO.get(tipo)
    if conf is None:
        raise Http404
    modelo, Form = conf["modelo"], conf["form"]
    obj = get_object_or_404(modelo, pk=pk) if pk else None
    editar = puede_editar_recetario(request.user, request.grupos)
    if not editar and (obj is None or request.method == "POST"):
        messages.error(request, "Solo Atención de pedidos puede crear o editar el Recetario.")
        return HttpResponseRedirect(reverse("pedidos:equipo_recetario"))

    usados = obj.pedidos.count() if obj else 0
    if request.method == "POST":
        if request.POST.get("accion") == "eliminar" and obj:
            if usados:
                messages.error(request, f"{obj.nombre} ya se usó en {usados} pedido{'s' if usados != 1 else ''}: "
                                        "no se borra, solo se deja de ofrecer (desmarca «Disponible para clientes»).")
                return HttpResponseRedirect(reverse("pedidos:equipo_recetario_item", args=[tipo, obj.pk]))
            LogEntry.objects.log_actions(user_id=request.user.pk, queryset=[obj], action_flag=DELETION,
                                         change_message="Eliminada del Recetario")
            nombre = obj.nombre
            obj.delete()
            messages.success(request, f"{nombre} se eliminó del Recetario.")
            return HttpResponseRedirect(reverse("pedidos:equipo_recetario"))
        form = Form(request.POST, instance=obj)
        if form.is_valid():
            nuevo = obj is None
            obj = form.save()
            LogEntry.objects.log_actions(user_id=request.user.pk, queryset=[obj],
                                         action_flag=ADDITION if nuevo else CHANGE,
                                         change_message="Creada en el Recetario" if nuevo else "Recetario actualizado",
                                         single_object=True)
            aviso = "" if obj.disponible else " Todavía no la ven los clientes: márcala «Disponible» cuando esté lista."
            messages.success(request, f"{obj.nombre} guardada.{aviso}")
            return HttpResponseRedirect(reverse("pedidos:equipo_recetario_item", args=[tipo, obj.pk]))
    else:
        # Lo nuevo nace pausado y al final de la lista del cliente.
        siguiente_orden = (modelo.objects.aggregate(m=Max("orden"))["m"] or 0) + 1
        form = Form(instance=obj) if obj else Form(initial={"disponible": False, "orden": siguiente_orden})

    return render(request, "pedidos/equipo/recetario_item.html", {
        "tipo": tipo, "conf": conf, "obj": obj, "form": form, "editar": editar, "usados": usados,
        "editando": obj is None or (editar and (request.GET.get("editar") == "1" or request.method == "POST")),
    })


# ---------------------------------------------------------------------------
# Equipo (spec 014): el administrador agrega personas sin tecnicismos
# ---------------------------------------------------------------------------

ROLES = [
    (ATENCION, "Atiende pedidos", "Confirma pedidos con las familias, asigna y edita el Recetario."),
    (COCINA, "Cocina", "Toma pedidos y los prepara siguiendo el Recetario."),
    (REPARTO, "Reparte", "Lleva los pasteles y los marca como entregados."),
]

PALABRAS = (
    "huesito galleta pastel patita collar pelota colita bigote manzana zanahoria ladrido siesta "
    "paseo jardin parque mantita cojin salto trufa canela miel avena yogur queso arroz pollo "
    "carne papa calabaza mango fresa coco nube luna sol estrella hoja flor arbol rio playa "
    "arena ola brisa lluvia nieve fuego chispa globo vela regalo fiesta torta lazo moño "
    "risa abrazo beso amigo hogar puerta ventana cama sofa taza"
).split()


def contrasena_facil():
    """Tres palabras y tres números: fácil de dictar, difícil de adivinar."""
    palabras = [secrets.choice(PALABRAS) for _ in range(3)]
    return "-".join(palabras) + f"-{secrets.randbelow(900) + 100}"


def _usuario_desde(nombre):
    base = slugify(nombre.split()[0] if nombre.split() else "persona").replace("-", "")[:20] or "persona"
    usuario, n = base, 2
    while get_user_model().objects.filter(username__iexact=usuario).exists():
        usuario, n = f"{base}{n}", n + 1
    return usuario


def solo_administrador(vista):
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.user.is_superuser:
            return render(request, "pedidos/equipo/sin_acceso.html", status=403)
        return vista(request, *args, **kwargs)
    return equipo_requerido(envoltura)


class PersonaForm(forms.Form):
    nombre = forms.CharField(label="Nombre", max_length=60,
                             widget=forms.TextInput(attrs={"class": INPUT, "placeholder": "Ej.: Carla Mendoza",
                                                           "autocomplete": "off", "autocapitalize": "words"}),
                             error_messages={"required": "Escribe el nombre de la persona."})
    roles = forms.MultipleChoiceField(label="¿Qué hace?", choices=[(g, n) for g, n, _ in ROLES],
                                      widget=forms.CheckboxSelectMultiple,
                                      error_messages={"required": "Marca al menos una tarea."})


def _roles_de(user):
    nombres = dict((g, n) for g, n, _ in ROLES)
    return [nombres[g] for g in user.groups.values_list("name", flat=True) if g in nombres]


def _guardar_credenciales(request, user, contrasena):
    request.session["credenciales"] = {"pk": user.pk, "usuario": user.username, "contrasena": contrasena}


@require_GET
@solo_administrador
def personas(request):
    gente = get_user_model().objects.order_by("-is_active", "-is_superuser", "first_name", "username")
    filas = [{"u": u, "roles": _roles_de(u)} for u in gente.prefetch_related("groups")]
    return render(request, "pedidos/equipo/personas.html", {"filas": filas})


@require_http_methods(["GET", "POST"])
@solo_administrador
def persona(request, pk=None):
    User = get_user_model()
    u = get_object_or_404(User, pk=pk) if pk else None
    if u and u.is_superuser and u != request.user:
        messages.error(request, "A otro administrador no se le edita desde aquí.")
        return HttpResponseRedirect(reverse("pedidos:equipo_personas"))

    if request.method == "POST" and u and request.POST.get("accion") in ("contrasena", "quitar", "devolver"):
        accion = request.POST["accion"]
        if accion == "contrasena":
            contrasena = contrasena_facil()
            u.set_password(contrasena)
            u.save(update_fields=["password"])
            _registrar(request, u, "Nueva contraseña (gestor)")
            _guardar_credenciales(request, u, contrasena)
        elif u == request.user:
            messages.error(request, "No puedes quitarte el acceso a ti mismo.")
        else:
            u.is_active = accion == "devolver"
            u.save(update_fields=["is_active"])
            _registrar(request, u, "Acceso devuelto (gestor)" if u.is_active else "Acceso quitado (gestor)")
            messages.success(request, f"{u.get_full_name() or u.username} {'vuelve a tener' if u.is_active else 'ya no tiene'} acceso al gestor.")
        return HttpResponseRedirect(reverse("pedidos:equipo_persona", args=[u.pk]))

    if request.method == "POST":
        form = PersonaForm(request.POST)
        if form.is_valid():
            nombre = " ".join(form.cleaned_data["nombre"].split())
            partes = nombre.split(" ", 1)
            nuevo = u is None
            if nuevo:
                u = User(username=_usuario_desde(nombre), is_staff=False)
                contrasena = contrasena_facil()
                u.set_password(contrasena)
            u.first_name, u.last_name = partes[0][:150], (partes[1] if len(partes) > 1 else "")[:150]
            u.save()
            if not u.is_superuser:
                u.groups.set(Group.objects.filter(name__in=form.cleaned_data["roles"]))
            _registrar(request, u, "Creada en el gestor" if nuevo else "Editada en el gestor")
            if nuevo:
                _guardar_credenciales(request, u, contrasena)
            else:
                messages.success(request, "Cambios guardados.")
            return HttpResponseRedirect(reverse("pedidos:equipo_persona", args=[u.pk]))
    else:
        form = PersonaForm(initial={"nombre": u.get_full_name(), "roles": list(u.groups.values_list("name", flat=True))}
                           if u else None)

    credenciales = request.session.pop("credenciales", None)
    if credenciales and (not u or credenciales["pk"] != u.pk):
        credenciales = None
    enlace = request.build_absolute_uri(reverse("pedidos:equipo_ingresar"))
    mensaje = ""
    if credenciales:
        mensaje = (f"Hola {u.first_name}, ya tienes acceso al equipo de Chester’s.\n"
                   f"Entra aquí: {enlace}\nUsuario: {credenciales['usuario']}\nContraseña: {credenciales['contrasena']}")
    return render(request, "pedidos/equipo/persona.html", {
        "u": u, "form": form, "roles": ROLES, "credenciales": credenciales, "mensaje": mensaje,
        "roles_actuales": _roles_de(u) if u else [], "es_yo": u == request.user,
    })


# ---------------------------------------------------------------------------
# Ajustes (spec 019): lo que el administrador configura sin ayuda técnica
# ---------------------------------------------------------------------------

class AjustesForm(forms.Form):
    whatsapp = forms.CharField(
        label="WhatsApp de Melloco", max_length=25,
        widget=forms.TextInput(attrs={"class": INPUT, "type": "tel", "inputmode": "tel", "autocomplete": "off",
                                      "placeholder": "0991234567"}),
        error_messages={"required": "Escribe el número de WhatsApp al que deben llegar los pedidos."},
    )

    def clean_whatsapp(self):
        numero = whatsapp_internacional(self.cleaned_data["whatsapp"])
        if not (11 <= len(numero) <= 15):
            raise forms.ValidationError("Revisa el número: escríbelo como en tu celular, por ejemplo 0991234567.")
        return numero


@require_http_methods(["GET", "POST"])
@solo_administrador
def ajustes(request):
    actuales = Ajustes.actuales()
    if request.method == "POST":
        form = AjustesForm(request.POST)
        if form.is_valid():
            actuales.whatsapp = form.cleaned_data["whatsapp"]
            actuales.actualizado_por = request.user
            actuales.save()
            _registrar(request, actuales, f"WhatsApp de Melloco: {actuales.whatsapp}")
            messages.success(request, "Listo: los pedidos ahora llegan a ese WhatsApp. Pruébalo con el botón.")
            return HttpResponseRedirect(reverse("pedidos:equipo_ajustes"))
    else:
        actual = whatsapp_melloco()  # con el número de prueba el campo empieza vacío
        form = AjustesForm(initial={"whatsapp": "" if actual == NUMERO_DE_PRUEBA else actual})

    numero = whatsapp_melloco()
    recetas_sin_pasos = list(Receta.objects.filter(disponible=True, pasos=""))
    formas_sin_armar = list(Forma.objects.filter(disponible=True, como_armarla=""))
    personas = get_user_model().objects.filter(is_active=True, is_superuser=False,
                                               groups__name__in=GRUPOS_EQUIPO).distinct().count()
    return render(request, "pedidos/equipo/ajustes.html", {
        "form": form, "numero": numero, "de_prueba": numero == NUMERO_DE_PRUEBA, "actuales": actuales,
        "recetas_sin_pasos": recetas_sin_pasos, "formas_sin_armar": formas_sin_armar, "personas": personas,
    })
