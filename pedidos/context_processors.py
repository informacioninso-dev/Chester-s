"""Datos para las etiquetas SEO del <head> (spec 004)."""

from django.templatetags.static import static
from django.urls import reverse

# Rutas de HTMX que, abiertas sin JavaScript, muestran la portada: su canónica es "/".
PAGINAS_PROPIAS = {"privacidad"}


def seo(request):
    nombre = getattr(request.resolver_match, "url_name", None)
    ruta = reverse(f"pedidos:{nombre}") if nombre in PAGINAS_PROPIAS else reverse("pedidos:index")
    return {
        "url_canonica": request.build_absolute_uri(ruta),
        "url_inicio": request.build_absolute_uri(reverse("pedidos:index")),
        "og_imagen": request.build_absolute_uri(static("pedidos/img/logo.jpg")),
    }
