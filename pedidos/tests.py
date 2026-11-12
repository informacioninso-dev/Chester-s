import datetime
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest import mock
from urllib.parse import parse_qs, urlparse

from django.core.cache import cache
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
        self.assertContains(r, "Su cumpleaños también merece pastel.")
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
        self.assertContains(r, "pedidos/css/chesters.css")  # mismo <head> que la landing

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
        self.assertContains(r, "Bajo el control de calidad de Melloco.")


class ConfirmarTests(TestCase):
    url = reverse("pedidos:confirmar")

    def setUp(self):
        cache.clear()

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
        self.assertContains(r, "te responde por ahí")

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

    def setUp(self):
        cache.clear()

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


# ---------------------------------------------------------------------------
# Spec 002 · Seguridad
# ---------------------------------------------------------------------------

RAIZ = Path(__file__).resolve().parent.parent
LEAD = {"nombre_humano": "Ana", "nombre_perro": "Luna", "fecha_cumple": "2021-03-10",
        "telefono": "0991234567", "acepta_datos": "on"}
PEDIDO = {"paso": 4, "nombre_perro": "Rocky", "fecha_cumple": "2099-12-15", "receta": "carne_pure",
          "estilo": "huesito", "nombre_cliente": "Ana", "telefono": "0991234567", "acepta_datos": "on"}


def correr_django(*args, **env):
    """Ejecuta manage.py en un proceso aparte con las variables de entorno dadas."""
    entorno = {k: v for k, v in os.environ.items() if not k.startswith("DJANGO_")}
    entorno.update(env)
    return subprocess.run([sys.executable, "manage.py", *args], cwd=RAIZ, env=entorno,
                          capture_output=True, text=True, timeout=60)


class ConfiguracionProduccionTests(TestCase):
    def test_sin_secret_key_en_produccion_no_arranca(self):
        r = correr_django("check", DJANGO_DEBUG="0")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Define DJANGO_SECRET_KEY", r.stderr)

    def test_check_deploy_sin_advertencias(self):
        r = correr_django("check", "--deploy", "--fail-level", "WARNING",
                          DJANGO_DEBUG="0", DJANGO_SECRET_KEY="k" * 60 + "-x_9#Q",
                          DJANGO_ALLOWED_HOSTS="chesters.ec")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_admin_en_la_ruta_configurada(self):
        from django.conf import settings
        self.assertEqual(reverse("admin:index"), "/" + settings.ADMIN_URL)

    def test_htmx_desde_estaticos_propios(self):
        r = self.client.get(reverse("pedidos:index"))
        self.assertContains(r, "/static/pedidos/js/htmx.min.js")
        self.assertNotContains(r, "unpkg.com")


@override_settings(CHESTERS_LIMITE_ENVIOS=2)
class LimiteEnviosTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_ruleta_frena_al_pasar_el_limite(self):
        for _ in range(2):
            self.assertEqual(self.client.post(reverse("pedidos:ruleta"), LEAD, **HTMX).status_code, 200)
        r = self.client.post(reverse("pedidos:ruleta"), LEAD, **HTMX)
        self.assertEqual(r.status_code, 429)
        self.assertContains(r, "Recibimos varios envíos seguidos", status_code=429)
        self.assertContains(r, 'value="Luna"', status_code=429)  # no se pierde lo escrito
        self.assertEqual(LeadCumple.objects.count(), 2)

    def test_pedido_frena_al_pasar_el_limite(self):
        for _ in range(2):
            self.client.post(reverse("pedidos:confirmar"), PEDIDO, **HTMX)
        r = self.client.post(reverse("pedidos:confirmar"), PEDIDO, **HTMX)
        self.assertEqual(r.status_code, 429)
        self.assertContains(r, "Recibimos varios envíos seguidos", status_code=429)
        self.assertContains(r, 'value="Rocky"', status_code=429)
        self.assertEqual(Cotizacion.objects.count(), 2)

    def test_los_errores_de_validacion_no_cuentan(self):
        for _ in range(5):
            self.client.post(reverse("pedidos:ruleta"), {}, **HTMX)
        self.assertEqual(self.client.post(reverse("pedidos:ruleta"), LEAD, **HTMX).status_code, 200)

    @override_settings(DETRAS_DE_PROXY=True)
    def test_detras_de_proxy_cuenta_la_ip_que_agrega_el_proxy(self):
        for i in range(2):
            self.client.post(reverse("pedidos:ruleta"), LEAD, HTTP_X_FORWARDED_FOR=f"1.1.1.{i}, 9.9.9.9", **HTMX)
        r = self.client.post(reverse("pedidos:ruleta"), LEAD, HTTP_X_FORWARDED_FOR="5.5.5.5, 9.9.9.9", **HTMX)
        self.assertEqual(r.status_code, 429)


