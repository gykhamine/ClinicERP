from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.accounts.urls')),
    path('patients/', include('apps.patients.urls')),
    path('consultations/', include('apps.consultations.urls')),
    path('pharmacie/', include('apps.pharmacie.urls')),
    path('laboratoire/', include('apps.laboratoire.urls')),
    path('facturation/', include('apps.facturation.urls')),
    path('rh/', include('apps.rh.urls')),
    path('rapports/', include('apps.rapports.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('hospitalisation/', include('apps.hospitalisation.urls')),
    path('urgences/', include('apps.urgences.urls')),
    path('bloc/', include('apps.bloc_operatoire.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
  + static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
