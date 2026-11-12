import datetime
import unicodedata

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

telefono_validator = RegexValidator(
    regex=r"^\+?\d{9,15}$",
    message="Ingresa un número válido, solo dígitos (ej. 0991234567).",
)


def _lineas(texto):
    return [linea.strip(" -•	") for linea in (texto or "").splitlines() if linea.strip(" -•	")]


class DelRecetario(models.Model):
    """Lo común a recetas y formas del Recetario (spec 013): lo ve el cliente y lo sigue la cocina."""

    clave = models.SlugField("clave", max_length=40, unique=True, editable=False)
    nombre = models.CharField("nombre", max_length=80)
    descripcion = models.CharField("descripción para el cliente", max_length=140, blank=True)
    notas = models.TextField("notas para la cocina", blank=True, max_length=1000)
    disponible = models.BooleanField("disponible para clientes", default=False, db_index=True)
    orden = models.PositiveSmallIntegerField("orden", default=0)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.clave:  # se fija al crear y no cambia: la usan el formulario, el chat y Binn
            base = slugify(self.nombre).replace("-", "_")[:34] or "item"
            clave, n = base, 2
            while type(self).objects.filter(clave=clave).exists():
                clave, n = f"{base}_{n}", n + 1
            self.clave = clave
        super().save(*args, **kwargs)


class Receta(DelRecetario):
    ingredientes = models.TextField("ingredientes", blank=True, max_length=2000,
                                    help_text="Uno por línea, con su cantidad.")
    pasos = models.TextField("pasos", blank=True, max_length=4000, help_text="Uno por línea, en orden.")
    contiene = models.CharField("contiene (alérgenos)", max_length=200, blank=True,
                                help_text="Ej.: Lácteos (yogur), huevo.")

    class Meta(DelRecetario.Meta):
        verbose_name = "receta"
        verbose_name_plural = "recetas"

    def lista_ingredientes(self):
        return _lineas(self.ingredientes)

    def lista_pasos(self):
        return _lineas(self.pasos)


class Forma(DelRecetario):
    frase_mensaje = models.CharField("cómo se dice en el mensaje", max_length=80, blank=True,
                                     help_text="Ej.: en forma de huesito")
    como_armarla = models.TextField("cómo armarla", blank=True, max_length=2000,
                                    help_text="Molde, decoración y terminado. Uno por línea.")

    class Meta(DelRecetario.Meta):
        verbose_name = "forma"
        verbose_name_plural = "formas"

    def frase(self):
        return self.frase_mensaje or f"en forma de {self.nombre.lower()}"

    def lista_como_armarla(self):
        return _lineas(self.como_armarla)


class FormaPago(models.TextChoices):
    EFECTIVO = "efectivo", "Efectivo"
    TRANSFERENCIA = "transferencia", "Transferencia"
    OTRO = "otro", "Otro"


class EstadoPedido(models.TextChoices):
    NUEVO = "nuevo", "Nuevo"
    CONFIRMADO = "confirmado", "Confirmado"
    EN_PREPARACION = "en_preparacion", "En preparación"
    ENTREGADO = "entregado", "Entregado"
    CANCELADO = "cancelado", "Cancelado"


def whatsapp_internacional(telefono):
    """'0991234567' -> '593991234567' (Ecuador). Números con código de país quedan igual."""
    digitos = "".join(c for c in telefono or "" if c.isdigit())
    if digitos.startswith("0"):
        return "593" + digitos[1:]
    return digitos


def clave_nombre(nombre):
    """'  Rocky Bálboa ' -> 'rocky balboa': sin mayúsculas, tildes ni espacios de más."""
    sin_tildes = unicodedata.normalize("NFKD", nombre or "")
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    return " ".join(sin_tildes.lower().split())


class ConWhatsAppCliente:
    @property
    def url_whatsapp_cliente(self):
        return f"https://wa.me/{whatsapp_internacional(self.telefono)}"


class Tamano(models.TextChoices):
    PEQUENO = "pequeno", "Pequeño"
    MEDIANO = "mediano", "Mediano"
    GRANDE = "grande", "Grande"


