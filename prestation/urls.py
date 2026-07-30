from django.urls import path
from . import views

urlpatterns = [
        # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Authentification
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    
    # Sessions de prestation
    path('sessions/', views.sessions_list, name='sessions_list'),
    path('sessions/<int:session_id>/', views.session_detail, name='session_detail'),
    path('sessions/ouvrir/', views.ouvrir_session, name='ouvrir_session'),
    path('sessions/clore/<int:session_id>/', views.clore_session, name='clore_session'),
    
    # Pointage
    path('pointage/arrivee/', views.pointer_arrivee, name='pointer_arrivee'),
    path('pointage/depart/', views.pointer_depart, name='pointer_depart'),
    path('pointage/', views.pointage, name='pointage'),
    
    # Prestations générales
    path('prestations-generales/', views.prestations_list, name='prestations_list'),
    
    # Prestations enseignants
    path('prestations-enseignants/', views.prestations_enseignants_list, name='prestations_enseignants_list'),
    path('prestations-enseignants/creer/', views.prestation_enseignant_create, name='prestation_enseignant_create'),
    
    # API temps réel
    path('api/dashboard-stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
    path('api/prestations-en-cours/', views.api_prestations_en_cours, name='api_prestations_en_cours'),
    
    # Entités existantes
    path('agents/', views.agents_list, name='agents'),
    path('agents/creer/', views.agent_create, name='agent_create'),
    path('agents/<int:agent_id>/', views.agent_show, name='agent_show'),
    path('agents/<int:agent_id>/modifier/', views.agent_edit, name='agent_edit'),
    path('agents/<int:agent_id>/supprimer/', views.agent_delete, name='agent_delete'),
    
    path('services/', views.services_list, name='services'),
    path('services/creer/', views.service_create, name='service_create'),
    path('services/<int:service_id>/', views.service_show, name='service_show'),
    path('services/<int:service_id>/modifier/', views.service_edit, name='service_edit'),
    path('services/<int:service_id>/supprimer/', views.service_delete, name='service_delete'),
    
    path('classes/', views.classes_list, name='classes'),
    path('classes/creer/', views.classe_create, name='classe_create'),
    path('classes/<int:classe_id>/', views.classe_show, name='classe_show'),
    path('classes/<int:classe_id>/modifier/', views.classe_edit, name='classe_edit'),
    path('classes/<int:classe_id>/supprimer/', views.classe_delete, name='classe_delete'),
    
    path('cours/', views.cours_list, name='cours'),
    path('cours/creer/', views.cours_create, name='cours_create'),
    path('cours/<int:cours_id>/', views.cours_show, name='cours_show'),
    path('cours/<int:cours_id>/modifier/', views.cours_edit, name='cours_edit'),
    path('cours/<int:cours_id>/supprimer/', views.cours_delete, name='cours_delete'),
    
    path('fonctions/', views.fonctions_list, name='fonctions'),
    path('fonctions/creer/', views.fonction_create, name='fonction_create'),
    path('fonctions/<int:fonction_id>/', views.fonction_show, name='fonction_show'),
    path('fonctions/<int:fonction_id>/modifier/', views.fonction_edit, name='fonction_edit'),
    path('fonctions/<int:fonction_id>/supprimer/', views.fonction_delete, name='fonction_delete'),
    
    path('mois/', views.mois_list, name='mois'),
    path('mois/creer/', views.mois_create, name='mois_create'),
    path('mois/<int:mois_id>/', views.mois_show, name='mois_show'),
    path('mois/<int:mois_id>/modifier/', views.mois_edit, name='mois_edit'),
    path('mois/<int:mois_id>/supprimer/', views.mois_delete, name='mois_delete'),
    
    path('utilisateurs/', views.utilisateurs_list, name='utilisateurs'),
    path('utilisateurs/creer/', views.utilisateur_create, name='utilisateur_create'),
    path('utilisateurs/<int:utilisateur_id>/', views.utilisateur_show, name='utilisateur_show'),
    path('utilisateurs/<int:utilisateur_id>/modifier/', views.utilisateur_edit, name='utilisateur_edit'),
    path('utilisateurs/<int:utilisateur_id>/reset-password/', views.utilisateur_reset_password, name='utilisateur_reset_password'),
    path('utilisateurs/<int:utilisateur_id>/supprimer/', views.utilisateur_delete, name='utilisateur_delete'),
    
    path('messages/', views.messages_view, name='messages'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('rapports/', views.rapports_view, name='rapports'),
    path('parametres/', views.parametres_view, name='parametres'),
    path('profile/', views.profile_view, name='profile'),
    path('mon-historique/', views.mon_historique, name='mon_historique'),
    path('changer-mot-de-passe/', views.changer_mot_de_passe, name='changer_mot_de_passe'),
    path('modifier-mes-infos/', views.modifier_mes_infos, name='modifier_mes_infos'),
]
