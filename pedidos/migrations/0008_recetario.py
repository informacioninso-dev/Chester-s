"""Spec 013: recetas y formas pasan del código a un Recetario administrable.

Crea las tablas, carga las 2 recetas y las 2 formas que ya existían (mismas claves, para que
Binn y los pedidos viejos no cambien) y enlaza cada pedido a su receta y su forma.
"""

import django.db.models.deletion
from django.db import migrations, models

RECETAS = [
    {"clave": "carne_pure", "nombre": "Carne y puré", "orden": 1,
     "descripcion": "Contundente y casera. La favorita de los más glotones."},
    {"clave": "manzana_zanahoria_yogur", "nombre": "Manzana, zanahoria y yogur", "orden": 2,
     "descripcion": "Fresca y ligera, con un toque cremoso de yogur.", "contiene": "Lácteos (yogur)"},
]
FORMAS = [
    {"clave": "huesito", "nombre": "Huesito", "orden": 1, "descripcion": "El clásico de Chester.",
     "frase_mensaje": "en forma de huesito"},
    {"clave": "redondo", "nombre": "Redondo", "orden": 2, "descripcion": "Elegante, con un huesito encima.",
     "frase_mensaje": "en forma redonda"},
]


def cargar_y_enlazar(apps, schema_editor):
    Receta = apps.get_model("pedidos", "Receta")
    Forma = apps.get_model("pedidos", "Forma")
    Cotizacion = apps.get_model("pedidos", "Cotizacion")
    recetas = {r["clave"]: Receta.objects.create(disponible=True, **r) for r in RECETAS}
    formas = {f["clave"]: Forma.objects.create(disponible=True, **f) for f in FORMAS}
    for c in Cotizacion.objects.all():
        c.receta_ref = recetas.get(c.receta) or recetas["carne_pure"]
        c.estilo_ref = formas.get(c.estilo) or formas["huesito"]
        c.save(update_fields=["receta_ref", "estilo_ref"])


def deshacer(apps, schema_editor):
    Cotizacion = apps.get_model("pedidos", "Cotizacion")
    for c in Cotizacion.objects.select_related("receta_ref", "estilo_ref"):
        c.receta, c.estilo = c.receta_ref.clave, c.estilo_ref.clave
        c.save(update_fields=["receta", "estilo"])


def _campos_comunes():
    return [
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
        ("clave", models.SlugField(editable=False, max_length=40, unique=True, verbose_name="clave")),
        ("nombre", models.CharField(max_length=80, verbose_name="nombre")),
        ("descripcion", models.CharField(blank=True, max_length=140, verbose_name="descripción para el cliente")),
        ("notas", models.TextField(blank=True, max_length=1000, verbose_name="notas para la cocina")),
        ("disponible", models.BooleanField(db_index=True, default=False, verbose_name="disponible para clientes")),
        ("orden", models.PositiveSmallIntegerField(default=0, verbose_name="orden")),
        ("creado_en", models.DateTimeField(auto_now_add=True)),
        ("actualizado_en", models.DateTimeField(auto_now=True)),
    ]


class Migration(migrations.Migration):
    dependencies = [
        ("pedidos", "0007_entrega"),
    ]

    operations = [
        migrations.CreateModel(
            name="Receta",
            fields=_campos_comunes() + [
                ("ingredientes", models.TextField(blank=True, help_text="Uno por línea, con su cantidad.", max_length=2000, verbose_name="ingredientes")),
                ("pasos", models.TextField(blank=True, help_text="Uno por línea, en orden.", max_length=4000, verbose_name="pasos")),
                ("contiene", models.CharField(blank=True, help_text="Ej.: Lácteos (yogur), huevo.", max_length=200, verbose_name="contiene (alérgenos)")),
            ],
            options={"verbose_name": "receta", "verbose_name_plural": "recetas", "ordering": ["orden", "nombre"], "abstract": False},
        ),
        migrations.CreateModel(
            name="Forma",
            fields=_campos_comunes() + [
                ("frase_mensaje", models.CharField(blank=True, help_text="Ej.: en forma de huesito", max_length=80, verbose_name="cómo se dice en el mensaje")),
                ("como_armarla", models.TextField(blank=True, help_text="Molde, decoración y terminado. Uno por línea.", max_length=2000, verbose_name="cómo armarla")),
            ],
            options={"verbose_name": "forma", "verbose_name_plural": "formas", "ordering": ["orden", "nombre"], "abstract": False},
        ),
        migrations.AddField(
            model_name="cotizacion", name="receta_ref",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name="+", to="pedidos.receta"),
        ),
        migrations.AddField(
            model_name="cotizacion", name="estilo_ref",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name="+", to="pedidos.forma"),
        ),
        migrations.RunPython(cargar_y_enlazar, deshacer),
        migrations.RemoveField(model_name="cotizacion", name="receta"),
        migrations.RemoveField(model_name="cotizacion", name="estilo"),
        migrations.RenameField(model_name="cotizacion", old_name="receta_ref", new_name="receta"),
        migrations.RenameField(model_name="cotizacion", old_name="estilo_ref", new_name="estilo"),
        migrations.AlterField(
            model_name="cotizacion", name="receta",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pedidos", to="pedidos.receta", verbose_name="receta"),
        ),
        migrations.AlterField(
            model_name="cotizacion", name="estilo",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pedidos", to="pedidos.forma", verbose_name="forma"),
        ),
    ]
