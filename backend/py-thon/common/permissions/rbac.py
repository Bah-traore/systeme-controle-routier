"""Classes de permissions DRF pour le contrôle d'accès RBAC+ABAC."""
from rest_framework.permissions import BasePermission


class HasPermission(BasePermission):
    """
    Vérifie qu'un utilisateur possède une permission via son affectation active.

    Usage :
        class MaView(APIView):
            permission_classes = [HasPermission('pv.create')]
    """

    def __init__(self, permission_code: str):
        self.permission_code = permission_code

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return _utilisateur_a_permission(request.user, self.permission_code)

    def __call__(self):
        return self


def _utilisateur_a_permission(utilisateur, code_permission: str) -> bool:
    """
    Vérifie si un utilisateur a une permission via ses affectations actives.
    La vérification passe par : Affectation → Role → Permission.
    """
    from apps.organisation.models import Affectation
    from django.utils import timezone

    today = timezone.now().date()
    affectations_actives = Affectation.objects.filter(
        utilisateur=utilisateur,
        statut='ACTIVE',
        date_debut__lte=today,
    ).filter(
        models.Q(date_fin__isnull=True) | models.Q(date_fin__gte=today)
    ).select_related('role').prefetch_related('role__permissions')

    for affectation in affectations_actives:
        if affectation.role.permissions.filter(code=code_permission).exists():
            return True
    return False


class IsAgentTerrain(BasePermission):
    """L'utilisateur doit avoir le rôle AGENT_TERRAIN dans une affectation active."""

    message = "Accès réservé aux agents de terrain."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return _utilisateur_a_role(request.user, 'AGENT_TERRAIN')


class IsSuperviseur(BasePermission):
    """L'utilisateur doit avoir le rôle SUPERVISEUR dans une affectation active."""

    message = "Accès réservé aux superviseurs."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return _utilisateur_a_role(request.user, 'SUPERVISEUR')


class IsAdministrateur(BasePermission):
    """L'utilisateur doit avoir le rôle ADMINISTRATEUR dans une affectation active."""

    message = "Accès réservé aux administrateurs."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_staff or _utilisateur_a_role(request.user, 'ADMINISTRATEUR')


class IsAdminOuSuperviseur(BasePermission):
    """Superviseur ou Administrateur."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return (
            request.user.is_staff
            or _utilisateur_a_role(request.user, 'SUPERVISEUR')
            or _utilisateur_a_role(request.user, 'ADMINISTRATEUR')
        )


def _utilisateur_a_role(utilisateur, code_role: str) -> bool:
    """Vérifie si un utilisateur a un rôle actif via ses affectations."""
    from apps.organisation.models import Affectation
    from django.utils import timezone
    from django.db import models

    today = timezone.now().date()
    return Affectation.objects.filter(
        utilisateur=utilisateur,
        statut='ACTIVE',
        role__code=code_role,
        date_debut__lte=today,
    ).filter(
        models.Q(date_fin__isnull=True) | models.Q(date_fin__gte=today)
    ).exists()


# Import manquant
from django.db import models
