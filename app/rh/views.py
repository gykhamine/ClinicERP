from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import FichePersonnel, Departement, Conge, PlanningTravail
from apps.accounts.models import Utilisateur
from apps.accounts.decorators import chef_only, personnel_only

@login_required
@chef_only
def liste_personnel(request):
    fiches = FichePersonnel.objects.select_related('utilisateur','departement').filter(actif=True)
    return render(request, 'rh/liste.html', {'fiches': fiches})

@login_required
@chef_only
def creer_fiche(request):
    if request.method == 'POST':
        u = get_object_or_404(Utilisateur, pk=request.POST['utilisateur'])
        dept, _ = Departement.objects.get_or_create(nom=request.POST.get('departement','Général'))
        FichePersonnel.objects.create(
            utilisateur=u, departement=dept,
            poste=request.POST['poste'],
            type_contrat=request.POST['type_contrat'],
            date_embauche=request.POST['date_embauche'],
            salaire_base=request.POST.get('salaire_base',0),
            diplome=request.POST.get('diplome',''),
            specialisation=request.POST.get('specialisation',''),
            numero_ordre=request.POST.get('numero_ordre',''),
        )
        messages.success(request, f"Fiche RH créée pour {u.get_full_name()}.")
        return redirect('liste_personnel')
    users_sans_fiche = Utilisateur.objects.filter(role__in=['medecin','infirmier','pharmacien','laborantin','receptionniste','comptable','chef']).exclude(fiche_personnel__isnull=False)
    departements = Departement.objects.all()
    return render(request, 'rh/form_fiche.html', {'utilisateurs': users_sans_fiche, 'departements': departements})

@login_required
@personnel_only
def demander_conge(request):
    try:
        fiche = request.user.fiche_personnel
    except:
        messages.error(request, "Aucune fiche personnel trouvée.")
        return redirect('dashboard')
    if request.method == 'POST':
        Conge.objects.create(
            personnel=fiche,
            type_conge=request.POST['type_conge'],
            date_debut=request.POST['date_debut'],
            date_fin=request.POST['date_fin'],
            motif=request.POST['motif'],
        )
        messages.success(request, "Demande de congé soumise.")
        return redirect('mes_conges')
    return render(request, 'rh/form_conge.html')

@login_required
@personnel_only
def mes_conges(request):
    try:
        conges = request.user.fiche_personnel.conges.all()
    except:
        conges = []
    return render(request, 'rh/mes_conges.html', {'conges': conges})

@login_required
@chef_only
def gerer_conges(request):
    conges = Conge.objects.select_related('personnel__utilisateur').filter(statut='demande')
    if request.method == 'POST':
        conge = get_object_or_404(Conge, pk=request.POST['conge_id'])
        conge.statut = request.POST['decision']
        conge.approuve_par = request.user
        conge.save()
        messages.success(request, f"Congé {conge.get_statut_display()}.")
        return redirect('gerer_conges')
    return render(request, 'rh/gerer_conges.html', {'conges': conges})

@login_required
@chef_only
def planning(request):
    fiches = FichePersonnel.objects.filter(actif=True).select_related('utilisateur')
    return render(request, 'rh/planning.html', {'fiches': fiches})
