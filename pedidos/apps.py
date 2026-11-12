from django.apps import AppConfig


class PedidosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pedidos"
    verbose_name = "Chester's · Pedidos"

    def ready(self):
        from . import seguridad  # noqa: F401  (conecta el freno de intentos al ingresar, spec 016)