class Perrito(ConWhatsAppCliente, models.Model):
    """Ficha de cada perrito (spec 010): junta sus pedidos y su cumpleaños, y lo que sabemos de él.

    Mismo WhatsApp + mismo nombre (sin mayúsculas, tildes ni espacios) = mismo perrito.
    """

    nombre = models.CharField("nombre", max_length=80)
    nombre_clave = models.CharField(max_length=80, editable=False)
    telefono = models.CharField("WhatsApp", max_length=20)
    telefono_clave = models.CharField(max_length=20, editable=False)
    familia = models.CharField("familia", max_length=120, blank=True)
    raza = models.CharField("raza", max_length=60, blank=True)
    tamano = models.CharField("tamaño", max_length=10, choices=Tamano.choices, blank=True)
    le_encanta = models.TextField("le encanta", blank=True, max_length=500)
    no_le_gusta = models.TextField("no le gusta / alergias", blank=True, max_length=500)
    notas = models.TextField("notas", blank=True, max_length=1000)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "perrito"
        verbose_name_plural = "perritos"
        constraints = [
            models.UniqueConstraint(fields=["telefono_clave", "nombre_clave"], name="perrito_unico_por_familia"),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.familia or self.telefono})"

    @classmethod
    def de(cls, telefono, nombre, familia=""):
        """Ficha del perrito de ese WhatsApp con ese nombre; la crea si no existe."""
        perrito, creado = cls.objects.get_or_create(
            telefono_clave=whatsapp_internacional(telefono),
            nombre_clave=clave_nombre(nombre),
            defaults={"nombre": " ".join((nombre or "").split()), "telefono": telefono, "familia": familia},
        )
        if not creado and familia and not perrito.familia:
            perrito.familia = familia
            perrito.save(update_fields=["familia", "actualizado_en"])
        return perrito


class ConFichaDePerrito(models.Model):
    """Pedidos y cumpleaños se enlazan solos a la ficha de su perrito al guardarse."""

    perrito = models.ForeignKey(Perrito, null=True, blank=True, on_delete=models.SET_NULL,
                                related_name="%(class)s_set", verbose_name="ficha del perrito")

    class Meta:
        abstract = True

    def nombre_familia(self):
        raise NotImplementedError

    def save(self, *args, **kwargs):
        if self.perrito_id is None and self.telefono and self.nombre_perro:
            self.perrito = Perrito.de(self.telefono, self.nombre_perro, self.nombre_familia())
        super().save(*args, **kwargs)


class SincronizableCRM(models.Model):
    """Campos comunes para la sincronización con el CRM Binn."""

    creado_en = models.DateTimeField(auto_now_add=True, db_index=True)
    # LOPDP: dejamos constancia de cuándo la persona aceptó el tratamiento de datos.
    consentimiento_en = models.DateTimeField(
        "consentimiento de datos", default=timezone.now
    )
    sincronizado_crm = models.BooleanField(
        "sincronizado con Binn", default=False, db_index=True
    )
    sincronizado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def marcar_sincronizado(self):
        self.sincronizado_crm = True
        self.sincronizado_en = timezone.now()
        self.save(update_fields=["sincronizado_crm", "sincronizado_en"])


class Cotizacion(ConWhatsAppCliente, ConFichaDePerrito, SincronizableCRM):
    """Pedido armado en el configurador y enviado a Melloco por WhatsApp."""

    nombre_cliente = models.CharField("nombre del cliente", max_length=120)
    telefono = models.CharField(
        "WhatsApp", max_length=20, validators=[telefono_validator]
    )
    nombre_perro = models.CharField("nombre del perrito", max_length=80)
    fecha_cumple = models.DateField("fecha del cumpleaños")
    receta = models.ForeignKey(Receta, on_delete=models.PROTECT, related_name="pedidos", verbose_name="receta")
    estilo = models.ForeignKey(Forma, on_delete=models.PROTECT, related_name="pedidos", verbose_name="forma")
    estado = models.CharField(
        max_length=20, choices=EstadoPedido.choices, default=EstadoPedido.NUEVO, db_index=True
    )
    # Spec 010: lo que la familia nos contó al pedir (alergias, gustos). Opcional.
    nota_familia = models.TextField("lo que nos contó la familia", blank=True, max_length=300)
    cocinero = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                 related_name="pedidos_en_cocina", verbose_name="lo cocina")
    repartidor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name="pedidos_en_reparto", verbose_name="lo reparte")
    # Spec 011: la entrega la coordina el equipo por WhatsApp y la anota en el gestor.
    direccion_entrega = models.TextField("dirección de entrega", blank=True, max_length=300)
    hora_entrega = models.TimeField("hora de entrega", null=True, blank=True)
    # Spec 015: el cobro va aparte del estado (puede haber un anticipo antes de entregar).
    cobrado = models.BooleanField("cobrado", default=False, db_index=True)
    cobrado_en = models.DateTimeField("cobrado el", null=True, blank=True)
    cobrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="pedidos_cobrados", verbose_name="lo cobró")
    monto_cobrado = models.DecimalField("monto cobrado", max_digits=8, decimal_places=2, null=True, blank=True)
    forma_pago = models.CharField("forma de pago", max_length=15, choices=FormaPago.choices, blank=True)

    class Meta:
        ordering = ["-creado_en"]
        verbose_name = "cotización"
        verbose_name_plural = "cotizaciones"

    def __str__(self):
        return f"{self.nombre_perro} · {self.receta.nombre} ({self.fecha_cumple:%d/%m/%Y})"

    def nombre_familia(self):
        return self.nombre_cliente

    def to_crm(self):
        return {
            "tipo": "cotizacion",
            "id": self.pk,
            "nombre_cliente": self.nombre_cliente,
            "telefono": self.telefono,
            "nombre_perro": self.nombre_perro,
            "fecha_cumple": self.fecha_cumple.isoformat(),
            "receta": self.receta.clave,
            "receta_nombre": self.receta.nombre,
            "estilo": self.estilo.clave,
            "estilo_nombre": self.estilo.nombre,
            "estado": self.estado,
            "estado_nombre": self.get_estado_display(),
            "nota_familia": self.nota_familia,
            "cobrado": self.cobrado,
            "monto_cobrado": str(self.monto_cobrado) if self.monto_cobrado is not None else None,
            "forma_pago": self.forma_pago,
            "creado_en": self.creado_en.isoformat(),
        }


