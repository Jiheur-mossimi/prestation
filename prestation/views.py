from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import Agent, Service, Cours, Classe, Fonction, Mois

# ============================
# DASHBOARD
# ============================
def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    context = {
        'total_agents': Agent.objects.filter(etat=True).count(),
        'total_services': Service.objects.count(),
        'total_cours': Cours.objects.filter(actif=True).count(),
        'total_classes': Classe.objects.filter(status='ACTIF').count(),
    }
    return render(request, 'dashboard.html', context)

# ============================
# LOGIN/LOGOUT
# ============================
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        from django.contrib.auth import authenticate, login
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenue {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Email ou mot de passe incorrect.')
    
    return render(request, 'login.html')

def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('login')

# ============================
# PROFILE
# ============================
@login_required
def profile(request):
    return render(request, 'profile.html')

@login_required
def profile_update(request):
    if request.method == 'POST':
        user = request.user
        user.email = request.POST.get('email')
        
        if hasattr(user, 'utilisateur') and hasattr(user.utilisateur, 'agent'):
            user.utilisateur.agent.telephone = request.POST.get('telephone')
            user.utilisateur.agent.adresse = request.POST.get('adresse')
            
            # Gestion de la photo de profil
            if 'photo' in request.FILES:
                user.utilisateur.agent.photo = request.FILES['photo']
            
            user.utilisateur.agent.save()
        user.save()
        messages.success(request, 'Profil mis à jour avec succès.')
    return redirect('profile')

@login_required
def change_password(request):
    if request.method == 'POST':
        from django.contrib.auth import update_session_auth_hash
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(old_password):
            messages.error(request, 'Mot de passe actuel incorrect.')
        elif new_password != confirm_password:
            messages.error(request, 'Les nouveaux mots de passe ne correspondent pas.')
        else:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Mot de passe changé avec succès.')
    return redirect('profile')

# ============================
# AGENTS
# ============================
@login_required
def agents_index(request):
    agents = Agent.objects.all().order_by('nom', 'postnom')
    return render(request, 'agents/index.html', {'agents': agents})

@login_required
def agent_create(request):
    if request.method == 'POST':
        from .forms import AgentForm
        form = AgentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Agent créé avec succès.')
            return redirect('agents')
    else:
        from .forms import AgentForm
        form = AgentForm()
    
    services = Service.objects.all()
    return render(request, 'agents/form.html', {
        'form': form,
        'form_title': 'Nouvel Agent',
        'services': services
    })

@login_required
def agent_edit(request, id):
    agent = get_object_or_404(Agent, id=id)
    
    if request.method == 'POST':
        from .forms import AgentForm
        form = AgentForm(request.POST, request.FILES, instance=agent)
        if form.is_valid():
            form.save()
            messages.success(request, 'Agent modifié avec succès.')
            return redirect('agents')
    else:
        from .forms import AgentForm
        form = AgentForm(instance=agent)
    
    services = Service.objects.all()
    return render(request, 'agents/form.html', {
        'form': form,
        'form_title': "Modifier l'Agent",
        'services': services,
        'agent': agent
    })

@login_required
def agent_show(request, id):
    agent = get_object_or_404(Agent, id=id)
    return render(request, 'agents/show.html', {'agent': agent})

@login_required
def agent_delete(request, id):
    agent = get_object_or_404(Agent, id=id)
    if request.method == 'POST':
        agent.delete()
        messages.success(request, 'Agent supprimé avec succès.')
    return redirect('agents')

# ============================
# SERVICES
# ============================
@login_required
def services_index(request):
    services = Service.objects.all()
    return render(request, 'services/index.html', {'services': services})

@login_required
def service_show(request, id):
    service = get_object_or_404(Service, id=id)
    return render(request, 'services/show.html', {'service': service})

@login_required
def service_create(request):
    if request.method == 'POST':
        from .forms import ServiceForm
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Service créé avec succès.')
            return redirect('services')
    else:
        from .forms import ServiceForm
        form = ServiceForm()
    
    return render(request, 'services/form.html', {
        'form': form,
        'form_title': 'Nouveau Service'
    })

@login_required
def service_edit(request, id):
    service = get_object_or_404(Service, id=id)
    
    if request.method == 'POST':
        from .forms import ServiceForm
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, 'Service modifié avec succès.')
            return redirect('services')
    else:
        from .forms import ServiceForm
        form = ServiceForm(instance=service)
    
    return render(request, 'services/form.html', {
        'form': form,
        'form_title': 'Modifier le Service'
    })

@login_required
def service_delete(request, id):
    service = get_object_or_404(Service, id=id)
    if request.method == 'POST':
        service.delete()
        messages.success(request, 'Service supprimé avec succès.')
    return redirect('services')

# ============================
# COURS
# ============================
@login_required
def cours_index(request):
    cours = Cours.objects.all()
    return render(request, 'cours/index.html', {'cours': cours})

@login_required
def cours_show(request, id):
    cour = get_object_or_404(Cours, id=id)
    return render(request, 'cours/show.html', {'cour': cour})

@login_required
def cours_create(request):
    if request.method == 'POST':
        from .forms import CoursForm
        form = CoursForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cours créé avec succès.')
            return redirect('cours')
    else:
        from .forms import CoursForm
        form = CoursForm()
    
    return render(request, 'cours/form.html', {
        'form': form,
        'form_title': 'Nouveau Cours'
    })

@login_required
def cours_edit(request, id):
    cour = get_object_or_404(Cours, id=id)
    
    if request.method == 'POST':
        from .forms import CoursForm
        form = CoursForm(request.POST, instance=cour)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cours modifié avec succès.')
            return redirect('cours')
    else:
        from .forms import CoursForm
        form = CoursForm(instance=cour)
    
    return render(request, 'cours/form.html', {
        'form': form,
        'form_title': 'Modifier le Cours'
    })

