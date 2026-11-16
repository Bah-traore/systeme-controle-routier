"""Administration Django pour l'app Identité."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import Utilisateur, SessionSecurisee, AuthenticationMFA, ContexteAcces


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    model = Utilisateur
    list_display = [
        'matricule', 'nom', 'prenom', 'email',
        'statut_badge', 'is_staff', 'date_creation'
    ]
    list_filter = ['statut', 'is_staff', 'is_superuser', 'date_creation']
    search_fields = ['matricule', 'nom', 'prenom', 'email']
    ordering = ['nom', 'prenom']
    readonly_fields = ['id', 'date_creation', 'date_modification', 'derniere_connexion_ip']

    fieldsets = (
        ('Identité', {'fields': ('id', 'matricule', 'nom', 'prenom', 'email', 'telephone', 'photo')}),
        ('Statut', {'fields': ('statut', 'is_active', 'is_staff', 'is_superuser')}),
        ('Authentification', {'fields': ('password',)}),
        ('Groupes et permissions', {'fields': ('groups', 'user_permissions')}),
        ('Traçabilité', {'fields': ('date_creation', 'date_modification', 'derniere_connexion_ip')}),
    )

    add_fieldsets = (
        ('Création d\'utilisateur', {
            'classes': ('wide',),
            'fields': ('matricule', 'nom', 'prenom', 'email', 'password1', 'password2', 'statut'),
        }),
    )

    USERNAME_FIELD = 'matricule'

    @admin.display(description='Statut')
    def statut_badge(self, obj):
        colors = {
            'ACTIF': '#28a745',
            'SUSPENDU': '#ffc107',
            'REVOQUE': '#dc3545',
            'INACTIF': '#6c757d',
        }
        color = colors.get(obj.statut, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.statut
        )


@admin.register(SessionSecurisee)
class SessionSecuriseeAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'adresse_ip', 'type_mfa', 'statut', 'date_creation', 'date_expiration']
    list_filter = ['statut', 'type_mfa', 'date_creation']
    search_fields = ['utilisateur__matricule', 'adresse_ip']
    readonly_fields = ['id', 'token_hash', 'date_creation']
    ordering = ['-date_creation']

    def has_add_permission(self, request):
        return False


@admin.register(AuthenticationMFA)
class AuthenticationMFAAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'type_mfa', 'actif', 'date_activation']
    list_filter = ['type_mfa', 'actif']
    search_fields = ['utilisateur__matricule']
    readonly_fields = ['id', 'date_activation']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('utilisateur')


@admin.register(ContexteAcces)
class ContexteAccesAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'adresse_ip', 'niveau_risque', 'localisation', 'date_heure']
    list_filter = ['niveau_risque', 'date_heure']
    search_fields = ['utilisateur__matricule', 'adresse_ip']
    readonly_fields = ['id', 'date_heure']
    ordering = ['-date_heure']

    def has_add_permission(self, request):
        return False
