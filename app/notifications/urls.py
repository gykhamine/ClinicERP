from django.urls import path
from . import views
urlpatterns = [
    path('', views.liste_notifications, name='liste_notifications'),
    path('<int:pk>/lue/', views.marquer_lue, name='marquer_lue'),
    path('count/', views.count_non_lues, name='count_notifications'),
]
