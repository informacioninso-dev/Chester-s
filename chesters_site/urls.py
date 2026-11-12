from django.conf import settings
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from pedidos import views as pedidos_views
from pedidos.sitemaps import PaginasSitemap

admin.site.site_header = "Chester's · Panel de Melloco"
admin.site.site_title = "Chester's"
admin.site.index_title = "Pedidos y cumpleaños"

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("robots.txt", pedidos_views.robots_txt, name="robots"),
    path("sitemap.xml", sitemap, {"sitemaps": {"paginas": PaginasSitemap}}, name="sitemap"),
    path("", include("pedidos.urls")),
]
