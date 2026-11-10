from django.contrib import admin

from .models import Cotizacion, LeadCumple


@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ("nombre_perro", "fecha_cumple", "receta", "estilo", "nombre_cliente", "telefono", "sincronizado_crm", "creado_en")
    list_filter = ("receta", "estilo", "sincronizado_crm", "fecha_cumple")
    search_fields = ("nombre_perro", "nombre_cliente", "telefono")
    date_hierarchy = "fecha_cumple"
    readonly_fields = ("creado_en", "consentimiento_en", "sincronizado_en")


@admin.register(LeadCumple)
class LeadCumpleAdmin(admin.ModelAdmin):
    list_display = ("nombre_perro", "nombre_humano", "fecha_cumple", "regalo", "telefono", "sincronizado_crm", "creado_en")
    list_filter = ("sincronizado_crm",)
    search_fields = ("nombre_perro", "nombre_humano", "telefono")
    readonly_fields = ("creado_en", "consentimiento_en", "sincronizado_en")

    @admin.display(description="enviar regalo el")
    def regalo(self, obj):
        return obj.fecha_regalo()
