from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
import re


# ==========================
# SERVICE
# ==========================

class Service(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nom']
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
        indexes = [
            models.Index(fields=['nom']),
        ]

    def __str__(self):
        return self.nom


# ==========================
# AGENT
# ==========================

class Agent(models.Model):
    SEXE_CHOICES = (
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    )

    TYPE_AGENT = (
        ('ENSEIGNANT', 'Enseignant'),
        ('ADMINISTRATIF', 'Administratif'),
        ('DISCIPLINE', 'Préfet de discipline'),
    )

    matricule_validator = RegexValidator(
        regex=r'^[A-Z0-9]{3,20}$',
        message='Le matricule doit contenir 3 à 20 caractères alphanumériques en majuscules.'
    )

    phone_validator = RegexValidator(
        regex=r'^\+?[\d\s\-\(\)]{8,20}$',
        message='Numéro de téléphone invalide. Format attendu: +243 81 234 5678'
    )

    matricule = models.CharField(
        max_length=20,
        unique=True,
        validators=[matricule_validator]
    )
    nom = models.CharField(max_length=100)
    postnom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    sexe = models.CharField(max_length=10, choices=SEXE_CHOICES)
    telephone = models.CharField(
        max_length=30,
        validators=[phone_validator]
    )
    email = models.EmailField()
    adresse = models.CharField(max_length=255)
    photo = models.ImageField(upload_to='agents/', blank=True, null=True)
    type_agent = models.CharField(
        max_length=20,
        choices=TYPE_AGENT
    )
    etat = models.BooleanField(default=True)
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name="agents"
    )
    date_naissance = models.DateField(null=True, blank=True)
    lieu_naissance = models.CharField(max_length=100, blank=True)
    nationalite = models.CharField(max_length=50, default='Congolaise')
    province_origine = models.CharField(max_length=100, blank=True)
    territoire_origine = models.CharField(max_length=100, blank=True)
    secteur = models.CharField(max_length=100, blank=True)
    groupement = models.CharField(max_length=100, blank=True)
    village_origine = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nom', 'postnom', 'prenom']
        verbose_name = 'Agent'
        verbose_name_plural = 'Agents'
        indexes = [
            models.Index(fields=['matricule']),
            models.Index(fields=['type_agent']),
            models.Index(fields=['service']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['email'],
                name='unique_agent_email'
            ),
        ]

    def __str__(self):
        return f"{self.nom} {self.postnom} {self.prenom}"

    def nom_complet(self):
        """Retourne le nom complet de l'agent"""
        return f"{self.nom} {self.postnom} {self.prenom}"


# ==========================
# UTILISATEUR
# ==========================

class Utilisateur(models.Model):
    ROLE_CHOICES = (
        ('ADMIN', 'Administrateur'),
        ('SECRETAIRE', 'Secrétaire'),
        ('ENSEIGNANT', 'Enseignant'),
        ('AGENT', 'Agent'),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='utilisateur'
    )
    agent = models.OneToOneField(
        'Agent',
        on_delete=models.CASCADE,
        related_name='utilisateur'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    must_change_password = models.BooleanField(
        default=True,
        help_text='Indique si l\'utilisateur doit changer son mot de passe à la prochaine connexion'
    )
    mot_de_passe_temporaire = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text='Mot de passe temporaire visible par l\'administrateur (effacé après changement par l\'utilisateur)'
    )
    two_factor_secret = models.CharField(
        max_length=64,
        blank=True,
        default='',
        help_text='Clé secrète pour Google Authenticator (2FA)'
    )
    two_factor_enabled = models.BooleanField(
        default=False,
        help_text='Indique si le 2FA est activé pour cet utilisateur'
    )

    class Meta:
        ordering = ['user__username']
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        indexes = [
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        """Override save pour valider le rôle avant sauvegarde"""
        self.full_clean()
        super().save(*args, **kwargs)


# ==========================
# CLASSE
# ==========================

class Classe(models.Model):
    STATUS_CHOICES = (
        ('ACTIF', 'Actif'),
        ('INACTIF', 'Inactif'),
        ('ARCHIVE', 'Archivé'),
    )

    nom = models.CharField(max_length=50)
    niveau = models.CharField(max_length=50)
    effectif = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Nombre d\'élèves dans la classe'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIF'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['niveau', 'nom']
        verbose_name = 'Classe'
        verbose_name_plural = 'Classes'
        indexes = [
            models.Index(fields=['niveau']),
            models.Index(fields=['status']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['nom', 'niveau'],
                name='unique_classe_nom_niveau'
            ),
        ]

    def __str__(self):
        return f"{self.nom} ({self.niveau})"


# ==========================
# COURS
# ==========================

class Cours(models.Model):
    code_validator = RegexValidator(
        regex=r'^[A-Z]{2,4}[0-9]{1,3}$',
        message='Format du code: 2-4 lettres suivies de 1-3 chiffres (ex: MATH101)'
    )

    code = models.CharField(
        max_length=20,
        unique=True,
        validators=[code_validator]
    )
    libelle = models.CharField(max_length=150)
    coefficient = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['libelle']
        verbose_name = 'Cours'
        verbose_name_plural = 'Cours'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['actif']),
        ]

    def __str__(self):
        return f"{self.libelle} (x{self.coefficient})"

    def clean(self):
        """Validation personnalisée"""
        from django.core.exceptions import ValidationError
        if self.libelle:
            if self.libelle.isdigit():
                raise ValidationError({'libelle': 'Le libellé ne peut pas être uniquement numérique'})


