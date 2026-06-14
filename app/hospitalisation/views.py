from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Service, Chambre, Lit, Hospitalisation, SuiviQuotidien, Batiment, TransfertService
from apps.patients.models import Patient
from apps.accounts.models import Utilisateur
from apps.accounts.decorators import personnel_only, medecin_only, chef_only


@login_required
@personnel_only
def carte_lits(request):
    """Vue carte de l'occupation des lits en temps réel"""
    services = Service.objects.filter(actif=True).prefetch_related('chambres__lits')
    total_lits = Lit.objects.exclude(statut='hors_service').count()
    lits_libres = Lit.objects.filter(statut='libre').count()
    lits_occupes = Lit.objects.filter(statut='occupe').count()
    taux = round(lits_occupes / total_lits * 100) if total_lits else 0
    ctx = {
        'services': services,
        'total_lits': total_lits,
        'lits_libres': lits_libres,
        'lits_occupes': lits_occupes,
        'taux_occupation': taux,
    }
    return render(request, 'hospitalisation/carte_lits.html', ctx)


@login_required
@personnel_only
def liste_hospitalisations(request):
    statut = request.GET.get('statut', 'en_cours')
    service_id = request.GET.get('service', '')
    hosps = Hospitalisation.objects.select_related(
        'patient__utilisateur', 'lit__chambre__service', 'medecin_responsable', 'service'
    )
    if statut:
        hosps = hosps.filter(statut=statut)
    if service_id:
        hosps = hosps.filter(service_id=service_id)
    services = Service.objects.filter(actif=True)
    return render(request, 'hospitalisation/liste.html', {
        'hospitalisations': hosps,
        'statut_filtre': statut,
        'services': services,
        'service_filtre': service_id,
    })


@login_required
@personnel_only
def detail_hospitalisation(request, pk):
    hosp = get_object_or_404(Hospitalisation, pk=pk)
    suivis = hosp.suivis.all()
    transferts = hosp.transferts.all()
    return render(request, 'hospitalisation/detail.html', {
        'hosp': hosp,
        'suivis': suivis,
        'transferts': transferts,
    })


@login_required
@personnel_only
def admettre_patient(request):
    if request.method == 'POST':
        patient = get_object_or_404(Patient, pk=request.POST['patient'])
        lit = get_object_or_404(Lit, pk=request.POST['lit'])
        if lit.statut != 'libre':
            messages.error(request, "Ce lit n'est pas disponible.")
            return redirect('admettre_patient')
        medecin = get_object_or_404(Utilisateur, pk=request.POST['medecin'])
        hosp = Hospitalisation.objects.create(
            patient=patient,
            lit=lit,
            service=lit.chambre.service,
            medecin_responsable=medecin,
            mode_entree=request.POST.get('mode_entree', 'programmee'),
            date_entree=request.POST['date_entree'],
            date_sortie_prevue=request.POST.get('date_sortie_prevue') or None,
            motif_hospitalisation=request.POST['motif_hospitalisation'],
            diagnostic_entree=request.POST.get('diagnostic_entree', ''),
            created_by=request.user,
        )
        # Marquer le lit comme occupé
        lit.statut = 'occupe'
        lit.save()
        # Notification
        from apps.notifications.models import Notification
        Notification.objects.create(
            destinataire=medecin,
            expediteur=request.user,
            titre=f"Admission — {patient}",
            message=f"{patient} admis en {lit.chambre.service} lit {lit.numero}",
            type_notif='info',
        )
        messages.success(request, f"Patient {patient} admis — {lit}")
        return redirect('detail_hospitalisation', pk=hosp.pk)

    patients = Patient.objects.select_related('utilisateur').all()
    lits_libres = Lit.objects.filter(statut='libre').select_related('chambre__service')
    medecins = Utilisateur.objects.filter(role__in=['medecin', 'chef'])
    services = Service.objects.filter(actif=True)
    return render(request, 'hospitalisation/admettre.html', {
        'patients': patients,
        'lits_libres': lits_libres,
        'medecins': medecins,
        'services': services,
    })


