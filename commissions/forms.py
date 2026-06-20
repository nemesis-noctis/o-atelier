from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_noop as _noop

from core.utils import set_form_field_classes
from . import models


class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if not data:
            if self.required:
                raise ValidationError(self.error_messages['required'], code='required')
            return []

        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


class CommissionForm(forms.ModelForm):
    reference_images = MultipleImageField(required=False)

    class Meta:
        model = models.Commission
        exclude = ["uuid", "user", "stage", "category", "price_brl", "price_usd", "created_at", 'finished_at']
        widgets = {
            "final_stage": forms.RadioSelect,
            "character_type": forms.RadioSelect,
            "complexity": forms.RadioSelect,
            "clothing": forms.RadioSelect,
            "body_type": forms.RadioSelect,
            "background": forms.RadioSelect,
            "aspect_ratio": forms.RadioSelect,
            "art_type": forms.RadioSelect,
            "fx": forms.RadioSelect
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        fields = self.fields.values()
        set_form_field_classes(fields)
        for field in fields:
            if isinstance(field.widget, forms.RadioSelect):
                field.choices = [
                    (key, value) for key, value in field.choices
                    if key is not None and key != ''
                ]

        self.fields["description"].widget.attrs["placeholder"] = _noop(
            "Ex: Gostaria de uma fanart do Satoru Gojo de jujutsu kaisen.")
        self.fields["contact_social"].widget.attrs["placeholder"] = _noop("Ex: Whatsapp, Twitter, Instagram")
        self.fields["contact_username"].widget.attrs["placeholder"] = _noop("Ex: @lirio_guinevere, (00)0000-0000")

    def clean_reference_images(self):
        images = self.cleaned_data.get("reference_images")
        if len(images) > 10:
            raise ValidationError(
                _noop("O número de arquivos enviados excede o limite (10). Por favor, tente novamente."))

        for image in images:
            if image.size > 10 * 1024 * 1024:
                raise ValidationError(
                    _noop(f"A imagem {image.name} excede o limite de tamanho (10MB). Por favor, tente novamente"))