@override_settings(BINN_WEBHOOK_URL="https://binn.example/webhook")
class CampoTrampaTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_ruleta_con_trampa_responde_bien_pero_no_guarda(self):
        with mock.patch("pedidos.views.notificar_binn") as notificar:
            r = self.client.post(reverse("pedidos:ruleta"), {**LEAD, "sitio_web": "http://spam"}, **HTMX)
        self.assertContains(r, "¡Melloco ha guardado la fecha!")
        self.assertEqual(LeadCumple.objects.count(), 0)
        notificar.assert_not_called()

    def test_pedido_con_trampa_responde_bien_pero_no_guarda(self):
        with mock.patch("pedidos.views.notificar_binn") as notificar:
            r = self.client.post(reverse("pedidos:confirmar"), {**PEDIDO, "sitio_web": "x"}, **HTMX)
        self.assertEqual(r.status_code, 200)
        self.assertIn("abrirWhatsapp", r["HX-Trigger-After-Settle"])
        self.assertEqual(Cotizacion.objects.count(), 0)
        notificar.assert_not_called()

    def test_formularios_incluyen_el_campo_trampa(self):
        self.assertContains(self.client.get(reverse("pedidos:index")), 'name="sitio_web"', count=1)
        r = self.client.post(reverse("pedidos:configurador"),
                             {**PEDIDO, "paso": 3, "ir_a": 4}, **HTMX)
        self.assertContains(r, 'name="sitio_web"')


@override_settings(BINN_API_TOKEN="secreto")
class ApiLimiteTests(TestCase):
    def test_limite_fuera_de_rango_no_da_500(self):
        LeadCumple.objects.create(nombre_humano="Ana", nombre_perro="Luna",
                                  fecha_cumple=datetime.date(2021, 3, 10), telefono="0991234567")
        for valor in ("-1", "0", "abc", "999999"):
            r = self.client.get(reverse("pedidos:api_leads") + f"?limite={valor}", HTTP_X_BINN_TOKEN="secreto")
            self.assertEqual(r.status_code, 200, valor)
            self.assertEqual(len(r.json()["resultados"]), 1, valor)


# ---------------------------------------------------------------------------
# Spec 003 · Rendimiento
# ---------------------------------------------------------------------------

