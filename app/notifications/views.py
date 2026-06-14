from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification

@login_required
def liste_notifications(request):
    notifs = Notification.objects.filter(destinataire=request.user)
    notifs.filter(lue=False).update(lue=True)
    return render(request, 'notifications/liste.html', {'notifications': notifs})

@login_required
def marquer_lue(request, pk):
    Notification.objects.filter(pk=pk, destinataire=request.user).update(lue=True)
    return JsonResponse({'ok': True})

@login_required
def count_non_lues(request):
    n = Notification.objects.filter(destinataire=request.user, lue=False).count()
    return JsonResponse({'count': n})
