import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from channels.security.websocket import OriginValidator
import Routes.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotbotChatbotBackend.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # Handles HTTP requests

    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                Routes.routing.websocket_urlpatterns  # WebSocket URL patterns
            )
        )
    ),
})
