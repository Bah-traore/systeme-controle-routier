"""
Modèles de l'application Organisation.

Gère les structures administratives, zones de contrôle, rôles,
permissions atomiques et affectations des agents.
"""
import uuid
from django.db import models
from django.contrib.gis.db import models as gis_models
from django.utils import timezone


class TypeStructure(models.TextChoices):
    NATIONALE = 'NATIONALE', 'Direction Nationale'
    REGIONALE = 'REGIONALE', 'Direction Régionale'
    LOCALE = 'LOCALE', 'Service Local'
    UNITE = 'UNITE', 'Unité de Contrôle'


class StatutAffectation(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    SUSPENDUE = 'SUSPENDUE', 'Suspendue'
    TERMINEE = 'TERMINEE', 'Terminée'
    EN_ATTENTE = 'EN_ATTENTE', 'En attente'


class StructureAdministrative(models.Model):
    """
    Structure administrative dans la hiérarchie nationale.

    La hiérarchie est : Direction Nationale → Direction Régionale
                        → Service Local → Unité de Contrôle.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Code',
        help_text='Code unique (ex: DN-001, DR-BKO-001)'
    )
    nom = models.CharField(max_length=200, verbose_name='Nom')
    type = models.CharField(
        max_length=20,
        choices=TypeStructure.choices,
        verbose_name='Type de structure'
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='sous_structures',
        verbose_name='Structure parente'
    )
    adresse = models.TextField(blank=True, verbose_name='Adresse')
    telephone = models.CharField(max_length=20, blank=True, verbose_name='Téléphone')
    email = models.EmailField(blank=True, verbose_name='Email')
    actif = models.BooleanField(default=True, verbose_name='Actif')
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name='Créée le')
    date_modification = models.DateTimeField(auto_now=True, verbose_name='Modifiée le')

    class Meta:
        db_table = 'organisation_structure'
        verbose_name = 'Structure administrative'
        verbose_name_plural = 'Structures administratives'
        ordering = ['type', 'nom']

    def __str__(self):
        return f"[{self.code}] {self.nom}"

    def get_chemin(self) -> str:
        """Retourne le chemin hiérarchique complet."""
        parts = [self.nom]
        parent = self.parent
        while parent:
            parts.insert(0, parent.nom)
            parent = parent.parent
        return ' > '.join(parts)

    def get_descendants(self):
        """Retourne toutes les sous-structures récursivement."""
        descendants = []
        for sous_structure in self.sous_structures.filter(actif=True):
            descendants.append(sous_structure)
            descendants.extend(sous_structure.get_descendants())
        return descendants


class ZoneControle(models.Model):
    """
    Zone géographique de compétence d'une structure de contrôle.

    La géométrie est stockée comme polygone WGS84 (EPSG:4326).
    Utilisée pour la géolocalisation des missions et agents.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True, verbose_name='Code')
    nom = models.CharField(max_length=200, verbose_name='Nom de la zone')
    structure = models.ForeignKey(
        StructureAdministrative,
        on_delete=models.PROTECT,
        related_name='zones',
        verbose_name='Structure compétente'
    )
    geometrie = gis_models.PolygonField(
        null=True,
        blank=True,
        srid=4326,
        verbose_name='Délimitation géographique',
        help_text='Polygone WGS84 (GeoJSON)'
    )
    description = models.TextField(blank=True, verbose_name='Description')
    actif = models.BooleanField(default=True, verbose_name='Active')
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name='Créée le')

    class Meta:
        db_table = 'organisation_zone_controle'
        verbose_name = 'Zone de contrôle'
        verbose_name_plural = 'Zones de contrôle'
        ordering = ['nom']

    def __str__(self):
        return f"[{self.code}] {self.nom} ({self.structure.code})"


class Permission(models.Model):
    """
    Permission atomique du système (principe du moindre privilège).

    Format du code : <ressource>.<action>
    Exemples : 'pv.create', 'mission.view', 'utilisateur.admin'
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Code',
        help_text='Format: <ressource>.<action> (ex: pv.create)'
    )
    nom = models.CharField(max_length=200, verbose_name='Libellé')
    ressource = models.CharField(
        max_length=50,
        verbose_name='Ressource',
        help_text='Ex: pv, mission, utilisateur, rapport'
    )
    action = models.CharField(
        max_length=20,
        verbose_name='Action',
        help_text='Ex: create, read, update, delete, approve, sign'
    )
    description = models.TextField(blank=True, verbose_name='Description')

    class Meta:
        db_table = 'organisation_permission'
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'
        ordering = ['ressource', 'action']
        unique_together = [['ressource', 'action']]

    def __str__(self):
        return f"{self.code} — {self.nom}"


class Role(models.Model):
    """
    Rôle fonctionnel regroupant des permissions.

    Les rôles prédéfinis : AGENT_TERRAIN, SUPERVISEUR, ADMINISTRATEUR,
    DIRECTEUR, ANALYSTE, JURISTE.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Code',
        help_text='Ex: AGENT_TERRAIN, SUPERVISEUR, ADMINISTRATEUR'
    )
    nom = models.CharField(max_length=100, verbose_name='Nom du rôle')
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name='roles',
        verbose_name='Permissions accordées'
    )
    description = models.TextField(blank=True, verbose_name='Description')
    actif = models.BooleanField(default=True, verbose_name='Actif')

    class Meta:
        db_table = 'organisation_role'
        verbose_name = 'Rôle'
        verbose_name_plural = 'Rôles'
        ordering = ['nom']

    def __str__(self):
        return f"[{self.code}] {self.nom}"


class Affectation(models.Model):
    """
    Affectation d'un utilisateur à une structure avec un rôle.

    Une affectation est active quand :
    - statut = ACTIVE
    - date_debut <= aujourd'hui
    - date_fin >= aujourd'hui ou date_fin est null
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilisateur = models.ForeignKey(
        'identite.Utilisateur',
        on_delete=models.CASCADE,
        related_name='affectations',
        verbose_name='Utilisateur'
    )
    structure = models.ForeignKey(
        StructureAdministrative,
        on_delete=models.PROTECT,
        related_name='affectations',
        verbose_name='Structure'
    )
    zone = models.ForeignKey(
        ZoneControle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='affectations',
        verbose_name='Zone de compétence'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name='affectations',
        verbose_name='Rôle'
    )
    statut = models.CharField(
        max_length=20,
        choices=StatutAffectation.choices,
        default=StatutAffectation.ACTIVE,
        verbose_name='Statut'
    )
    date_debut = models.DateField(verbose_name='Date de début')
    date_fin = models.DateField(null=True, blank=True, verbose_name='Date de fin')
    numero_decision = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='N° de décision d\'affectation'
    )
    notes = models.TextField(blank=True, verbose_name='Notes')
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name='Créée le')
    created_by = models.ForeignKey(
        'identite.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        related_name='affectations_crees',
        verbose_name='Créée par'
    )

    class Meta:
        db_table = 'organisation_affectation'
        verbose_name = 'Affectation'
        verbose_name_plural = 'Affectations'
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.utilisateur.matricule} → {self.structure.code} [{self.role.code}]"

    @property
    def est_active(self) -> bool:
        """Vérifie si l'affectation est actuellement active."""
        today = timezone.now().date()
        return (
            self.statut == StatutAffectation.ACTIVE
            and self.date_debut <= today
            and (self.date_fin is None or self.date_fin >= today)
        )

    def terminer(self, date_fin=None):
        """Termine l'affectation."""
        self.date_fin = date_fin or timezone.now().date()
        self.statut = StatutAffectation.TERMINEE
        self.save(update_fields=['date_fin', 'statut'])
