"""
Configuration des URLs racine — Système de Contrôle Routier.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # Administration Django
    path('admin/', admin.site.urls),

    # API v1
    path('api/v1/auth/', include('apps.identite.urls', namespace='identite')),
    path('api/v1/organisation/', include('apps.organisation.urls', namespace='organisation')),
    # Phase 2+
    # path('api/v1/parc/', include('apps.parc_automobile.urls', namespace='parc')),
    # path('api/v1/controle/', include('apps.controle.urls', namespace='controle')),
    # path('api/v1/reglementation/', include('apps.reglementation.urls', namespace='reglementation')),
    # path('api/v1/pv/', include('apps.verbalisation.urls', namespace='verbalisation')),
    # path('api/v1/recours/', include('apps.recours.urls', namespace='recours')),
    # path('api/v1/stats/', include('apps.observatoire.urls', namespace='observatoire')),

    # Documentation OpenAPI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# En développement : servir les fichiers médias via Django
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
