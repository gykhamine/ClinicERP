from django.urls import path
from . import views
urlpatterns = [
    path('', views.liste_analyses, name='liste_analyses'),
    path('prescrire/', views.prescrire_analyse, name='prescrire_analyse'),
    path('<int:pk>/resultats/', views.saisir_resultats, name='saisir_resultats'),
    path('<int:pk>/', views.detail_analyse, name='detail_analyse'),
]
