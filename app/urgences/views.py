from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import PassageUrgence, ActeUrgence, TRIAGE_CHOICES
from apps.patients.models import Patient
from apps.accounts.models import Utilisateur
from apps.accounts.decorators import personnel_only, medecin_only


@login_required
@personnel_only
def tableau_urgences(request):
    """Tableau de bord temps réel des urgences"""
    passages_actifs = PassageUrgence.objects.filter(
        statut__in=['attente_triage','triage_fait','en_cours','observation']
    ).select_related('patient__utilisateur', 'medecin_prise_en_charge', 'infirmier_triage')

    # Compter par niveau de triage
    stats_triage = {}
    for i in range(1, 6):
        stats_triage[i] = passages_actifs.filter(niveau_triage=i).count()

    ctx = {
        'passages': passages_actifs,
        'stats_triage': stats_triage,
        'triage_choices': TRIAGE_CHOICES,
        'total_actifs': passages_actifs.count(),
        'en_attente': passages_actifs.filter(statut='attente_triage').count(),
    }
    return render(request, 'urgences/tableau.html', ctx)


@login_required
@personnel_only
def enregistrer_arrivee(request):
    if request.method == 'POST':
        patient = get_object_or_404(Patient, pk=request.POST['patient'])
        passage = PassageUrgence.objects.create(
            patient=patient,
            motif_venue=request.POST['motif_venue'],
            created_by=request.user,
        )
        messages.success(request, f"Arrivée de {patient} enregistrée. N° URG-{passage.pk}")
        return redirect('detail_urgence', pk=passage.pk)
    patients = Patient.objects.select_related('utilisateur').all()
    return render(request, 'urgences/form_arrivee.html', {'patients': patients})


@login_required
@personnel_only
def triage(request, pk):
    passage = get_object_or_404(PassageUrgence, pk=pk)
    if request.method == 'POST':
        passage.niveau_triage = int(request.POST['niveau_triage'])
        passage.tension = request.POST.get('tension', '')
        passage.temperature = request.POST.get('temperature') or None
        passage.frequence_cardiaque = request.POST.get('frequence_cardiaque') or None
        passage.saturation_o2 = request.POST.get('saturation_o2') or None
        passage.frequence_respiratoire = request.POST.get('frequence_respiratoire') or None
        passage.glasgow = request.POST.get('glasgow') or None
        passage.symptomes = request.POST.get('symptomes', '')
        passage.infirmier_triage = request.user
        passage.date_triage = timezone.now()
        passage.statut = 'triage_fait'
        passage.save()
        # Notification médecin si P1 ou P2
        if passage.niveau_triage <= 2:
            from apps.notifications.models import Notification
            for med in Utilisateur.objects.filter(role__in=['medecin', 'chef']):
                Notification.objects.create(
                    destinataire=med, expediteur=request.user,
                    titre=f"🚨 Triage P{passage.niveau_triage} — {patient}",
                    message=f"Patient {passage.patient} nécessite une prise en charge immédiate. Urgences salle {pk}",
                    type_notif='urgence',
                )
        messages.success(request, f"Triage effectué — Priorité P{passage.niveau_triage}")
        return redirect('detail_urgence', pk=pk)
    return render(request, 'urgences/triage.html', {'passage': passage, 'triage_choices': TRIAGE_CHOICES})


@login_required
@personnel_only
def detail_urgence(request, pk):
    passage = get_object_or_404(PassageUrgence, pk=pk)
    actes = passage.actes.all()
    medecins = Utilisateur.objects.filter(role__in=['medecin', 'chef'])
    return render(request, 'urgences/detail.html', {
        'passage': passage, 'actes': actes, 'medecins': medecins,
        'triage_choices': TRIAGE_CHOICES,
    })


@login_required
@medecin_only
def prise_en_charge(request, pk):
    passage = get_object_or_404(PassageUrgence, pk=pk)
    if request.method == 'POST':
        passage.medecin_prise_en_charge = request.user
        passage.date_prise_en_charge = timezone.now()
        passage.diagnostic = request.POST.get('diagnostic', '')
        passage.traitement_urgence = request.POST.get('traitement_urgence', '')
        passage.observations = request.POST.get('observations', '')
        passage.statut = request.POST.get('statut', 'en_cours')
        passage.save()
        # Acte
        desc = request.POST.get('acte_desc', '')
        if desc:
            ActeUrgence.objects.create(passage=passage, description=desc, realise_par=request.user)
        messages.success(request, "Prise en charge enregistrée.")
        return redirect('detail_urgence', pk=pk)
    return render(request, 'urgences/prise_en_charge.html', {'passage': passage})


@login_required
@personnel_only
def sortie_urgence(request, pk):
    passage = get_object_or_404(PassageUrgence, pk=pk)
    if request.method == 'POST':
        passage.statut = 'sorti' if request.POST.get('motif_sortie') != 'hospitalisation' else 'hospitalise'
        passage.motif_sortie = request.POST.get('motif_sortie', 'domicile')
        passage.date_sortie = timezone.now()
        passage.save()
        messages.success(request, "Sortie des urgences enregistrée.")
        return redirect('tableau_urgences')
    return render(request, 'urgences/sortie.html', {'passage': passage})


@login_required
@personnel_only
def ajouter_acte(request, pk):
    passage = get_object_or_404(PassageUrgence, pk=pk)
    if request.method == 'POST':
        ActeUrgence.objects.create(
            passage=passage,
            description=request.POST['description'],
            realise_par=request.user,
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, "Acte enregistré.")
    return redirect('detail_urgence', pk=pk)


@login_required
@personnel_only
def historique_urgences(request):
    passages = PassageUrgence.objects.select_related(
        'patient__utilisateur'
    ).filter(statut__in=['sorti','hospitalise','dcd','parti_sans_soins'])[:100]
    return render(request, 'urgences/historique.html', {'passages': passages})
