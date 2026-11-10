"""Integración con el CRM Binn.

Dos modos, compatibles entre sí:

* PUSH (webhook): si BINN_WEBHOOK_URL está configurado, cada registro nuevo se
  envía en un hilo aparte, sin bloquear ni romper la respuesta al cliente.
  El cuerpo va firmado con HMAC-SHA256 (header X-Chesters-Signature) cuando
  BINN_WEBHOOK_SECRET está definido.
* PULL (API): Binn consulta /api/binn/... con el header X-Binn-Token
  (ver views.api_*). Útil también para reintentar lo que el webhook no entregó.
"""

import hashlib
import hmac
import json
import logging
import threading
import urllib.request

from django.conf import settings
from django.db import close_old_connections, transaction

logger = logging.getLogger(__name__)


def _firmar(cuerpo: bytes) -> str:
    secreto = settings.BINN_WEBHOOK_SECRET.encode()
    return hmac.new(secreto, cuerpo, hashlib.sha256).hexdigest()


def _enviar(modelo, pk):
    close_old_connections()
    try:
        obj = modelo.objects.get(pk=pk)
        cuerpo = json.dumps({"evento": f"{obj.to_crm()['tipo']}.creado", "datos": obj.to_crm()}).encode()
        req = urllib.request.Request(
            settings.BINN_WEBHOOK_URL,
            data=cuerpo,
            method="POST",
            headers={"Content-Type": "application/json", "User-Agent": "chesters-web/1.0"},
        )
        if settings.BINN_WEBHOOK_SECRET:
            req.add_header("X-Chesters-Signature", f"sha256={_firmar(cuerpo)}")
        with urllib.request.urlopen(req, timeout=8) as resp:
            if 200 <= resp.status < 300:
                obj.marcar_sincronizado()
    except Exception:  # noqa: BLE001 - nunca debe afectar al cliente
        logger.warning("No se pudo enviar %s #%s a Binn; quedará pendiente para la API.", modelo.__name__, pk, exc_info=True)
    finally:
        close_old_connections()


def notificar_binn(obj):
    """Envía el registro a Binn en segundo plano (si hay webhook configurado)."""
    if not settings.BINN_WEBHOOK_URL:
        return
    hilo = threading.Thread(target=_enviar, args=(type(obj), obj.pk), daemon=True)
    transaction.on_commit(hilo.start)
