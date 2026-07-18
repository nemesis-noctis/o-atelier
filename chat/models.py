from uuid import uuid7

from django.db import models

from accounts.models import CustomUser
from commissions.models import Commission


# Create your models here.

class MessageImage(models.Model):
    uuid = models.UUIDField(primary_key=True, editable=False, default=uuid7)
    image = models.ImageField(upload_to="messages_media", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Message(models.Model):
    uuid = models.UUIDField(primary_key=True, editable=False, default=uuid7)
    commission = models.ForeignKey(Commission, on_delete=models.CASCADE, related_name="messages")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True)
    image = models.ForeignKey(MessageImage, on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField(max_length=600)
    created_at = models.DateTimeField(auto_now_add=True)
