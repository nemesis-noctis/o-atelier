import json

from channels.generic.websocket import AsyncWebsocketConsumer
from django.template.loader import render_to_string

from accounts.models import CustomUser
from chat.models import Message
from commissions.models import Commission


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user: CustomUser = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        self.comm_uuid = self.scope["url_route"]["kwargs"]["uuid"]
        if self.user.is_superuser:
            self.commission = await Commission.objects.aget(uuid=self.comm_uuid)
        else:
            self.commission = await self.user.commissions.aget(uuid=self.comm_uuid)

        await self.channel_layer.group_add(str(self.comm_uuid).replace("-", "_"), self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(str(self.comm_uuid).replace("-", "_"), self.channel_name)

    async def receive(self, text_data, bytes_data=None):
        text_data_json = json.loads(text_data)
        content = text_data_json["content"]
        message = await Message.objects.acreate(
            content=content,
            user=self.user,
            commission=self.commission,
        )

        event = {
            "type": "message_handler",
            "message_uuid": message.uuid
        }

        await self.channel_layer.group_send(str(self.comm_uuid).replace("-", "_"), event)

    async def message_handler(self, event):
        message_uuid = event["message_uuid"]
        message = await Message.objects.select_related("user").aget(uuid=message_uuid)
        context = {"message": message, "user": self.user}
        html = render_to_string("accounts/partials/message_wrapper.html", context=context)
        await self.send(text_data=html)
