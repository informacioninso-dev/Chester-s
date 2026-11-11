import datetime
import json
from unittest import mock
from urllib.parse import parse_qs, urlparse

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Cotizacion, LeadCumple

HTMX = {"HTTP_HX_REQUEST": "true"}


def manana():
    return (timezone.localdate() + datetime.timedelta(days=1)).isoformat()


class IndexTests(TestCase):
    def test_landing_tiene_las_cuatro_secciones(self):
        r = self.client.get(reverse("pedidos:index"))
        self.assertContains(r, "Celebra su vida.")
        self.assertContains(r, "Crear el pastel de mi perrito")
        self.assertContains(r, 'id="configurador-panel"')
        self.assertContains(r, "La Ruleta de Melloco")
        self.assertContains(r, "nuestro mejor amigo <span class=\"italic\">barbón.</span>", html=False)
        self.assertContains(r, 'hx-post="/configurador/"')

    def test_sin_ids_duplicados(self):
        """El configurador y la ruleta conviven en la página: sus ids no deben chocar."""
        import re
        html = self.client.get(reverse("pedidos:index")).content.decode()
        ids = re.findall(r'id="([^"]+)"', html)
        duplicados = {i for i in ids if ids.count(i) > 1}
        self.assertEqual(duplicados, set())


class PrivacidadTests(TestCase):
    url = reverse("pedidos:privacidad")

    def test_pagina_de_politica(self):
        r = self.client.get(self.url)
        self.assertContains(r, "Política de privacidad")
        for seccion in ("Quién es responsable", "Qué datos guardamos", "Para qué los usamos",
                        "Con qué base legal", "Con quién los compartimos", "Cuánto tiempo", "Tus derechos"):
            self.assertContains(r, seccion)
        self.assertContains(r, "Binn")
        self.assertContains(r, "cdn.tailwindcss.com")  # mismo <head> que la landing

    def test_footer_y_ruleta_enlazan_la_politica(self):
        r = self.client.get(reverse("pedidos:index"))
        # Footer + texto de autorización de la Ruleta.
        self.assertContains(r, f'href="{self.url}"', count=2)

    def test_autorizacion_del_configurador_enlaza_la_politica(self):
        datos = {"paso": 3, "ir_a": 4, "nombre_perro": "Rocky", "fecha_cumple": manana(),
                 "receta": "carne_pure", "estilo": "huesito"}
        r = self.client.post(reverse("pedidos:configurador"), datos, **HTMX)
        self.assertContains(r, f'href="{self.url}"')


class ConfiguradorTests(TestCase):
    url = reverse("pedidos:configurador")

    def test_paso1_sin_datos_muestra_errores(self):
        r = self.client.post(self.url, {"paso": 1, "ir_a": 2}, **HTMX)
        self.assertContains(r, "¿Cómo se llama tu perrito?")
        self.assertContains(r, 'name="paso" value="1"')
        self.assertNotContains(r, "<html")  # solo el fragmento

    def test_errores_enlazados_a_su_campo(self):
        r = self.client.post(self.url, {"paso": 1, "ir_a": 2}, **HTMX)
        html = r.content.decode()
        self.assertIn('aria-describedby="id_nombre_perro_error"', html)
        self.assertIn('id="id_nombre_perro_error"', html)
        self.assertIn('id="id_fecha_cumple_helptext"', html)

    def test_fecha_pasada_no_se_acepta(self):
        ayer = (timezone.localdate() - datetime.timedelta(days=1)).isoformat()
        r = self.client.post(self.url, {"paso": 1, "ir_a": 2, "nombre_perro": "Rocky", "fecha_cumple": ayer}, **HTMX)
        self.assertContains(r, "Elige una fecha de hoy en adelante.")

    def test_avanza_y_conserva_datos_en_ocultos(self):
        r = self.client.post(self.url, {"paso": 1, "ir_a": 2, "nombre_perro": "Rocky", "fecha_cumple": manana()}, **HTMX)
        self.assertContains(r, 'name="paso" value="2"')
        self.assertContains(r, '<input type="hidden" name="nombre_perro" value="Rocky">', html=True)
        self.assertContains(r, "Carne y puré")
        self.assertNotContains(r, "Elige una receta")  # sin errores prematuros
        self.assertNotContains(r, 'aria-invalid')

    def test_paso2_requiere_receta(self):
        datos = {"paso": 2, "ir_a": 3, "nombre_perro": "Rocky", "fecha_cumple": manana()}
        r = self.client.post(self.url, datos, **HTMX)
        self.assertContains(r, "Elige una receta para continuar.")

    def test_atras_no_valida(self):
        r = self.client.post(self.url, {"paso": 3, "ir_a": 2, "nombre_perro": "Rocky", "fecha_cumple": manana(), "receta": "carne_pure"}, **HTMX)
        self.assertContains(r, 'name="paso" value="2"')
        self.assertContains(r, 'value="carne_pure" class="peer sr-only" checked')

    def test_paso4_muestra_resumen(self):
        datos = {"paso": 3, "ir_a": 4, "nombre_perro": "Rocky", "fecha_cumple": manana(), "receta": "manzana_zanahoria_yogur", "estilo": "redondo"}
        r = self.client.post(self.url, datos, **HTMX)
        self.assertContains(r, "Todo listo para la fiesta")
        self.assertContains(r, "Manzana, zanahoria y yogur")
        self.assertContains(r, 'hx-post="/configurador/confirmar/"')