# ==========================
# FONCTION
# ==========================

class Fonction(models.Model):
    libelle = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['libelle']
        verbose_name = 'Fonction'
        verbose_name_plural = 'Fonctions'

    def __str__(self):
        return self.libelle


# ==========================
# MOIS
# ==========================

class Mois(models.Model):
    libelle = models.CharField(max_length=50)
    mois_num = models.IntegerField()
    annee = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['annee', 'mois_num']
        verbose_name = 'Mois'
        verbose_name_plural = 'Mois'
        constraints = [
            models.UniqueConstraint(
                fields=['mois_num', 'annee'],
                name='unique_mois_annee'
            ),
        ]

    def __str__(self):
        return f"{self.libelle} {self.annee}"


# ==========================
# SESSION DE PRESTATION
# ==========================

class SessionPrestation(models.Model):
    STATUT_SESSION = (
        ('EN_COURS', 'En cours'),
        ('TERMINEE', 'Terminée'),
    )

    date = models.DateField()
    heure_ouverture = models.TimeField(null=True, blank=True)
    heure_fermeture = models.TimeField(null=True, blank=True)
    heure_limite = models.TimeField(
        null=True,
        blank=True,
        help_text='Heure limite pour arriver à l\'heure (après cette heure, l\'agent est en retard)'
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_SESSION,
        default='EN_COURS'
    )
    ouvert_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sessions_ouvertes"
    )
    cloture_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions_cloturees"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Session de Prestation'
        verbose_name_plural = 'Sessions de Prestation'
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['statut']),
        ]

    def __str__(self):
        return f"Session du {self.date.strftime('%d/%m/%Y')} - {self.get_statut_display()}"

    def nombre_agents_presents(self):
        return self.prestations.filter(statut__in=['PRESENT', 'RETARD', 'TERMINE']).count()

    def nombre_prestations_enseignants(self):
        return PrestationEnseignant.objects.filter(prestation__session=self).count()


# ==========================
# PRESTATION GENERALE
# ==========================

