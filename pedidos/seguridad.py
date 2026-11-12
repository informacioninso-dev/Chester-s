"""Freno de intentos al ingresar (spec 016).

Cuenta los ingresos fallidos por conexión (IP) y por usuario. Al pasar el límite, el ingreso se
bloquea durante la ventana, aunque luego se escriba la contraseña correcta. Un ingreso correcto
reinicia los contadores. Aplica al gestor (/equipo/ingresar/) y al panel de Django.
"""

from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.dispatch import receiver

LIMITE_POR_IP = 10
LIMITE_POR_USUARIO = 20
VENTANA = 15 * 60  # segundos

MENSAJE = ("Demasiados intentos fallidos. Por seguridad, espera 15 minutos y vuelve a intentarlo. "
           "Si olvidaste tu contraseña, pídele al administrador una nueva.")


def _ip(request):
    if request is None:
        return ""
    from .views import _ip as ip_real  # misma regla que el freno de formularios (spec 002)
    return ip_real(request)


def _claves(request, usuario):
    claves = []
    ip = _ip(request)
    if ip:
        claves.append((f"ingreso:ip:{ip}", LIMITE_POR_IP))
    usuario = " ".join((usuario or "").split()).lower()
    if usuario:
        claves.append((f"ingreso:usuario:{usuario}", LIMITE_POR_USUARIO))
    return claves


def bloqueado(request, usuario):
    return any((cache.get(clave) or 0) >= limite for clave, limite in _claves(request, usuario))


def _sumar(clave):
    if cache.add(clave, 1, VENTANA):
        return
    try:
        cache.incr(clave)
    except ValueError:  # expiró entre add() e incr()
        cache.set(clave, 1, VENTANA)


@receiver(user_login_failed)
def contar_fallo(sender, credentials, request=None, **kwargs):
    for clave, _ in _claves(request, credentials.get("username", "")):
        _sumar(clave)


@receiver(user_logged_in)
def reiniciar(sender, request, user, **kwargs):
    for clave, _ in _claves(request, user.get_username()):
        cache.delete(clave)


class FrenoDeIntentos:
    """Mezclar antes de AuthenticationForm: revisa el bloqueo antes de autenticar."""

    def clean(self):
        if bloqueado(self.request, self.data.get("username", "")):
            raise ValidationError(MENSAJE, code="demasiados_intentos")
        return super().clean()
