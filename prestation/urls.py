from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.login_view, name='login'),

    # Connexion
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Agents
    path('agents/', views.agents_index, name='agents'),
    path('agents/create/', views.agent_create, name='agent_create'),
    path('agents/edit/<int:id>/', views.agent_edit, name='agent_edit'),
    path('agents/show/<int:id>/', views.agent_show, name='agent_show'),
    path('agents/delete/<int:id>/', views.agent_delete, name='agent_delete'),
    
    # Services
    path('services/', views.services_index, name='services'),
    path('services/create/', views.service_create, name='service_create'),
    path('services/show/<int:id>/', views.service_show, name='service_show'),
    path('services/edit/<int:id>/', views.service_edit, name='service_edit'),
    path('services/delete/<int:id>/', views.service_delete, name='service_delete'),
    
    # Cours
    path('cours/', views.cours_index, name='cours'),
    path('cours/create/', views.cours_create, name='cours_create'),
    path('cours/show/<int:id>/', views.cours_show, name='cours_show'),
    path('cours/edit/<int:id>/', views.cours_edit, name='cours_edit'),
    path('cours/delete/<int:id>/', views.cours_delete, name='cours_delete'),
    
    # Classes
    path('classes/', views.classes_index, name='classes'),
    path('classes/create/', views.classe_create, name='classe_create'),
    path('classes/show/<int:id>/', views.classe_show, name='classe_show'),
    path('classes/edit/<int:id>/', views.classe_edit, name='classe_edit'),
    path('classes/delete/<int:id>/', views.classe_delete, name='classe_delete'),
    
    # Fonctions
    path('fonctions/', views.fonctions_index, name='fonctions'),
    path('fonctions/create/', views.fonction_create, name='fonction_create'),
    path('fonctions/show/<int:id>/', views.fonction_show, name='fonction_show'),
    path('fonctions/edit/<int:id>/', views.fonction_edit, name='fonction_edit'),
    path('fonctions/delete/<int:id>/', views.fonction_delete, name='fonction_delete'),
    
    # Mois
    path('mois/', views.mois_index, name='mois'),
    path('mois/create/', views.mois_create, name='mois_create'),
    path('mois/show/<int:id>/', views.mois_show, name='mois_show'),
    path('mois/edit/<int:id>/', views.mois_edit, name='mois_edit'),
    path('mois/delete/<int:id>/', views.mois_delete, name='mois_delete'),
    
    # Rapports
    path('rapports/', views.rapports_index, name='rapports'),
    
    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    
    # Messages/Chat
    path('messages/', views.messages_chat, name='messages'),
    
    # Utilisateurs
    path('utilisateurs/', views.utilisateurs_index, name='utilisateurs'),
    
    # Paramètres
    path('parametres/', views.parametres_index, name='parametres'),
    
    # Profile
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.profile_update, name='profile_update'),
    path('profile/change-password/', views.change_password, name='change_password'),
    
]