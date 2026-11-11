from django.urls import path

from . import views

app_name = "pedidos"

urlpatterns = [
    path("", views.index, name="index"),
    path("privacidad/", views.privacidad, name="privacidad"),
    # Fragmentos HTMX
    path("configurador/", views.configurador, name="configurador"),
    path("configurador/confirmar/", views.confirmar_pedido, name="confirmar"),
    path("ruleta/", views.registrar_lead, name="ruleta"),
    # API para el CRM Binn
    path("api/binn/leads/", views.api_leads, name="api_leads"),
    path("api/binn/cotizaciones/", views.api_cotizaciones, name="api_cotizaciones"),
    path("api/binn/sincronizados/", views.api_marcar_sincronizados, name="api_sincronizados"),
]
