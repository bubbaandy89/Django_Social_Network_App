from typing import List

from django.urls import URLPattern, re_path

from . import consumers

websocket_urlpatterns: List[URLPattern] = [
    re_path(r"ws/chat/(?P<room_name>\w+)/$", consumers.ChatRoomConsumer.as_asgi()),
    re_path(r"ws/shout/(?P<shoutbox_id>\w+)/$", consumers.ShoutBoxConsumer.as_asgi()),
]
