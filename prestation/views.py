from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.utils import timezone
from django.http import JsonResponse
from django.contrib import messages
from datetime import date, timedelta
from .models import (
    SessionPrestation, Prestation, PrestationEnseignant,
    Agent, Service, Classe, Cours, Fonction, Mois,
    Utilisateur, Remarque, CodeTemporaire
)
from .forms import AgentForm, ServiceForm, CoursForm, ClasseForm, FonctionForm, MoisForm


# ==============================
# DASHBOARD
# ==============================
@login_required
def dashboard(request):
    today = date.today()
    role = request.user.utilisateur.role
    agent = request.user.utilisateur.agent

    if role in ['ADMIN', 'SECRETAIRE']:
        # Vue globale pour admin/secrétaire
        stats = {
            'agents_presents': Prestation.objects.filter(date=today, statut='PRESENT').count(),
            'agents_retard': Prestation.objects.filter(date=today, statut='RETARD').count(),
            'agents_absents': Prestation.objects.filter(date=today, statut='ABSENT').count(),
            'total_prestations': Prestation.objects.filter(date=today).count(),
            'prestations_enseignants': PrestationEnseignant.objects.filter(prestation__date=today).count(),
            'cours_enregistres': Cours.objects.filter(prestations__prestation__date=today).distinct().count(),
        }
        prestations_recentes = Prestation.objects.filter(
            date=today, statut__in=['EN_COURS', 'RETARD']
        ).select_related('agent', 'agent__service').order_by('-heure_arrivee')[:10]
        prestations_enseignants_recentes = PrestationEnseignant.objects.filter(
            prestation__date=today
        ).select_related('prestation__agent', 'cours', 'classe').order_by('-prestation__created_at')[:20]
        evolution_labels = []
        evolution_data = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            evolution_labels.append(day.strftime('%d/%m'))
            evolution_data.append(Prestation.objects.filter(date=day).count())
        repartition_data = [
            stats['agents_presents'],
            stats['agents_retard'],
            stats['agents_absents'],
            stats['prestations_enseignants']
        ]
        enseignant_chart_labels = []
        enseignant_chart_data = []
        enseignant_cours_names = []
    else:
        # Vue personnalisée pour agent/enseignant
        total_prestations = Prestation.objects.filter(agent=agent).count()
        presents = Prestation.objects.filter(agent=agent, statut='PRESENT').count()
        retards = Prestation.objects.filter(agent=agent, statut='RETARD').count()
        absents = Prestation.objects.filter(agent=agent, statut='ABSENT').count()

        stats = {
            'total_prestations': total_prestations,
            'agents_presents': presents,
            'agents_retard': retards,
            'agents_absents': absents,
            'prestations_enseignants': PrestationEnseignant.objects.filter(prestation__agent=agent).count(),
            'cours_enregistres': Cours.objects.filter(prestations__prestation__agent=agent).distinct().count(),
        }

        prestations_recentes = Prestation.objects.filter(
            agent=agent
        ).select_related('agent', 'agent__service').order_by('-date', '-heure_arrivee')[:10]

        prestations_enseignants_recentes = PrestationEnseignant.objects.filter(
            prestation__agent=agent
        ).select_related('prestation__agent', 'cours', 'classe').order_by('-prestation__date', 'heure_debut')[:20]

        # Évolution sur 7 jours pour cet agent
        evolution_labels = []
        evolution_data = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            evolution_labels.append(day.strftime('%d/%m'))
            evolution_data.append(Prestation.objects.filter(agent=agent, date=day).count())

        repartition_data = [presents, retards, absents, stats['prestations_enseignants']]

        # Taux de prestations enseignants par cours (pour graphique)
        from django.db.models import Count
        qs = PrestationEnseignant.objects.filter(prestation__agent=agent).values('cours__libelle').annotate(total=Count('id')).order_by('cours__libelle')
        enseignant_cours_names = [item['cours__libelle'] for item in qs]
        enseignant_chart_labels = list(qs.values_list('cours__libelle', flat=True))
        enseignant_chart_data = list(qs.values_list('total', flat=True))

    session_today = SessionPrestation.objects.filter(date=today).first()
    stats['session_ouverte'] = session_today is not None and session_today.statut == 'EN_COURS'

    return render(request, 'dashboard.html', {
        'stats': stats,
        'session_today': session_today,
        'prestations_recentes': prestations_recentes,
        'prestations_enseignants_recentes': prestations_enseignants_recentes,
        'today': today,
        'nb_services': Service.objects.count(),
        'nb_sessions': SessionPrestation.objects.count(),
        'evolution_labels': evolution_labels,
        'evolution_data': evolution_data,
        'repartition_data': repartition_data,
        'enseignant_chart_labels': enseignant_chart_labels,
        'enseignant_chart_data': enseignant_chart_data,
    })


# ==============================
# SESSIONS
# ==============================
@login_required
def sessions_list(request):
    sessions = SessionPrestation.objects.all().order_by('-date')
    return render(request, 'prestation/sessions_list.html', {'sessions': sessions})


@login_required
def session_detail(request, session_id):
    session = get_object_or_404(SessionPrestation, pk=session_id)
    prestations = Prestation.objects.filter(session=session).select_related('agent', 'agent__service')
    
    # Récupérer les prestations enseignants pour cette session
    prestations_enseignants = PrestationEnseignant.objects.filter(
        prestation__session=session
    ).select_related('prestation__agent', 'cours', 'classe').order_by('heure_debut')
    
    # Grouper les prestations par statut
    prestations_presents = prestations.filter(statut='PRESENT')
    prestations_retards = prestations.filter(statut='RETARD')
    prestations_absents = prestations.filter(statut='ABSENT')
    prestations_termines = prestations.filter(statut='TERMINE')
    prestations_en_cours = prestations.filter(statut='EN_COURS')
    
    # Calculer les statistiques
    stats_session = {
        'total_presents': prestations_presents.count(),
        'total_retards': prestations_retards.count(),
        'total_absents': prestations_absents.count(),
        'total_termines': prestations_termines.count(),
        'total_en_cours': prestations_en_cours.count(),
        'total_agents': prestations.count(),
        'total_cours': prestations_enseignants.count(),
    }
    
    return render(request, 'prestation/session_detail.html', {
        'session': session,
        'prestations': prestations,
        'prestations_presents': prestations_presents,
        'prestations_retards': prestations_retards,
        'prestations_absents': prestations_absents,
        'prestations_termines': prestations_termines,
        'prestations_en_cours': prestations_en_cours,
        'prestations_enseignants': prestations_enseignants,
        'stats_session': stats_session,
    })


@login_required
@user_passes_test(lambda u: u.utilisateur.role in ['ADMIN', 'SECRETAIRE'])
def ouvrir_session(request):
    today = date.today()
    
    if request.method == 'POST':
        try:
            heure_limite = request.POST.get('heure_limite')
            session = SessionPrestation.objects.create(
                date=today, 
                heure_ouverture=timezone.now().time(),
                heure_limite=heure_limite if heure_limite else None,
                statut='EN_COURS', 
                ouvert_par=request.user.utilisateur
            )
            
            # Envoyer une notification à tous les agents et enseignants
            sujet = f'Session de prestation ouverte - {today.strftime("%d/%m/%Y")}'
            message = f'Une session de prestation a été ouverte par {request.user.utilisateur.agent.nom_complet()}.\nHeure limite d\'arrivée: {heure_limite if heure_limite else "Non définie"}.\nVeuillez pointer votre arrivée.'
            
            # Envoyer à tous les utilisateurs sauf l'admin lui-même
            count_notifications = 0
            for utilisateur in Utilisateur.objects.exclude(user=request.user):
                Remarque.objects.create(
                    categorie='NOTIFICATION',
                    sujet=sujet,
                    message=message,
                    expediteur=request.user,
                    destinataire=utilisateur.user,
                    lu=False
                )
                count_notifications += 1
            
            messages.success(request, f'Session du {today.strftime("%d/%m/%Y")} ouverte avec succès! {count_notifications} notifications envoyées. Les agents peuvent maintenant pointer leur arrivée.')
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'ouverture de la session: {str(e)}')
            return redirect('ouvrir_session')
    
    # Afficher le formulaire de création de session avec heure limite
    return render(request, 'prestation/ouvrir_session.html')


