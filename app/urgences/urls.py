from django.urls import path
from . import views
urlpatterns = [
    path('', views.tableau_urgences, name='tableau_urgences'),
    path('arrivee/', views.enregistrer_arrivee, name='enregistrer_arrivee'),
    path('<int:pk>/', views.detail_urgence, name='detail_urgence'),
    path('<int:pk>/triage/', views.triage, name='triage'),
    path('<int:pk>/prise-en-charge/', views.prise_en_charge, name='prise_en_charge'),
    path('<int:pk>/sortie/', views.sortie_urgence, name='sortie_urgence'),
    path('<int:pk>/acte/', views.ajouter_acte, name='ajouter_acte'),
    path('historique/', views.historique_urgences, name='historique_urgences'),
]
