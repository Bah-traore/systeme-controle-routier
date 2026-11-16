"""Configuration de l'application Identité."""
from django.apps import AppConfig


class IdentiteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.identite'
    label = 'identite'
    verbose_name = 'Identité'

    def ready(self):
        """Importer les signaux au démarrage de l'application."""
        try:
            import apps.identite.signals  # noqa: F401
        except ImportError:
            pass
