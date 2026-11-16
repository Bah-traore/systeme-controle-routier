"""Vues API pour l'application Identité."""
import hashlib
import logging
from datetime import timedelta

import pyotp
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError

from common.permissions.rbac import IsAdministrateur
from common.utils.responses import success_response, error_response, created_response
from .models import Utilisateur, SessionSecurisee, StatutSession
from .serializers import (
    LoginSerializer,
    MFAVerifySerializer,
    ChangePasswordSerializer,
    UtilisateurSerializer,
    UtilisateurCreateSerializer,
    UtilisateurUpdateSerializer,
    SessionSecuriseeSerializer,
)

logger = logging.getLogger(__name__)


def _get_client_ip(request) -> str:
    """Extrait l'adresse IP réelle du client."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


def _get_device_fingerprint(request) -> str:
    """Génère une empreinte d'appareil à partir des headers."""
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    accept_lang = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    raw = f"{user_agent}|{accept_lang}"
    return hashlib.sha256(raw.encode()).hexdigest()[:64]


class LoginView(APIView):
    """
    POST /api/v1/auth/login/

    Authentification avec matricule + mot de passe.
    Si MFA activé, retourne un challenge ; sinon, les tokens JWT directement.
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return error_response(
                message='Identifiants invalides.',
                errors=serializer.errors,
                status=401
            )

        utilisateur = serializer.validated_data['utilisateur']
        empreinte = serializer.validated_data.get('empreinte_appareil') or \
                    _get_device_fingerprint(request)

        # Vérifier si MFA est activé
        try:
            mfa = utilisateur.mfa
            if mfa.actif and mfa.type_mfa != 'NONE':
                # Retourner un challenge MFA (token temporaire)
                temp_token = RefreshToken.for_user(utilisateur)
                temp_token['mfa_required'] = True
                temp_token['mfa_type'] = mfa.type_mfa
                return success_response(
                    data={
                        'mfa_required': True,
                        'mfa_type': mfa.type_mfa,
                        'session_token': str(temp_token.access_token),
                    },
                    message='Vérification MFA requise.',
                    status=200
                )
        except Utilisateur.mfa.RelatedObjectDoesNotExist:
            pass

        # Pas de MFA → générer les tokens JWT
        return self._emit_tokens(utilisateur, empreinte, request, mfa_type='NONE')

    def _emit_tokens(self, utilisateur, empreinte: str, request, mfa_type: str):
        """Génère et enregistre les tokens JWT + session."""
        refresh = RefreshToken.for_user(utilisateur)
        access = refresh.access_token

        # Enregistrer la session
        token_hash = hashlib.sha256(str(refresh).encode()).hexdigest()
        SessionSecurisee.objects.create(
            utilisateur=utilisateur,
            token_hash=token_hash,
            type_mfa=mfa_type,
            empreinte_appareil=empreinte,
            adresse_ip=_get_client_ip(request),
            date_expiration=timezone.now() + timedelta(days=7),
        )

        # Mettre à jour la dernière IP
        utilisateur.derniere_connexion_ip = _get_client_ip(request)
        utilisateur.save(update_fields=['derniere_connexion_ip'])

        logger.info("Connexion réussie : %s depuis %s", utilisateur.matricule, _get_client_ip(request))

        return success_response(
            data={
                'access': str(access),
                'refresh': str(refresh),
                'utilisateur': UtilisateurSerializer(utilisateur).data,
            },
            message='Connexion réussie.'
        )


class MFAVerifyView(APIView):
    """
    POST /api/v1/auth/mfa/verify/

    Vérifie le code MFA et retourne les tokens définitifs.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = MFAVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(message='Données invalides.', errors=serializer.errors)

        code = serializer.validated_data['code']

        try:
            mfa = request.user.mfa
        except Exception:
            return error_response(message='MFA non configuré.', status=400)

        # Vérifier code TOTP
        if mfa.type_mfa == 'TOTP':
            totp = pyotp.TOTP(mfa.secret_totp)
            code_hash = hashlib.sha256(code.encode()).hexdigest()

            if mfa.dernier_code_hash == code_hash:
                return error_response(
                    message='Ce code a déjà été utilisé. Attendez le prochain.',
                    status=400
                )
            if not totp.verify(code, valid_window=1):
                return error_response(message='Code MFA invalide.', status=401)

            # Marquer le code comme utilisé (anti-rejeu)
            mfa.dernier_code_hash = code_hash
            mfa.save(update_fields=['dernier_code_hash'])

        empreinte = _get_device_fingerprint(request)
        refresh = RefreshToken.for_user(request.user)

        token_hash = hashlib.sha256(str(refresh).encode()).hexdigest()
        SessionSecurisee.objects.create(
            utilisateur=request.user,
            token_hash=token_hash,
            type_mfa=mfa.type_mfa,
            empreinte_appareil=empreinte,
            adresse_ip=_get_client_ip(request),
            date_expiration=timezone.now() + timedelta(days=7),
        )

        return success_response(
            data={
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'utilisateur': UtilisateurSerializer(request.user).data,
            },
            message='Authentification MFA réussie.'
        )


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/

    Révoque le refresh token et la session associée.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return error_response(message='Le refresh token est requis.')

        try:
            token = RefreshToken(refresh_token)
            token_hash = hashlib.sha256(str(refresh_token).encode()).hexdigest()

            # Révoquer la session
            SessionSecurisee.objects.filter(
                utilisateur=request.user,
                token_hash=token_hash,
                statut=StatutSession.ACTIVE
            ).update(statut=StatutSession.REVOQUEE)

            token.blacklist()
        except TokenError:
            pass  # Token déjà invalide

        logger.info("Déconnexion : %s", request.user.matricule)
        return success_response(message='Déconnexion réussie.')


