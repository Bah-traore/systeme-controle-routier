"""
Modèles abstraits partagés — Système de Contrôle Routier.

Toutes les entités métier héritent de BaseModel pour uniformité
et traçabilité. L'audit est géré par AuditableMixin.
"""
import uuid
from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    """
    Modèle de base pour toutes les entités métier.

    Fournit :
    - UUID comme clé primaire (immuable, globalement unique)
    - Timestamps de création et modification automatiques
    - Référence vers l'auteur de la création
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='Identifiant'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Créé le'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Modifié le'
    )
    created_by = models.ForeignKey(
        'identite.Utilisateur',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_created',
        verbose_name='Créé par'
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def __str__(self):
        return str(self.id)


class SoftDeleteManager(models.Manager):
    """Manager qui exclut automatiquement les enregistrements supprimés."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def with_deleted(self):
        """Inclure les enregistrements supprimés."""
        return super().get_queryset()

    def deleted_only(self):
        """Retourner uniquement les enregistrements supprimés."""
        return super().get_queryset().filter(is_deleted=True)


class SoftDeleteModel(BaseModel):
    """
    Extension de BaseModel avec suppression logique.

    Les enregistrements ne sont jamais réellement supprimés de la BDD.
    Le manager par défaut filtre is_deleted=True.
    """
    is_deleted = models.BooleanField(default=False, verbose_name='Supprimé')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Supprimé le')
    deleted_by = models.ForeignKey(
        'identite.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_deleted',
        verbose_name='Supprimé par'
    )

    objects = SoftDeleteManager()
    all_objects = models.Manager()  # Accès à tous les enregistrements

    class Meta:
        abstract = True

    def delete(self, deleted_by=None, *args, **kwargs):
        """Suppression logique — marque l'enregistrement sans le détruire."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if deleted_by:
            self.deleted_by = deleted_by
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def restore(self):
        """Restaurer un enregistrement supprimé logiquement."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def hard_delete(self, *args, **kwargs):
        """Suppression physique — à n'utiliser qu'en cas d'absolue nécessité."""
        super().delete(*args, **kwargs)
