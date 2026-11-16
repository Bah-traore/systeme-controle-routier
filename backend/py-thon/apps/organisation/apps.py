"""Configuration de l'application Organisation."""
from django.apps import AppConfig


class OrganisationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.organisation'
    label = 'organisation'
    verbose_name = 'Organisation'

    def ready(self):
        """Initialisation de l'application."""
        pass
