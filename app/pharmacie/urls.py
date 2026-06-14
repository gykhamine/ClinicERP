from django.urls import path
from . import views
urlpatterns = [
    path('', views.liste_medicaments, name='liste_medicaments'),
    path('nouveau/', views.creer_medicament, name='creer_medicament'),
    path('<int:pk>/mouvement/', views.mouvement_stock, name='mouvement_stock'),
    path('ordonnance/<int:ordonnance_pk>/dispenser/', views.dispenser_ordonnance, name='dispenser_ordonnance'),
    path('historique/', views.historique_mouvements, name='historique_mouvements'),
]
