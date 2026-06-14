from django.urls import path
from . import views
urlpatterns = [
    path('', views.liste_hospitalisations, name='liste_hospitalisations'),
    path('carte/', views.carte_lits, name='carte_lits'),
    path('admettre/', views.admettre_patient, name='admettre_patient'),
    path('<int:pk>/', views.detail_hospitalisation, name='detail_hospitalisation'),
    path('<int:pk>/suivi/', views.ajouter_suivi, name='ajouter_suivi'),
    path('<int:pk>/sortie/', views.sortie_patient, name='sortie_patient'),
    path('<int:pk>/transfert/', views.transfert_service, name='transfert_service'),
    path('structure/', views.gestion_structure, name='gestion_structure'),
    path('structure/service/', views.creer_service, name='creer_service'),
    path('structure/service/<int:service_pk>/lits/', views.creer_lits, name='creer_lits'),
]