@login_required
@user_passes_test(lambda u: u.utilisateur.role in ['ADMIN', 'SECRETAIRE'])
def clore_session(request, session_id):
    session = get_object_or_404(SessionPrestation, pk=session_id)
    if session.statut == 'TERMINEE':
        return redirect('session_detail', session_id=session.id)
    
    # Récupérer toutes les prestations de la session
    prestations = Prestation.objects.filter(session=session)
    
    # Pour chaque prestation :
    for prestation in prestations:
        # Si l'agent n'a jamais pointé (pas d'heure_arrivee) → marquer ABSENT
        if not prestation.heure_arrivee:
            prestation.statut = Prestation.STATUS_ABSENT
            prestation.heure_depart = None
            prestation.save()
        # Si l'agent a pointé arrivée mais pas départ → affecter heure actuelle
        elif prestation.heure_arrivee and not prestation.heure_depart:
            # Récupérer l'heure actuelle pour le départ
            heure_depart_auto = timezone.now().time()
            prestation.heure_depart = heure_depart_auto
            # Garder le statut PRESENT ou RETARD selon l'heure d'arrivée
            # Ne pas utiliser TERMINE
            prestation.save()
        # Si l'agent a pointé les deux → garder PRESENT ou RETARD
        elif prestation.heure_arrivee and prestation.heure_depart:
            # Ne pas changer le statut, garder PRESENT ou RETARD
            pass
    
    # Vérifier les agents actifs qui n'ont pas de prestation pour cette session
    agents_actifs = Agent.objects.filter(etat=True)
    agents_avec_prestation = prestations.values_list('agent_id', flat=True)
    agents_sans_prestation = agents_actifs.exclude(id__in=agents_avec_prestation)
    
    # Créer des prestations ABSENT pour les agents sans prestation
    count_agents_absents = 0
    for agent in agents_sans_prestation:
        Prestation.objects.create(
            agent=agent,
            date=session.date,
            session=session,
            statut=Prestation.STATUS_ABSENT,
            heure_arrivee=None,
            heure_depart=None
        )
        count_agents_absents += 1
    
    session.statut = 'TERMINEE'
    session.heure_fermeture = timezone.now().time()
    session.cloture_par = request.user.utilisateur
    session.save()
    
    # Notification de clôture
    sujet = f'Session de prestation clôturée - {session.date.strftime("%d/%m/%Y")}'
    message = f'La session de prestation du {session.date.strftime("%d/%m/%Y")} a été clôturée par {request.user.utilisateur.agent.nom_complet()}.\nHeure de fermeture: {session.heure_fermeture.strftime("%H:%M")}.\nVous pouvez consulter vos prestations.'
    
    for utilisateur in Utilisateur.objects.exclude(user=request.user):
        Remarque.objects.create(
            categorie='NOTIFICATION',
            sujet=sujet,
            message=message,
            expediteur=request.user,
            destinataire=utilisateur.user,
            lu=False
        )
    
    total_prestations = prestations.count() + count_agents_absents
    messages.success(request, f'Session clôturée avec succès! {total_prestations} prestations traitées ({count_agents_absents} agents ajoutés comme absents).')
    
    # Ajouter une notification pour informer que les départs ont été automatiquement pointés
    count_departs_auto = prestations.filter(heure_arrivee__isnull=False, heure_depart__isnull=False).count()
    if count_departs_auto > 0:
        messages.info(request, f'{count_departs_auto} départs ont été automatiquement enregistrés avec l\'heure actuelle.')
    return redirect('session_detail', session_id=session.id)


@login_required
@user_passes_test(lambda u: u.utilisateur.role in ['ADMIN', 'SECRETAIRE'])
def modifier_heure_limite(request, session_id):
    session = get_object_or_404(SessionPrestation, pk=session_id)
    
    if request.method == 'POST':
        heure_limite = request.POST.get('heure_limite')
        if heure_limite:
            session.heure_limite = heure_limite
            session.save()
            messages.success(request, f'Heure limite modifiée avec succès : {heure_limite}')
        else:
            session.heure_limite = None
            session.save()
            messages.success(request, 'Heure limite supprimée')
    
    return redirect('session_detail', session_id=session.id)


# ==============================
# POINTAGE
# ==============================
@login_required
def pointer_arrivee(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})
    
    today = date.today()
    session = SessionPrestation.objects.filter(date=today, statut='EN_COURS').order_by('-id').first()
    if not session:
        return JsonResponse({'success': False, 'message': 'Aucune session ouverte'})
    
    agent = request.user.utilisateur.agent
    heure_actuelle = timezone.now().time()
    
    # Vérifier si l'agent a déjà pointé son arrivée pour CETTE session
    prestation_existante = Prestation.objects.filter(agent=agent, session=session).first()
    if prestation_existante and prestation_existante.heure_arrivee:
        return JsonResponse({'success': False, 'message': 'Arrivée déjà pointée pour cette session'})
    
    # Déterminer le statut en fonction de l'heure limite
    statut = 'PRESENT'
    if session.heure_limite and heure_actuelle > session.heure_limite:
        statut = 'RETARD'
    
    if prestation_existante:
        prestation_existante.heure_arrivee = heure_actuelle
        prestation_existante.statut = statut
        prestation_existante.save()
        return JsonResponse({'success': True, 'message': 'Arrivée enregistrée', 'heure_arrivee': prestation_existante.heure_arrivee.strftime('%H:%M'), 'statut': statut})
    
    prestation = Prestation.objects.create(
        agent=agent, date=today, session=session,
        statut=statut, heure_arrivee=heure_actuelle
    )
    return JsonResponse({'success': True, 'message': 'Arrivée enregistrée', 'heure_arrivee': prestation.heure_arrivee.strftime('%H:%M'), 'statut': statut})


@login_required
def pointer_depart(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})
    
    today = date.today()
    agent = request.user.utilisateur.agent
    session = SessionPrestation.objects.filter(date=today, statut='EN_COURS').order_by('-id').first()
    if not session:
        return JsonResponse({'success': False, 'message': 'Aucune session ouverte'})
    
    prestation = Prestation.objects.filter(agent=agent, session=session).first()
    if not prestation:
        return JsonResponse({'success': False, 'message': 'Aucune prestation trouvée pour cette session'})
    if not prestation.heure_arrivee:
        return JsonResponse({'success': False, 'message': 'Vous devez pointer votre arrivée avant le départ'})
    if prestation.heure_depart:
        return JsonResponse({'success': False, 'message': 'Départ déjà pointé'})
    
    prestation.heure_depart = timezone.now().time()
    # Garder le statut PRESENT ou RETARD, ne pas utiliser TERMINE
    prestation.save()
    return JsonResponse({'success': True, 'message': 'Départ enregistré', 'heure_depart': prestation.heure_depart.strftime('%H:%M'), 'duree': prestation.duree_prestation()})


@login_required
def pointage(request):
    today = date.today()
    session = SessionPrestation.objects.filter(statut='EN_COURS').order_by('-id').first()
    context = {'session_active': session is not None and session.statut == 'EN_COURS', 'peut_pointer_arrivee': False, 'peut_pointer_depart': False, 'prestation_terminee': False}
    
    if session:
        agent = request.user.utilisateur.agent
        prestation = Prestation.objects.filter(agent=agent, session=session).first()
        if prestation:
            context.update({
                'peut_pointer_arrivee': not prestation.heure_arrivee and session.statut == 'EN_COURS',
                'peut_pointer_depart': prestation.heure_arrivee and not prestation.heure_depart and session.statut == 'EN_COURS',
                'prestation_terminee': prestation.heure_depart is not None or session.statut == 'TERMINEE',
                'heure_arrivee': prestation.heure_arrivee,
                'heure_depart': prestation.heure_depart,
                'duree': prestation.duree_prestation(),
                'statut': prestation.get_statut_display(),
            })
            
            # Ajouter le total des prestations de la journée si la session est clôturée
            if session.statut == 'TERMINEE':
                context['total_prestations_jour'] = Prestation.objects.filter(
                    date=today, 
                    statut__in=['PRESENT', 'RETARD']
                ).count()
            
            # Pour les enseignants: récupérer les cours et classes disponibles
            if request.user.utilisateur.role == 'ENSEIGNANT':
                context['cours_list'] = Cours.objects.filter(actif=True)
                context['classe_list'] = Classe.objects.filter(status='ACTIF')
                
                # Récupérer les prestations enseignants du jour
                context['prestations_cours'] = PrestationEnseignant.objects.filter(
                    prestation=prestation
                ).select_related('cours', 'classe').order_by('heure_debut')
        else:
            if session.statut == 'EN_COURS':
                context['peut_pointer_arrivee'] = True
    
    # Ajouter la session au contexte pour pouvoir vérifier session.heure_fermeture dans le template
    context['session'] = session
    return render(request, 'prestation/pointage.html', context)


