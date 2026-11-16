"""Administration Django pour l'app Organisation."""
from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from .models import StructureAdministrative, ZoneControle, Permission, Role, Affectation


@admin.register(StructureAdministrative)
class StructureAdministrativeAdmin(admin.ModelAdmin):
    list_display = ['code', 'nom', 'type', 'parent', 'actif', 'date_creation']
    list_filter = ['type', 'actif']
    search_fields = ['code', 'nom']
    readonly_fields = ['id', 'date_creation', 'date_modification']
    ordering = ['type', 'nom']
    fieldsets = (
        ('Identification', {'fields': ('id', 'code', 'nom', 'type', 'parent')}),
        ('Contact', {'fields': ('adresse', 'telephone', 'email')}),
        ('Statut', {'fields': ('actif',)}),
        ('Dates', {'fields': ('date_creation', 'date_modification')}),
    )


@admin.register(ZoneControle)
class ZoneControleAdmin(GISModelAdmin):
    list_display = ['code', 'nom', 'structure', 'actif', 'date_creation']
    list_filter = ['actif', 'structure__type']
    search_fields = ['code', 'nom', 'structure__nom']
    readonly_fields = ['id', 'date_creation']


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['code', 'nom', 'ressource', 'action']
    list_filter = ['ressource', 'action']
    search_fields = ['code', 'nom']
    readonly_fields = ['id']
    ordering = ['ressource', 'action']

    def has_delete_permission(self, request, obj=None):
        """Empêcher la suppression de permissions en production."""
        return request.user.is_superuser


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['code', 'nom', 'nb_permissions', 'actif']
    list_filter = ['actif']
    search_fields = ['code', 'nom']
    readonly_fields = ['id']
    filter_horizontal = ['permissions']

    @admin.display(description='Nb permissions')
    def nb_permissions(self, obj):
        return obj.permissions.count()


@admin.register(Affectation)
class AffectationAdmin(admin.ModelAdmin):
    list_display = [
        'utilisateur', 'structure', 'role', 'statut',
        'date_debut', 'date_fin', 'est_active'
    ]
    list_filter = ['statut', 'role', 'structure__type']
    search_fields = [
        'utilisateur__matricule', 'utilisateur__nom',
        'structure__code', 'numero_decision'
    ]
    readonly_fields = ['id', 'date_creation', 'created_by']
    ordering = ['-date_debut']
    autocomplete_fields = ['utilisateur', 'structure', 'role']
    fieldsets = (
        ('Affectation', {'fields': ('id', 'utilisateur', 'structure', 'zone', 'role')}),
        ('Période', {'fields': ('date_debut', 'date_fin', 'statut')}),
        ('Référence', {'fields': ('numero_decision', 'notes')}),
        ('Traçabilité', {'fields': ('date_creation', 'created_by')}),
    )

    @admin.display(description='Active ?', boolean=True)
    def est_active(self, obj):
        return obj.est_active