class Prestation(models.Model):
    STATUS_PRESENT = 'PRESENT'
    STATUS_RETARD = 'RETARD'
    STATUS_ABSENT = 'ABSENT'
    STATUS_EN_COURS = 'EN_COURS'

    STATUT = (
        (STATUS_PRESENT, 'Présent'),
        (STATUS_RETARD, 'Retard'),
        (STATUS_ABSENT, 'Absent'),
        (STATUS_EN_COURS, 'En cours'),
    )

    session = models.ForeignKey(
        SessionPrestation,
        on_delete=models.CASCADE,
        related_name="prestations",
        null=True,
        blank=True
    )
    agent = models.ForeignKey(
        'Agent',
        on_delete=models.PROTECT,
        related_name="prestations"
    )
    date = models.DateField()
    heure_arrivee = models.TimeField(
        blank=True,
        null=True
    )
    heure_depart = models.TimeField(
        blank=True,
        null=True
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT
    )
    observation = models.TextField(
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-heure_arrivee']
        verbose_name = 'Prestation'
        verbose_name_plural = 'Prestations'
        indexes = [
            models.Index(fields=['agent', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['statut']),
        ]
        constraints = []

    def __str__(self):
        return f"{self.agent.nom_complet()} - {self.date.strftime('%d/%m/%Y')} ({self.get_statut_display()})"

    def duree_prestation(self):
        """Calcule la durée de la prestation si l'agent est parti"""
        if self.heure_depart and self.heure_arrivee:
            from datetime import datetime
            arrivee = datetime.combine(self.date, self.heure_arrivee)
            depart = datetime.combine(self.date, self.heure_depart)
            duree = depart - arrivee
            heures = duree.seconds // 3600
            minutes = (duree.seconds % 3600) // 60
            return f"{heures}h{minutes:02d}"
        return None

    def get_statut_display_custom(self):
        """Retourne un statut détaillé selon l'heure d'arrivée et de départ"""
        if self.statut == self.STATUS_EN_COURS:
            return "En cours"
        elif self.statut == self.STATUS_ABSENT:
            return "Absent"
        elif self.statut == self.STATUS_RETARD:
            return "Retard"
        elif self.statut == self.STATUS_PRESENT:
            # Vérifier si c'est vraiment présent ou retard selon l'heure limite
            if self.session and self.session.heure_limite and self.heure_arrivee:
                from datetime import datetime
                limite = datetime.combine(self.date, self.session.heure_limite)
                arrivee = datetime.combine(self.date, self.heure_arrivee)
                if arrivee > limite:
                    return "Retard"
            return "Présent"
        return self.get_statut_display()

    def clean(self):
        """Validation personnalisée"""
        from django.core.exceptions import ValidationError
        if self.heure_depart and self.heure_arrivee:
            if self.heure_depart <= self.heure_arrivee:
                raise ValidationError({
                    'heure_depart': 'L\'heure de départ doit être postérieure à l\'heure d\'arrivée.'
                })


# ==========================
# PRESTATION ENSEIGNANT
# ==========================

class PrestationEnseignant(models.Model):
    prestation = models.ForeignKey(
        Prestation,
        on_delete=models.CASCADE,
        related_name="prestations_cours"
    )
    cours = models.ForeignKey(
        Cours,
        on_delete=models.PROTECT,
        related_name="prestations"
    )
    classe = models.ForeignKey(
        Classe,
        on_delete=models.PROTECT,
        related_name="prestations"
    )
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    observation = models.TextField(
        blank=True,
        null=True
    )
    valide = models.BooleanField(
        default=False,
        help_text='Indique si la prestation enseignant a été validée par un administrateur/secrétaire'
    )
    valide_par = models.ForeignKey(
        Utilisateur,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='prestations_enseignants_validees'
    )
    date_validation = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['prestation__date', 'heure_debut']
        verbose_name = 'Prestation Enseignant'
        verbose_name_plural = 'Prestations Enseignants'
        indexes = [
            models.Index(fields=['cours']),
            models.Index(fields=['classe']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['prestation', 'cours', 'classe'],
                name='unique_prestation_cours_classe'
            ),
        ]

    def __str__(self):
        return f"{self.cours.libelle} - {self.classe.nom} ({self.prestation.date.strftime('%d/%m/%Y')})"

    def duree_cours(self):
        """Calcule la durée du cours"""
        from datetime import datetime
        debut = datetime.combine(self.prestation.date, self.heure_debut)
        fin = datetime.combine(self.prestation.date, self.heure_fin)
        duree = fin - debut
        heures = duree.seconds // 3600
        minutes = (duree.seconds % 3600) // 60
        return f"{heures}h{minutes:02d}"

    def clean(self):
        """Validation personnalisée"""
        from django.core.exceptions import ValidationError
        if self.heure_fin <= self.heure_debut:
            raise ValidationError({
                'heure_fin': 'L\'heure de fin doit être postérieure à l\'heure de début.'
            })


# ==========================
# REMARQUE (MESSAGERIE)
# ==========================

class Remarque(models.Model):
    CATEGORIE_CHOICES = (
        ('MESSAGE', 'Message'),
        ('APPROBATION', 'Demande d\'approbation'),
        ('NOTIFICATION', 'Notification'),
    )

    categorie = models.CharField(
        max_length=20,
        choices=CATEGORIE_CHOICES,
        default='MESSAGE'
    )
    sujet = models.CharField(max_length=120)
    message = models.TextField()
    expediteur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='remarques_envoyees'
    )
    destinataire = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='remarques_recues'
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='reponses'
    )
    lu = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Remarque'
        verbose_name_plural = 'Remarques'
        indexes = [
            models.Index(fields=['categorie', 'lu']),
            models.Index(fields=['expediteur', 'destinataire']),
        ]

    def __str__(self):
        return f"{self.sujet} - {self.expediteur.username} → {self.destinataire.username}"