class MeView(APIView):
    """
    GET /api/v1/auth/me/

    Retourne les informations de l'utilisateur authentifié avec son
    affectation active et ses permissions.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UtilisateurSerializer(request.user, context={'request': request})
        return success_response(data=serializer.data)


class ChangePasswordView(APIView):
    """
    POST /api/v1/auth/change-password/

    Changement de mot de passe avec vérification de l'ancien.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(message='Données invalides.', errors=serializer.errors)

        if not request.user.check_password(serializer.validated_data['ancien_password']):
            return error_response(
                message='Ancien mot de passe incorrect.',
                status=400
            )

        request.user.set_password(serializer.validated_data['nouveau_password'])
        request.user.save(update_fields=['password'])

        logger.info("Mot de passe changé : %s", request.user.matricule)
        return success_response(message='Mot de passe modifié avec succès.')


class UtilisateurViewSet(viewsets.ModelViewSet):
    """
    CRUD complet des utilisateurs.
    Réservé aux administrateurs.
    """
    queryset = Utilisateur.objects.all().order_by('nom', 'prenom')
    permission_classes = [IsAuthenticated, IsAdministrateur]

    def get_serializer_class(self):
        if self.action == 'create':
            return UtilisateurCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UtilisateurUpdateSerializer
        return UtilisateurSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # Filtres
        statut = self.request.query_params.get('statut')
        if statut:
            qs = qs.filter(statut=statut)
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                models.Q(nom__icontains=search) |
                models.Q(prenom__icontains=search) |
                models.Q(matricule__icontains=search) |
                models.Q(email__icontains=search)
            )
        return qs

    @action(detail=True, methods=['post'], url_path='suspendre')
    def suspendre(self, request, pk=None):
        """Suspendre un utilisateur."""
        utilisateur = self.get_object()
        utilisateur.statut = 'SUSPENDU'
        utilisateur.save(update_fields=['statut'])
        return success_response(message=f'Utilisateur {utilisateur.matricule} suspendu.')

    @action(detail=True, methods=['post'], url_path='reactiver')
    def reactiver(self, request, pk=None):
        """Réactiver un utilisateur suspendu."""
        utilisateur = self.get_object()
        utilisateur.statut = 'ACTIF'
        utilisateur.save(update_fields=['statut'])
        return success_response(message=f'Utilisateur {utilisateur.matricule} réactivé.')

    @action(detail=True, methods=['get'], url_path='sessions')
    def sessions(self, request, pk=None):
        """Lister les sessions d'un utilisateur."""
        utilisateur = self.get_object()
        sessions = utilisateur.sessions.order_by('-date_creation')[:20]
        return success_response(data=SessionSecuriseeSerializer(sessions, many=True).data)


# Import manquant
from django.db import models