class RendimientoTests(TestCase):
    def test_usa_css_compilado_y_no_el_cdn_de_tailwind(self):
        r = self.client.get(reverse("pedidos:index"))
        self.assertNotContains(r, "cdn.tailwindcss.com")
        self.assertContains(r, 'href="/static/pedidos/css/chesters.css"')
        self.assertTrue((RAIZ / "pedidos/static/pedidos/css/chesters.css").stat().st_size > 1000)

    def test_imagenes_en_webp_con_respaldo_jpg(self):
        r = self.client.get(reverse("pedidos:index"))
        for archivo in ("logo-640.webp", "logo.webp", "chester-avatar-96.webp", "chester-avatar.webp"):
            self.assertContains(r, f"/static/pedidos/img/{archivo}")
            self.assertTrue((RAIZ / "pedidos/static/pedidos/img" / archivo).exists(), archivo)
        self.assertContains(r, 'type="image/webp"', count=3)  # menú, portada e historia (Melloco es SVG)
        self.assertContains(r, "/static/pedidos/img/logo.jpg")

    def test_melloco_en_la_insignia_y_el_chat(self):
        r = self.client.get(reverse("pedidos:index"))
        # Dibujo de Melloco en el sello de calidad, la cabecera del chat y el botón flotante.
        self.assertContains(r, "APROBADO POR MELLOCO · DIRECTOR DE CALIDAD")
        self.assertContains(r, "Control de calidad Melloco")
        self.assertContains(r, "/static/pedidos/img/melloco.svg", count=3)
        svg = (RAIZ / "pedidos/static/pedidos/img/melloco.svg").read_text(encoding="utf-8")
        self.assertIn("<title", svg)
        self.assertLess(len(svg), 10_000)

    def test_produccion_usa_estaticos_con_hash_y_whitenoise(self):
        r = correr_django("shell", "-c",
                          "from django.conf import settings as s; print(s.STORAGES['staticfiles']['BACKEND']); "
                          "print('whitenoise.middleware.WhiteNoiseMiddleware' in s.MIDDLEWARE)",
                          DJANGO_DEBUG="0", DJANGO_SECRET_KEY="x" * 50)
        self.assertIn("whitenoise.storage.CompressedManifestStaticFilesStorage", r.stdout, r.stderr)
        self.assertIn("True", r.stdout)


# ---------------------------------------------------------------------------
# Spec 004 · SEO
# ---------------------------------------------------------------------------

class SeoTests(TestCase):
    def test_canonica_absoluta_y_fragmentos_apuntan_a_la_portada(self):
        casos = {
            reverse("pedidos:index"): "http://testserver/",
            reverse("pedidos:configurador"): "http://testserver/",
            reverse("pedidos:ruleta"): "http://testserver/",
            reverse("pedidos:privacidad"): "http://testserver/privacidad/",
        }
        for ruta, canonica in casos.items():
            r = self.client.get(ruta)
            self.assertContains(r, f'<link rel="canonical" href="{canonica}">', msg_prefix=ruta)
            self.assertContains(r, f'<meta property="og:url" content="{canonica}">', msg_prefix=ruta)

    def test_open_graph_completo_con_imagen_absoluta(self):
        r = self.client.get(reverse("pedidos:index"))
        self.assertContains(r, '<meta property="og:image" content="http://testserver/static/pedidos/img/logo.jpg">')
        for etiqueta in ('og:image:width" content="1000"', 'og:image:height" content="914"',
                         'og:type" content="website"', 'og:locale" content="es_EC"',
                         'og:site_name" content="Chester’s"', 'twitter:card" content="summary_large_image"'):
            self.assertContains(r, etiqueta)

    def test_privacidad_tiene_titulo_y_descripcion_propios(self):
        portada = self.client.get(reverse("pedidos:index")).content.decode()
        r = self.client.get(reverse("pedidos:privacidad"))
        self.assertContains(r, "<title>Política de privacidad | Chester’s</title>")
        self.assertContains(r, '<meta name="description" content="Qué datos guarda Chester’s')
        self.assertNotIn("Qué datos guarda", portada)

    def test_robots_txt(self):
        r = self.client.get("/robots.txt")
        self.assertEqual(r["Content-Type"], "text/plain; charset=utf-8")
        texto = r.content.decode()
        for linea in ("User-agent: *", "Disallow: /api/", "Disallow: /configurador/",
                      "Disallow: /ruleta/", "Disallow: /chat/", "Sitemap: http://testserver/sitemap.xml"):
            self.assertIn(linea, texto)
        self.assertNotIn("admin", texto)  # no revelar la ruta del panel

    def test_sitemap(self):
        r = self.client.get("/sitemap.xml")
        self.assertContains(r, "<loc>http://testserver/</loc>")
        self.assertContains(r, "<loc>http://testserver/privacidad/</loc>")
        self.assertNotContains(r, "configurador")

    @override_settings(CHESTERS_WHATSAPP="593991112233")
    def test_datos_estructurados_bakery(self):
        html = self.client.get(reverse("pedidos:index")).content.decode()
        inicio = html.index('<script type="application/ld+json">') + len('<script type="application/ld+json">')
        datos = json.loads(html[inicio:html.index("</script>", inicio)])
        self.assertEqual(datos["@type"], "Bakery")
        self.assertEqual(datos["name"], "Chester’s")
        self.assertEqual(datos["url"], "http://testserver/")
        self.assertEqual(datos["telephone"], "+593991112233")
        self.assertTrue(datos["logo"].startswith("http://testserver/static/"))


