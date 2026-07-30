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
    Utilisateur, Remarque
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
    return render(request, 'prestation/session_detail.html', {'session': session, 'prestations': prestations})


@login_required
@user_passes_test(lambda u: u.utilisateur.role in ['ADMIN', 'SECRETAIRE'])
def ouvrir_session(request):
    today = date.today()
    if SessionPrestation.objects.filter(date=today, statut='EN_COURS').exists():
        return redirect('dashboard')
    
    session = SessionPrestation.objects.create(
        date=today, heure_ouverture=timezone.now().time(),
        statut='EN_COURS', ouvert_par=request.user.utilisateur
    )
    for agent in Agent.objects.filter(etat=True):
        Prestation.objects.get_or_create(
            agent=agent, date=today, session=session,
            defaults={'heure_arrivee': None, 'statut': 'ABSENT'}
        )
    return redirect('dashboard')


@login_required
@user_passes_test(lambda u: u.utilisateur.role in ['ADMIN', 'SECRETAIRE'])
def clore_session(request, session_id):
    session = get_object_or_404(SessionPrestation, pk=session_id)
    if session.statut == 'TERMINEE':
        return redirect('session_detail', session_id=session.id)
    
    Prestation.objects.filter(
        session=session, statut__in=['PRESENT', 'RETARD', 'EN_COURS']
    ).update(statut='TERMINE')
    
    session.statut = 'TERMINEE'
    session.heure_fermeture = timezone.now().time()
    session.cloture_par = request.user.utilisateur
    session.save()
    return redirect('session_detail', session_id=session.id)


# ==============================
# POINTAGE
# ==============================
@login_required
def pointer_arrivee(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})
    
    today = date.today()
    session = SessionPrestation.objects.filter(date=today, statut='EN_COURS').first()
    if not session:
        return JsonResponse({'success': False, 'message': 'Aucune session ouverte'})
    
    agent = request.user.utilisateur.agent
    prestation, created = Prestation.objects.get_or_create(
        agent=agent, date=today,
        defaults={'session': session, 'statut': 'PRESENT', 'heure_arrivee': timezone.now().time()}
    )
    if not created:
        return JsonResponse({'success': False, 'message': 'Arrivée déjà pointée'})
    
    return JsonResponse({'success': True, 'message': 'Arrivée enregistrée', 'heure_arrivee': prestation.heure_arrivee.strftime('%H:%M')})


@login_required
def pointer_depart(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})
    
    today = date.today()
    agent = request.user.utilisateur.agent
    prestation = get_object_or_404(Prestation, agent=agent, date=today)
    if not prestation.heure_arrivee:
        return JsonResponse({'success': False, 'message': 'Vous devez pointer votre arrivée avant le départ'})
    if prestation.heure_depart:
        return JsonResponse({'success': False, 'message': 'Départ déjà pointé'})
    
    prestation.heure_depart = timezone.now().time()
    prestation.statut = 'TERMINE'
    prestation.save()
    return JsonResponse({'success': True, 'message': 'Départ enregistré', 'heure_depart': prestation.heure_depart.strftime('%H:%M'), 'duree': prestation.duree_prestation()})


@login_required
def pointage(request):
    today = date.today()
    session = SessionPrestation.objects.filter(date=today, statut='EN_COURS').first()
    context = {'session_active': session is not None, 'peut_pointer_arrivee': False, 'peut_pointer_depart': False, 'prestation_terminee': False}
    
    if session:
        agent = request.user.utilisateur.agent
        try:
            prestation = Prestation.objects.get(agent=agent, date=today)
            context.update({
                'peut_pointer_arrivee': not prestation.heure_arrivee,
                'peut_pointer_depart': prestation.heure_arrivee and not prestation.heure_depart,
                'prestation_terminee': prestation.heure_depart is not None,
                'heure_arrivee': prestation.heure_arrivee,
                'heure_depart': prestation.heure_depart,
                'duree': prestation.duree_prestation(),
                'statut': prestation.get_statut_display(),
            })
        except Prestation.DoesNotExist:
            context['peut_pointer_arrivee'] = True
    
    return render(request, 'prestation/pointage.html', context)


# ==============================
# PRESTATIONS
# ==============================
@login_required
def prestations_list(request):
    sessions = SessionPrestation.objects.all().order_by('-date')
    return render(request, 'prestation/prestations_list.html', {'sessions': sessions})


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
    for pe in prestations:
        date_key = pe.prestation.date
        if date_key not in by_date:
            by_date[date_key] = []
        by_date[date_key].append(pe)
    
    return render(request, 'prestation/prestations_enseignants_list.html', {'prestations_by_date': by_date})


@login_required
def mon_historique(request):
    agent = request.user.utilisateur.agent
    today = date.today()

    # Récupérer les paramètres de filtre
    date_filter = request.GET.get('date', '')
    mois_filter = request.GET.get('mois', '')
    annee_filter = request.GET.get('annee', '')

    # Construire le queryset de base
    queryset = Prestation.objects.filter(agent=agent)

    # Appliquer les filtres
    if date_filter:
        queryset = queryset.filter(date=date_filter)
    elif mois_filter and annee_filter:
        queryset = queryset.filter(date__year=annee_filter, date__month=mois_filter)
    elif annee_filter:
        queryset = queryset.filter(date__year=annee_filter)

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
    })


@login_required
def prestation_enseignant_create(request):
    if request.method == 'POST':
        try:
            agent = request.user.utilisateur.agent
            prestation = Prestation.objects.get(agent=agent, date=date.today())
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
def agent_show(request, agent_id):
    return render(request, 'agents/show.html', {'agent': get_object_or_404(Agent, pk=agent_id)})


@login_required
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
def login_view(request):
    from django.contrib.auth import authenticate, login as auth_login
    from django.contrib import messages
    
    if request.user.is_authenticated:
        messages.success(request, 'Bienvenue, vous êtes déjà connecté.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not password:
            messages.error(request, 'Veuillez remplir tous les champs.')
            return render(request, 'login.html')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            messages.success(request, f'✅ Connexion réussie ! Bienvenue {user.username}.')
            return redirect('dashboard')
        else:
            messages.error(request, '❌ Identifiants incorrects. Veuillez vérifier votre nom d\'utilisateur et mot de passe.')
    
    return render(request, 'login.html')


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
    msgs = Remarque.objects.filter(
        Q(expediteur=request.user) | Q(destinataire=request.user)
    ).select_related('expediteur', 'destinataire').order_by('-created_at')
    return render(request, 'messages/chat.html', {'messages': msgs})


@login_required
def notifications_view(request):
    return render(request, 'notifications.html', {
        'notifications': Remarque.objects.filter(destinataire=request.user, categorie='NOTIFICATION').order_by('-created_at')
    })


@login_required
def rapports_view(request):
    return render(request, 'rapports/index.html', {
        'services': Service.objects.all(),
        'agents': Agent.objects.filter(etat=True),
    })


@login_required
def parametres_view(request):
    return render(request, 'parametres/index.html')


@login_required
def profile_view(request):
    return render(request, 'profile.html')


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
def api_prestations_en_cours(request):
    today = date.today()
    prestations = Prestation.objects.filter(
        date=today, statut__in=['EN_COURS', 'RETARD']
    ).select_related('agent', 'agent__service').values(
        'agent__nom', 'agent__postnom', 'agent__prenom',
        'agent__service__nom', 'heure_arrivee', 'statut'
    )[:20]
    return JsonResponse({'prestations': list(prestations)})