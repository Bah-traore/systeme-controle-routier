"""
Modèles de l'application Identité.

Gère les utilisateurs, les sessions sécurisées et l'authentification MFA.
AUTH_USER_MODEL = 'identite.Utilisateur'
"""
import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class StatutUtilisateur(models.TextChoices):
    ACTIF = 'ACTIF', 'Actif'
    SUSPENDU = 'SUSPENDU', 'Suspendu'
    REVOQUE = 'REVOQUE', 'Révoqué'
    INACTIF = 'INACTIF', 'Inactif'


class TypeMFA(models.TextChoices):
    TOTP = 'TOTP', 'Application TOTP (Google Authenticator, etc.)'
    SMS = 'SMS', 'Code par SMS'
    NONE = 'NONE', 'Aucun (non recommandé)'


class StatutSession(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    EXPIREE = 'EXPIREE', 'Expirée'
    REVOQUEE = 'REVOQUEE', 'Révoquée'


class UtilisateurManager(BaseUserManager):
    """Manager personnalisé pour le modèle Utilisateur."""

    def create_user(self, matricule: str, email: str, password: str = None, **extra_fields):
        """Crée et sauvegarde un utilisateur standard."""
        if not matricule:
            raise ValueError('Le matricule est obligatoire.')
        if not email:
            raise ValueError("L'adresse email est obligatoire.")
        email = self.normalize_email(email)
        user = self.model(matricule=matricule, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, matricule: str, email: str, password: str, **extra_fields):
        """Crée et sauvegarde un super-utilisateur."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('statut', StatutUtilisateur.ACTIF)

        if not extra_fields.get('is_staff'):
            raise ValueError('Le superutilisateur doit avoir is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Le superutilisateur doit avoir is_superuser=True.')

        return self.create_user(matricule, email, password, **extra_fields)


class Utilisateur(AbstractBaseUser, PermissionsMixin):
    """
    Utilisateur du Système de Contrôle Routier.

    Remplace le modèle utilisateur Django par défaut.
    L'authentification se fait via le matricule (et non le nom d'utilisateur).
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='Identifiant'
    )
    matricule = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Matricule',
        help_text='Identifiant unique de l\'agent (ex: AGT-2024-001)'
    )
    nom = models.CharField(max_length=100, verbose_name='Nom')
    prenom = models.CharField(max_length=100, verbose_name='Prénom')
    email = models.EmailField(unique=True, verbose_name='Adresse email')
    telephone = models.CharField(max_length=20, blank=True, verbose_name='Téléphone')
    photo = models.ImageField(
        upload_to='agents/photos/',
        null=True,
        blank=True,
        verbose_name='Photo'
    )

    statut = models.CharField(
        max_length=20,
        choices=StatutUtilisateur.choices,
        default=StatutUtilisateur.ACTIF,
        verbose_name='Statut'
    )

    # Champs Django auth
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Traçabilité
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    date_modification = models.DateTimeField(auto_now=True, verbose_name='Modifié le')
    derniere_connexion_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Dernière IP de connexion'
    )

    USERNAME_FIELD = 'matricule'
    REQUIRED_FIELDS = ['email', 'nom', 'prenom']

    objects = UtilisateurManager()

    class Meta:
        db_table = 'identite_utilisateur'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['nom', 'prenom']

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.matricule})"

    @property
    def nom_complet(self) -> str:
        """Retourne le nom complet de l'utilisateur."""
        return f"{self.prenom} {self.nom}"

    def get_affectation_active(self):
        """Retourne l'affectation active courante ou None."""
        today = timezone.now().date()
        return self.affectations.filter(
            statut='ACTIVE',
            date_debut__lte=today,
        ).filter(
            models.Q(date_fin__isnull=True) | models.Q(date_fin__gte=today)
        ).select_related('role', 'structure').first()

    def get_permissions_codes(self) -> set:
        """Retourne l'ensemble des codes de permission de l'utilisateur."""
        affectation = self.get_affectation_active()
        if not affectation:
            return set()
        return set(
            affectation.role.permissions.values_list('code', flat=True)
        )


