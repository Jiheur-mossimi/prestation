import os
import sys
import random
from datetime import date, time, timedelta, datetime
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
    help = 'Génère des données de démonstration complètes pour l\'application de prestations'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('🔄 Génération des données de démonstration...'))
        
        # Désactiver le signal pour éviter les créations automatiques
        from django.db.models.signals import post_save
        from prestation.models import creer_utilisateur
        post_save.disconnect(creer_utilisateur, sender=Agent)
        
        # Nettoyage préalable
        self.stdout.write(self.style.NOTICE('🧹 Nettoyage des données existantes...'))
        Remarque.objects.all().delete()
        PrestationEnseignant.objects.all().delete()
        Prestation.objects.all().delete()
        SessionPrestation.objects.all().delete()
        Utilisateur.objects.exclude(user__is_superuser=True).delete()
        User.objects.filter(is_superuser=False).delete()
        Agent.objects.exclude(matricule='ADMIN').delete()
        
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
        classes = []
        for c in classes_data:
            classe, created = Classe.objects.get_or_create(
                nom=c['nom'], niveau=c['niveau'],
                defaults={'effectif': c['effectif'], 'status': 'ACTIF'}
            )
            if created:
                self.stdout.write(f'  ✅ Classe créée : {c["nom"]} ({c["niveau"]})')
            classes.append(classe)

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
        fonctions = []
        for f in fonctions_data:
            obj, created = Fonction.objects.get_or_create(libelle=f['libelle'], defaults=f)
            if created:
                self.stdout.write(f'  ✅ Fonction créée : {f["libelle"]}')
            fonctions.append(obj)

        # ==========================================
        # 4. CRÉATION DES MOIS (12 derniers mois)
        # ==========================================
        self.stdout.write(self.style.NOTICE('📅 Création des mois...'))
        mois_names = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                      'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
        mois_list = []
        for i in range(12):
            mois_num = (date.today().month - i) % 12 or 12
            annee = date.today().year - (i // 12)
            mois, created = Mois.objects.get_or_create(
                mois_num=mois_num, annee=annee,
                defaults={'libelle': f'{mois_names[mois_num-1]} {annee}'}
            )
            if created:
                self.stdout.write(f'  ✅ Mois créé : {mois.libelle}')
            mois_list.append(mois)

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
        cours = []
        for c in cours_data:
            cour, created = Cours.objects.get_or_create(code=c['code'], defaults=c)
            if created:
                self.stdout.write(f'  ✅ Cours créé : {c["libelle"]} ({c["code"]})')
            cours.append(cour)

        # ==========================================
        # 6. CRÉATION DES AGENTS (50 agents)
        # ==========================================
        self.stdout.write(self.style.NOTICE('👥 Création des agents...'))
        
        # Liste de noms pour générer des données variées
        noms = [
            ('MUKENDI', 'KABILA', 'Jean-Pierre'), ('TSHIMANGA', 'MUTOMBO', 'Marie'),
            ('KABONGO', 'KALALA', 'Paul'), ('MWAMBA', 'TSHIBA', 'Esther'),
            ('ILUNGA', 'KABEYA', 'David'), ('KATUMBA', 'MUSAU', 'Nicole'),
            ('MBUYI', 'KALONDA', 'Robert'), ('KASANDA', 'MPOYI', 'Béatrice'),
            ('MUTOMBO', 'NTUMBA', 'Pierre'), ('KAPENGA', 'MBIYA', 'Sophie'),
            ('LUKUSA', 'KABAMBA', 'Albert'), ('NGOYI', 'MALANGU', 'Catherine'),
            ('BANZA', 'KITOKO', 'Joseph'), ('MASANGU', 'MUKALA', 'Florence'),
            ('KANDA', 'MBOLO', 'Emmanuel'), ('TSHIBANGU', 'MUTEBA', 'Rachel'),
            ('MULUMBA', 'KASONGO', 'François'), ('KALUME', 'MWAMBA', 'Marguerite'),
            ('KABEYA', 'KIBADI', 'André'), ('MBUYAMBA', 'TSHIBOLA', 'Louise'),
            ('KALALA', 'MUPANDA', 'Henri'), ('MUTSHIPAYI', 'MUKENDI', 'Alice'),
            ('KABUNDI', 'LUKUSA', 'Georges'), ('NSENGA', 'MALUNDA', 'Thérèse'),
            ('KASONGO', 'KABONGO', 'Michel'), ('KABILA', 'TSHIBANGU', 'Claudine'),
            ('MBIYA', 'KAPENGA', 'Daniel'), ('NTUMBA', 'MUTOMBO', 'Jeanne'),
            ('KIBADI', 'KABEYA', 'Marc'), ('MPOYI', 'KASANDA', 'Sylvie'),
            ('MUKALA', 'MASANGU', 'Pauline'), ('MBOLO', 'KANDA', 'Antoine'),
            ('MUTEBA', 'TSHIBANGU', 'Diane'), ('KASONGO', 'MULUMBA', 'Hervé'),
            ('MWAMBA', 'KALUME', 'Isabelle'), ('KIBADI', 'MBUYAMBA', 'Luc'),
            ('MALUNDA', 'NSENGA', 'Martine'), ('KABONGO', 'KASONGO', 'Nicolas'),
            ('TSHIBOLA', 'MBUYAMBA', 'Olga'), ('MUPANDA', 'KALALA', 'Philippe'),
            ('MUKENDI', 'MUTSHIPAYI', 'Quentin'), ('LUKUSA', 'KABUNDI', 'Rose'),
            ('KITOKO', 'BANZA', 'Samuel'), ('MUKANYA', 'TSHITENGE', 'Tatiana'),
            ('KATEPA', 'KALUBI', 'Urbain'), ('MUKUNA', 'KAPITA', 'Victoire'),
            ('NSOMPO', 'KAYEMBE', 'Walter'), ('KABEYA', 'MUKENDI', 'Xavier'),
            ('MUTOMBO', 'KALONGA', 'Yvette'), ('KABILA', 'MUKENDI', 'Zachée'),
        ]
        
        agents_enseignants = []
        agents_administratifs = []
        
        # Créer 40 enseignants
        for i, (nom, postnom, prenom) in enumerate(noms[:40]):
            service = services[i % 5]
            matricule = f'ENS{str(i+1).zfill(3)}'
            sexe = 'M' if i % 2 == 0 else 'F'
            agent, created = Agent.objects.get_or_create(
                matricule=matricule,
                defaults={
                    'nom': nom, 'postnom': postnom, 'prenom': prenom,
                    'sexe': sexe,
                    'telephone': f'+24381{random.randint(1000000, 9999999)}',
                    'email': f'{prenom.lower()}.{postnom.lower()}@ecole.cd',
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
        
        # Créer 10 agents administratifs
        for i, (nom, postnom, prenom) in enumerate(noms[40:]):
            service = services[2 + (i % 3)]
            matricule = f'ADM{str(i+1).zfill(3)}'
            sexe = 'M' if i % 2 == 0 else 'F'
            agent, created = Agent.objects.get_or_create(
                matricule=matricule,
                defaults={
                    'nom': nom, 'postnom': postnom, 'prenom': prenom,
                    'sexe': sexe,
                    'telephone': f'+24382{random.randint(1000000, 9999999)}',
                    'email': f'{prenom.lower()}.{postnom.lower()}@ecole.cd',
                    'adresse': f'{200 + i} Avenue du Centre, Kinshasa',
                    'type_agent': 'ADMINISTRATIF', 'etat': True,
                    'service': service, 'nationalite': 'Congolaise',
                    'date_naissance': date(1975 + i, 3 + (i % 10), 1 + (i % 28)),
                    'province_origine': 'Kinshasa',
                }
            )
            if created:
                self.stdout.write(f'  ✅ Admin créé : {agent.nom_complet()} ({matricule})')
            agents_administratifs.append(agent)

        # ==========================================
        # 7. CRÉATION DES UTILISATEURS
        # ==========================================
        self.stdout.write(self.style.NOTICE('🔑 Création des utilisateurs...'))
        
        # Admin superuser
        admin_agent, _ = Agent.objects.get_or_create(
            matricule='ADMIN',
            defaults={
                'nom': 'ADMIN', 'postnom': 'SYSTEME', 'prenom': 'Super',
                'sexe': 'M', 'telephone': '+243899999991', 'email': 'admin@ecole.cd',
                'adresse': 'Bureau de Direction', 'type_agent': 'ADMINISTRATIF',
                'etat': True, 'service': services[2], 'nationalite': 'Congolaise',
            }
        )
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

        # Secrétaire
        secre_user, _ = User.objects.get_or_create(
            username='secretaire',
            defaults={'email': 'secretaire@ecole.cd', 'first_name': 'Innocent', 'last_name': 'Kabange'}
        )
        if not Utilisateur.objects.filter(user=secre_user).exists():
            secre_user.set_password('demo123')
            secre_user.save()
            Utilisateur.objects.get_or_create(
                user=secre_user, agent=agents_administratifs[0],
                defaults={'role': 'SECRETAIRE', 'must_change_password': False}
            )
        self.stdout.write(self.style.SUCCESS('  ✅ Secrétaire - Identifiants: secretaire / demo123'))

        # Agent (préfet/discipline)
        prefet_user, _ = User.objects.get_or_create(
            username='prefet',
            defaults={'email': 'prefet@ecole.cd', 'first_name': 'Odette', 'last_name': 'Mukanya'}
        )
        if not Utilisateur.objects.filter(user=prefet_user).exists():
            prefet_user.set_password('demo123')
            prefet_user.save()
            Utilisateur.objects.get_or_create(
                user=prefet_user, agent=agents_administratifs[3],
                defaults={'role': 'AGENT', 'must_change_password': False}
            )
        self.stdout.write(self.style.SUCCESS('  ✅ Préfet - Identifiants: prefet / demo123'))

        # Enseignant test
        ens_user, _ = User.objects.get_or_create(
            username='enseignant',
            defaults={'email': 'enseignant@ecole.cd', 'first_name': 'Jean-Pierre', 'last_name': 'Mukendi'}
        )
        if not Utilisateur.objects.filter(user=ens_user).exists():
            ens_user.set_password('demo123')
            ens_user.save()
            Utilisateur.objects.get_or_create(
                user=ens_user, agent=agents_enseignants[0],
                defaults={'role': 'ENSEIGNANT', 'must_change_password': False}
            )
        self.stdout.write(self.style.SUCCESS('  ✅ Enseignant - Identifiants: enseignant / demo123'))

        # ==========================================
        # 8. CRÉATION DES SESSIONS (30 jours)
        # ==========================================
        self.stdout.write(self.style.NOTICE('📅 Création des sessions de prestation...'))
        sessions = []
        for i in range(30):
            session_date = date.today() - timedelta(days=i)
            session, created = SessionPrestation.objects.get_or_create(
                date=session_date,
                defaults={
                    'heure_ouverture': time(7, 0),
                    'heure_limite': time(8, 0),
                    'statut': 'TERMINEE',
                    'ouvert_par': admin_user.utilisateur,
                }
            )
            if i == 0:
                # Session d'aujourd'hui encore ouverte
                session.statut = 'EN_COURS'
                session.heure_limite = time(8, 0)
                session.save()
            
            if created or i < 5:
                session.heure_fermeture = time(17, 0 + (i % 2))
                session.cloture_par = admin_user.utilisateur
                session.save()
            
            if created:
                self.stdout.write(f'  ✅ Session créée : {session_date.strftime("%d/%m/%Y")}')
            sessions.append(session)

        # ==========================================
        # 9. CRÉATION DES PRESTATIONS GÉNÉRALES
        # ==========================================
        self.stdout.write(self.style.NOTICE('📊 Création des prestations générales...'))
        total_prestations = 0
        for session in sessions:
            if session.statut == 'EN_COURS':
                continue
                
            for agent in agents_enseignants + agents_administratifs:
                rand = random.random()
                if rand < 0.8:
                    statut = 'PRESENT'
                    heure_arrivee = time(7 + random.randint(0, 1), random.randint(0, 59))
                    heure_depart = time(17 + random.randint(0, 1), random.randint(0, 59))
                elif rand < 0.9:
                    statut = 'RETARD'
                    heure_arrivee = time(8 + random.randint(0, 2), random.randint(0, 59))
                    heure_depart = time(17 + random.randint(0, 1), random.randint(0, 59))
                else:
                    statut = 'ABSENT'
                    heure_arrivee = None
                    heure_depart = None
                
                prestation, created = Prestation.objects.get_or_create(
                    agent=agent, date=session.date,
                    defaults={
                        'session': session,
                        'statut': statut,
                        'heure_arrivee': heure_arrivee,
                        'heure_depart': heure_depart,
                    }
                )
                if created:
                    total_prestations += 1
        
        self.stdout.write(f'  ✅ {total_prestations} prestations créées')

        # ==========================================
        # 10. CRÉATION DES PRESTATIONS ENSEIGNANTS
        # ==========================================
        self.stdout.write(self.style.NOTICE('📚 Création des prestations enseignants...'))
        total_pe = 0
        horaires_cours = [
            ('07:00', '08:30'), ('08:45', '10:15'), ('10:30', '12:00'),
            ('13:00', '14:30'), ('14:45', '16:15'), ('16:30', '18:00'),
        ]
        
        for session in sessions[:15]:
            enseignants_session = random.sample(agents_enseignants, min(10, len(agents_enseignants)))
            
            for agent in enseignants_session:
                try:
                    prestation = Prestation.objects.get(agent=agent, date=session.date)
                except Prestation.DoesNotExist:
                    continue
                
                nb_cours = random.randint(2, 4)
                cours_choisis = random.sample(cours, min(nb_cours, len(cours)))
                classes_choisies = random.sample(classes, min(nb_cours, len(classes)))
                
                for i in range(nb_cours):
                    debut, fin = horaires_cours[i % len(horaires_cours)]
                    heure_debut = datetime.strptime(debut, '%H:%M').time()
                    heure_fin = datetime.strptime(fin, '%H:%M').time()
                    
                    try:
                        pe, created = PrestationEnseignant.objects.get_or_create(
                            prestation=prestation,
                            cours=cours_choisis[i % len(cours_choisis)],
                            classe=classes_choisies[i % len(classes_choisies)],
                            defaults={
                                'heure_debut': heure_debut,
                                'heure_fin': heure_fin,
                                'observation': random.choice([
                                    'Cours effectué normalement',
                                    'Évaluation effectuée',
                                    'Travaux dirigés',
                                    'Cours de rattrapage',
                                    '',
                                ]),
                            }
                        )
                        if created:
                            total_pe += 1
                    except:
                        pass
        
        self.stdout.write(f'  ✅ {total_pe} prestations enseignants créées')

        # ==========================================
        # 11. CRÉATION DE MESSAGES/NOTIFICATIONS
        # ==========================================
        self.stdout.write(self.style.NOTICE('💬 Création des messages et notifications...'))
        
        messages_data = [
            ('Réunion du personnel', 'Réunion prévue demain à 14h00 dans la salle de conférence.'),
            ('Rapport mensuel', 'Veuillez soumettre vos rapports avant la fin du mois.'),
            ('Congés', 'Demande de congé approuvée pour la période du 15 au 20.'),
            ('Formation', 'Formation sur les nouvelles méthodes pédagogiques prévue la semaine prochaine.'),
            ('Matériel pédagogique', 'Le nouveau matériel est disponible au secrétariat.'),
            ('Note de service', 'Veuillez consulter la nouvelle note de service concernant les horaires.'),
            ('Inventaire', 'Inventaire du matériel pédagogique à effectuer cette semaine.'),
            ('Réunion parents', 'Réunion des parents d\'élèves prévue le 15 du mois.'),
        ]
        
        total_messages = 0
        for i in range(30):
            expediteur = random.choice([admin_user, secre_user, ens_user])
            destinataire = random.choice([secre_user, ens_user, prefet_user, admin_user])
            
            msg, created = Remarque.objects.get_or_create(
                sujet=f"{messages_data[i % len(messages_data)][0]} #{i+1}",
                expediteur=expediteur,
                destinataire=destinataire,
                defaults={
                    'categorie': random.choice(['MESSAGE', 'NOTIFICATION', 'APPROBATION']),
                    'message': messages_data[i % len(messages_data)][1],
                    'lu': random.choice([True, False]),
                    'parent': None,
                }
            )
            if created:
                total_messages += 1
        
        self.stdout.write(f'  ✅ {total_messages} messages créés')

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
        self.stdout.write(f'   ✅ {SessionPrestation.objects.count()} sessions')
        self.stdout.write(f'   ✅ {Prestation.objects.count()} prestations')
        self.stdout.write(f'   ✅ {PrestationEnseignant.objects.count()} prestations enseignants')
        self.stdout.write(f'   ✅ {Remarque.objects.count()} messages')
        self.stdout.write(f'\n🔐 Comptes de connexion :')
        self.stdout.write(f'   👑 admin / admin123')
        self.stdout.write(f'   📋 secretaire / demo123')
        self.stdout.write(f'   📚 enseignant / demo123')
        self.stdout.write(f'   ⚖️ prefet / demo123')
        
        # Réactiver le signal
        post_save.connect(creer_utilisateur, sender=Agent)
