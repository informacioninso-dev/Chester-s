from django.contrib import admin
from django.utils.html import format_html

from .models import Cotizacion, LeadCumple, Perrito


class WhatsAppClienteMixin:
    @admin.display(description="contacto")
    def escribir_whatsapp(self, obj):
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">Escribir por WhatsApp</a>',
            obj.url_whatsapp_cliente,
        )


@admin.register(Cotizacion)
class CotizacionAdmin(WhatsAppClienteMixin, admin.ModelAdmin):
    list_display = ("nombre_perro", "fecha_cumple", "estado", "receta", "estilo", "nombre_cliente",
                    "telefono", "escribir_whatsapp", "sincronizado_crm", "creado_en")
    list_display_links = ("nombre_perro",)
    list_editable = ("estado",)
    list_filter = ("estado", "receta", "estilo", "cocinero", "repartidor", "sincronizado_crm", "fecha_cumple")
    search_fields = ("nombre_perro", "nombre_cliente", "telefono")
    date_hierarchy = "fecha_cumple"
    readonly_fields = ("creado_en", "consentimiento_en", "sincronizado_crm", "sincronizado_en")
    autocomplete_fields = ("perrito",)


@admin.register(LeadCumple)
class LeadCumpleAdmin(WhatsAppClienteMixin, admin.ModelAdmin):
    list_display = ("nombre_perro", "nombre_humano", "fecha_cumple", "regalo", "regalo_enviado",
                    "telefono", "escribir_whatsapp", "sincronizado_crm", "creado_en")
    list_display_links = ("nombre_perro",)
    list_editable = ("regalo_enviado",)
    list_filter = ("regalo_enviado", "sincronizado_crm")
    search_fields = ("nombre_perro", "nombre_humano", "telefono")
    readonly_fields = ("creado_en", "consentimiento_en", "sincronizado_crm", "sincronizado_en")

    autocomplete_fields = ("perrito",)

    @admin.display(description="enviar regalo el")
    def regalo(self, obj):
        return obj.fecha_regalo()


@admin.register(Perrito)
class PerritoAdmin(WhatsAppClienteMixin, admin.ModelAdmin):
    """Fichas de los perritos (spec 010). El equipo las edita en /equipo/; aquí, correcciones."""

    list_display = ("nombre", "familia", "telefono", "raza", "tamano", "escribir_whatsapp", "actualizado_en")
    list_filter = ("tamano",)
    search_fields = ("nombre", "familia", "telefono")
    readonly_fields = ("creado_en", "actualizado_en")