class SessionSecurisee(models.Model):
    """
    Session sécurisée avec traçabilité complète.

    Le token JWT n'est jamais stocké en clair — uniquement son hash SHA256.
    Cela permet la révocation sans exposer le secret.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name='Utilisateur'
    )
    token_hash = models.CharField(
        max_length=64,
        verbose_name='Hash du token',
        help_text='SHA256 du refresh token JWT'
    )
    type_mfa = models.CharField(
        max_length=10,
        choices=TypeMFA.choices,
        default=TypeMFA.NONE,
        verbose_name='Type MFA utilisé'
    )
    empreinte_appareil = models.CharField(
        max_length=255,
        verbose_name='Empreinte de l\'appareil'
    )
    adresse_ip = models.GenericIPAddressField(verbose_name='Adresse IP')
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name='Créée le')
    date_expiration = models.DateTimeField(verbose_name='Expire le')
    statut = models.CharField(
        max_length=20,
        choices=StatutSession.choices,
        default=StatutSession.ACTIVE,
        verbose_name='Statut'
    )

    class Meta:
        db_table = 'identite_session_securisee'
        verbose_name = 'Session sécurisée'
        verbose_name_plural = 'Sessions sécurisées'
        ordering = ['-date_creation']

    def __str__(self):
        return f"Session {self.utilisateur.matricule} — {self.statut}"

    @property
    def est_active(self) -> bool:
        return (
            self.statut == StatutSession.ACTIVE
            and self.date_expiration > timezone.now()
        )

    def revoquer(self):
        """Révoquer cette session."""
        self.statut = StatutSession.REVOQUEE
        self.save(update_fields=['statut'])


class AuthenticationMFA(models.Model):
    """
    Configuration MFA d'un utilisateur.

    Stocke le secret TOTP chiffré ou le numéro SMS pour la vérification.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilisateur = models.OneToOneField(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='mfa',
        verbose_name='Utilisateur'
    )
    type_mfa = models.CharField(
        max_length=10,
        choices=TypeMFA.choices,
        default=TypeMFA.TOTP,
        verbose_name='Type MFA'
    )
    # TOTP
    secret_totp = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Secret TOTP',
        help_text='Base32 — à chiffrer en production'
    )
    # SMS
    telephone_sms = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Numéro SMS'
    )
    date_activation = models.DateTimeField(auto_now_add=True, verbose_name='Activé le')
    dernier_code_hash = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Hash du dernier code utilisé',
        help_text='Anti-rejeu : empêche la réutilisation d\'un code TOTP'
    )
    actif = models.BooleanField(default=True, verbose_name='Actif')

    class Meta:
        db_table = 'identite_authentication_mfa'
        verbose_name = 'Configuration MFA'
        verbose_name_plural = 'Configurations MFA'

    def __str__(self):
        return f"MFA {self.type_mfa} — {self.utilisateur.matricule}"


class ContexteAcces(models.Model):
    """
    Contexte d'un accès pour la politique ABAC.

    Enregistré à chaque connexion pour évaluation du niveau de risque.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='contextes_acces',
        verbose_name='Utilisateur'
    )
    adresse_ip = models.GenericIPAddressField(verbose_name='Adresse IP')
    empreinte_appareil = models.CharField(
        max_length=255,
        verbose_name='Empreinte appareil'
    )
    localisation = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Localisation approximative'
    )
    niveau_risque = models.IntegerField(
        default=0,
        verbose_name='Niveau de risque',
        help_text='0=faible, 1=modéré, 2=élevé, 3=critique'
    )
    date_heure = models.DateTimeField(auto_now_add=True, verbose_name='Date/heure')

    class Meta:
        db_table = 'identite_contexte_acces'
        verbose_name = 'Contexte d\'accès'
        verbose_name_plural = 'Contextes d\'accès'
        ordering = ['-date_heure']

    def __str__(self):
        return f"Accès {self.utilisateur.matricule} depuis {self.adresse_ip}"
