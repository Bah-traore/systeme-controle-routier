"""Gestionnaire d'exceptions DRF personnalisé."""
import logging
from rest_framework.views import exception_handler
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Gestionnaire d'exceptions DRF personnalisé.
    Normalise toutes les erreurs au format standard :
    { "success": false, "message": "...", "errors": {...} }
    """
    response = exception_handler(exc, context)

    if response is not None:
        message = _extract_message(response.data)
        response.data = {
            'success': False,
            'message': message,
            'errors': response.data if isinstance(response.data, dict) else {'detail': response.data},
        }
    else:
        # Erreur non gérée par DRF → 500
        logger.exception("Erreur interne non gérée : %s", exc)
        response = Response(
            {
                'success': False,
                'message': 'Erreur interne du serveur.',
                'code': 'INTERNAL_SERVER_ERROR',
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response


def _extract_message(data) -> str:
    """Extrait un message lisible depuis les données d'erreur DRF."""
    if isinstance(data, dict):
        if 'detail' in data:
            return str(data['detail'])
        if 'non_field_errors' in data:
            errors = data['non_field_errors']
            return str(errors[0]) if errors else 'Erreur de validation.'
        return 'Erreur de validation des données.'
    if isinstance(data, list):
        return str(data[0]) if data else 'Erreur inconnue.'
    return str(data)
