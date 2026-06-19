from django import forms
from django.utils.translation import gettext_noop as _noop

from core.utils import set_form_field_classes
from . import models


class MultipleFileField(forms.FileInput):
    allow_multiple_selected = True


class CommissionForm(forms.ModelForm):
    # reference_images = forms.ImageField(widget=MultipleFileField(attrs={'multiple': True}))

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
