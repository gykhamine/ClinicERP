from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Facture, LigneFacture, Paiement, ServiceClinic
from apps.patients.models import Patient
from apps.accounts.decorators import comptable_only, personnel_only

@login_required
@comptable_only
def liste_factures(request):
    statut = request.GET.get('statut','')
    factures = Facture.objects.select_related('patient__utilisateur','caissier').all()
    if statut:
        factures = factures.filter(statut=statut)
    total_emis = sum(f.total() for f in factures.filter(statut__in=['emise','partiel','payee']))
    total_paye = sum(f.total() for f in factures.filter(statut='payee'))
    return render(request, 'facturation/liste.html', {
        'factures': factures, 'statut_filtre': statut,
        'total_emis': total_emis, 'total_paye': total_paye
    })

@login_required
@comptable_only
def creer_facture(request):
    if request.method == 'POST':
        patient = get_object_or_404(Patient, pk=request.POST['patient'])
        facture = Facture.objects.create(
            patient=patient,
            statut='brouillon',
            remise_pourcent=request.POST.get('remise_pourcent',0),
            notes=request.POST.get('notes',''),
            caissier=request.user,
        )
        descriptions = request.POST.getlist('description[]')
        qtys = request.POST.getlist('quantite[]')
        prix = request.POST.getlist('prix_unitaire[]')
        for i in range(len(descriptions)):
            if descriptions[i] and prix[i]:
                LigneFacture.objects.create(
                    facture=facture,
                    description=descriptions[i],
                    quantite=float(qtys[i]) if i < len(qtys) else 1,
                    prix_unitaire=float(prix[i]),
                )
        messages.success(request, f"Facture {facture.numero} créée.")
        return redirect('detail_facture', pk=facture.pk)
    patients = Patient.objects.select_related('utilisateur').all()
    services = ServiceClinic.objects.filter(actif=True)
    return render(request, 'facturation/form.html', {'patients': patients, 'services': services})

@login_required
@personnel_only
def detail_facture(request, pk):
    facture = get_object_or_404(Facture, pk=pk)
    if request.user.role == 'patient':
        try:
            if facture.patient.utilisateur != request.user:
                return redirect('dashboard')
        except: return redirect('dashboard')
    return render(request, 'facturation/detail.html', {'facture': facture})

@login_required
@comptable_only
def enregistrer_paiement(request, pk):
    facture = get_object_or_404(Facture, pk=pk)
    if request.method == 'POST':
        montant = float(request.POST['montant'])
        Paiement.objects.create(
            facture=facture, montant=montant,
            mode=request.POST['mode'],
            reference=request.POST.get('reference',''),
            caissier=request.user,
            notes=request.POST.get('notes',''),
        )
        # Update facture status
        total_paye = sum(p.montant for p in facture.paiements.all())
        if total_paye >= facture.total():
            facture.statut = 'payee'
        else:
            facture.statut = 'partiel'
        facture.mode_paiement = request.POST['mode']
        facture.save()
        messages.success(request, f"Paiement de {montant} FCFA enregistré.")
        return redirect('detail_facture', pk=pk)
    return render(request, 'facturation/paiement.html', {'facture': facture})

@login_required
@comptable_only
def emettre_facture(request, pk):
    facture = get_object_or_404(Facture, pk=pk)
    facture.statut = 'emise'
    facture.save()
    messages.success(request, "Facture émise.")
    return redirect('detail_facture', pk=pk)

@login_required
@comptable_only
def liste_services(request):
    services = ServiceClinic.objects.all()
    if request.method == 'POST':
        ServiceClinic.objects.create(
            nom=request.POST['nom'], code=request.POST['code'],
            prix=request.POST['prix'], description=request.POST.get('description','')
        )
        messages.success(request, "Service ajouté.")
    return render(request, 'facturation/services.html', {'services': services})
