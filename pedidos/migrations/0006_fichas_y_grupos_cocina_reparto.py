"""Spec 010: fichas de los perritos que ya existen y grupos "Cocina" y "Reparto"."""

import unicodedata

from django.contrib.auth.management import create_permissions
from django.db import migrations

GRUPOS_NUEVOS = ["Cocina", "Reparto"]
PERMISOS_ATENCION = ["view_perrito", "change_perrito"]


# Copias fijas de las funciones de models.py: una migración no debe cambiar si el código cambia.
def _telefono_clave(telefono):
    digitos = "".join(c for c in telefono or "" if c.isdigit())
    return "593" + digitos[1:] if digitos.startswith("0") else digitos


def _nombre_clave(nombre):
    texto = unicodedata.normalize("NFKD", nombre or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.lower().split())


def crear_fichas_y_grupos(apps, schema_editor):
    Perrito = apps.get_model("pedidos", "Perrito")
    fichas = {}

    def ficha(telefono, nombre, familia):
        clave = (_telefono_clave(telefono), _nombre_clave(nombre))
        if clave not in fichas:
            fichas[clave], _ = Perrito.objects.get_or_create(
                telefono_clave=clave[0], nombre_clave=clave[1],
                defaults={"nombre": " ".join(nombre.split()), "telefono": telefono, "familia": familia},
            )
        return fichas[clave]

    # Del más antiguo al más nuevo: la ficha toma el nombre tal como se escribió la primera vez.
    for modelo, campo_familia in (("Cotizacion", "nombre_cliente"), ("LeadCumple", "nombre_humano")):
        for obj in apps.get_model("pedidos", modelo).objects.filter(perrito__isnull=True).order_by("creado_en"):
            obj.perrito = ficha(obj.telefono, obj.nombre_perro, getattr(obj, campo_familia))
            obj.save(update_fields=["perrito"])

    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    for nombre in GRUPOS_NUEVOS:
        Group.objects.get_or_create(name=nombre)
    atencion, _ = Group.objects.get_or_create(name="Atención de pedidos")
    atencion.permissions.add(*Permission.objects.filter(content_type__app_label="pedidos",
                                                        codename__in=PERMISOS_ATENCION))


def deshacer(apps, schema_editor):
    apps.get_model("auth", "Group").objects.filter(name__in=GRUPOS_NUEVOS).delete()
    apps.get_model("pedidos", "Perrito").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("pedidos", "0005_ficha_del_perrito_y_asignaciones"),
    ]

    operations = [migrations.RunPython(crear_fichas_y_grupos, deshacer)]
