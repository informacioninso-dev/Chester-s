"""Grupo "Atención de pedidos" (spec 006): ve y edita pedidos y cumpleaños, sin borrar."""

from django.contrib.auth.management import create_permissions
from django.db import migrations

GRUPO = "Atención de pedidos"
PERMISOS = [
    "view_cotizacion", "change_cotizacion",
    "view_leadcumple", "change_leadcumple",
]


def crear_grupo(apps, schema_editor):
    # En una base nueva los permisos se crean recién al final de migrate: los forzamos aquí.
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    grupo, _ = Group.objects.get_or_create(name=GRUPO)
    grupo.permissions.set(
        Permission.objects.filter(content_type__app_label="pedidos", codename__in=PERMISOS)
    )


def borrar_grupo(apps, schema_editor):
    apps.get_model("auth", "Group").objects.filter(name=GRUPO).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("pedidos", "0003_estado_y_regalo_enviado"),
    ]

    operations = [migrations.RunPython(crear_grupo, borrar_grupo)]
