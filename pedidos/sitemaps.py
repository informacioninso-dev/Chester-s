from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class PaginasSitemap(Sitemap):
    """Páginas públicas del sitio (spec 004)."""

    changefreq = "monthly"

    def items(self):
        return ["pedidos:index", "pedidos:privacidad"]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return 1.0 if item == "pedidos:index" else 0.3
