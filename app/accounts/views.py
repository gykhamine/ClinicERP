from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Utilisateur
from .decorators import chef_only, personnel_only
from .forms import LoginForm, UtilisateurForm

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user and user.actif:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Identifiants invalides ou compte désactivé.')
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    from apps.patients.models import Patient
    from apps.consultations.models import RendezVous, Consultation
    from apps.pharmacie.models import Medicament
    from apps.facturation.models import Facture
    from apps.notifications.models import Notification
    from django.utils import timezone
    from datetime import date

    ctx = {'user': request.user}
    today = date.today()

    if request.user.role == 'patient':
        try:
            patient = request.user.profil_patient
            ctx['rendez_vous'] = RendezVous.objects.filter(patient=patient, statut__in=['attente', 'confirme'])[:5]
            ctx['consultations'] = Consultation.objects.filter(patient=patient)[:5]
            ctx['factures'] = Facture.objects.filter(patient=patient, statut__in=['emise', 'partiel'])[:5]
        except:
            pass
    else:
        ctx['nb_patients'] = Patient.objects.count()
        ctx['rdv_aujourd_hui'] = RendezVous.objects.filter(
            date_heure__date=today,
            statut__in=['attente', 'confirme']
        ).count()

        ctx['consultations_du_jour'] = Consultation.objects.filter(
            date__date=today
        ).count()

        ctx['medicaments_alerte'] = Medicament.objects.filter(
            actif=True
        ).count()

        if request.user.role in ['medecin', 'chef']:
            ctx['mes_rdv'] = RendezVous.objects.filter(
                medecin=request.user,
                date_heure__date=today,
                statut__in=['attente', 'confirme']
            )[:8]

            ctx['mes_consultations'] = Consultation.objects.filter(
                medecin=request.user
            )[:5]

        if request.user.role in ['pharmacien', 'chef']:
            ctx['ruptures'] = Medicament.objects.filter(
                actif=True,
                stock__lte=10
            )[:5]

        if request.user.role in ['comptable', 'chef', 'receptionniste']:
            ctx['factures_impayees'] = Facture.objects.filter(
                statut__in=['emise', 'partiel']
            )[:5]

    # Stats hôpital pour le personnel
    if request.user.role != 'patient':
        try:
            from apps.urgences.models import PassageUrgence
            from apps.hospitalisation.models import Hospitalisation, Lit
            from apps.bloc_operatoire.models import ProgrammeOperatoire

            ctx['urgences_actives'] = PassageUrgence.objects.filter(
                statut__in=['attente_triage', 'triage_fait', 'en_cours']
            ).count()

            ctx['lits_occupes'] = Lit.objects.filter(
                statut='occupe'
            ).count()

            ctx['lits_libres'] = Lit.objects.filter(
                statut='libre'
            ).count()

            ctx['ops_aujourd_hui'] = ProgrammeOperatoire.objects.filter(
                date_heure_prevue__date=today,
                statut__in=['programme', 'confirme', 'en_cours']
            ).count()

        except:
            pass

    ctx['notifications'] = Notification.objects.filter(
        destinataire=request.user,
        lue=False
    )[:5]

    return render(request, 'accounts/dashboard.html', ctx)
    
@login_required
@chef_only
def liste_utilisateurs(request):
    q = request.GET.get('q', '')
    role = request.GET.get('role', '')
    users = Utilisateur.objects.all()
    if q:
        users = users.filter(Q(first_name__icontains=q)|Q(last_name__icontains=q)|Q(username__icontains=q))
    if role:
        users = users.filter(role=role)
    return render(request, 'accounts/utilisateurs.html', {'utilisateurs': users, 'q': q, 'role_filtre': role})

@login_required
@chef_only
def creer_utilisateur(request):
    form = UtilisateurForm()
    if request.method == 'POST':
        form = UtilisateurForm(request.POST, request.FILES)
        if form.is_valid():
            u = form.save(commit=False)
            u.set_password(form.cleaned_data['password1'])
            u.save()
            messages.success(request, f"Utilisateur {u.get_full_name()} créé avec succès.")
            return redirect('liste_utilisateurs')
    return render(request, 'accounts/form_utilisateur.html', {'form': form, 'titre': 'Créer un utilisateur'})

@login_required
def mon_profil(request):
    return render(request, 'accounts/profil.html', {'u': request.user})
