from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/room/(?P<room_name>\w+)/$', consumers.WaitingLobbyConsumer.as_asgi()),
    re_path(r'ws/InGame/(?P<room_name>\w+)/$', consumers.InGameConsumer.as_asgi()),
]