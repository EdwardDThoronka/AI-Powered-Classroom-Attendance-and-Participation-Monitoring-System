from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/screen-sharing/(?P<session_id>[^/]+)/$', consumers.ScreenSharingConsumer.as_asgi()),
]
