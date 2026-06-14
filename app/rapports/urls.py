from django.urls import path
from . import views
urlpatterns = [
    path('', views.tableau_de_bord_stats, name='rapports_dashboard'),
    path('financier/', views.rapport_financier, name='rapport_financier'),
    path('activite/', views.rapport_activite, name='rapport_activite'),
    path('pdf/<str:type_rapport>/', views.exporter_pdf, name='exporter_pdf'),
]
