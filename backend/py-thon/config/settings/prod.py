"""Settings de production."""
from .base import *
from django.core.exceptions import ImproperlyConfigured

DEBUG = False

if not ALLOWED_HOSTS or any(
    host in {'localhost', '127.0.0.1', '[::1]', '::1', '*'}
    for host in ALLOWED_HOSTS
):
    raise ImproperlyConfigured(
        'ALLOWED_HOSTS doit contenir uniquement les hôtes de production.'
    )

if not CORS_ALLOWED_ORIGINS or any(
    'localhost' in origin or '127.0.0.1' in origin
    for origin in CORS_ALLOWED_ORIGINS
):
    raise ImproperlyConfigured(
        'CORS_ALLOWED_ORIGINS doit contenir les origines de production.'
    )

if SECRET_KEY.startswith('replace-with-'):
    raise ImproperlyConfigured(
        'SECRET_KEY doit être remplacé par une clé aléatoire en production.'
    )

# Sécurité HTTPS
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
if not SECURE_SSL_REDIRECT:
    raise ImproperlyConfigured(
        'SECURE_SSL_REDIRECT doit rester activé en production.'
    )
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'
LOGGING['loggers']['apps']['level'] = 'INFO'
