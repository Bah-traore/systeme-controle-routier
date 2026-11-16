"""Serializers pour l'application Identité."""
import hashlib
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Utilisateur, SessionSecurisee, AuthenticationMFA, ContexteAcces


class LoginSerializer(serializers.Serializer):
    """Serializer pour la connexion avec matricule + mot de passe."""
    matricule = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    empreinte_appareil = serializers.CharField(max_length=255, required=False, default='unknown')

    def validate(self, attrs):
        matricule = attrs.get('matricule')
        password = attrs.get('password')

        utilisateur = authenticate(
            request=self.context.get('request'),
            username=matricule,
            password=password
        )

        if not utilisateur:
            raise serializers.ValidationError(
                {'detail': 'Matricule ou mot de passe incorrect.'},
                code='authentication_failed'
            )
        if utilisateur.statut != 'ACTIF':
            raise serializers.ValidationError(
                {'detail': f'Compte {utilisateur.statut.lower()}. Contactez votre administrateur.'},
                code='account_disabled'
            )

        attrs['utilisateur'] = utilisateur
        return attrs


class MFAVerifySerializer(serializers.Serializer):
    """Serializer pour la vérification du code MFA."""
    code = serializers.CharField(max_length=8, min_length=6)
    session_token = serializers.CharField()  # Token temporaire pré-MFA


class ChangePasswordSerializer(serializers.Serializer):
    """Changement de mot de passe."""
    ancien_password = serializers.CharField(write_only=True)
    nouveau_password = serializers.CharField(write_only=True, min_length=10)
    confirmation_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['nouveau_password'] != attrs['confirmation_password']:
            raise serializers.ValidationError(
                {'confirmation_password': 'Les mots de passe ne correspondent pas.'}
            )
        return attrs


class UtilisateurSerializer(serializers.ModelSerializer):
    """Lecture des données d'un utilisateur (sans champs sensibles)."""
    nom_complet = serializers.ReadOnlyField()
    affectation_active = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Utilisateur
        fields = [
            'id', 'matricule', 'nom', 'prenom', 'nom_complet',
            'email', 'telephone', 'photo', 'statut',
            'date_creation', 'date_modification',
            'affectation_active', 'permissions',
        ]
        read_only_fields = ['id', 'date_creation', 'date_modification']

    def get_affectation_active(self, obj):
        affectation = obj.get_affectation_active()
        if not affectation:
            return None
        return {
            'id': str(affectation.id),
            'structure': {
                'id': str(affectation.structure.id),
                'code': affectation.structure.code,
                'nom': affectation.structure.nom,
                'type': affectation.structure.type,
            },
            'role': {
                'id': str(affectation.role.id),
                'code': affectation.role.code,
                'nom': affectation.role.nom,
            },
        }

    def get_permissions(self, obj):
        return list(obj.get_permissions_codes())


class UtilisateurCreateSerializer(serializers.ModelSerializer):
    """Création d'un nouvel utilisateur."""
    password = serializers.CharField(write_only=True, min_length=10)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = Utilisateur
        fields = [
            'matricule', 'nom', 'prenom', 'email',
            'telephone', 'password', 'confirm_password', 'statut',
        ]

    def validate(self, attrs):
        if attrs.get('password') != attrs.pop('confirm_password', None):
            raise serializers.ValidationError(
                {'confirm_password': 'Les mots de passe ne correspondent pas.'}
            )
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        utilisateur = Utilisateur(**validated_data)
        utilisateur.set_password(password)
        utilisateur.save()
        return utilisateur


class UtilisateurUpdateSerializer(serializers.ModelSerializer):
    """Mise à jour partielle d'un utilisateur."""
    class Meta:
        model = Utilisateur
        fields = ['nom', 'prenom', 'email', 'telephone', 'photo', 'statut']


class SessionSecuriseeSerializer(serializers.ModelSerializer):
    """Lecture des sessions (sans token hash)."""
    class Meta:
        model = SessionSecurisee
        fields = [
            'id', 'type_mfa', 'empreinte_appareil',
            'adresse_ip', 'date_creation', 'date_expiration', 'statut',
        ]
        read_only_fields = fields
