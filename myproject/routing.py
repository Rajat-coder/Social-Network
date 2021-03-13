from channels.routing import ProtocolTypeRouter,URLRouter
from chat.consumers import EchoConsumer
from django.urls import path

application=ProtocolTypeRouter({
    "websocket":URLRouter([
        path('ws/chat/',EchoConsumer)
    ])
})