# ==========================
# ACTIVITY LOG
# ==========================

class ActivityLog(models.Model):
    ACTION_CHOICES = (
        ('CREATE', 'Création'),
        ('UPDATE', 'Modification'),
        ('DELETE', 'Suppression'),
        ('MESSAGE', 'Message'),
        ('LOGIN', 'Connexion'),
        ('LOGOUT', 'Déconnexion'),
    )

    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    object_repr = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    actor = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='activity_logs'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Journal d\'activité'
        verbose_name_plural = 'Journaux d\'activité'
        indexes = [
            models.Index(fields=['action', 'model_name']),
            models.Index(fields=['actor', 'created_at']),
        ]

    def __str__(self):
        return f"{self.get_action_display()} - {self.model_name} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"


# ==========================
# CODE TEMPORAIRE (AUTH QR)
# ==========================

class CodeTemporaire(models.Model):
    """Code unique généré pour l'authentification par QR code"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='codes_temporaires'
    )
    code = models.CharField(max_length=6, unique=True)
    est_utilise = models.BooleanField(default=False)
    cree_le = models.DateTimeField(auto_now_add=True)
    expire_le = models.DateTimeField()
    
    class Meta:
        ordering = ['-cree_le']
        verbose_name = 'Code temporaire'
        verbose_name_plural = 'Codes temporaires'
    
    def __str__(self):
        return f"Code {self.code} - {self.user.username} - {'Utilisé' if self.est_utilise else 'Actif'}"
    
    def est_valide(self):
        """Vérifie si le code est encore valide (non utilisé et non expiré)"""
        from django.utils import timezone
        return not self.est_utilise and self.expire_le > timezone.now()


# ==========================
# MESSAGING SETTINGS
# ==========================

class MessagingSettings(models.Model):
    envoi_bloque = models.BooleanField(
        default=False,
        help_text='Bloquer l\'envoi de messages entre utilisateurs'
    )
    message_blocage = models.TextField(
        blank=True,
        help_text='Message affiché aux utilisateurs quand l\'envoi est bloqué'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Paramètre de messagerie'
        verbose_name_plural = 'Paramètres de messagerie'

    def __str__(self):
        return f"Paramètres messagerie (Bloqué: {self.envoi_bloque})"

    @classmethod
    def current(cls):
        """Retourne les paramètres actuels (singleton)"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


# ==========================
# SIGNAL : Création automatique
# d'un Utilisateur lié à un Agent
# ==========================

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.hashers import make_password
import secrets


@receiver(post_save, sender=Agent)
def creer_utilisateur(sender, instance, created, **kwargs):
    """
    Crée automatiquement un utilisateur Django lors de la création d'un agent.
    Utilise le mot de passe par défaut 'demo123' pour tous les utilisateurs.
    """
    if created:
        username = instance.matricule.lower()
        password = 'demo123'

        user = User.objects.create_user(
            username=username,
            password=password,
            email=instance.email,
            first_name=instance.prenom,
            last_name=f"{instance.nom} {instance.postnom}"
        )

        # Mapper le type_agent vers un rôle Utilisateur valide
        role_mapping = {
            'ENSEIGNANT': 'ENSEIGNANT',
            'ADMINISTRATIF': 'SECRETAIRE',
            'DISCIPLINE': 'AGENT',
        }
        role = role_mapping.get(instance.type_agent, 'AGENT')

        Utilisateur.objects.create(
            user=user,
            agent=instance,
            role=role,
            must_change_password=True,
            mot_de_passe_temporaire=password
        )

        print(f"Utilisateur créé pour {instance.nom_complet()}")
        print(f"Username: {username}")
        print(f"Mot de passe: {password}")