class LeadCumple(ConWhatsAppCliente, ConFichaDePerrito, SincronizableCRM):
    """Registro de 'La Ruleta de Melloco': regalo sorpresa antes del cumpleaños."""

    nombre_humano = models.CharField("nombre del humano", max_length=120)
    nombre_perro = models.CharField("nombre del perrito", max_length=80)
    fecha_cumple = models.DateField("fecha de cumpleaños")
    telefono = models.CharField(
        "teléfono", max_length=20, validators=[telefono_validator]
    )

    regalo_enviado = models.BooleanField("regalo enviado", default=False, db_index=True)

    class Meta:
        ordering = ["-creado_en"]
        verbose_name = "lead de cumpleaños"
        verbose_name_plural = "leads de cumpleaños"

    def __str__(self):
        return f"{self.nombre_perro} ({self.nombre_humano})"

    def nombre_familia(self):
        return self.nombre_humano

    def proximo_cumple(self, hoy=None):
        """Próxima fecha en que se celebra el cumpleaños (hoy cuenta)."""
        hoy = hoy or timezone.localdate()
        for anio in (hoy.year, hoy.year + 1):
            try:
                fecha = self.fecha_cumple.replace(year=anio)
            except ValueError:  # 29 de febrero en año no bisiesto
                fecha = datetime.date(anio, 2, 28)
            if fecha >= hoy:
                return fecha
        return fecha

    def fecha_regalo(self, hoy=None):
        """Día en que Melloco debe enviar el regalo sorpresa."""
        dias = getattr(settings, "CHESTERS_DIAS_REGALO", 15)
        return self.proximo_cumple(hoy) - datetime.timedelta(days=dias)

    def to_crm(self):
        return {
            "tipo": "lead_cumple",
            "id": self.pk,
            "nombre_humano": self.nombre_humano,
            "nombre_perro": self.nombre_perro,
            "telefono": self.telefono,
            "fecha_cumple": self.fecha_cumple.isoformat(),
            "proximo_cumple": self.proximo_cumple().isoformat(),
            "fecha_regalo": self.fecha_regalo().isoformat(),
            "regalo_enviado": self.regalo_enviado,
            "creado_en": self.creado_en.isoformat(),
        }


# ---------------------------------------------------------------------------
# Ajustes del negocio (spec 019): los cambia el administrador desde el gestor.
# ---------------------------------------------------------------------------

NUMERO_DE_PRUEBA = "593990000000"


class Ajustes(models.Model):
    """Una sola fila (pk=1). Lo que no esté aquí sale de las variables del servidor."""

    whatsapp = models.CharField("WhatsApp de Melloco", max_length=15, blank=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    actualizado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                        related_name="+", verbose_name="actualizado por")

    class Meta:
        verbose_name = "ajustes"
        verbose_name_plural = "ajustes"

    def __str__(self):
        return "Ajustes del negocio"

    @classmethod
    def actuales(cls):
        return cls.objects.get_or_create(pk=1)[0]


def whatsapp_melloco():
    """Número al que llegan los pedidos: el de Ajustes; si nadie lo configuró, el del servidor."""
    numero = Ajustes.objects.filter(pk=1).values_list("whatsapp", flat=True).first()
    return numero or settings.CHESTERS_WHATSAPP
