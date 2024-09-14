from django.urls import re_path
from . import consumer

wwebsocket_urlpatterns = [
    re_path(r'^ws/chat/(?P<room_name>\w+)/$', consumer.ChatConsumer.as_asgi()),
]