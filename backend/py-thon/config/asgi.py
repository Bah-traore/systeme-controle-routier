"""
Configuration ASGI — Support HTTP et WebSocket via Django Channels.
"""
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

# Initialisation Django
django_asgi_app = get_asgi_application()

# Import des routes WebSocket (Phase 6)
# from apps.synchronisation.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    # 'websocket': AllowedHostsOriginValidator(
    #     AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
    # ),
})