@login_required
def cours_delete(request, id):
    cour = get_object_or_404(Cours, id=id)
    if request.method == 'POST':
        cour.delete()
        messages.success(request, 'Cours supprimé avec succès.')
    return redirect('cours')

# ============================
# CLASSES
# ============================
@login_required
def classes_index(request):
    classes = Classe.objects.all()
    return render(request, 'classes/index.html', {'classes': classes})

@login_required
def classe_show(request, id):
    classe = get_object_or_404(Classe, id=id)
    return render(request, 'classes/show.html', {'classe': classe})

@login_required
def classe_create(request):
    if request.method == 'POST':
        from .forms import ClasseForm
        form = ClasseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Classe créée avec succès.')
            return redirect('classes')
    else:
        from .forms import ClasseForm
        form = ClasseForm()
    
    return render(request, 'classes/form.html', {
        'form': form,
        'form_title': 'Nouvelle Classe'
    })

@login_required
def classe_edit(request, id):
    classe = get_object_or_404(Classe, id=id)
    
    if request.method == 'POST':
        from .forms import ClasseForm
        form = ClasseForm(request.POST, instance=classe)
        if form.is_valid():
            form.save()
            messages.success(request, 'Classe modifiée avec succès.')
            return redirect('classes')
    else:
        from .forms import ClasseForm
        form = ClasseForm(instance=classe)
    
    return render(request, 'classes/form.html', {
        'form': form,
        'form_title': 'Modifier la Classe'
    })

@login_required
def classe_delete(request, id):
    classe = get_object_or_404(Classe, id=id)
    if request.method == 'POST':
        classe.delete()
        messages.success(request, 'Classe supprimée avec succès.')
    return redirect('classes')

# ============================
# FONCTIONS
# ============================
@login_required
def fonctions_index(request):
    fonctions = Fonction.objects.all()
    return render(request, 'fonctions/index.html', {'fonctions': fonctions})

@login_required
def fonction_show(request, id):
    fonction = get_object_or_404(Fonction, id=id)
    return render(request, 'fonctions/show.html', {'fonction': fonction})

@login_required
def fonction_create(request):
    if request.method == 'POST':
        from .forms import FonctionForm
        form = FonctionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fonction créée avec succès.')
            return redirect('fonctions')
    else:
        from .forms import FonctionForm
        form = FonctionForm()
    
    return render(request, 'fonctions/form.html', {
        'form': form,
        'form_title': 'Nouvelle Fonction'
    })

@login_required
def fonction_edit(request, id):
    fonction = get_object_or_404(Fonction, id=id)
    
    if request.method == 'POST':
        from .forms import FonctionForm
        form = FonctionForm(request.POST, instance=fonction)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fonction modifiée avec succès.')
            return redirect('fonctions')
    else:
        from .forms import FonctionForm
        form = FonctionForm(instance=fonction)
    
    return render(request, 'fonctions/form.html', {
        'form': form,
        'form_title': 'Modifier la Fonction'
    })

@login_required
def fonction_delete(request, id):
    fonction = get_object_or_404(Fonction, id=id)
    if request.method == 'POST':
        fonction.delete()
        messages.success(request, 'Fonction supprimée avec succès.')
    return redirect('fonctions')

# ============================
# MOIS
# ============================
@login_required
def mois_index(request):
    mois_list = Mois.objects.all().order_by('-annee', '-mois_num')
    return render(request, 'mois/index.html', {'mois_list': mois_list})

@login_required
def mois_show(request, id):
    mois = get_object_or_404(Mois, id=id)
    return render(request, 'mois/show.html', {'mois': mois})

@login_required
def mois_create(request):
    if request.method == 'POST':
        from .forms import MoisForm
        form = MoisForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Mois créé avec succès.')
            return redirect('mois')
    else:
        from .forms import MoisForm
        form = MoisForm()
    
    return render(request, 'mois/form.html', {
        'form': form,
        'form_title': 'Nouveau Mois'
    })

@login_required
def mois_edit(request, id):
    mois = get_object_or_404(Mois, id=id)
    
    if request.method == 'POST':
        from .forms import MoisForm
        form = MoisForm(request.POST, instance=mois)
        if form.is_valid():
            form.save()
            messages.success(request, 'Mois modifié avec succès.')
            return redirect('mois')
    else:
        from .forms import MoisForm
        form = MoisForm(instance=mois)
    
    return render(request, 'mois/form.html', {
        'form': form,
        'form_title': 'Modifier le Mois'
    })

@login_required
def mois_delete(request, id):
    mois = get_object_or_404(Mois, id=id)
    if request.method == 'POST':
        mois.delete()
        messages.success(request, 'Mois supprimé avec succès.')
    return redirect('mois')

# ============================
# RAPPORTS
# ============================
@login_required
def rapports_index(request):
    services = Service.objects.all()
    agents = Agent.objects.filter(etat=True)
    return render(request, 'rapports/index.html', {
        'services': services,
        'agents': agents
    })

# ============================
# NOTIFICATIONS
# ============================
@login_required
def notifications(request):
    return render(request, 'notifications.html')

# ============================
# MESSAGES
# ============================
@login_required
def messages_chat(request):
    return render(request, 'messages/chat.html')

# ============================
# UTILISATEURS
# ============================
@login_required
def utilisateurs_index(request):
    from django.contrib.auth.models import User
    utilisateurs = User.objects.filter(utilisateur__isnull=False).select_related('utilisateur__agent')
    return render(request, 'utilisateurs/index.html', {'utilisateurs': utilisateurs})

# ============================
# PARAMÈTRES
# ============================
@login_required
def parametres_index(request):
    return render(request, 'parametres/index.html')