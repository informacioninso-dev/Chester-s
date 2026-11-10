import re

from django import forms
from django.utils import timezone

from .models import Cotizacion, Estilo, LeadCumple, Receta

INPUT = (
    "block w-full rounded-2xl border border-stone-300 bg-white px-4 py-3.5 "
    "text-slate-900 placeholder:text-stone-400 shadow-sm transition "
    "focus:border-collar-600 focus:outline-none focus:ring-4 focus:ring-collar-600/15 "
    "aria-[invalid=true]:border-collar-600 aria-[invalid=true]:bg-collar-50/40"
)


def limpiar_telefono(valor):
    """Quita espacios, guiones y paréntesis: '099 123-4567' -> '0991234567'."""
    return re.sub(r"[\s\-().]", "", valor or "")


class TelefonoMixin:
    def clean_telefono(self):
        return limpiar_telefono(self.cleaned_data.get("telefono"))


class PedidoForm(TelefonoMixin, forms.ModelForm):
    """Formulario único del configurador. Cada paso valida solo sus campos;
    los datos de los pasos anteriores viajan como inputs ocultos."""

    PASOS = {
        1: ["nombre_perro", "fecha_cumple"],
        2: ["receta"],
        3: ["estilo"],
        4: ["nombre_cliente", "telefono", "acepta_datos"],
    }
    TOTAL_PASOS = len(PASOS)

    receta = forms.ChoiceField(
        choices=Receta.choices,
        widget=forms.RadioSelect,
        error_messages={"required": "Elige una receta para continuar."},
    )
    estilo = forms.ChoiceField(
        choices=Estilo.choices,
        widget=forms.RadioSelect,
        error_messages={"required": "Elige un estilo para continuar."},
    )
    acepta_datos = forms.BooleanField(
        error_messages={"required": "Necesitamos tu autorización para procesar el pedido."},
    )

    class Meta:
        model = Cotizacion
        fields = ["nombre_perro", "fecha_cumple", "receta", "estilo", "nombre_cliente", "telefono"]
        widgets = {
            "nombre_perro": forms.TextInput(
                attrs={"class": INPUT, "placeholder": "Ej. Rocky", "autocomplete": "off"}
            ),
            "fecha_cumple": forms.DateInput(
                format="%Y-%m-%d", attrs={"class": INPUT, "type": "date"}
            ),
            "nombre_cliente": forms.TextInput(
                attrs={"class": INPUT, "placeholder": "Tu nombre", "autocomplete": "name"}
            ),
            "telefono": forms.TextInput(
                attrs={
                    "class": INPUT,
                    "placeholder": "099 123 4567",
                    "inputmode": "tel",
                    "autocomplete": "tel",
                }
            ),
        }
        error_messages = {
            "nombre_perro": {"required": "¿Cómo se llama tu perrito?"},
            "fecha_cumple": {"required": "Indícanos la fecha del cumpleaños."},
            "nombre_cliente": {"required": "Cuéntanos tu nombre."},
            "telefono": {"required": "Déjanos tu WhatsApp para confirmar."},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        hoy = timezone.localdate().isoformat()
        self.fields["fecha_cumple"].widget.attrs["min"] = hoy

    def clean_fecha_cumple(self):
        fecha = self.cleaned_data["fecha_cumple"]
        if fecha < timezone.localdate():
            raise forms.ValidationError("Elige una fecha de hoy en adelante.")
        return fecha

    @classmethod
    def campos_hasta(cls, paso):
        return [c for n in range(1, paso + 1) for c in cls.PASOS[n]]

    def primer_paso_con_error(self, paso):
        """Primer paso (1..paso) que tiene errores, o None si todo está bien."""
        for n in range(1, paso + 1):
            if any(c in self.errors for c in self.PASOS[n]):
                return n
        return None


class LeadCumpleForm(TelefonoMixin, forms.ModelForm):
    acepta_datos = forms.BooleanField(
        error_messages={"required": "Necesitamos tu autorización para guardar la fecha."},
    )

    class Meta:
        model = LeadCumple
        fields = ["nombre_humano", "nombre_perro", "fecha_cumple", "telefono"]
        widgets = {
            "nombre_humano": forms.TextInput(
                attrs={"class": INPUT, "placeholder": "Tu nombre", "autocomplete": "name"}
            ),
            "nombre_perro": forms.TextInput(
                attrs={"class": INPUT, "placeholder": "Nombre de tu perrito", "autocomplete": "off"}
            ),
            "fecha_cumple": forms.DateInput(
                format="%Y-%m-%d", attrs={"class": INPUT, "type": "date"}
            ),
            "telefono": forms.TextInput(
                attrs={
                    "class": INPUT,
                    "placeholder": "099 123 4567",
                    "inputmode": "tel",
                    "autocomplete": "tel",
                }
            ),
        }
        error_messages = {
            "nombre_humano": {"required": "Cuéntanos tu nombre."},
            "nombre_perro": {"required": "¿Cómo se llama tu perrito?"},
            "fecha_cumple": {"required": "Indícanos su fecha de cumpleaños."},
            "telefono": {"required": "Necesitamos un número para escribirte."},
        }
