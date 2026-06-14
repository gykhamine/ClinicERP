from django.urls import path
from . import views
urlpatterns = [
    path('', views.liste_patients, name='liste_patients'),
    path('nouveau/', views.creer_patient, name='creer_patient'),
    path('<int:pk>/', views.detail_patient, name='detail_patient'),
    path('<int:pk>/modifier/', views.modifier_patient, name='modifier_patient'),
    path('<int:patient_pk>/dossier/', views.ajouter_dossier, name='ajouter_dossier'),
]