class ConfirmarTests(TestCase):
    url = reverse("pedidos:confirmar")

    def datos(self, **extra):
        base = {
            "paso": 4, "nombre_perro": "Rocky", "fecha_cumple": "2099-12-15",
            "receta": "carne_pure", "estilo": "huesito",
            "nombre_cliente": "Ana", "telefono": "099 123-4567", "acepta_datos": "on",
        }
        base.update(extra)
        return base

    @override_settings(CHESTERS_WHATSAPP="593991112233")
    def test_guarda_cotizacion_y_dispara_whatsapp(self):
        r = self.client.post(self.url, self.datos(), **HTMX)
        self.assertEqual(r.status_code, 200)
        c = Cotizacion.objects.get()
        self.assertEqual((c.nombre_cliente, c.telefono, c.nombre_perro), ("Ana", "0991234567", "Rocky"))
        self.assertFalse(c.sincronizado_crm)

        url = json.loads(r["HX-Trigger-After-Settle"])["abrirWhatsapp"]["url"]
        partes = urlparse(url)
        self.assertEqual(partes.netloc + partes.path, "wa.me/593991112233")
        self.assertEqual(
            parse_qs(partes.query)["text"][0],
            "Hola Melloco, quiero confirmar el pastel de carne y puré en forma de huesito "
            "para el cumpleaños de Rocky el 15 de diciembre de 2099",
        )
        self.assertContains(r, "¡Casi listo! Solo falta enviarle el mensaje a Melloco.")
        self.assertContains(r, "el pedido de Rocky ya escrito")

    def test_sin_consentimiento_no_guarda(self):
        r = self.client.post(self.url, self.datos(acepta_datos=""), **HTMX)
        self.assertContains(r, "Marca la casilla de autorización para continuar.")
        self.assertEqual(Cotizacion.objects.count(), 0)

    def test_telefono_invalido(self):
        r = self.client.post(self.url, self.datos(telefono="abc"), **HTMX)
        self.assertContains(r, "Ingresa un número válido")
        self.assertEqual(Cotizacion.objects.count(), 0)

    def test_si_falta_un_paso_anterior_vuelve_a_el(self):
        r = self.client.post(self.url, self.datos(estilo=""), **HTMX)
        self.assertContains(r, 'name="paso" value="3"')
        self.assertContains(r, "Elige un estilo para continuar.")

    def test_sin_htmx_redirige_a_whatsapp(self):
        r = self.client.post(self.url, self.datos())
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r["Location"].startswith("https://wa.me/"))


