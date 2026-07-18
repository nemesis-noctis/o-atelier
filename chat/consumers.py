import json

from channels.generic.websocket import WebsocketConsumer
from django.template.loader import render_to_string

from accounts.models import CustomUser
from chat.models import Message
from commissions.models import Commission


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.user: CustomUser = self.scope["user"]
        self.comm_uuid = self.scope["url_route"]["kwargs"]["uuid"]
        if self.user.is_superuser:
            self.commission = Commission.objects.get(uuid=self.comm_uuid)
        else:
            self.commission = self.user.commissions.get(uuid=self.comm_uuid)

        self.accept()

    def receive(self, text_data, bytes_data=None):
        text_data_json = json.loads(text_data)
        content = text_data_json["content"]
        message = Message.objects.create(
            content=content,
            user=self.user,
            commission=self.commission,
            is_event=False
        )

        context = {"message": message, "user": self.user}
        html = render_to_string("accounts/partials/message_wrapper.html", context=context)
        self.send(text_data=html)
