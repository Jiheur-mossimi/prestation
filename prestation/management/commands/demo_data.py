import os
import sys
from datetime import date, time, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from prestation.models import (
    Service, Agent, Classe, Cours, Fonction, Mois,
    Utilisateur, SessionPrestation, Prestation, PrestationEnseignant,
    Remarque
)


class Command(BaseCommand):
    help = 'Génère des données de démonstration pour l\'application de prestations'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('🔄 Génération des données de démonstration...'))
        
        # Désactiver le signal pour éviter les créations automatiques
        from django.db.models.signals import post_save
        from prestation.models import creer_utilisateur
        
        # Nettoyage préalable
        self.stdout.write(self.style.NOTICE('🧹 Nettoyage des données existantes...'))
        PrestationEnseignant.objects.all().delete()
        Prestation.objects.all().delete()
        SessionPrestation.objects.all().delete()
        Utilisateur.objects.all().delete()
        User.objects.filter(is_superuser=False, username__startswith='ens').delete()
        # Garder l'admin existant
        
        # ==========================================
        # 1. CRÉATION DES SERVICES
        # ==========================================
        self.stdout.write(self.style.NOTICE('📁 Création des services...'))
        services_data = [
            {'nom': 'Enseignement Secondaire', 'description': 'Service d\'enseignement pour le secondaire'},
            {'nom': 'Enseignement Primaire', 'description': 'Service d\'enseignement pour le primaire'},
            {'nom': 'Administration', 'description': 'Service administratif de l\'établissement'},
            {'nom': 'Discipline', 'description': 'Service de discipline et surveillance'},
            {'nom': 'Comptabilité', 'description': 'Service de comptabilité et finances'},
            {'nom': 'Bibliothèque', 'description': 'Service de gestion de la bibliothèque'},
            {'nom': 'Santé Scolaire', 'description': 'Service médical et infirmier'},
            {'nom': 'Informatique', 'description': 'Service informatique et maintenance'},
        ]
        services = []
        for s in services_data:
            service, created = Service.objects.get_or_create(nom=s['nom'], defaults=s)
            if created:
                self.stdout.write(f'  ✅ Service créé : {s["nom"]}')
            services.append(service)

        # ==========================================
        # 2. CRÉATION DES CLASSES
        # ==========================================
        self.stdout.write(self.style.NOTICE('🏫 Création des classes...'))
        classes_data = [
            {'nom': '7ème A', 'niveau': 'Secondaire', 'effectif': 45},
            {'nom': '7ème B', 'niveau': 'Secondaire', 'effectif': 42},
            {'nom': '8ème A', 'niveau': 'Secondaire', 'effectif': 48},
            {'nom': '8ème B', 'niveau': 'Secondaire', 'effectif': 40},
            {'nom': '1ère A', 'niveau': 'Secondaire', 'effectif': 35},
            {'nom': '1ère B', 'niveau': 'Secondaire', 'effectif': 38},
            {'nom': '2ème A', 'niveau': 'Secondaire', 'effectif': 32},
            {'nom': '2ème B', 'niveau': 'Secondaire', 'effectif': 30},
            {'nom': '3ème A', 'niveau': 'Secondaire', 'effectif': 28},
            {'nom': '3ème B', 'niveau': 'Secondaire', 'effectif': 25},
            {'nom': '4ème A', 'niveau': 'Secondaire', 'effectif': 22},
            {'nom': '4ème B', 'niveau': 'Secondaire', 'effectif': 20},
            {'nom': '5ème A', 'niveau': 'Secondaire', 'effectif': 18},
            {'nom': '5ème B', 'niveau': 'Secondaire', 'effectif': 15},
            {'nom': '6ème A', 'niveau': 'Secondaire', 'effectif': 12},
            {'nom': '6ème B', 'niveau': 'Secondaire', 'effectif': 10},
            {'nom': '1ère Primaire', 'niveau': 'Primaire', 'effectif': 55},
            {'nom': '2ème Primaire', 'niveau': 'Primaire', 'effectif': 52},
            {'nom': '3ème Primaire', 'niveau': 'Primaire', 'effectif': 50},
            {'nom': '4ème Primaire', 'niveau': 'Primaire', 'effectif': 48},
            {'nom': '5ème Primaire', 'niveau': 'Primaire', 'effectif': 45},
            {'nom': '6ème Primaire', 'niveau': 'Primaire', 'effectif': 42},
        ]
        for c in classes_data:
            classe, created = Classe.objects.get_or_create(
                nom=c['nom'], niveau=c['niveau'],
                defaults={'effectif': c['effectif'], 'status': 'ACTIF'}
            )
            if created:
                self.stdout.write(f'  ✅ Classe créée : {c["nom"]} ({c["niveau"]})')

        # ==========================================
        # 3. CRÉATION DES FONCTIONS
        # ==========================================
        self.stdout.write(self.style.NOTICE('📋 Création des fonctions...'))
        fonctions_data = [
            {'libelle': 'Professeur', 'description': 'Enseignant titulaire'},
            {'libelle': 'Directeur', 'description': 'Directeur de l\'établissement'},
            {'libelle': 'Préfet', 'description': 'Préfet de discipline'},
            {'libelle': 'Secrétaire', 'description': 'Secrétaire de direction'},
            {'libelle': 'Comptable', 'description': 'Comptable de l\'établissement'},
            {'libelle': 'Bibliothécaire', 'description': 'Gestionnaire de la bibliothèque'},
            {'libelle': 'Infirmier', 'description': 'Infirmier scolaire'},
            {'libelle': 'Informaticien', 'description': 'Technicien informatique'},
            {'libelle': 'Surveillant', 'description': 'Surveillant général'},
            {'libelle': 'Agent d\'entretien', 'description': 'Agent de maintenance'},
        ]
        for f in fonctions_data:
            obj, created = Fonction.objects.get_or_create(libelle=f['libelle'], defaults=f)
            if created:
                self.stdout.write(f'  ✅ Fonction créée : {f["libelle"]}')

        # ==========================================
        # 4. CRÉATION DES MOIS
        # ==========================================
        self.stdout.write(self.style.NOTICE('📅 Création des mois...'))
        mois_names = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                      'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
        for i, name in enumerate(mois_names, 1):
            Mois.objects.get_or_create(
                mois_num=i, annee=2026,
                defaults={'libelle': f'{name} 2026'}
            )
        self.stdout.write('  ✅ 12 mois créés')

        # ==========================================
        # 5. CRÉATION DES COURS
        # ==========================================
        self.stdout.write(self.style.NOTICE('📚 Création des cours...'))
        cours_data = [
            {'code': 'MATH1', 'libelle': 'Mathématiques 1ère', 'coefficient': 5, 'description': 'Algèbre et géométrie'},
            {'code': 'MATH2', 'libelle': 'Mathématiques 2ème', 'coefficient': 5, 'description': 'Algèbre avancée'},
            {'code': 'FRAN1', 'libelle': 'Français 1ère', 'coefficient': 4, 'description': 'Grammaire et littérature'},
            {'code': 'FRAN2', 'libelle': 'Français 2ème', 'coefficient': 4, 'description': 'Littérature française'},
            {'code': 'PHYS1', 'libelle': 'Physique 1ère', 'coefficient': 4, 'description': 'Mécanique et électricité'},
            {'code': 'CHIM1', 'libelle': 'Chimie 1ère', 'coefficient': 3, 'description': 'Chimie générale'},
            {'code': 'BIOL1', 'libelle': 'Biologie 1ère', 'coefficient': 3, 'description': 'Biologie générale'},
            {'code': 'HIST1', 'libelle': 'Histoire 1ère', 'coefficient': 2, 'description': 'Histoire générale'},
            {'code': 'GEO1', 'libelle': 'Géographie 1ère', 'coefficient': 2, 'description': 'Géographie générale'},
            {'code': 'ANGL1', 'libelle': 'Anglais 1ère', 'coefficient': 3, 'description': 'Anglais général'},
            {'code': 'INFO1', 'libelle': 'Informatique 1ère', 'coefficient': 2, 'description': 'Bases de l\'informatique'},
            {'code': 'EDPH1', 'libelle': 'Éducation Physique', 'coefficient': 1, 'description': 'Sport et éducation physique'},
            {'code': 'SVT1', 'libelle': 'Sciences de la Vie', 'coefficient': 3, 'description': 'SVT'},
            {'code': 'PHIL1', 'libelle': 'Philosophie', 'coefficient': 2, 'description': 'Philosophie générale'},
            {'code': 'LAT1', 'libelle': 'Latin', 'coefficient': 2, 'description': 'Latin débutant'},
        ]
        for c in cours_data:
            cours, created = Cours.objects.get_or_create(code=c['code'], defaults=c)
            if created:
                self.stdout.write(f'  ✅ Cours créé : {c["libelle"]} ({c["code"]})')

        # ==========================================
        # 6. CRÉATION DES AGENTS
        # ==========================================
        self.stdout.write(self.style.NOTICE('👥 Création des agents...'))
        
        # Désactiver le signal de création d'utilisateur
        post_save.disconnect(creer_utilisateur, sender=Agent)
        
        enseignants_data = [
            {'nom': 'MUKENDI', 'postnom': 'KABILA', 'prenom': 'Jean-Pierre'},
            {'nom': 'TSHIMANGA', 'postnom': 'MUTOMBO', 'prenom': 'Marie'},
            {'nom': 'KABONGO', 'postnom': 'KALALA', 'prenom': 'Paul'},
            {'nom': 'MWAMBA', 'postnom': 'TSHIBA', 'prenom': 'Esther'},
            {'nom': 'ILUNGA', 'postnom': 'KABEYA', 'prenom': 'David'},
            {'nom': 'KATUMBA', 'postnom': 'MUSAU', 'prenom': 'Nicole'},
            {'nom': 'MBUYI', 'postnom': 'KALONDA', 'prenom': 'Robert'},
            {'nom': 'KASANDA', 'postnom': 'MPOYI', 'prenom': 'Béatrice'},
            {'nom': 'MUTOMBO', 'postnom': 'NTUMBA', 'prenom': 'Pierre'},
            {'nom': 'KAPENGA', 'postnom': 'MBIYA', 'prenom': 'Sophie'},
            {'nom': 'LUKUSA', 'postnom': 'KABAMBA', 'prenom': 'Albert'},
            {'nom': 'NGOYI', 'postnom': 'MALANGU', 'prenom': 'Catherine'},
            {'nom': 'BANZA', 'postnom': 'KITOKO', 'prenom': 'Joseph'},
            {'nom': 'MASANGU', 'postnom': 'MUKALA', 'prenom': 'Florence'},
            {'nom': 'KANDA', 'postnom': 'MBOLO', 'prenom': 'Emmanuel'},
            {'nom': 'TSHIBANGU', 'postnom': 'MUTEBA', 'prenom': 'Rachel'},
            {'nom': 'MULUMBA', 'postnom': 'KASONGO', 'prenom': 'François'},
            {'nom': 'KALUME', 'postnom': 'MWAMBA', 'prenom': 'Marguerite'},
            {'nom': 'KABEYA', 'postnom': 'KIBADI', 'prenom': 'André'},
            {'nom': 'MBUYAMBA', 'postnom': 'TSHIBOLA', 'prenom': 'Louise'},
            {'nom': 'KALALA', 'postnom': 'MUPANDA', 'prenom': 'Henri'},
            {'nom': 'MUTSHIPAYI', 'postnom': 'MUKENDI', 'prenom': 'Alice'},
            {'nom': 'KABUNDI', 'postnom': 'LUKUSA', 'prenom': 'Georges'},
            {'nom': 'NSENGA', 'postnom': 'MALUNDA', 'prenom': 'Thérèse'},
            {'nom': 'KASONGO', 'postnom': 'KABONGO', 'prenom': 'Michel'},
        ]

        administratifs_data = [
            {'nom': 'KABANGE', 'postnom': 'MUTEBA', 'prenom': 'Innocent'},
            {'nom': 'LUBALA', 'postnom': 'MWENZE', 'prenom': 'Jacqueline'},
            {'nom': 'KALUBI', 'postnom': 'KATEPA', 'prenom': 'Marcel'},
            {'nom': 'MUKANYA', 'postnom': 'TSHITENGE', 'prenom': 'Odette'},
            {'nom': 'KAPITA', 'postnom': 'MUKUNA', 'prenom': 'Patrice'},
            {'nom': 'KAYEMBE', 'postnom': 'NSOMPO', 'prenom': 'Gisèle'},
            {'nom': 'MUKENDI', 'postnom': 'KABEYA', 'prenom': 'Fidèle'},
            {'nom': 'KALONGA', 'postnom': 'MUTOMBO', 'prenom': 'Rosine'},
        ]

        agents_enseignants = []
        for i, a in enumerate(enseignants_data):
            service = services[i % 2]
            matricule = f'ENS{str(i+1).zfill(3)}'
            sexe = 'M' if i % 2 == 0 else 'F'
            agent, created = Agent.objects.get_or_create(
                matricule=matricule,
                defaults={
                    'nom': a['nom'], 'postnom': a['postnom'], 'prenom': a['prenom'],
                    'sexe': sexe,
                    'telephone': f'+2438112345{i+61:02d}',
                    'email': f'{a["prenom"].lower()}.{a["postnom"].lower()}@ecole.cd',
                    'adresse': f'{100 + i} Avenue de l\'École, Kinshasa',
                    'type_agent': 'ENSEIGNANT', 'etat': True,
                    'service': service, 'nationalite': 'Congolaise',
                    'date_naissance': date(1970 + (i % 25), 1 + (i % 12), 1 + (i % 28)),
                    'province_origine': 'Kinshasa',
                }
            )
            if created:
                self.stdout.write(f'  ✅ Enseignant créé : {agent.nom_complet()} ({matricule})')
            agents_enseignants.append(agent)

        agents_admin = []
        for i, a in enumerate(administratifs_data):
            service = services[2 + (i % 3)]
            matricule = f'ADM{str(i+1).zfill(3)}'
            sexe = 'M' if i % 2 == 0 else 'F'
            agent, created = Agent.objects.get_or_create(
                matricule=matricule,
                defaults={
                    'nom': a['nom'], 'postnom': a['postnom'], 'prenom': a['prenom'],
                    'sexe': sexe,
                    'telephone': f'+2438223456{i+11:02d}',
                    'email': f'{a["prenom"].lower()}.{a["postnom"].lower()}@ecole.cd',
                    'adresse': f'{200 + i} Avenue du Centre, Kinshasa',
                    'type_agent': 'ADMINISTRATIF', 'etat': True,
                    'service': service, 'nationalite': 'Congolaise',
                    'date_naissance': date(1975 + i, 3 + i, 15),
                    'province_origine': 'Kinshasa',
                }
            )
            if created:
                self.stdout.write(f'  ✅ Admin créé : {agent.nom_complet()} ({matricule})')
            agents_admin.append(agent)

        # ==========================================
        # 7. CRÉATION DE L'ADMIN SUPER USER
        # ==========================================
        self.stdout.write(self.style.NOTICE('🔑 Création des utilisateurs...'))
        
        admin_agent, _ = Agent.objects.get_or_create(
            matricule='ADMIN',
            defaults={
                'nom': 'ADMIN', 'postnom': 'SYSTEME', 'prenom': 'Super',
                'sexe': 'M', 'telephone': '+243899999991', 'email': 'admin@ecole.cd',
                'adresse': 'Bureau de Direction', 'type_agent': 'ADMINISTRATIF',
                'etat': True, 'service': services[2], 'nationalite': 'Congolaise',
            }
        )
        
        # Créer l'utilisateur admin
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@ecole.cd', 'first_name': 'Super', 'last_name': 'Admin',
                      'is_staff': True, 'is_superuser': True}
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
        
        Utilisateur.objects.get_or_create(
            user=admin_user, agent=admin_agent,
            defaults={'role': 'ADMIN', 'must_change_password': False}
        )
        self.stdout.write(self.style.SUCCESS('  ✅ Admin - Identifiants: admin / admin123'))

        # Créer secrétaire
        secre_user, _ = User.objects.get_or_create(
            username='secretaire',
            defaults={'email': 'secretaire@ecole.cd', 'first_name': 'Innocent', 'last_name': 'Kabange'}
        )
        if created or not Utilisateur.objects.filter(user=secre_user).exists():
            secre_user.set_password('secret123')
            secre_user.save()
            Utilisateur.objects.get_or_create(
                user=secre_user, agent=agents_admin[0],
                defaults={'role': 'SECRETAIRE', 'must_change_password': False}
            )
        self.stdout.write(self.style.SUCCESS('  ✅ Secrétaire - Identifiants: secretaire / secret123'))

        # Créer préfet
        prefet_user, _ = User.objects.get_or_create(
            username='prefet',
            defaults={'email': 'prefet@ecole.cd', 'first_name': 'Odette', 'last_name': 'Mukanya'}
        )
        if not Utilisateur.objects.filter(user=prefet_user).exists():
            prefet_user.set_password('prefet123')
            prefet_user.save()
            Utilisateur.objects.get_or_create(
                user=prefet_user, agent=agents_admin[3],
                defaults={'role': 'PREFET', 'must_change_password': False}
            )
        self.stdout.write(self.style.SUCCESS('  ✅ Préfet - Identifiants: prefet / prefet123'))

        # Créer enseignant de test
        ens_user, _ = User.objects.get_or_create(
            username='enseignant',
            defaults={'email': 'enseignant@ecole.cd', 'first_name': 'Jean-Pierre', 'last_name': 'Mukendi'}
        )
        if not Utilisateur.objects.filter(user=ens_user).exists():
            ens_user.set_password('ens123')
            ens_user.save()
            Utilisateur.objects.get_or_create(
                user=ens_user, agent=agents_enseignants[0],
                defaults={'role': 'ENSEIGNANT', 'must_change_password': False}
            )
        self.stdout.write(self.style.SUCCESS('  ✅ Enseignant - Identifiants: enseignant / ens123'))

        # Réactiver le signal
        post_save.connect(creer_utilisateur, sender=Agent)
        
        # ==========================================
        # RÉSULTAT FINAL
        # ==========================================
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('🎉 DONNÉES DE DÉMONSTRATION GÉNÉRÉES AVEC SUCCÈS !'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f'📊 Résumé :')
        self.stdout.write(f'   ✅ {Service.objects.count()} services')
        self.stdout.write(f'   ✅ {Classe.objects.count()} classes')
        self.stdout.write(f'   ✅ {Cours.objects.count()} cours')
        self.stdout.write(f'   ✅ {Fonction.objects.count()} fonctions')
        self.stdout.write(f'   ✅ {Mois.objects.count()} mois')
        self.stdout.write(f'   ✅ {Agent.objects.count()} agents')
        self.stdout.write(f'   ✅ {Utilisateur.objects.count()} utilisateurs')
        self.stdout.write(f'\n🔐 Comptes de connexion :')
        self.stdout.write(f'   👑 admin / admin123')
        self.stdout.write(f'   📋 secretaire / secret123')
        self.stdout.write(f'   📚 enseignant / ens123')
        self.stdout.write(f'   ⚖️ prefet / prefet123')