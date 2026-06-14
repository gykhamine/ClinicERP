from django.urls import path
from . import views
urlpatterns = [
    path('', views.liste_factures, name='liste_factures'),
    path('nouvelle/', views.creer_facture, name='creer_facture'),
    path('<int:pk>/', views.detail_facture, name='detail_facture'),
    path('<int:pk>/paiement/', views.enregistrer_paiement, name='enregistrer_paiement'),
    path('<int:pk>/emettre/', views.emettre_facture, name='emettre_facture'),
    path('services/', views.liste_services, name='liste_services'),
]
