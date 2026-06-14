from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import DemandeAnalyse, TypeAnalyse, ResultatAnalyse
from apps.patients.models import Patient
from apps.accounts.decorators import laborantin_only, medecin_only, personnel_only

@login_required
@personnel_only
def liste_analyses(request):
    statut = request.GET.get('statut','')
    priorite = request.GET.get('priorite','')
    analyses = DemandeAnalyse.objects.select_related('patient__utilisateur','medecin_prescripteur').all()
    if statut:
        analyses = analyses.filter(statut=statut)
    if priorite:
        analyses = analyses.filter(priorite=priorite)
    if request.user.role == 'laborantin':
        analyses = analyses.filter(statut__in=['demande','en_cours'])
    return render(request, 'laboratoire/liste.html', {'analyses': analyses, 'statut_filtre': statut})

@login_required
@medecin_only
def prescrire_analyse(request):
    if request.method == 'POST':
        patient = get_object_or_404(Patient, pk=request.POST['patient'])
        demande = DemandeAnalyse.objects.create(
            patient=patient,
            medecin_prescripteur=request.user,
            priorite=request.POST.get('priorite','normale'),
            notes_cliniques=request.POST.get('notes',''),
        )
        types_ids = request.POST.getlist('types_analyses')
        demande.types_analyses.set(types_ids)
        from apps.notifications.models import Notification
        for lab in __import__('apps.accounts.models', fromlist=['Utilisateur']).Utilisateur.objects.filter(role='laborantin'):
            Notification.objects.create(
                destinataire=lab, expediteur=request.user,
                titre=f"Nouvelle analyse – {patient}",
                message=f"Demande d'analyse de Dr.{request.user.last_name}",
                type_notif='rappel' if demande.priorite=='normale' else 'urgence',
            )
        messages.success(request, "Demande d'analyse envoyée au laboratoire.")
        return redirect('liste_analyses')
    patients = Patient.objects.select_related('utilisateur').all()
    types = TypeAnalyse.objects.all()
    return render(request, 'laboratoire/form_demande.html', {'patients': patients, 'types': types})

@login_required
@laborantin_only
def saisir_resultats(request, pk):
    demande = get_object_or_404(DemandeAnalyse, pk=pk)
    if request.method == 'POST':
        for ta in demande.types_analyses.all():
            valeur = request.POST.get(f'valeur_{ta.pk}','')
            if valeur:
                ResultatAnalyse.objects.update_or_create(
                    demande=demande, type_analyse=ta,
                    defaults={
                        'valeur': valeur,
                        'unite': request.POST.get(f'unite_{ta.pk}',''),
                        'interpretation': request.POST.get(f'interp_{ta.pk}',''),
                        'anormal': request.POST.get(f'anormal_{ta.pk}') == 'on',
                        'laborantin': request.user,
                    }
                )
        demande.statut = 'termine'
        demande.date_realisation = timezone.now()
        demande.save()
        # Notify prescribing doctor
        from apps.notifications.models import Notification
        Notification.objects.create(
            destinataire=demande.medecin_prescripteur, expediteur=request.user,
            titre=f"Résultats disponibles – {demande.patient}",
            message="Les résultats d'analyses sont disponibles.",
            type_notif='info',
        )
        messages.success(request, "Résultats enregistrés.")
        return redirect('liste_analyses')
    return render(request, 'laboratoire/saisir_resultats.html', {'demande': demande})

@login_required
@personnel_only
def detail_analyse(request, pk):
    demande = get_object_or_404(DemandeAnalyse, pk=pk)
    return render(request, 'laboratoire/detail.html', {'demande': demande})
