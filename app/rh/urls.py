from django.urls import path
from . import views
urlpatterns = [
    path('', views.liste_personnel, name='liste_personnel'),
    path('fiche/nouvelle/', views.creer_fiche, name='creer_fiche'),
    path('conge/demander/', views.demander_conge, name='demander_conge'),
    path('conge/mes/', views.mes_conges, name='mes_conges'),
    path('conge/gerer/', views.gerer_conges, name='gerer_conges'),
    path('planning/', views.planning, name='planning'),
]