# ==============================
# PRESTATIONS
# ==============================
@login_required
def prestations_list(request):
    sessions = SessionPrestation.objects.all().order_by('-date')
    return render(request, 'prestation/prestations_list.html', {'sessions': sessions})


@login_required
def prestations_du_jour(request, statut=None):
    today = date.today()
    # Récupérer toutes les prestations du jour
    prestations = Prestation.objects.filter(date=today).select_related('agent', 'agent__service').order_by('-heure_arrivee')
    
    # Filtrer par statut si fourni
    if statut:
        prestations = prestations.filter(statut=statut)
    
    # Grouper par statut pour l'affichage
    context = {
        'prestations': prestations,
        'stats': {
            'PRESENT': Prestation.objects.filter(date=today, statut='PRESENT').count(),
            'RETARD': Prestation.objects.filter(date=today, statut='RETARD').count(),
            'ABSENT': Prestation.objects.filter(date=today, statut='ABSENT').count(),
            'EN_COURS': Prestation.objects.filter(date=today, statut='EN_COURS').count(),
        },
        'statut_filtre': statut,
        'today': today,
    }
    return render(request, 'prestation/prestations_du_jour.html', context)


@login_required
def prestations_enseignants_list(request):
    if request.user.utilisateur.role == 'ENSEIGNANT':
        prestations = PrestationEnseignant.objects.filter(
            prestation__agent=request.user.utilisateur.agent
        ).select_related('prestation', 'cours', 'classe').order_by('-prestation__date', 'heure_debut')
    else:
        prestations = PrestationEnseignant.objects.all().select_related(
            'prestation__agent', 'cours', 'classe'
        ).order_by('-prestation__date', 'heure_debut')
    
    by_date = {}
    total_by_date = {}
    for pe in prestations:
        date_key = pe.prestation.date
        if date_key not in by_date:
            by_date[date_key] = []
            total_by_date[date_key] = 0
        by_date[date_key].append(pe)
        # Calculer la durée en minutes
        if pe.heure_debut and pe.heure_fin:
            from datetime import datetime
            debut = datetime.combine(pe.prestation.date, pe.heure_debut)
            fin = datetime.combine(pe.prestation.date, pe.heure_fin)
            duree = fin - debut
            total_by_date[date_key] += duree.seconds // 60
    
    return render(request, 'prestation/prestations_enseignants_list.html', {
        'prestations_by_date': by_date,
        'total_by_date': total_by_date
    })


@login_required
@user_passes_test(lambda u: u.utilisateur.role in ['ADMIN', 'SECRETAIRE'])
def valider_prestation_enseignant(request, prestation_enseignant_id):
    pe = get_object_or_404(PrestationEnseignant, pk=prestation_enseignant_id)
    if request.method == 'POST':
        pe.valide = True
        pe.valide_par = request.user.utilisateur
        pe.date_validation = timezone.now()
        pe.save()
        messages.success(request, f'Prestation enseignant validée avec succès : {pe.cours.libelle} - {pe.classe.nom}')
    return redirect('prestations_enseignants_list')


@login_required
def mon_historique(request):
    agent = request.user.utilisateur.agent
    today = date.today()

    # Récupérer les paramètres de filtre
    date_filter = request.GET.get('date', '')
    mois_filter = request.GET.get('mois', '')
    annee_filter = request.GET.get('annee', '')
    statut_filter = request.GET.get('statut', '')

    # Construire le queryset de base
    queryset = Prestation.objects.filter(agent=agent)

    # Appliquer les filtres
    if date_filter:
        queryset = queryset.filter(date=date_filter)
    elif mois_filter and annee_filter:
        queryset = queryset.filter(date__year=annee_filter, date__month=mois_filter)
    elif annee_filter:
        queryset = queryset.filter(date__year=annee_filter)
    
    # Filtrer par statut si demandé
    if statut_filter:
        queryset = queryset.filter(statut=statut_filter)

    # Statistiques basées sur le filtre
    stats = {
        'total_prestations': queryset.count(),
        'agents_presents': queryset.filter(statut='PRESENT').count(),
        'agents_retard': queryset.filter(statut='RETARD').count(),
        'agents_absents': queryset.filter(statut='ABSENT').count(),
    }

    prestations = queryset.select_related('agent', 'agent__service').order_by('-date', '-heure_arrivee')[:50]

    # Liste des années disponibles pour le filtre
    annees_disponibles = Prestation.objects.filter(agent=agent).dates('date', 'year')
    annees_list = [d.year for d in annees_disponibles]

    # Liste des mois pour le filtre
    mois_choices = [
        ('01', 'Janvier'), ('02', 'Février'), ('03', 'Mars'), ('04', 'Avril'),
        ('05', 'Mai'), ('06', 'Juin'), ('07', 'Juillet'), ('08', 'Août'),
        ('09', 'Septembre'), ('10', 'Octobre'), ('11', 'Novembre'), ('12', 'Décembre')
    ]

    context = {
        'prestations': prestations,
        'stats': stats,
        'agent': agent,
        'date_filter': date_filter,
        'mois_filter': mois_filter,
        'annee_filter': annee_filter,
        'statut_filter': statut_filter,
        'annees_list': annees_list,
        'mois_choices': mois_choices,
    }
    return render(request, 'prestation/mon_historique.html', context)


@login_required
def changer_mot_de_passe(request):
    if request.method == 'POST':
        from django.contrib.auth.hashers import make_password
        ancien = request.POST.get('ancien_mot_de_passe', '')
        nouveau = request.POST.get('nouveau_mot_de_passe', '')
        confirmer = request.POST.get('confirmer_mot_de_passe', '')
        
        if not request.user.check_password(ancien):
            messages.error(request, 'Ancien mot de passe incorrect.')
        elif nouveau != confirmer:
            messages.error(request, 'Les mots de passe ne correspondent pas.')
        elif len(nouveau) < 6:
            messages.error(request, 'Le mot de passe doit contenir au moins 6 caractères.')
        else:
            request.user.password = make_password(nouveau)
            request.user.save()
            messages.success(request, 'Mot de passe modifié avec succès !')
            return redirect('dashboard')
    
    return render(request, 'prestation/changer_mot_de_passe.html')


@login_required
def modifier_mes_infos(request):
    agent = request.user.utilisateur.agent
    if request.method == 'POST':
        from .forms import AgentForm
        form = AgentForm(request.POST, request.FILES, instance=agent)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vos informations ont été modifiées avec succès !')
            return redirect('dashboard')
        else:
            messages.error(request, 'Veuillez corriger les erreurs.')
    else:
        from .forms import AgentForm
        form = AgentForm(instance=agent)
    
    return render(request, 'prestation/modifier_mes_infos.html', {
        'form': form,
        'agent': agent,
        'mot_de_passe_temporaire': request.user.utilisateur.mot_de_passe_temporaire,
    })


@login_required
def prestation_enseignant_create(request):
    if request.method == 'POST':
        try:
            agent = request.user.utilisateur.agent
            session = SessionPrestation.objects.filter(statut='EN_COURS').order_by('-id').first()
            if not session:
                messages.error(request, 'Aucune session en cours')
                return redirect('prestations_enseignants_list')
            prestation = Prestation.objects.filter(agent=agent, session=session).first()
            if not prestation:
                messages.error(request, 'Vous devez pointer votre arrivée avant d\'enregistrer un cours')
                return redirect('prestations_enseignants_list')
            cours = get_object_or_404(Cours, pk=request.POST['cours'])
            classe = get_object_or_404(Classe, pk=request.POST['classe'])
            PrestationEnseignant.objects.create(
                prestation=prestation, cours=cours, classe=classe,
                heure_debut=request.POST['heure_debut'],
                heure_fin=request.POST['heure_fin'],
                observation=request.POST.get('observation', '')
            )
            return redirect('prestations_enseignants_list')
        except Exception:
            pass
    
    return render(request, 'prestation/prestation_enseignant_form.html', {
        'cours_list': Cours.objects.filter(actif=True),
        'classe_list': Classe.objects.filter(status='ACTIF'),
    })


