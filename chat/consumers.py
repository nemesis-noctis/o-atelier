import json

from channels.generic.websocket import AsyncWebsocketConsumer
from django.template.loader import render_to_string

from accounts.forms import SendMessageForm
from accounts.models import CustomUser
from chat.models import Message, MessageImage
from commissions.models import Commission


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user: CustomUser = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        self.comm_uuid = self.scope["url_route"]["kwargs"]["uuid"]

        try:
            if self.user.is_superuser:
                self.commission = await Commission.objects.aget(uuid=self.comm_uuid)
            else:
                self.commission = await self.user.commissions.aget(uuid=self.comm_uuid)
        except Commission.DoesNotExist:
            await self.close()
            return

        await self.channel_layer.group_add(str(self.comm_uuid).replace("-", "_"), self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(str(self.comm_uuid).replace("-", "_"), self.channel_name)

    async def receive(self, text_data, bytes_data=None):
        text_data_json = json.loads(text_data)
        content = text_data_json["content"]
        image_uuid = text_data_json.get("image_uuid", None)
        form = SendMessageForm(text_data_json)

        if (not form.is_valid()) or (content.strip() == "" and image_uuid is None):
            return

        try:
            message_image = await MessageImage.objects.aget(uuid=image_uuid) if image_uuid else None
        except MessageImage.DoesNotExist:
            await self.close()
            return

        message = await Message.objects.acreate(
            content=content,
            user=self.user,
            commission=self.commission,
            image=message_image
        )

        event = {
            "type": "message_handler",
            "message_uuid": str(message.uuid)
        }

        await self.channel_layer.group_send(str(self.comm_uuid).replace("-", "_"), event)

    async def message_handler(self, event):
        message_uuid = event["message_uuid"]
        message = await Message.objects.select_related("user", "image").aget(uuid=message_uuid)
        context = {"message": message, "user": self.user}
        html = render_to_string("accounts/partials/message_wrapper.html", context=context)
        await self.send(text_data=html)
