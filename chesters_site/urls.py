from django.conf import settings
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Chester's · Panel de Melloco"
admin.site.site_title = "Chester's"
admin.site.index_title = "Pedidos y cumpleaños"

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("", include("pedidos.urls")),
]