@login_required
@medecin_only
def ajouter_suivi(request, pk):
    hosp = get_object_or_404(Hospitalisation, pk=pk)
    if request.method == 'POST':
        SuiviQuotidien.objects.create(
            hospitalisation=hosp,
            medecin=request.user,
            tension=request.POST.get('tension', ''),
            temperature=request.POST.get('temperature') or None,
            poids=request.POST.get('poids') or None,
            frequence_cardiaque=request.POST.get('frequence_cardiaque') or None,
            saturation_o2=request.POST.get('saturation_o2') or None,
            evolution=request.POST['evolution'],
            traitement_en_cours=request.POST.get('traitement_en_cours', ''),
            observations=request.POST.get('observations', ''),
            prescriptions_nouvelles=request.POST.get('prescriptions_nouvelles', ''),
        )
        messages.success(request, "Suivi enregistré.")
        return redirect('detail_hospitalisation', pk=pk)
    return render(request, 'hospitalisation/form_suivi.html', {'hosp': hosp})


@login_required
@medecin_only
def sortie_patient(request, pk):
    hosp = get_object_or_404(Hospitalisation, pk=pk)
    if request.method == 'POST':
        hosp.statut = request.POST.get('statut', 'sorti')
        hosp.date_sortie_reelle = timezone.now()
        hosp.diagnostic_sortie = request.POST.get('diagnostic_sortie', '')
        hosp.compte_rendu_sortie = request.POST.get('compte_rendu_sortie', '')
        hosp.save()
        # Libérer le lit
        lit = hosp.lit
        lit.statut = 'nettoyage'
        lit.save()
        messages.success(request, f"Sortie enregistrée. Lit {lit.numero} mis en nettoyage.")
        return redirect('liste_hospitalisations')
    return render(request, 'hospitalisation/sortie.html', {'hosp': hosp})


@login_required
@medecin_only
def transfert_service(request, pk):
    hosp = get_object_or_404(Hospitalisation, pk=pk)
    if request.method == 'POST':
        lit_dest = get_object_or_404(Lit, pk=request.POST['lit_destination'])
        if lit_dest.statut != 'libre':
            messages.error(request, "Le lit de destination n'est pas libre.")
            return redirect('detail_hospitalisation', pk=pk)
        TransfertService.objects.create(
            hospitalisation=hosp,
            service_origine=hosp.service,
            lit_origine=hosp.lit,
            service_destination=lit_dest.chambre.service,
            lit_destination=lit_dest,
            motif=request.POST['motif'],
            medecin=request.user,
        )
        # Libérer ancien lit, occuper nouveau
        hosp.lit.statut = 'nettoyage'
        hosp.lit.save()
        hosp.lit = lit_dest
        hosp.service = lit_dest.chambre.service
        hosp.statut = 'en_cours'
        hosp.save()
        lit_dest.statut = 'occupe'
        lit_dest.save()
        messages.success(request, f"Patient transféré vers {lit_dest.chambre.service}.")
        return redirect('detail_hospitalisation', pk=pk)
    lits_libres = Lit.objects.filter(statut='libre').select_related('chambre__service')
    return render(request, 'hospitalisation/transfert.html', {'hosp': hosp, 'lits_libres': lits_libres})


@login_required
@chef_only
def gestion_structure(request):
    """Gestion bâtiments / services / chambres / lits"""
    batiments = Batiment.objects.all()
    services = Service.objects.select_related('batiment').all()
    return render(request, 'hospitalisation/structure.html', {
        'batiments': batiments, 'services': services
    })


@login_required
@chef_only
def creer_service(request):
    if request.method == 'POST':
        bat, _ = Batiment.objects.get_or_create(nom=request.POST.get('batiment', 'Principal'))
        Service.objects.create(
            nom=request.POST['nom'], code=request.POST['code'],
            batiment=bat, capacite=request.POST.get('capacite', 10),
            description=request.POST.get('description', ''),
        )
        messages.success(request, "Service créé.")
        return redirect('gestion_structure')
    batiments = Batiment.objects.all()
    return render(request, 'hospitalisation/form_service.html', {'batiments': batiments})


@login_required
@chef_only
def creer_lits(request, service_pk):
    """Créer chambres et lits pour un service"""
    service = get_object_or_404(Service, pk=service_pk)
    if request.method == 'POST':
        num_chambre = request.POST['num_chambre']
        type_ch = request.POST.get('type_chambre', 'standard')
        etage = int(request.POST.get('etage', 1))
        nb_lits = int(request.POST.get('nb_lits', 2))
        chambre, _ = Chambre.objects.get_or_create(
            service=service, numero=num_chambre,
            defaults={'type_chambre': type_ch, 'etage': etage}
        )
        for i in range(1, nb_lits + 1):
            Lit.objects.get_or_create(chambre=chambre, numero=str(i))
        messages.success(request, f"Chambre {num_chambre} avec {nb_lits} lit(s) créée.")
        return redirect('gestion_structure')
    return render(request, 'hospitalisation/form_lits.html', {'service': service})