# ---------------------------------------------------------------------------
# Spec 005 · Chat de pedidos
# ---------------------------------------------------------------------------

class ChatTests(TestCase):
    url = reverse("pedidos:chat")

    def setUp(self):
        cache.clear()

    def responder(self, campo, valor=None, **datos):
        cuerpo = {"campo": campo, **datos}
        if valor is not None:
            cuerpo[campo] = valor
        return self.client.post(self.url, cuerpo, **HTMX)

    def test_portada_tiene_el_boton_y_el_chat_con_el_saludo(self):
        r = self.client.get(reverse("pedidos:index"))
        self.assertContains(r, 'id="chat-abrir"')
        self.assertContains(r, "Pedir con Melloco")
        self.assertContains(r, 'role="log"')
        self.assertContains(r, "Cuéntame, ¿cómo se llama tu perrito?")
        self.assertContains(r, 'name="campo" value="nombre_perro"')

    def test_empezar_de_nuevo(self):
        r = self.client.get(self.url)
        self.assertContains(r, 'id="chat-log"')
        self.assertContains(r, "Soy Melloco")
        self.assertNotContains(r, "Empezar de nuevo")

    def test_pregunta_en_orden_y_conserva_las_respuestas(self):
        r = self.responder("nombre_perro", "Rocky")
        self.assertContains(r, "<span class=\"sr-only\">Tú: </span>Rocky", html=False)
        self.assertContains(r, "¿Qué día celebran a Rocky?")
        self.assertContains(r, 'hx-swap-oob="true"')
        self.assertContains(r, 'name="campo" value="fecha_cumple"')
        self.assertContains(r, '<input type="hidden" name="nombre_perro" value="Rocky">', html=False)
        self.assertContains(r, 'type="date"')

        r = self.responder("fecha_cumple", "2099-12-15", nombre_perro="Rocky")
        self.assertContains(r, "15 de diciembre de 2099")
        self.assertContains(r, 'name="receta" value="carne_pure"')
        self.assertContains(r, 'name="receta" value="manzana_zanahoria_yogur"')

        base = {"nombre_perro": "Rocky", "fecha_cumple": "2099-12-15"}
        r = self.responder("receta", "carne_pure", **base)
        self.assertContains(r, "Carne y puré")
        self.assertContains(r, 'name="estilo" value="huesito"')

        base["receta"] = "carne_pure"
        r = self.responder("estilo", "redondo", **base)
        self.assertContains(r, "¿Y tú cómo te llamas?")

        base["estilo"] = "redondo"
        r = self.responder("nombre_cliente", "Ana", **base)
        self.assertContains(r, "Gracias, Ana.")
        self.assertContains(r, 'type="tel"')

        base["nombre_cliente"] = "Ana"
        r = self.responder("telefono", "099 123 4567", **base)
        self.assertContains(r, "Así queda el pedido de Rocky:")
        self.assertContains(r, "<dt class=\"text-slate-500\">Forma</dt>", html=False)
        self.assertContains(r, 'name="acepta_datos"')
        self.assertContains(r, 'href="/privacidad/"')
        self.assertContains(r, 'name="sitio_web"')

    def test_respuesta_invalida_explica_y_repite_la_pregunta(self):
        r = self.responder("nombre_perro", "")
        self.assertContains(r, "¿Cómo se llama tu perrito?")
        self.assertContains(r, 'name="campo" value="nombre_perro"')

        r = self.responder("fecha_cumple", "2001-01-01", nombre_perro="Rocky")
        self.assertContains(r, "Elige una fecha de hoy en adelante.")
        self.assertContains(r, 'name="campo" value="fecha_cumple"')
        self.assertNotContains(r, 'name="fecha_cumple" value="2001-01-01"')

        r = self.responder("receta", "chocolate", nombre_perro="Rocky", fecha_cumple="2099-12-15")
        self.assertContains(r, 'name="campo" value="receta"')

    def test_escapa_lo_que_escribe_la_persona(self):
        r = self.responder("nombre_perro", "<script>alert(1)</script>")
        self.assertNotContains(r, "<script>alert(1)</script>")
        self.assertContains(r, "&lt;script&gt;")

    @override_settings(CHESTERS_WHATSAPP="593991112233")
    def test_confirmar_guarda_y_abre_whatsapp_con_el_mismo_mensaje(self):
        with mock.patch("pedidos.views.notificar_binn") as notificar:
            r = self.responder("acepta_datos", "on", **{k: v for k, v in PEDIDO.items() if k not in ("paso", "acepta_datos")})
        self.assertEqual(r.status_code, 200)
        c = Cotizacion.objects.get()
        self.assertEqual((c.nombre_perro, c.telefono, c.receta), ("Rocky", "0991234567", "carne_pure"))
        notificar.assert_called_once_with(c)
        url = json.loads(r["HX-Trigger-After-Settle"])["abrirWhatsapp"]["url"]
        self.assertTrue(url.startswith("https://wa.me/593991112233?text="))
        self.assertIn(quote_mensaje("Hola Melloco, quiero confirmar el pastel de carne y puré"), url)
        self.assertContains(r, "Abrir WhatsApp")
        self.assertContains(r, "Hacer otro pedido")

    def test_sin_autorizacion_no_guarda(self):
        datos = {k: v for k, v in PEDIDO.items() if k not in ("paso", "acepta_datos")}
        r = self.responder("acepta_datos", None, **datos)
        self.assertContains(r, "Marca la casilla de autorización")
        self.assertEqual(Cotizacion.objects.count(), 0)

    def test_campo_trampa_no_guarda(self):
        datos = {k: v for k, v in PEDIDO.items() if k not in ("paso", "acepta_datos")}
        r = self.responder("acepta_datos", "on", sitio_web="spam", **datos)
        self.assertIn("abrirWhatsapp", r["HX-Trigger-After-Settle"])
        self.assertEqual(Cotizacion.objects.count(), 0)

    @override_settings(CHESTERS_LIMITE_ENVIOS=1)
    def test_comparte_el_limite_con_el_configurador(self):
        self.client.post(reverse("pedidos:confirmar"), PEDIDO, **HTMX)
        datos = {k: v for k, v in PEDIDO.items() if k not in ("paso", "acepta_datos")}
        r = self.responder("acepta_datos", "on", **datos)
        self.assertEqual(r.status_code, 429)
        self.assertContains(r, "Recibí varios pedidos seguidos", status_code=429)
        self.assertEqual(Cotizacion.objects.count(), 1)

    def test_sin_htmx_vuelve_a_la_portada(self):
        r = self.client.post(self.url, {"campo": "nombre_perro", "nombre_perro": "Rocky"})
        self.assertRedirects(r, reverse("pedidos:index"))


