from django.db import models

from accounts.models import CustomUser


# Create your models here.
class Notification(models.Model):
    template_key = models.CharField(max_length=60)
    level = models.CharField(max_length=24, default="MESSAGE")
    context = models.JSONField(default=dict)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="notifications")
