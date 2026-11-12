from django.contrib.auth.views import LogoutView
from django.urls import path, reverse_lazy

from . import views, views_equipo

app_name = "pedidos"

urlpatterns = [
    path("", views.index, name="index"),
    path("privacidad/", views.privacidad, name="privacidad"),
    # Fragmentos HTMX
    path("configurador/", views.configurador, name="configurador"),
    path("configurador/confirmar/", views.confirmar_pedido, name="confirmar"),
    path("ruleta/", views.registrar_lead, name="ruleta"),
    path("chat/", views.chat, name="chat"),
    # Gestor del equipo (spec 010)
    path("equipo/", views_equipo.pedidos, name="equipo"),
    path("equipo/ingresar/", views_equipo.Ingresar.as_view(), name="equipo_ingresar"),
    path("equipo/salir/", LogoutView.as_view(next_page=reverse_lazy("pedidos:equipo_ingresar")), name="equipo_salir"),
    path("equipo/pedido/<int:pk>/", views_equipo.pedido, name="equipo_pedido"),
    path("equipo/pedido/<int:pk>/accion/", views_equipo.accion, name="equipo_accion"),
    path("equipo/perritos/", views_equipo.perritos, name="equipo_perritos"),
    path("equipo/perrito/<int:pk>/", views_equipo.ficha, name="equipo_ficha"),
    # API para el CRM Binn
    path("api/binn/leads/", views.api_leads, name="api_leads"),
    path("api/binn/cotizaciones/", views.api_cotizaciones, name="api_cotizaciones"),
    path("api/binn/sincronizados/", views.api_marcar_sincronizados, name="api_sincronizados"),
]