def quote_mensaje(texto):
    from urllib.parse import quote
    return quote(texto)


# ---------------------------------------------------------------------------
# Spec 006 · Equipo y gestión de pedidos
# ---------------------------------------------------------------------------

class EquipoYGestionTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import Group, User
        self.pedido = Cotizacion.objects.create(
            nombre_cliente="Ana", telefono="0991234567", nombre_perro="Rocky",
            fecha_cumple=datetime.date(2099, 12, 15), receta="carne_pure", estilo="huesito")
        self.lead = LeadCumple.objects.create(nombre_humano="Ana", nombre_perro="Luna",
                                              fecha_cumple=datetime.date(2021, 3, 10), telefono="0991234567")
        self.equipo = User.objects.create_user("vale", password="clave-de-prueba-123", is_staff=True)
        self.equipo.groups.add(Group.objects.get(name="Atención de pedidos"))
        self.client.force_login(self.equipo)

    def test_grupo_con_permisos_justos(self):
        from django.contrib.auth.models import Group
        permisos = set(Group.objects.get(name="Atención de pedidos").permissions.values_list("codename", flat=True))
        self.assertEqual(permisos, {"view_cotizacion", "change_cotizacion", "view_leadcumple", "change_leadcumple"})

    def test_el_equipo_ve_y_edita_pero_no_borra_ni_gestiona_usuarios(self):
        self.assertEqual(self.client.get(reverse("admin:pedidos_cotizacion_changelist")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:pedidos_leadcumple_changelist")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:pedidos_cotizacion_delete", args=[self.pedido.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse("admin:auth_user_changelist")).status_code, 403)
        self.assertEqual(self.client.get(reverse("admin:auth_user_add")).status_code, 403)

    def test_pedidos_nuevos_entran_como_nuevo(self):
        self.assertEqual(self.pedido.estado, "nuevo")
        cache.clear()
        self.client.post(reverse("pedidos:confirmar"), PEDIDO, **HTMX)
        self.assertEqual(Cotizacion.objects.latest("creado_en").estado, "nuevo")

    def test_estado_se_cambia_desde_la_lista_y_se_filtra(self):
        url = reverse("admin:pedidos_cotizacion_changelist")
        r = self.client.get(url)
        self.assertContains(r, 'name="form-0-estado"')
        self.assertContains(r, "En preparación")
        r = self.client.post(url, {
            "form-TOTAL_FORMS": "1", "form-INITIAL_FORMS": "1",
            "form-0-id": str(self.pedido.pk), "form-0-estado": "confirmado", "_save": "Guardar",
        })
        self.assertEqual(r.status_code, 302)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, "confirmado")
        self.assertContains(self.client.get(url + "?estado__exact=confirmado"), "Rocky")
        self.assertNotContains(self.client.get(url + "?estado__exact=entregado"), ">Rocky<")

    def test_enlace_whatsapp_del_cliente(self):
        r = self.client.get(reverse("admin:pedidos_cotizacion_changelist"))
        self.assertContains(r, 'href="https://wa.me/593991234567"')
        self.assertContains(r, "Escribir por WhatsApp")

    def test_numeros_a_formato_internacional(self):
        from .models import whatsapp_internacional
        self.assertEqual(whatsapp_internacional("0991234567"), "593991234567")
        self.assertEqual(whatsapp_internacional("+593991234567"), "593991234567")
        self.assertEqual(whatsapp_internacional("593991234567"), "593991234567")

    def test_regalo_enviado_desde_la_lista(self):
        url = reverse("admin:pedidos_leadcumple_changelist")
        self.assertContains(self.client.get(url), 'name="form-0-regalo_enviado"')
        self.client.post(url, {
            "form-TOTAL_FORMS": "1", "form-INITIAL_FORMS": "1",
            "form-0-id": str(self.lead.pk), "form-0-regalo_enviado": "on", "_save": "Guardar",
        })
        self.lead.refresh_from_db()
        self.assertTrue(self.lead.regalo_enviado)
        self.assertContains(self.client.get(url + "?regalo_enviado__exact=0"), "0 leads")

    @override_settings(BINN_API_TOKEN="secreto")
    def test_estado_y_regalo_viajan_a_binn(self):
        self.assertEqual(self.pedido.to_crm()["estado"], "nuevo")
        self.assertEqual(self.pedido.to_crm()["estado_nombre"], "Nuevo")
        self.assertIs(self.lead.to_crm()["regalo_enviado"], False)
        r = self.client.get(reverse("pedidos:api_cotizaciones"), HTTP_X_BINN_TOKEN="secreto")
        self.assertEqual(r.json()["resultados"][0]["estado"], "nuevo")
