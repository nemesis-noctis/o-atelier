from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path("ws/comm_chat/<uuid:uuid>", consumers.ChatConsumer.as_asgi(), name="ws_chat")
]
