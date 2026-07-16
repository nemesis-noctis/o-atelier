import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_noop as _noop

from accounts.models import CustomUser


# Create your models here.
class Commission(models.Model):
    stages_indexes = {
        "waiting_confirmation": 0,
        "waiting_deposit_payment": 1,
        "sketch": 2,
        "lineart": 3,
        "flat_colour": 4,
        "render": 5,
        "waiting_full_payment": 6,
        "finished": 7,
        "canceled": 8,
    }
    stage_choices = {
        "waiting_confirmation": _noop("aguardando confirmação"),
        "waiting_deposit_payment": _noop("aguardando pagamento da garantia"),
        "sketch": _noop("esboço"),
        "lineart": _noop("lineart"),
        "flat_colour": _noop("cor flat"),
        "render": _noop("render"),
        "waiting_full_payment": _noop("aguardando pagamento total"),
        "finished": _noop("concluído"),
        "canceled": _noop("cancelado"),
    }
    final_stage_choices = {
        "lineart": _noop("lineart"),
        "flat_colour": _noop("cor flat"),
        "render": _noop("render")
    }
    category_choices = {
        "character": _noop("personagem"),
        "landscape": _noop("cenário"),
        "object": _noop("objetos")
    }
    character_type_choices = {
        "human": _noop("humano"),
        "furry": _noop("furry"),
        "chibi": _noop("chibi"),
        "simple_creature": _noop("criatura simples"),
        "complex_creature": _noop("criatura complexa"),
    }
    complexity_choices = {
        "simple": _noop("simples"),
        "complex": _noop("complexo")
    }
    art_type_choices = {
        "illustration": _noop("ilustração"),
        "scene": _noop("cena"),
        "sheet": _noop("sheet")
    }
    clothing_choices = {
        "mannequin": _noop("manequim"),
        "simple": _noop("simples"),
        "complex": _noop("complexo"),
        "accessories": _noop("acessórios")
    }
    body_type_choices = {
        "bust": _noop("busto"),
        "waist": _noop("quadril"),
        "full": _noop("full")
    }
    background_choices = {
        "simple": _noop("simples"),
        "complex": _noop("complexo"),
        "preset": _noop("preset")
    }
    aspect_ratio_choices = {
        "1:1": "1:1",
        "3:2": "3:2",
        "16:9": "16:9",
        "1.85:1": "1.85:1"
    }
    fx_choices = {
        True: "sim",
        False: "não"
    }
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="commissions")
    stage = models.CharField(max_length=24, choices=stage_choices)
    category = models.CharField(max_length=24, choices=category_choices, default="character")
    final_stage = models.CharField(max_length=24, choices=final_stage_choices, default="render")
    character_type = models.CharField(max_length=24, choices=character_type_choices, blank=True, null=True,
                                      default="human")
    count = models.IntegerField(default=1, blank=True, null=True,
                                validators=[MinValueValidator(1), MaxValueValidator(5)])
    complexity = models.CharField(max_length=12, choices=complexity_choices, blank=True, null=True, default="simple")
    art_type = models.CharField(max_length=24, choices=art_type_choices, blank=True, null=True, default="illustration")
    clothing = models.CharField(max_length=24, choices=clothing_choices, blank=True, null=True, default="simple")
    body_type = models.CharField(max_length=12, choices=body_type_choices, blank=True, null=True, default="full")
    background = models.CharField(max_length=12, choices=background_choices, blank=True, null=True, default="simple")
    aspect_ratio = models.CharField(max_length=12, choices=aspect_ratio_choices, default="3:2")
    fx = models.BooleanField(default=False, choices=fx_choices)
    description = models.TextField(max_length=3000)
    commercial = models.BooleanField(default=False)
    share_permission = models.BooleanField(default=False)
    contact_social = models.CharField(max_length=30)
    contact_username = models.CharField(max_length=60)
    price_brl = models.FloatField()
    price_usd = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True)

    @property
    def stage_index(self):
        return self.stages_indexes[self.stage]

    @property
    def final_stage_index(self):
        return self.stages_indexes[self.final_stage]


class ReferenceImage(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    commission = models.ForeignKey(Commission, on_delete=models.CASCADE, null=True, related_name="reference_images")
    is_temp = models.BooleanField(default=True)
    image = models.ImageField(upload_to="commission/reference")
    created_at = models.DateTimeField(auto_now_add=True)


class ProgressImage(models.Model):
    stage_choices = {
        "sketch": _noop("esboço"),
        "lineart": _noop("lineart"),
        "flat_colour": _noop("cor flat"),
        "render": _noop("render"),
    }

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    stage = models.CharField(max_length=24, choices=stage_choices)
    commission = models.ForeignKey(Commission, on_delete=models.CASCADE, null=True, related_name="progress_image")
    image = models.ImageField(upload_to="commission/progress")
    created_at = models.DateTimeField(auto_now_add=True)
