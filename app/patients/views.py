from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Patient, DossierMedical
from apps.accounts.models import Utilisateur
from apps.accounts.decorators import personnel_only, chef_only, medecin_only
from .forms import PatientForm, DossierMedicalForm

@login_required
@personnel_only
def liste_patients(request):
    q = request.GET.get('q', '')
    patients = Patient.objects.select_related('utilisateur', 'medecin_traitant').all()
    if q:
        patients = patients.filter(
            Q(utilisateur__first_name__icontains=q) |
            Q(utilisateur__last_name__icontains=q) |
            Q(numero_dossier__icontains=q) |
            Q(utilisateur__telephone__icontains=q)
        )
    return render(request, 'patients/liste.html', {'patients': patients, 'q': q})

@login_required
def detail_patient(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    # Patient can only see own profile
    if request.user.role == 'patient':
        try:
            if request.user.profil_patient.pk != pk:
                messages.error(request, "Accès refusé.")
                return redirect('dashboard')
        except: 
            return redirect('dashboard')
    from apps.consultations.models import Consultation, RendezVous
    from apps.facturation.models import Facture
    from apps.laboratoire.models import DemandeAnalyse
    ctx = {
        'patient': patient,
        'consultations': Consultation.objects.filter(patient=patient)[:10],
        'rendez_vous': RendezVous.objects.filter(patient=patient)[:10],
        'factures': Facture.objects.filter(patient=patient)[:10],
        'analyses': DemandeAnalyse.objects.filter(patient=patient)[:10],
        'dossiers': DossierMedical.objects.filter(patient=patient),
    }
    return render(request, 'patients/detail.html', ctx)

@login_required
@personnel_only
def creer_patient(request):
    form = PatientForm()
    if request.method == 'POST':
        form = PatientForm(request.POST, request.FILES)
        if form.is_valid():
            # Create user account
            u = Utilisateur.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                telephone=form.cleaned_data['telephone'],
                role='patient'
            )
            p = Patient(
                utilisateur=u,
                groupe_sanguin=form.cleaned_data.get('groupe_sanguin',''),
                allergies=form.cleaned_data.get('allergies',''),
                antecedents=form.cleaned_data.get('antecedents',''),
                medecin_traitant=form.cleaned_data.get('medecin_traitant'),
                assurance=form.cleaned_data.get('assurance',''),
                contact_urgence_nom=form.cleaned_data.get('contact_urgence_nom',''),
                contact_urgence_tel=form.cleaned_data.get('contact_urgence_tel',''),
            )
            p.save()
            messages.success(request, f"Patient {u.get_full_name()} enregistré. Dossier: {p.numero_dossier}")
            return redirect('detail_patient', pk=p.pk)
    return render(request, 'patients/form.html', {'form': form, 'titre': 'Nouveau patient'})

@login_required
@personnel_only
def modifier_patient(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        u = patient.utilisateur
        u.first_name = request.POST.get('first_name', u.first_name)
        u.last_name = request.POST.get('last_name', u.last_name)
        u.email = request.POST.get('email', u.email)
        u.telephone = request.POST.get('telephone', u.telephone)
        u.save()
        patient.groupe_sanguin = request.POST.get('groupe_sanguin', patient.groupe_sanguin)
        patient.allergies = request.POST.get('allergies', patient.allergies)
        patient.antecedents = request.POST.get('antecedents', patient.antecedents)
        patient.assurance = request.POST.get('assurance', patient.assurance)
        patient.contact_urgence_nom = request.POST.get('contact_urgence_nom', patient.contact_urgence_nom)
        patient.contact_urgence_tel = request.POST.get('contact_urgence_tel', patient.contact_urgence_tel)
        medecin_id = request.POST.get('medecin_traitant')
        if medecin_id:
            patient.medecin_traitant = Utilisateur.objects.filter(pk=medecin_id).first()
        patient.save()
        messages.success(request, "Dossier patient mis à jour.")
        return redirect('detail_patient', pk=pk)
    medecins = Utilisateur.objects.filter(role__in=['medecin','chef'])
    return render(request, 'patients/modifier.html', {
        'patient': patient,
        'medecins': medecins,
        'choices': Patient.GROUPE_SANGUIN,
    })


@login_required
@medecin_only
def ajouter_dossier(request, patient_pk):
    patient = get_object_or_404(Patient, pk=patient_pk)
    if request.method == 'POST':
        DossierMedical.objects.create(
            patient=patient,
            titre=request.POST['titre'],
            contenu=request.POST['contenu'],
            medecin=request.user,
            confidentiel=request.POST.get('confidentiel') == 'on',
        )
        messages.success(request, "Document ajouté au dossier.")
        return redirect('detail_patient', pk=patient_pk)
    return render(request, 'patients/dossier_form.html', {'patient': patient})
