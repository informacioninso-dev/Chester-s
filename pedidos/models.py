import datetime

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

telefono_validator = RegexValidator(
    regex=r"^\+?\d{9,15}$",
    message="Ingresa un número válido, solo dígitos (ej. 0991234567).",
)


class Receta(models.TextChoices):
    CARNE_PURE = "carne_pure", "Carne y puré"
    MANZANA_ZANAHORIA_YOGUR = "manzana_zanahoria_yogur", "Manzana, zanahoria y yogur"


class Estilo(models.TextChoices):
    HUESITO = "huesito", "Huesito"
    REDONDO = "redondo", "Redondo"


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


class Cotizacion(SincronizableCRM):
    """Pedido armado en el configurador y enviado a Melloco por WhatsApp."""

    nombre_cliente = models.CharField("nombre del cliente", max_length=120)
    telefono = models.CharField(
        "WhatsApp", max_length=20, validators=[telefono_validator]
    )
    nombre_perro = models.CharField("nombre del perrito", max_length=80)
    fecha_cumple = models.DateField("fecha del cumpleaños")
    receta = models.CharField(max_length=40, choices=Receta.choices)
    estilo = models.CharField(max_length=20, choices=Estilo.choices)

    class Meta:
        ordering = ["-creado_en"]
        verbose_name = "cotización"
        verbose_name_plural = "cotizaciones"

    def __str__(self):
        return f"{self.nombre_perro} · {self.get_receta_display()} ({self.fecha_cumple:%d/%m/%Y})"

    def to_crm(self):
        return {
            "tipo": "cotizacion",
            "id": self.pk,
            "nombre_cliente": self.nombre_cliente,
            "telefono": self.telefono,
            "nombre_perro": self.nombre_perro,
            "fecha_cumple": self.fecha_cumple.isoformat(),
            "receta": self.receta,
            "receta_nombre": self.get_receta_display(),
            "estilo": self.estilo,
            "estilo_nombre": self.get_estilo_display(),
            "creado_en": self.creado_en.isoformat(),
        }


class LeadCumple(SincronizableCRM):
    """Registro de 'La Ruleta de Melloco': regalo sorpresa antes del cumpleaños."""

    nombre_humano = models.CharField("nombre del humano", max_length=120)
    nombre_perro = models.CharField("nombre del perrito", max_length=80)
    fecha_cumple = models.DateField("fecha de cumpleaños")
    telefono = models.CharField(
        "teléfono", max_length=20, validators=[telefono_validator]
    )

    class Meta:
        ordering = ["-creado_en"]
        verbose_name = "lead de cumpleaños"
        verbose_name_plural = "leads de cumpleaños"

    def __str__(self):
        return f"{self.nombre_perro} ({self.nombre_humano})"

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
            "creado_en": self.creado_en.isoformat(),
        }