# ==============================
# AGENTS
# ==============================
@login_required
def agents_list(request):
    service_id = request.GET.get('service', '')
    agents = Agent.objects.select_related('service').all()
    if service_id:
        agents = agents.filter(service_id=service_id)
    return render(request, 'agents/index.html', {
        'agents': agents,
        'services': Service.objects.all(),
        'service_filter': service_id,
    })


@login_required
def agent_create(request):
    form_title = 'Nouvel Agent'
    if request.method == 'POST':
        form = AgentForm(request.POST, request.FILES)
        if form.is_valid():
            agent = form.save()
            messages.success(request, f'Agent {agent.nom_complet()} créé avec succès !')
            return redirect('agent_show', agent_id=agent.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = AgentForm()
    return render(request, 'agents/form.html', {
        'form': form, 'form_title': form_title, 'services': Service.objects.all()
    })


@login_required
@user_passes_test(lambda u: u.utilisateur.role in ['ADMIN', 'SECRETAIRE'])
def agent_show(request, agent_id):
    return render(request, 'agents/show.html', {'agent': get_object_or_404(Agent, pk=agent_id)})


@login_required
@user_passes_test(lambda u: u.utilisateur.role == 'ADMIN')
def agent_edit(request, agent_id):
    agent = get_object_or_404(Agent, pk=agent_id)
    form_title = 'Modifier l\'Agent'
    if request.method == 'POST':
        form = AgentForm(request.POST, request.FILES, instance=agent)
        if form.is_valid():
            agent = form.save()
            messages.success(request, f'Agent {agent.nom_complet()} modifié avec succès !')
            return redirect('agent_show', agent_id=agent.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = AgentForm(instance=agent)
    return render(request, 'agents/form.html', {
        'form': form, 'form_title': form_title, 'agent': agent, 'services': Service.objects.all()
    })


@login_required
@user_passes_test(lambda u: u.utilisateur.role == 'ADMIN')
def agent_delete(request, agent_id):
    agent = get_object_or_404(Agent, pk=agent_id)
    if request.method == 'POST':
        nom = agent.nom_complet()
        agent.delete()
        messages.success(request, f'Agent {nom} supprimé avec succès !')
        return redirect('agents')
    return redirect('agents')


# ==============================
# SERVICES
# ==============================
@login_required
def services_list(request):
    return render(request, 'services/index.html', {'services': Service.objects.annotate(nb_agents=Count('agents')).all()})


@login_required
def service_create(request):
    form_title = 'Nouveau Service'
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save()
            messages.success(request, f'Service {service.nom} créé avec succès !')
            return redirect('service_show', service_id=service.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = ServiceForm()
    return render(request, 'services/form.html', {'form': form, 'form_title': form_title})


@login_required
def service_show(request, service_id):
    return render(request, 'services/show.html', {'service': get_object_or_404(Service, pk=service_id)})


@login_required
@user_passes_test(lambda u: u.utilisateur.role == 'ADMIN')
def service_edit(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    form_title = 'Modifier le Service'
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            service = form.save()
            messages.success(request, f'Service {service.nom} modifié avec succès !')
            return redirect('service_show', service_id=service.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = ServiceForm(instance=service)
    return render(request, 'services/form.html', {'form': form, 'form_title': form_title, 'service': service})


@login_required
@user_passes_test(lambda u: u.utilisateur.role == 'ADMIN')
def service_delete(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    if request.method == 'POST':
        nom = service.nom
        service.delete()
        messages.success(request, f'Service {nom} supprimé avec succès !')
        return redirect('services')
    return redirect('services')


# ==============================
# CLASSES
# ==============================
@login_required
def classes_list(request):
    return render(request, 'classes/index.html', {'classes': Classe.objects.all()})


@login_required
def classe_create(request):
    form_title = 'Nouvelle Classe'
    if request.method == 'POST':
        form = ClasseForm(request.POST)
        if form.is_valid():
            classe = form.save()
            messages.success(request, f'Classe {classe.nom} créée avec succès !')
            return redirect('classe_show', classe_id=classe.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = ClasseForm()
    return render(request, 'classes/form.html', {'form': form, 'form_title': form_title})


@login_required
def classe_show(request, classe_id):
    return render(request, 'classes/show.html', {'classe': get_object_or_404(Classe, pk=classe_id)})


@login_required
@user_passes_test(lambda u: u.utilisateur.role == 'ADMIN')
def classe_edit(request, classe_id):
    classe = get_object_or_404(Classe, pk=classe_id)
    form_title = 'Modifier la Classe'
    if request.method == 'POST':
        form = ClasseForm(request.POST, instance=classe)
        if form.is_valid():
            classe = form.save()
            messages.success(request, f'Classe {classe.nom} modifiée avec succès !')
            return redirect('classe_show', classe_id=classe.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = ClasseForm(instance=classe)
    return render(request, 'classes/form.html', {'form': form, 'form_title': form_title, 'classe': classe})


@login_required
@user_passes_test(lambda u: u.utilisateur.role == 'ADMIN')
def classe_delete(request, classe_id):
    classe = get_object_or_404(Classe, pk=classe_id)
    if request.method == 'POST':
        nom = classe.nom
        classe.delete()
        messages.success(request, f'Classe {nom} supprimée avec succès !')
        return redirect('classes')
    return redirect('classes')


# ==============================
# COURS
# ==============================
@login_required
def cours_list(request):
    return render(request, 'cours/index.html', {'cours': Cours.objects.all()})


@login_required
def cours_create(request):
    form_title = 'Nouveau Cours'
    if request.method == 'POST':
        form = CoursForm(request.POST)
        if form.is_valid():
            cours = form.save()
            messages.success(request, f'Cours {cours.libelle} créé avec succès !')
            return redirect('cours_show', cours_id=cours.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = CoursForm()
    return render(request, 'cours/form.html', {'form': form, 'form_title': form_title})


@login_required
def cours_show(request, cours_id):
    return render(request, 'cours/show.html', {'cours': get_object_or_404(Cours, pk=cours_id)})


@login_required
@user_passes_test(lambda u: u.utilisateur.role == 'ADMIN')
def cours_edit(request, cours_id):
    cours = get_object_or_404(Cours, pk=cours_id)
    form_title = 'Modifier le Cours'
    if request.method == 'POST':
        form = CoursForm(request.POST, instance=cours)
        if form.is_valid():
            cours = form.save()
            messages.success(request, f'Cours {cours.libelle} modifié avec succès !')
            return redirect('cours_show', cours_id=cours.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = CoursForm(instance=cours)
    return render(request, 'cours/form.html', {'form': form, 'form_title': form_title, 'cours': cours})


@login_required
@user_passes_test(lambda u: u.utilisateur.role == 'ADMIN')
def cours_delete(request, cours_id):
    cours = get_object_or_404(Cours, pk=cours_id)
    if request.method == 'POST':
        libelle = cours.libelle
        cours.delete()
        messages.success(request, f'Cours {libelle} supprimé avec succès !')
        return redirect('cours')
    return redirect('cours')


# ==============================
# FONCTIONS
# ==============================
@login_required
def fonctions_list(request):
    return render(request, 'fonctions/index.html', {'fonctions': Fonction.objects.all()})


@login_required
def fonction_create(request):
    form_title = 'Nouvelle Fonction'
    if request.method == 'POST':
        form = FonctionForm(request.POST)
        if form.is_valid():
            fonction = form.save()
            messages.success(request, f'Fonction {fonction.libelle} créée avec succès !')
            return redirect('fonction_show', fonction_id=fonction.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = FonctionForm()
    return render(request, 'fonctions/form.html', {'form': form, 'form_title': form_title})


@login_required
def fonction_show(request, fonction_id):
    return render(request, 'fonctions/show.html', {'fonction': get_object_or_404(Fonction, pk=fonction_id)})


@login_required
@user_passes_test(lambda u: u.utilisateur.role == 'ADMIN')
def fonction_edit(request, fonction_id):
    fonction = get_object_or_404(Fonction, pk=fonction_id)
    form_title = 'Modifier la Fonction'
    if request.method == 'POST':
        form = FonctionForm(request.POST, instance=fonction)
        if form.is_valid():
            fonction = form.save()
            messages.success(request, f'Fonction {fonction.libelle} modifiée avec succès !')
            return redirect('fonction_show', fonction_id=fonction.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = FonctionForm(instance=fonction)
    return render(request, 'fonctions/form.html', {'form': form, 'form_title': form_title, 'fonction': fonction})


@login_required
@user_passes_test(lambda u: u.utilisateur.role == 'ADMIN')
def fonction_delete(request, fonction_id):
    fonction = get_object_or_404(Fonction, pk=fonction_id)
    if request.method == 'POST':
        libelle = fonction.libelle
        fonction.delete()
        messages.success(request, f'Fonction {libelle} supprimée avec succès !')
        return redirect('fonctions')
    return redirect('fonctions')


# ==============================
# MOIS
# ==============================
@login_required
def mois_list(request):
    return render(request, 'mois/index.html', {'mois_list': Mois.objects.all()})


@login_required
def mois_create(request):
    form_title = 'Nouveau Mois'
    if request.method == 'POST':
        form = MoisForm(request.POST)
        if form.is_valid():
            mois = form.save()
            messages.success(request, f'Mois {mois.libelle} créé avec succès !')
            return redirect('mois_show', mois_id=mois.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = MoisForm()
    return render(request, 'mois/form.html', {'form': form, 'form_title': form_title})


@login_required
def mois_show(request, mois_id):
    return render(request, 'mois/show.html', {'mois': get_object_or_404(Mois, pk=mois_id)})


@login_required
@user_passes_test(lambda u: u.utilisateur.role == 'ADMIN')
def mois_edit(request, mois_id):
    mois = get_object_or_404(Mois, pk=mois_id)
    form_title = 'Modifier le Mois'
    if request.method == 'POST':
        form = MoisForm(request.POST, instance=mois)
        if form.is_valid():
            mois = form.save()
            messages.success(request, f'Mois {mois.libelle} modifié avec succès !')
            return redirect('mois_show', mois_id=mois.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = MoisForm(instance=mois)
    return render(request, 'mois/form.html', {'form': form, 'form_title': form_title, 'mois': mois})


@login_required
@user_passes_test(lambda u: u.utilisateur.role == 'ADMIN')
def mois_delete(request, mois_id):
    mois = get_object_or_404(Mois, pk=mois_id)
    if request.method == 'POST':
        libelle = mois.libelle
        mois.delete()
        messages.success(request, f'Mois {libelle} supprimé avec succès !')
        return redirect('mois')
    return redirect('mois')


# ==============================
# VUES SYSTÈME
# ==============================
def logout_view(request):
    from django.contrib.auth import logout as auth_logout
    from django.contrib import messages
    auth_logout(request)
    messages.success(request, '✅ Vous avez été déconnecté avec succès.')
    return redirect('login')


@login_required
@user_passes_test(lambda u: u.utilisateur.role == 'ADMIN')
def utilisateurs_list(request):
    return render(request, 'utilisateurs/index.html', {'utilisateurs': Utilisateur.objects.select_related('user', 'agent').all()})


@login_required
@user_passes_test(lambda u: u.utilisateur.role == 'ADMIN')
def utilisateur_create(request):
    """Crée un nouvel utilisateur en l'associant à un agent existant et en lui attribuant un rôle."""
    import secrets
    from django.contrib.auth.models import User
    from django.contrib.auth.hashers import make_password

    # Agents qui n'ont pas encore d'utilisateur associé
    agents_sans_user = Agent.objects.filter(utilisateur__isnull=True, etat=True)

    if request.method == 'POST':
        agent_id = request.POST.get('agent')
        username = request.POST.get('username', '').strip().lower()
        role = request.POST.get('role')
        password = request.POST.get('password', '').strip()

        # Validations
        if not agent_id or not username or not role:
            messages.error(request, 'Veuillez remplir tous les champs obligatoires.')
            return render(request, 'utilisateurs/create.html', {
                'agents_sans_user': agents_sans_user,
                'role_choices': Utilisateur.ROLE_CHOICES,
            })

        if User.objects.filter(username=username).exists():
            messages.error(request, f'Le nom d\'utilisateur "{username}" existe déjà.')
            return render(request, 'utilisateurs/create.html', {
                'agents_sans_user': agents_sans_user,
                'role_choices': Utilisateur.ROLE_CHOICES,
            })

        if role not in dict(Utilisateur.ROLE_CHOICES).keys():
            messages.error(request, 'Rôle invalide.')
            return render(request, 'utilisateurs/create.html', {
                'agents_sans_user': agents_sans_user,
                'role_choices': Utilisateur.ROLE_CHOICES,
            })

        agent = get_object_or_404(Agent, pk=agent_id)
        if Utilisateur.objects.filter(agent=agent).exists():
            messages.error(request, 'Cet agent a déjà un compte utilisateur.')
            return render(request, 'utilisateurs/create.html', {
                'agents_sans_user': agents_sans_user,
                'role_choices': Utilisateur.ROLE_CHOICES,
            })

        # Générer un mot de passe si non fourni
        if not password:
            password = secrets.token_urlsafe(12)

        # Créer le User Django
        user = User.objects.create_user(
            username=username,
            password=password,
            email=agent.email,
            first_name=agent.prenom,
            last_name=f"{agent.nom} {agent.postnom}"
        )

        # Créer le Utilisateur lié
        utilisateur = Utilisateur.objects.create(
            user=user,
            agent=agent,
            role=role,
            must_change_password=True,
            mot_de_passe_temporaire=password
        )

        messages.success(request, f'Utilisateur "{username}" créé avec succès ! Mot de passe temporaire : {password}')
        return redirect('utilisateur_show', utilisateur_id=utilisateur.id)

    return render(request, 'utilisateurs/create.html', {
        'agents_sans_user': agents_sans_user,
        'role_choices': Utilisateur.ROLE_CHOICES,
    })


@login_required
@user_passes_test(lambda u: u.utilisateur.role == 'ADMIN')
def utilisateur_edit(request, utilisateur_id):
    """Permet de modifier le rôle d'un utilisateur et l'état must_change_password."""
    utilisateur = get_object_or_404(Utilisateur, pk=utilisateur_id)
    if request.method == 'POST':
        nouveau_role = request.POST.get('role')
        must_change = request.POST.get('must_change_password') == 'on'
        if nouveau_role in dict(Utilisateur.ROLE_CHOICES).keys():
            utilisateur.role = nouveau_role
            utilisateur.must_change_password = must_change
            utilisateur.save()
            messages.success(request, f'Utilisateur {utilisateur.user.username} modifié avec succès !')
        else:
            messages.error(request, 'Rôle invalide.')
        return redirect('utilisateurs')
    return render(request, 'utilisateurs/edit.html', {'utilisateur': utilisateur})


@login_required
@user_passes_test(lambda u: u.utilisateur.role == 'ADMIN')
def utilisateur_show(request, utilisateur_id):
    """Affiche les détails d'un utilisateur."""
    utilisateur = get_object_or_404(Utilisateur, pk=utilisateur_id)
    return render(request, 'utilisateurs/show.html', {'utilisateur': utilisateur})


@login_required
@user_passes_test(lambda u: u.utilisateur.role == 'ADMIN')
def utilisateur_reset_password(request, utilisateur_id):
    """Réinitialise le mot de passe d'un utilisateur avec un mot de passe temporaire."""
    import secrets
    from django.contrib.auth.hashers import make_password
    utilisateur = get_object_or_404(Utilisateur, pk=utilisateur_id)
    if request.method == 'POST':
        nouveau_password = secrets.token_urlsafe(12)
        utilisateur.user.password = make_password(nouveau_password)
        utilisateur.user.save()
        utilisateur.must_change_password = True
        utilisateur.mot_de_passe_temporaire = nouveau_password
        utilisateur.save()
        messages.success(request, f'Mot de passe réinitialisé pour {utilisateur.user.username}. Nouveau mot de passe temporaire : {nouveau_password}')
        return redirect('utilisateur_show', utilisateur_id=utilisateur.id)
    return render(request, 'utilisateurs/reset_password.html', {'utilisateur': utilisateur})


@login_required
@user_passes_test(lambda u: u.utilisateur.role == 'ADMIN')
def utilisateur_delete(request, utilisateur_id):
    """Supprime un utilisateur (et son compte Django associé)."""
    utilisateur = get_object_or_404(Utilisateur, pk=utilisateur_id)
    if request.method == 'POST':
        username = utilisateur.user.username
        # Supprimer le User cascade vers Utilisateur
        utilisateur.user.delete()
        messages.success(request, f'Utilisateur {username} supprimé avec succès !')
        return redirect('utilisateurs')
    return render(request, 'utilisateurs/delete_confirm.html', {'utilisateur': utilisateur})


@login_required
def messages_view(request):
    user_role = request.user.utilisateur.role
    
    if user_role in ['AGENT', 'ENSEIGNANT']:
        # Agents et enseignants ne voient que les messages envoyés par les administrateurs
        msgs = Remarque.objects.filter(
            destinataire=request.user,
            expediteur__utilisateur__role='ADMIN'
        ).select_related('expediteur', 'destinataire').order_by('-created_at')
    else:
        # Admin et secrétaire voient tous leurs messages
        msgs = Remarque.objects.filter(
            Q(expediteur=request.user) | Q(destinataire=request.user)
        ).select_related('expediteur', 'destinataire').order_by('-created_at')
    
    return render(request, 'messages/chat.html', {'messages': msgs})


@login_required
def notifications_view(request):
    user_role = request.user.utilisateur.role
    
    if user_role in ['AGENT', 'ENSEIGNANT']:
        # Agents et enseignants ne voient que les notifications envoyées par les administrateurs
        notifications = Remarque.objects.filter(
            destinataire=request.user,
            categorie='NOTIFICATION',
            expediteur__utilisateur__role='ADMIN'
        ).order_by('-created_at')
    else:
        # Admin et secrétaire voient toutes leurs notifications
        notifications = Remarque.objects.filter(
            destinataire=request.user,
            categorie='NOTIFICATION'
        ).order_by('-created_at')
    
    return render(request, 'notifications.html', {'notifications': notifications})


@login_required
def rapports_view(request):
    from django.core.paginator import Paginator
    
    # Récupérer les paramètres de filtre
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    service_id = request.GET.get('service', '')
    agent_id = request.GET.get('agent', '')
    page_number = request.GET.get('page', 1)
    
    # Construire le queryset de base
    prestations = Prestation.objects.select_related('agent', 'agent__service')
    
    # Appliquer les filtres
    if date_debut:
        prestations = prestations.filter(date__gte=date_debut)
    if date_fin:
        prestations = prestations.filter(date__lte=date_fin)
    if service_id:
        prestations = prestations.filter(agent__service_id=service_id)
    if agent_id:
        prestations = prestations.filter(agent_id=agent_id)
    
    # Calculer les statistiques AVANT la pagination
    total_prestations = prestations.count()
    stats = {
        'total_prestations': total_prestations,
        'agents_presents': prestations.filter(statut='PRESENT').count(),
        'agents_retard': prestations.filter(statut='RETARD').count(),
        'agents_absents': prestations.filter(statut='ABSENT').count(),
        'taux_presence': round((prestations.filter(statut='PRESENT').count() / total_prestations * 100) if total_prestations > 0 else 0, 1),
    }
    
    # Trier et paginer (50 résultats par page)
    prestations = prestations.order_by('-date', '-heure_arrivee')
    paginator = Paginator(prestations, 50)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'rapports/index.html', {
        'services': Service.objects.all(),
        'agents': Agent.objects.filter(etat=True),
        'page_obj': page_obj,
        'stats': stats,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'service_id': service_id,
        'agent_id': agent_id,
    })


@login_required
@user_passes_test(lambda u: u.utilisateur.role in ['ADMIN', 'SECRETAIRE'])
def validation_prestations_enseignants(request):
    """Page de validation des prestations enseignants en temps réel"""
    return render(request, 'prestation/validation_prestations_enseignants.html')


@login_required
def parametres_view(request):
    return render(request, 'parametres/index.html')


@login_required
def profile_view(request):
    return render(request, 'profile.html')


@login_required
def qr_code_reseau(request):
    """Génère un QR-code pour se connecter au réseau WiFi"""
    import qrcode
    from io import BytesIO
    import base64
    
    # Informations du réseau WiFi (à personnaliser)
    wifi_info = {
        'ssid': 'itel Super 26 Ultra',
        'password': 'mossimi12',
        'security': 'WPA',
    }
    
    # Créer la chaîne de connexion WiFi
    wifi_string = f"WIFI:T:{wifi_info['security']};S:{wifi_info['ssid']};P:{wifi_info['password']};H:false;;"
    
    # Générer le QR-code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(wifi_string)
    qr.make(fit=True)
    
    # Créer l'image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Sauvegarder dans un buffer
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    # Convertir en base64
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return render(request, 'prestation/qr_code_reseau.html', {
        'qr_code': qr_code_base64,
        'wifi_info': wifi_info,
    })


# ==============================
# 2FA - GOOGLE AUTHENTICATOR
# ==============================
@login_required
def setup_2fa(request):
    """Génère un QR code pour configurer Google Authenticator"""
    import pyotp
    import qrcode
    from io import BytesIO
    import base64
    
    utilisateur = request.user.utilisateur
    
    # Générer un secret si non existant
    if not utilisateur.two_factor_secret:
        utilisateur.two_factor_secret = pyotp.random_base32()
        utilisateur.save()
    
    # Créer l'URI pour Google Authenticator
    totp = pyotp.TOTP(utilisateur.two_factor_secret)
    provisioning_uri = totp.provisioning_uri(
        name=request.user.username,
        issuer_name="Gestion Prestations"
    )
    
    # Générer le QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return render(request, 'prestation/setup_2fa.html', {
        'qr_code': qr_code_base64,
        'secret': utilisateur.two_factor_secret,
    })


@login_required
def verify_2fa(request):
    """Vérifie le code 2FA et active l'authentification"""
    import pyotp
    
    utilisateur = request.user.utilisateur
    
    if request.method == 'POST':
        code = request.POST.get('code_2fa', '').strip()
        totp = pyotp.TOTP(utilisateur.two_factor_secret)
        
        if totp.verify(code):
            utilisateur.two_factor_enabled = True
            utilisateur.save()
            messages.success(request, 'Authentification à deux facteurs activée avec succès !')
            return redirect('dashboard')
        else:
            messages.error(request, 'Code incorrect. Veuillez réessayer.')
    
    return render(request, 'prestation/verify_2fa.html')


def login_view(request):
    """Login avec 2FA pour ADMIN/SECRETAIRE"""
    from django.contrib.auth import authenticate, login as auth_login
    
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        code_2fa = request.POST.get('code_2fa', '').strip()
        
        if not username or not password:
            messages.error(request, 'Veuillez remplir tous les champs.')
            return render(request, 'login.html')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            utilisateur = user.utilisateur
            
            # Vérifier si 2FA est requis (ADMIN/SECRETAIRE)
            if utilisateur.role in ['ADMIN', 'SECRETAIRE']:
                if not utilisateur.two_factor_secret:
                    # Pas de secret 2FA, rediriger vers setup
                    auth_login(request, user)
                    messages.warning(request, 'Veuillez configurer Google Authenticator.')
                    return redirect('setup_2fa')
                
                if not utilisateur.two_factor_enabled:
                    # 2FA pas encore activé, rediriger vers setup
                    auth_login(request, user)
                    messages.warning(request, 'Veuillez activer Google Authenticator.')
                    return redirect('setup_2fa')
                
                # Vérifier le code 2FA
                if not code_2fa:
                    messages.error(request, 'Code Google Authenticator requis.')
                    return render(request, 'login.html', {'show_2fa': True, 'username': username})
                
                import pyotp
                totp = pyotp.TOTP(utilisateur.two_factor_secret)
                if not totp.verify(code_2fa):
                    messages.error(request, 'Code Google Authenticator incorrect.')
                    return render(request, 'login.html', {'show_2fa': True, 'username': username})
            
            auth_login(request, user)
            messages.success(request, f'Connexion réussie ! Bienvenue {user.username}.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Identifiants incorrects.')
    
    return render(request, 'login.html')


# ==============================
# TABLETTE DE POINTAGE
# ==============================
def tablette_pointage(request):
    """Interface tablette de pointage (sans dashboard)"""
    today = date.today()
    session = SessionPrestation.objects.filter(date=today, statut='EN_COURS').first()
    
    return render(request, 'prestation/tablette_pointage.html', {
        'session_active': session is not None,
    })


def tablette_arrivee(request):
    """Pointage arrivée depuis la tablette (username/password)"""
    if request.method == 'POST':
        from django.contrib.auth import authenticate
        import logging
        
        logger = logging.getLogger('prestation')
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # 1. Vérifier les identifiants
        user = authenticate(request, username=username, password=password)
        if user is None:
            logger.warning(f'Tentative connexion tablette échouée: {username}')
            return JsonResponse({'success': False, 'message': 'Identifiants incorrects'})
        
        # 2. Vérifier que le compte est actif
        if not user.is_active:
            return JsonResponse({'success': False, 'message': 'Compte désactivé'})
        
        # 3. Récupérer la session EN_COURS la plus récente
        session = SessionPrestation.objects.filter(statut='EN_COURS').order_by('-id').first()
        if not session:
            return JsonResponse({'success': False, 'message': 'Aucune prestation en cours'})
        
        agent = user.utilisateur.agent
        heure_actuelle = timezone.now().time()
        
        # 4. Vérifier que l'arrivée n'est pas déjà enregistrée pour CETTE session
        prestation_existante = Prestation.objects.filter(agent=agent, session=session).first()
        if prestation_existante and prestation_existante.heure_arrivee:
            return JsonResponse({
                'success': False, 
                'message': 'Votre arrivée est déjà enregistrée pour cette session. Veuillez pointer votre départ.',
                'proposer_depart': True
            })
        
        # Déterminer le statut
        statut = 'PRESENT'
        if session.heure_limite and heure_actuelle > session.heure_limite:
            statut = 'RETARD'
        
        # Enregistrer l'arrivée
        if prestation_existante:
            prestation_existante.heure_arrivee = heure_actuelle
            prestation_existante.statut = statut
            prestation_existante.save()
        else:
            prestation = Prestation.objects.create(
                agent=agent,
                date=session.date,
                session=session,
                statut=statut,
                heure_arrivee=heure_actuelle
            )
        
        logger.info(f'Arrivée enregistrée: {agent.nom_complet()} à {heure_actuelle.strftime("%H:%M")}')
        
        # Créer une notification pour l'agent
        Remarque.objects.create(
            categorie='NOTIFICATION',
            sujet='Pointage arrivée enregistré',
            message=f'Votre arrivée a été enregistrée à {heure_actuelle.strftime("%H:%M")} - Statut: {statut}',
            expediteur=user,
            destinataire=user,
            lu=False
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Arrivée enregistrée à {heure_actuelle.strftime("%H:%M")} - Statut: {statut}',
            'is_enseignant': user.utilisateur.role == 'ENSEIGNANT',
            'redirect': 'tablette_prestation_enseignant' if user.utilisateur.role == 'ENSEIGNANT' else None
        })
    
    return render(request, 'prestation/tablette_arrivee.html')


def tablette_prestation_enseignant(request):
    """Formulaire de prestation enseignant sur la tablette (2 étapes: login puis formulaire)"""
    from django.contrib.auth import authenticate
    import logging
    
    logger = logging.getLogger('prestation')
    
    # Récupérer la session EN_COURS la plus récente
    session = SessionPrestation.objects.filter(statut='EN_COURS').order_by('-id').first()
    
    if request.method == 'POST':
        if not session:
            return JsonResponse({'success': False, 'message': 'Aucune prestation en cours'})
        
        action = request.POST.get('action', 'login')
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # Étape 1 : Vérifier les identifiants
        user = authenticate(request, username=username, password=password)
        if user is None:
            return JsonResponse({'success': False, 'message': 'Identifiants incorrects'})
        
        # Vérifier que le compte est actif
        if not user.is_active:
            return JsonResponse({'success': False, 'message': 'Compte désactivé'})
        
        # Vérifier que c'est un enseignant
        if user.utilisateur.role != 'ENSEIGNANT':
            return JsonResponse({'success': False, 'message': 'Seuls les enseignants peuvent enregistrer des prestations'})
        
        agent = user.utilisateur.agent
        
        # Vérifier que l'arrivée est enregistrée pour cette session
        prestation = Prestation.objects.filter(agent=agent, session=session).first()
        if not prestation or not prestation.heure_arrivee:
            return JsonResponse({'success': False, 'message': 'Vous devez pointer votre arrivée avant d\'enregistrer un cours'})
        
        # Si c'est juste la vérification du login, retourner succès
        if action == 'login':
            return JsonResponse({
                'success': True,
                'message': f'Bienvenue {agent.nom_complet()} !',
                'agent_nom': agent.nom_complet()
            })
        
        # Étape 2 : Enregistrer la prestation
        cours_id = request.POST.get('cours', '')
        classe_id = request.POST.get('classe', '')
        heure_debut = request.POST.get('heure_debut', '')
        heure_fin = request.POST.get('heure_fin', '')
        
        if not cours_id or not classe_id or not heure_debut or not heure_fin:
            return JsonResponse({'success': False, 'message': 'Veuillez remplir tous les champs'})
        
        # Vérifier que l'heure de fin est après l'heure de début
        from datetime import datetime
        try:
            debut = datetime.strptime(heure_debut, '%H:%M').time()
            fin = datetime.strptime(heure_fin, '%H:%M').time()
            if fin <= debut:
                return JsonResponse({'success': False, 'message': 'L\'heure de fin doit être postérieure à l\'heure de début'})
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Format d\'heure invalide'})
        
        cours = get_object_or_404(Cours, pk=cours_id)
        classe = get_object_or_404(Classe, pk=classe_id)
        
        # Créer la prestation enseignant
        pe = PrestationEnseignant.objects.create(
            prestation=prestation,
            cours=cours,
            classe=classe,
            heure_debut=heure_debut,
            heure_fin=heure_fin,
            observation=request.POST.get('observation', '')
        )
        
        logger.info(f'Prestation enseignant enregistrée: {agent.nom_complet()} - {cours.libelle} - {classe.nom}')
        
        # Créer une notification pour le secrétaire/admin
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Récupérer tous les utilisateurs ADMIN et SECRETAIRE
        destinataires = User.objects.filter(
            utilisateur__role__in=['ADMIN', 'SECRETAIRE'],
            is_active=True
        )
        
        sujet = f'Nouvelle prestation enseignant - {agent.nom_complet()}'
        message = (
            f'Enseignant: {agent.nom_complet()}\n'
            f'Cours: {cours.libelle}\n'
            f'Classe: {classe.nom}\n'
            f'Date: {prestation.date.strftime("%d/%m/%Y")}\n'
            f'Heure: {heure_debut} - {heure_fin}\n'
            f'Durée: {pe.duree_cours()}\n'
            f'Observation: {request.POST.get("observation", "Aucune")}'
        )
        
        # Envoyer la notification à tous les admin/secrétaire
        for destinataire in destinataires:
            Remarque.objects.create(
                categorie='NOTIFICATION',
                sujet=sujet,
                message=message,
                expediteur=user,
                destinataire=destinataire,
                lu=False
            )
        
        # Créer une notification de confirmation pour l'enseignant
        Remarque.objects.create(
            categorie='NOTIFICATION',
            sujet='Prestation enseignant enregistrée',
            message=f'Votre prestation a été enregistrée avec succès.\nCours: {cours.libelle}\nClasse: {classe.nom}\nHeure: {heure_debut} - {heure_fin}\nDurée: {pe.duree_cours()}',
            expediteur=user,
            destinataire=user,
            lu=False
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Prestation enregistrée avec succès ! Durée: {pe.duree_cours()}',
            'duree': pe.duree_cours(),
            'prestation_id': pe.id
        })
    
    # GET - Afficher la page avec la card de login
    return render(request, 'prestation/tablette_prestation_enseignant.html', {
        'cours_list': Cours.objects.filter(actif=True),
        'classe_list': Classe.objects.filter(status='ACTIF'),
        'session_active': session is not None,
    })


def tablette_depart(request):
    """Pointage départ depuis la tablette (username/password)"""
    if request.method == 'POST':
        from django.contrib.auth import authenticate
        import logging
        
        logger = logging.getLogger('prestation')
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # 1. Vérifier les identifiants
        user = authenticate(request, username=username, password=password)
        if user is None:
            return JsonResponse({'success': False, 'message': 'Identifiants incorrects'})
        
        # 2. Récupérer la session EN_COURS la plus récente
        session = SessionPrestation.objects.filter(statut='EN_COURS').order_by('-id').first()
        if not session:
            return JsonResponse({'success': False, 'message': 'Aucune prestation en cours'})
        
        agent = user.utilisateur.agent
        
        # 3. Vérifier qu'une arrivée existe pour CETTE session
        prestation = Prestation.objects.filter(agent=agent, session=session).first()
        if not prestation or not prestation.heure_arrivee:
            return JsonResponse({'success': False, 'message': 'Aucune arrivée enregistrée pour cette session'})
        
        # 4. Vérifier qu'aucun départ n'a été enregistré
        if prestation.heure_depart:
            return JsonResponse({'success': False, 'message': 'Départ déjà enregistré'})
        
        # Enregistrer le départ
        heure_depart = timezone.now().time()
        prestation.heure_depart = heure_depart
        prestation.save()
        
        logger.info(f'Départ enregistré: {agent.nom_complet()} à {heure_depart.strftime("%H:%M")}')
        
        # Créer une notification pour l'agent
        Remarque.objects.create(
            categorie='NOTIFICATION',
            sujet='Pointage départ enregistré',
            message=f'Votre départ a été enregistré à {heure_depart.strftime("%H:%M")} - Durée: {prestation.duree_prestation()}',
            expediteur=user,
            destinataire=user,
            lu=False
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Départ enregistré à {heure_depart.strftime("%H:%M")} - Durée: {prestation.duree_prestation()}'
        })
    
    return render(request, 'prestation/tablette_depart.html')


# ==============================
# AUTHENTIFICATION PAR QR CODE
# ==============================
def qr_code_wifi(request):
    """Affiche uniquement le QR code pour se connecter au WiFi"""
    import qrcode
    from io import BytesIO
    import base64
    
    # Informations du réseau WiFi
    wifi_info = {
        'ssid': 'itel Super 26 Ultra',
        'password': 'mossimi12',
        'security': 'WPA',
    }
    
    # Créer la chaîne de connexion WiFi
    wifi_string = f"WIFI:T:{wifi_info['security']};S:{wifi_info['ssid']};P:{wifi_info['password']};H:false;;"
    
    # Générer le QR-code
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(wifi_string)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return render(request, 'prestation/qr_code_wifi.html', {
        'qr_code': qr_code_base64,
        'wifi_info': wifi_info,
    })


def mobile_login(request):
    """Vérifie le user sur le téléphone et génère un code unique"""
    from django.contrib.auth.models import User
    import random
    import string
    from django.utils import timezone
    from datetime import timedelta
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        
        # Vérifier si le user existe
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Utilisateur introuvable'})
        
        # Vérifier que le compte est actif
        if not user.is_active:
            return JsonResponse({'success': False, 'message': 'Compte désactivé'})
        
        # Générer un code unique à 6 chiffres
        code = ''.join(random.choices(string.digits, k=6))
        
        # Expiration dans 5 minutes
        expire_le = timezone.now() + timedelta(minutes=5)
        
        # Créer le code temporaire
        CodeTemporaire.objects.create(
            user=user,
            code=code,
            expire_le=expire_le
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Code généré ! Entrez le code {code} sur la machine',
            'code': code,
            'username': username,
            'expire_le': expire_le.strftime('%H:%M')
        })
    
    return render(request, 'prestation/mobile_login.html')


def tablette_verification(request):
    """Saisie du code sur la machine pour pointer"""
    from django.utils import timezone
    
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        
        # Chercher le code temporaire
        try:
            code_temp = CodeTemporaire.objects.get(code=code, est_utilise=False)
        except CodeTemporaire.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Code invalide ou déjà utilisé'})
        
        # Vérifier que le code n'est pas expiré
        if not code_temp.est_valide():
            return JsonResponse({'success': False, 'message': 'Code expiré. Veuillez recommencer'})
        
        # Marquer le code comme utilisé
        code_temp.est_utilise = True
        code_temp.save()
        
        # Récupérer la session active
        session = SessionPrestation.objects.filter(statut='EN_COURS').order_by('-id').first()
        if not session:
            return JsonResponse({'success': False, 'message': 'Aucune session en cours'})
        
        agent = code_temp.user.utilisateur.agent
        heure_actuelle = timezone.now().time()
        
        # Vérifier si l'agent a déjà pointé pour cette session
        prestation_existante = Prestation.objects.filter(agent=agent, session=session).first()
        if prestation_existante and prestation_existante.heure_arrivee:
            return JsonResponse({
                'success': False,
                'message': 'Arrivée déjà enregistrée pour cette session',
                'proposer_depart': True
            })
        
        # Déterminer le statut
        statut = 'PRESENT'
        if session.heure_limite and heure_actuelle > session.heure_limite:
            statut = 'RETARD'
        
        # Enregistrer l'arrivée
        if prestation_existante:
            prestation_existante.heure_arrivee = heure_actuelle
            prestation_existante.statut = statut
            prestation_existante.save()
        else:
            Prestation.objects.create(
                agent=agent,
                date=session.date,
                session=session,
                statut=statut,
                heure_arrivee=heure_actuelle
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Arrivée enregistrée pour {agent.nom_complet()} à {heure_actuelle.strftime("%H:%M")} - Statut: {statut}',
            'agent_nom': agent.nom_complet(),
            'heure_arrivee': heure_actuelle.strftime('%H:%M'),
            'statut': statut
        })
    
    return render(request, 'prestation/tablette_verification.html')


# ==============================
# API
# ==============================
@login_required
def api_dashboard_stats(request):
    today = date.today()
    return JsonResponse({
        'agents_presents': Prestation.objects.filter(date=today, statut='PRESENT').count(),
        'agents_retard': Prestation.objects.filter(date=today, statut='RETARD').count(),
        'agents_absents': Prestation.objects.filter(date=today, statut='ABSENT').count(),
        'total_prestations': Prestation.objects.filter(date=today).count(),
        'prestations_enseignants': PrestationEnseignant.objects.filter(prestation__date=today).count(),
    })


@login_required
def api_session_stats(request, session_id):
    session = get_object_or_404(SessionPrestation, pk=session_id)
    prestations = Prestation.objects.filter(session=session)
    
    return JsonResponse({
        'total_presents': prestations.filter(statut='PRESENT').count(),
        'total_retards': prestations.filter(statut='RETARD').count(),
        'total_absents': prestations.filter(statut='ABSENT').count(),
        'total_en_cours': prestations.filter(statut='EN_COURS').count(),
        'total_agents': prestations.count(),
    })


@login_required
def api_prestations_en_cours(request):
    today = date.today()
    prestations = Prestation.objects.filter(
        date=today, statut__in=['EN_COURS', 'RETARD']
    ).select_related('agent', 'agent__service').values(
        'agent__nom', 'agent__postnom', 'agent__prenom',
        'agent__service__nom', 'heure_arrivee', 'statut'
    )[:20]
    return JsonResponse({'prestations': list(prestations)})


@login_required
def api_prestations_enseignants_nouvelles(request):
    """API pour récupérer les prestations enseignants non validées"""
    if request.user.utilisateur.role not in ['ADMIN', 'SECRETAIRE']:
        return JsonResponse({'success': False, 'message': 'Accès refusé'})
    
    # Récupérer les prestations enseignants non validées d'aujourd'hui
    today = date.today()
    nouvelles_prestations = PrestationEnseignant.objects.filter(
        prestation__date=today,
        valide=False
    ).select_related(
        'prestation__agent',
        'cours',
        'classe'
    ).order_by('-created_at')
    
    result = []
    for pe in nouvelles_prestations:
        result.append({
            'id': pe.id,
            'agent_nom': pe.prestation.agent.nom_complet(),
            'cours': pe.cours.libelle,
            'classe': pe.classe.nom,
            'heure_debut': pe.heure_debut.strftime('%H:%M') if pe.heure_debut else None,
            'heure_fin': pe.heure_fin.strftime('%H:%M') if pe.heure_fin else None,
            'duree': pe.duree_cours(),
            'observation': pe.observation or '',
            'date': pe.prestation.date.strftime('%d/%m/%Y'),
        })
    
    return JsonResponse({
        'prestations': result
    })
