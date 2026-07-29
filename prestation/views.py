from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.utils import timezone
from django.http import JsonResponse
from datetime import date, timedelta
from .models import (
    SessionPrestation, Prestation, PrestationEnseignant,
    Agent, Service, Classe, Cours, Fonction, Mois,
    Utilisateur, Remarque
)


# ==============================
# DASHBOARD
# ==============================
@login_required
def dashboard(request):
    today = date.today()
    
    stats = {
        'agents_presents': Prestation.objects.filter(date=today, statut='PRESENT').count(),
        'agents_retard': Prestation.objects.filter(date=today, statut='RETARD').count(),
        'agents_absents': Prestation.objects.filter(date=today, statut='ABSENT').count(),
        'total_prestations': Prestation.objects.filter(date=today).count(),
        'prestations_enseignants': PrestationEnseignant.objects.filter(prestation__date=today).count(),
        'cours_enregistres': Cours.objects.filter(prestations__prestation__date=today).distinct().count(),
    }
    
    session_today = SessionPrestation.objects.filter(date=today).first()
    stats['session_ouverte'] = session_today is not None and session_today.statut == 'EN_COURS'
    
    prestations_recentes = Prestation.objects.filter(
        date=today, statut__in=['EN_COURS', 'RETARD']
    ).select_related('agent', 'agent__service').order_by('-heure_arrivee')[:10]
    
    prestations_enseignants_recentes = PrestationEnseignant.objects.filter(
        prestation__date=today
    ).select_related('prestation__agent', 'cours', 'classe').order_by('-prestation__created_at')[:20]
    
    return render(request, 'dashboard.html', {
        'stats': stats,
        'session_today': session_today,
        'prestations_recentes': prestations_recentes,
        'prestations_enseignants_recentes': prestations_enseignants_recentes,
        'today': today,
        'nb_services': Service.objects.count(),
        'nb_sessions': SessionPrestation.objects.count(),
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
    return render(request, 'agents/index.html', {'agents': Agent.objects.select_related('service').all()})


@login_required
def agent_create(request):
    if request.method == 'POST':
        pass
    return render(request, 'agents/form.html', {'services': Service.objects.all()})


@login_required
def agent_show(request, agent_id):
    return render(request, 'agents/show.html', {'agent': get_object_or_404(Agent, pk=agent_id)})


@login_required
def agent_edit(request, agent_id):
    agent = get_object_or_404(Agent, pk=agent_id)
    if request.method == 'POST':
        pass
    return render(request, 'agents/form.html', {'agent': agent, 'services': Service.objects.all()})


@login_required
@user_passes_test(lambda u: u.utilisateur.role == 'ADMIN')
def agent_delete(request, agent_id):
    get_object_or_404(Agent, pk=agent_id).delete()
    return redirect('agents')


# ==============================
# SERVICES
# ==============================
@login_required
def services_list(request):
    return render(request, 'services/index.html', {'services': Service.objects.annotate(nb_agents=Count('agents')).all()})


@login_required
def service_create(request):
    if request.method == 'POST':
        pass
    return render(request, 'services/form.html')


@login_required
def service_show(request, service_id):
    return render(request, 'services/show.html', {'service': get_object_or_404(Service, pk=service_id)})


@login_required
def service_edit(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    if request.method == 'POST':
        pass
    return render(request, 'services/form.html', {'service': service})


@login_required
@user_passes_test(lambda u: u.utilisateur.role == 'ADMIN')
def service_delete(request, service_id):
    get_object_or_404(Service, pk=service_id).delete()
    return redirect('services')


# ==============================
# CLASSES
# ==============================
@login_required
def classes_list(request):
    return render(request, 'classes/index.html', {'classes': Classe.objects.all()})


@login_required
def classe_create(request):
    if request.method == 'POST':
        pass
    return render(request, 'classes/form.html')


@login_required
def classe_show(request, classe_id):
    return render(request, 'classes/show.html', {'classe': get_object_or_404(Classe, pk=classe_id)})


@login_required
def classe_edit(request, classe_id):
    classe = get_object_or_404(Classe, pk=classe_id)
    if request.method == 'POST':
        pass
    return render(request, 'classes/form.html', {'classe': classe})


@login_required
@user_passes_test(lambda u: u.utilisateur.role == 'ADMIN')
def classe_delete(request, classe_id):
    get_object_or_404(Classe, pk=classe_id).delete()
    return redirect('classes')


# ==============================
# COURS
# ==============================
@login_required
def cours_list(request):
    return render(request, 'cours/index.html', {'cours': Cours.objects.all()})


@login_required
def cours_create(request):
    if request.method == 'POST':
        pass
    return render(request, 'cours/form.html')


@login_required
def cours_show(request, cours_id):
    return render(request, 'cours/show.html', {'cours': get_object_or_404(Cours, pk=cours_id)})


@login_required
def cours_edit(request, cours_id):
    cours = get_object_or_404(Cours, pk=cours_id)
    if request.method == 'POST':
        pass
    return render(request, 'cours/form.html', {'cours': cours})


@login_required
@user_passes_test(lambda u: u.utilisateur.role == 'ADMIN')
def cours_delete(request, cours_id):
    get_object_or_404(Cours, pk=cours_id).delete()
    return redirect('cours')


# ==============================
# FONCTIONS
# ==============================
@login_required
def fonctions_list(request):
    return render(request, 'fonctions/index.html', {'fonctions': Fonction.objects.all()})


@login_required
def fonction_create(request):
    if request.method == 'POST':
        pass
    return render(request, 'fonctions/form.html')


@login_required
def fonction_show(request, fonction_id):
    return render(request, 'fonctions/show.html', {'fonction': get_object_or_404(Fonction, pk=fonction_id)})


@login_required
def fonction_edit(request, fonction_id):
    fonction = get_object_or_404(Fonction, pk=fonction_id)
    if request.method == 'POST':
        pass
    return render(request, 'fonctions/form.html', {'fonction': fonction})


@login_required
@user_passes_test(lambda u: u.utilisateur.role == 'ADMIN')
def fonction_delete(request, fonction_id):
    get_object_or_404(Fonction, pk=fonction_id).delete()
    return redirect('fonctions')


# ==============================
# MOIS
# ==============================
@login_required
def mois_list(request):
    return render(request, 'mois/index.html', {'mois_list': Mois.objects.all()})


@login_required
def mois_create(request):
    if request.method == 'POST':
        pass
    return render(request, 'mois/form.html')


@login_required
def mois_show(request, mois_id):
    return render(request, 'mois/show.html', {'mois': get_object_or_404(Mois, pk=mois_id)})


@login_required
def mois_edit(request, mois_id):
    mois = get_object_or_404(Mois, pk=mois_id)
    if request.method == 'POST':
        pass
    return render(request, 'mois/form.html', {'mois': mois})


@login_required
@user_passes_test(lambda u: u.utilisateur.role == 'ADMIN')
def mois_delete(request, mois_id):
    get_object_or_404(Mois, pk=mois_id).delete()
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