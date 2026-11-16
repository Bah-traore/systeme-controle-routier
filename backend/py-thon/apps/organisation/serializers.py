"""Serializers pour l'application Organisation."""
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import (
    StructureAdministrative, ZoneControle,
    Permission, Role, Affectation
)


class StructureAdministrativeSerializer(serializers.ModelSerializer):
    chemin = serializers.SerializerMethodField()
    nb_agents = serializers.SerializerMethodField()

    class Meta:
        model = StructureAdministrative
        fields = [
            'id', 'code', 'nom', 'type', 'parent',
            'adresse', 'telephone', 'email', 'actif',
            'date_creation', 'chemin', 'nb_agents',
        ]
        read_only_fields = ['id', 'date_creation']

    def get_chemin(self, obj):
        return obj.get_chemin()

    def get_nb_agents(self, obj):
        return obj.affectations.filter(statut='ACTIVE').count()


class StructureAdministrativeListSerializer(serializers.ModelSerializer):
    """Version légère pour les listes."""
    class Meta:
        model = StructureAdministrative
        fields = ['id', 'code', 'nom', 'type', 'actif']


class ZoneControleSerializer(serializers.ModelSerializer):
    structure_detail = StructureAdministrativeListSerializer(source='structure', read_only=True)

    class Meta:
        model = ZoneControle
        fields = [
            'id', 'code', 'nom', 'structure', 'structure_detail',
            'geometrie', 'description', 'actif', 'date_creation',
        ]
        read_only_fields = ['id', 'date_creation']


class ZoneControleGeoSerializer(GeoFeatureModelSerializer):
    """Serializer GeoJSON pour affichage cartographique."""
    class Meta:
        model = ZoneControle
        geo_field = 'geometrie'
        fields = ['id', 'code', 'nom', 'actif']


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'code', 'nom', 'ressource', 'action', 'description']
        read_only_fields = ['id']


class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(),
        many=True,
        write_only=True,
        source='permissions',
        required=False
    )

    class Meta:
        model = Role
        fields = ['id', 'code', 'nom', 'permissions', 'permission_ids', 'description', 'actif']
        read_only_fields = ['id']


class RoleListSerializer(serializers.ModelSerializer):
    nb_permissions = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ['id', 'code', 'nom', 'nb_permissions', 'actif']

    def get_nb_permissions(self, obj):
        return obj.permissions.count()


class AffectationSerializer(serializers.ModelSerializer):
    utilisateur_detail = serializers.SerializerMethodField()
    structure_detail = StructureAdministrativeListSerializer(source='structure', read_only=True)
    role_detail = RoleListSerializer(source='role', read_only=True)
    est_active = serializers.ReadOnlyField()

    class Meta:
        model = Affectation
        fields = [
            'id', 'utilisateur', 'utilisateur_detail',
            'structure', 'structure_detail',
            'zone', 'role', 'role_detail',
            'statut', 'date_debut', 'date_fin',
            'numero_decision', 'notes', 'est_active', 'date_creation',
        ]
        read_only_fields = ['id', 'date_creation', 'created_by']

    def get_utilisateur_detail(self, obj):
        return {
            'id': str(obj.utilisateur.id),
            'matricule': obj.utilisateur.matricule,
            'nom_complet': obj.utilisateur.nom_complet,
        }

    def validate(self, attrs):
        date_debut = attrs.get('date_debut')
        date_fin = attrs.get('date_fin')
        if date_debut and date_fin and date_fin < date_debut:
            raise serializers.ValidationError(
                {'date_fin': 'La date de fin doit être après la date de début.'}
            )
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class AffectationListSerializer(serializers.ModelSerializer):
    """Version légère pour les listes."""
    utilisateur_matricule = serializers.CharField(source='utilisateur.matricule', read_only=True)
    structure_nom = serializers.CharField(source='structure.nom', read_only=True)
    role_code = serializers.CharField(source='role.code', read_only=True)
    est_active = serializers.ReadOnlyField()

    class Meta:
        model = Affectation
        fields = [
            'id', 'utilisateur_matricule', 'structure_nom',
            'role_code', 'statut', 'date_debut', 'date_fin', 'est_active',
        ]
