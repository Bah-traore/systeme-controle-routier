"""Vues API pour l'application Organisation."""
import logging
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from common.permissions.rbac import IsAdministrateur, IsAdminOuSuperviseur
from common.utils.responses import success_response, error_response
from .models import StructureAdministrative, ZoneControle, Permission, Role, Affectation
from .serializers import (
    StructureAdministrativeSerializer,
    StructureAdministrativeListSerializer,
    ZoneControleSerializer,
    ZoneControleGeoSerializer,
    PermissionSerializer,
    RoleSerializer,
    RoleListSerializer,
    AffectationSerializer,
    AffectationListSerializer,
)

logger = logging.getLogger(__name__)


class StructureAdministrativeViewSet(viewsets.ModelViewSet):
    """
    CRUD des structures administratives.
    Lecture : tous les utilisateurs authentifiés.
    Écriture : administrateurs uniquement.
    """
    queryset = StructureAdministrative.objects.all().select_related('parent')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'actif', 'parent']
    search_fields = ['nom', 'code']
    ordering_fields = ['nom', 'type', 'date_creation']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdministrateur()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'list':
            return StructureAdministrativeListSerializer
        return StructureAdministrativeSerializer

    @action(detail=True, methods=['get'], url_path='sous-structures')
    def sous_structures(self, request, pk=None):
        """Liste des sous-structures d'une structure."""
        structure = self.get_object()
        sous = structure.sous_structures.filter(actif=True)
        return success_response(
            data=StructureAdministrativeListSerializer(sous, many=True).data
        )

    @action(detail=True, methods=['get'], url_path='zones')
    def zones(self, request, pk=None):
        """Zones de contrôle d'une structure."""
        structure = self.get_object()
        zones = structure.zones.filter(actif=True)
        return success_response(
            data=ZoneControleSerializer(zones, many=True).data
        )

    @action(detail=True, methods=['get'], url_path='agents')
    def agents(self, request, pk=None):
        """Agents affectés à une structure."""
        structure = self.get_object()
        from apps.identite.serializers import UtilisateurSerializer
        affectations = structure.affectations.filter(statut='ACTIVE').select_related(
            'utilisateur', 'role'
        )
        data = [
            {
                'utilisateur': {
                    'id': str(a.utilisateur.id),
                    'matricule': a.utilisateur.matricule,
                    'nom_complet': a.utilisateur.nom_complet,
                },
                'role': a.role.code,
                'date_debut': a.date_debut,
            }
            for a in affectations
        ]
        return success_response(data=data)


class ZoneControleViewSet(viewsets.ModelViewSet):
    """CRUD des zones de contrôle avec support GeoJSON."""
    queryset = ZoneControle.objects.all().select_related('structure')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['structure', 'actif']
    search_fields = ['nom', 'code']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdministrateur()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.query_params.get('format') == 'geojson':
            return ZoneControleGeoSerializer
        return ZoneControleSerializer


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Liste et détail des permissions (lecture seule).
    Les permissions sont gérées via les fixtures/migrations.
    """
    queryset = Permission.objects.all().order_by('ressource', 'action')
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated, IsAdministrateur]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = ['ressource', 'action']
    search_fields = ['code', 'nom']


class RoleViewSet(viewsets.ModelViewSet):
    """CRUD des rôles."""
    queryset = Role.objects.prefetch_related('permissions')
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = ['actif']
    search_fields = ['code', 'nom']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdministrateur()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'list':
            return RoleListSerializer
        return RoleSerializer

    @action(detail=True, methods=['post'], url_path='ajouter-permission')
    def ajouter_permission(self, request, pk=None):
        """Ajouter une permission à un rôle."""
        role = self.get_object()
        permission_id = request.data.get('permission_id')
        try:
            perm = Permission.objects.get(id=permission_id)
            role.permissions.add(perm)
            return success_response(message=f'Permission {perm.code} ajoutée au rôle {role.code}.')
        except Permission.DoesNotExist:
            return error_response(message='Permission introuvable.', status=404)

    @action(detail=True, methods=['post'], url_path='retirer-permission')
    def retirer_permission(self, request, pk=None):
        """Retirer une permission d'un rôle."""
        role = self.get_object()
        permission_id = request.data.get('permission_id')
        try:
            perm = Permission.objects.get(id=permission_id)
            role.permissions.remove(perm)
            return success_response(message=f'Permission {perm.code} retirée du rôle {role.code}.')
        except Permission.DoesNotExist:
            return error_response(message='Permission introuvable.', status=404)


class AffectationViewSet(viewsets.ModelViewSet):
    """
    CRUD des affectations agents-structure-rôle.
    """
    queryset = Affectation.objects.all().select_related(
        'utilisateur', 'structure', 'role', 'zone'
    )
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['utilisateur', 'structure', 'role', 'statut']
    search_fields = ['utilisateur__matricule', 'structure__code', 'numero_decision']
    ordering_fields = ['date_debut', 'date_creation']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminOuSuperviseur()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'list':
            return AffectationListSerializer
        return AffectationSerializer

    @action(detail=True, methods=['post'], url_path='terminer')
    def terminer(self, request, pk=None):
        """Terminer une affectation."""
        affectation = self.get_object()
        affectation.terminer()
        return success_response(message='Affectation terminée.')

    @action(detail=False, methods=['get'], url_path='actives')
    def actives(self, request):
        """Liste des affectations actuellement actives."""
        from django.utils import timezone
        from django.db.models import Q
        today = timezone.now().date()
        qs = self.get_queryset().filter(
            statut='ACTIVE',
            date_debut__lte=today,
        ).filter(Q(date_fin__isnull=True) | Q(date_fin__gte=today))
        serializer = AffectationListSerializer(qs, many=True)
        return success_response(data=serializer.data)