class RuletaTests(TestCase):
    url = reverse("pedidos:ruleta")

    def test_registra_lead_y_muestra_exito(self):
        r = self.client.post(self.url, {
            "nombre_humano": "Ana", "nombre_perro": "Luna", "fecha_cumple": "2021-03-10",
            "telefono": "0991234567", "acepta_datos": "on",
        }, **HTMX)
        self.assertContains(r, "¡Melloco ha guardado la fecha! Te escribiremos pronto.")
        self.assertEqual(LeadCumple.objects.get().nombre_perro, "Luna")

    def test_errores(self):
        r = self.client.post(self.url, {}, **HTMX)
        self.assertContains(r, "Cuéntanos tu nombre.")
        self.assertEqual(LeadCumple.objects.count(), 0)

    def test_fecha_regalo_15_dias_antes_del_proximo_cumple(self):
        lead = LeadCumple(fecha_cumple=datetime.date(2020, 3, 10))
        self.assertEqual(lead.fecha_regalo(hoy=datetime.date(2026, 11, 10)), datetime.date(2027, 2, 23))
        self.assertEqual(lead.fecha_regalo(hoy=datetime.date(2026, 1, 5)), datetime.date(2026, 2, 23))

    def test_29_de_febrero(self):
        lead = LeadCumple(fecha_cumple=datetime.date(2020, 2, 29))
        self.assertEqual(lead.proximo_cumple(hoy=datetime.date(2026, 1, 1)), datetime.date(2026, 2, 28))


@override_settings(BINN_API_TOKEN="secreto")
class ApiBinnTests(TestCase):
    def setUp(self):
        self.lead = LeadCumple.objects.create(nombre_humano="Ana", nombre_perro="Luna", fecha_cumple=datetime.date(2021, 3, 10), telefono="0991234567")

    def test_requiere_token(self):
        self.assertEqual(self.client.get(reverse("pedidos:api_leads")).status_code, 401)

    @override_settings(BINN_API_TOKEN="")
    def test_deshabilitada_sin_token_configurado(self):
        self.assertEqual(self.client.get(reverse("pedidos:api_leads")).status_code, 503)

    def test_lista_y_marca_sincronizados(self):
        h = {"HTTP_X_BINN_TOKEN": "secreto"}
        r = self.client.get(reverse("pedidos:api_leads") + "?pendientes=1", **h)
        self.assertEqual(r.json()["resultados"][0]["nombre_perro"], "Luna")
        self.assertIn("fecha_regalo", r.json()["resultados"][0])

        r = self.client.post(reverse("pedidos:api_sincronizados"), json.dumps({"leads": [self.lead.pk]}), content_type="application/json", **h)
        self.assertEqual(r.json(), {"leads": 1, "cotizaciones": 0})
        r = self.client.get(reverse("pedidos:api_leads") + "?pendientes=1", **h)
        self.assertEqual(r.json()["resultados"], [])


class WebhookBinnTests(TestCase):
    @override_settings(BINN_WEBHOOK_URL="https://binn.example/webhook", BINN_WEBHOOK_SECRET="s")
    def test_envia_webhook_y_marca_sincronizado(self):
        respuesta = mock.MagicMock(status=200)
        respuesta.__enter__.return_value = respuesta
        with mock.patch("pedidos.crm.urllib.request.urlopen", return_value=respuesta) as urlopen, \
             mock.patch("pedidos.crm.threading.Thread") as Thread:
            Thread.side_effect = lambda target, args, daemon: mock.MagicMock(start=lambda: target(*args))
            with self.captureOnCommitCallbacks(execute=True):
                self.client.post(reverse("pedidos:ruleta"), {
                    "nombre_humano": "Ana", "nombre_perro": "Luna", "fecha_cumple": "2021-03-10",
                    "telefono": "0991234567", "acepta_datos": "on",
                }, **HTMX)
        req = urlopen.call_args.args[0]
        self.assertEqual(json.loads(req.data)["evento"], "lead_cumple.creado")
        self.assertTrue(req.get_header("X-chesters-signature").startswith("sha256="))
        self.assertTrue(LeadCumple.objects.get().sincronizado_crm)
