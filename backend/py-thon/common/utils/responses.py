"""Réponses API standardisées pour toute l'application."""
from rest_framework.response import Response
from rest_framework import status as http_status


def success_response(data=None, message: str = '', status: int = 200) -> Response:
    """
    Réponse de succès standardisée.

    Format :
        {
            "success": true,
            "message": "...",
            "data": {...}
        }
    """
    payload = {'success': True}
    if message:
        payload['message'] = message
    if data is not None:
        payload['data'] = data
    return Response(payload, status=status)


def error_response(
    message: str,
    errors=None,
    status: int = 400,
    code: str = None
) -> Response:
    """
    Réponse d'erreur standardisée.

    Format :
        {
            "success": false,
            "message": "...",
            "code": "...",
            "errors": {...}
        }
    """
    payload = {'success': False, 'message': message}
    if code:
        payload['code'] = code
    if errors:
        payload['errors'] = errors
    return Response(payload, status=status)


def created_response(data=None, message: str = 'Créé avec succès') -> Response:
    """Réponse 201 Created."""
    return success_response(data=data, message=message, status=201)


def not_found_response(message: str = 'Ressource introuvable') -> Response:
    """Réponse 404."""
    return error_response(message=message, status=404, code='NOT_FOUND')


def forbidden_response(message: str = 'Accès interdit') -> Response:
    """Réponse 403."""
    return error_response(message=message, status=403, code='FORBIDDEN')


def paginated_response(queryset, serializer_class, request, context=None) -> Response:
    """
    Réponse paginée standardisée.
    Utilise la pagination DRF configurée dans les settings.
    """
    from rest_framework.pagination import PageNumberPagination

    paginator = PageNumberPagination()
    paginator.page_size = request.query_params.get('page_size', 25)
    page = paginator.paginate_queryset(queryset, request)

    ctx = {'request': request}
    if context:
        ctx.update(context)

    serializer = serializer_class(page, many=True, context=ctx)
    return paginator.get_paginated_response(serializer.data)
