from django.test import TestCase
from django.contrib.auth.models import User
from .models import Agent, Service, Utilisateur, Remarque


class MessagesPermissionsTestCase(TestCase):
    def setUp(self):
        """Configuration des tests"""
        # Créer un service
        self.service = Service.objects.create(
            nom="Service Test",
            description="Description test"
        )
        
        # Créer un admin - le signal va créer l'utilisateur automatiquement
        self.admin_agent = Agent.objects.create(
            matricule='ADMIN001',
            nom='Admin',
            postnom='Test',
            prenom='Admin',
            sexe='M',
            telephone='+243 81 234 5678',
            email='admin@test.com',
            adresse='Adresse admin',
            type_agent='ENSEIGNANT',
            etat=True,
            service=self.service
        )
        # Le signal a créé l'utilisateur, on récupère et on modifie le rôle
        self.admin_user = self.admin_agent.utilisateur.user
        self.admin_utilisateur = self.admin_agent.utilisateur
        self.admin_utilisateur.role = 'ADMIN'
        self.admin_utilisateur.must_change_password = False
        self.admin_utilisateur.save()
        # Définir le mot de passe
        self.admin_user.set_password('admin123')
        self.admin_user.save()
        
        # Créer un agent
        self.agent = Agent.objects.create(
            matricule='AGENT001',
            nom='Agent',
            postnom='Test',
            prenom='Agent',
            sexe='M',
            telephone='+243 81 234 5679',
            email='agent@test.com',
            adresse='Adresse agent',
            type_agent='ADMINISTRATIF',
            etat=True,
            service=self.service
        )
        self.agent_user = self.agent.utilisateur.user
        self.agent_utilisateur = self.agent.utilisateur
        self.agent_utilisateur.role = 'AGENT'
        self.agent_utilisateur.must_change_password = False
        self.agent_utilisateur.save()
        self.agent_user.set_password('agent123')
        self.agent_user.save()
        
        # Créer un enseignant
        self.enseignant_agent = Agent.objects.create(
            matricule='ENS001',
            nom='Enseignant',
            postnom='Test',
            prenom='Enseignant',
            sexe='F',
            telephone='+243 81 234 5680',
            email='enseignant@test.com',
            adresse='Adresse enseignant',
            type_agent='ENSEIGNANT',
            etat=True,
            service=self.service
        )
        self.enseignant_user = self.enseignant_agent.utilisateur.user
        self.enseignant_utilisateur = self.enseignant_agent.utilisateur
        self.enseignant_utilisateur.role = 'ENSEIGNANT'
        self.enseignant_utilisateur.must_change_password = False
        self.enseignant_utilisateur.save()
        self.enseignant_user.set_password('enseignant123')
        self.enseignant_user.save()
        
        # Créer des messages de test
        # Message de l'admin vers l'agent
        self.msg_admin_to_agent = Remarque.objects.create(
            categorie='MESSAGE',
            sujet='Message de admin à agent',
            message='Contenu du message',
            expediteur=self.admin_user,
            destinataire=self.agent_user,
            lu=False
        )
        
        # Message de l'agent vers l'admin
        self.msg_agent_to_admin = Remarque.objects.create(
            categorie='MESSAGE',
            sujet='Message de agent à admin',
            message='Contenu du message',
            expediteur=self.agent_user,
            destinataire=self.admin_user,
            lu=False
        )
        
        # Notification de l'admin vers l'agent
        self.notif_admin_to_agent = Remarque.objects.create(
            categorie='NOTIFICATION',
            sujet='Notification admin à agent',
            message='Contenu notification',
            expediteur=self.admin_user,
            destinataire=self.agent_user,
            lu=False
        )
    
    def test_agent_voit_seulement_messages_admin(self):
        """Test que l'agent ne voit que les messages envoyés par l'admin"""
        # Simuler la logique de la vue messages_view pour un agent
        user_role = self.agent_utilisateur.role
        self.assertEqual(user_role, 'AGENT')
        
        # Agents et enseignants ne voient que les messages envoyés par les administrateurs
        msgs = Remarque.objects.filter(
            destinataire=self.agent_user,
            expediteur__utilisateur__role='ADMIN',
            categorie='MESSAGE'
        ).select_related('expediteur', 'destinataire').order_by('-created_at')
        
        # L'agent ne doit voir que les messages où il est destinataire ET l'expediteur est admin
        self.assertEqual(msgs.count(), 1)
        self.assertEqual(msgs[0].sujet, 'Message de admin à agent')
        self.assertEqual(msgs[0].expediteur, self.admin_user)
    
    def test_enseignant_voit_seulement_messages_admin(self):
        """Test que l'enseignant ne voit que les messages envoyés par l'admin"""
        # Créer un message de l'admin vers l'enseignant
        Remarque.objects.create(
            categorie='MESSAGE',
            sujet='Message admin à enseignant',
            message='Contenu',
            expediteur=self.admin_user,
            destinataire=self.enseignant_user,
            lu=False
        )
        
        user_role = self.enseignant_utilisateur.role
        self.assertEqual(user_role, 'ENSEIGNANT')
        
        if user_role in ['AGENT', 'ENSEIGNANT']:
            msgs = Remarque.objects.filter(
                destinataire=self.enseignant_user,
                expediteur__utilisateur__role='ADMIN'
            ).select_related('expediteur', 'destinataire').order_by('-created_at')
        else:
            msgs = Remarque.objects.filter(
                destinataire=self.enseignant_user
            ).select_related('expediteur', 'destinataire').order_by('-created_at')
        
        self.assertEqual(msgs.count(), 1)
        self.assertEqual(msgs[0].expediteur, self.admin_user)
    
    def test_admin_voit_tous_messages(self):
        """Test que l'admin voit tous ses messages"""
        user_role = self.admin_utilisateur.role
        self.assertEqual(user_role, 'ADMIN')
        
        # Admin voit tous ses messages (envoyés et reçus)
        msgs = Remarque.objects.filter(
            destinataire=self.admin_user
        ).select_related('expediteur', 'destinataire').order_by('-created_at')
        
        # L'admin doit voir les messages reçus (1 dans ce cas)
        self.assertEqual(msgs.count(), 1)
    
    def test_agent_voit_seulement_notifications_admin(self):
        """Test que l'agent ne voit que les notifications envoyées par l'admin"""
        user_role = self.agent_utilisateur.role
        self.assertEqual(user_role, 'AGENT')
        
        if user_role in ['AGENT', 'ENSEIGNANT']:
            notifications = Remarque.objects.filter(
                destinataire=self.agent_user,
                categorie='NOTIFICATION',
                expediteur__utilisateur__role='ADMIN'
            ).order_by('-created_at')
        else:
            notifications = Remarque.objects.filter(
                destinataire=self.agent_user,
                categorie='NOTIFICATION'
            ).order_by('-created_at')
        
        self.assertEqual(notifications.count(), 1)
        self.assertEqual(notifications[0].sujet, 'Notification admin à agent')
        self.assertEqual(notifications[0].expediteur, self.admin_user)
    
    def test_enseignant_voit_seulement_notifications_admin(self):
        """Test que l'enseignant ne voit que les notifications envoyées par l'admin"""
        # Créer une notification de l'admin vers l'enseignant
        Remarque.objects.create(
            categorie='NOTIFICATION',
            sujet='Notif admin à enseignant',
            message='Contenu',
            expediteur=self.admin_user,
            destinataire=self.enseignant_user,
            lu=False
        )
        
        user_role = self.enseignant_utilisateur.role
        self.assertEqual(user_role, 'ENSEIGNANT')
        
        if user_role in ['AGENT', 'ENSEIGNANT']:
            notifications = Remarque.objects.filter(
                destinataire=self.enseignant_user,
                categorie='NOTIFICATION',
                expediteur__utilisateur__role='ADMIN'
            ).order_by('-created_at')
        else:
            notifications = Remarque.objects.filter(
                destinataire=self.enseignant_user,
                categorie='NOTIFICATION'
            ).order_by('-created_at')
        
        self.assertEqual(notifications.count(), 1)
        self.assertEqual(notifications[0].expediteur, self.admin_user)
    
    def test_admin_voit_toutes_notifications(self):
        """Test que l'admin voit toutes ses notifications"""
        user_role = self.admin_utilisateur.role
        self.assertEqual(user_role, 'ADMIN')
        
        # Créer une notification destinée à l'admin
        Remarque.objects.create(
            categorie='NOTIFICATION',
            sujet='Notification pour admin',
            message='Contenu',
            expediteur=self.admin_user,
            destinataire=self.admin_user,
            lu=False
        )
        
        # Admin voit toutes ses notifications
        notifications = Remarque.objects.filter(
            destinataire=self.admin_user,
            categorie='NOTIFICATION'
        ).order_by('-created_at')
        
        # L'admin doit voir toutes ses notifications (1 dans ce cas)
        self.assertEqual(notifications.count(), 1)
