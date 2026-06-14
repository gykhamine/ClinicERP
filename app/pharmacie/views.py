from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Medicament, CategorieMedicament, MouvementStock, DispensationMedicament
from apps.accounts.decorators import pharmacien_only, personnel_only

@login_required
@personnel_only
def liste_medicaments(request):
    q = request.GET.get('q','')
    alerte = request.GET.get('alerte','')
    meds = Medicament.objects.filter(actif=True).select_related('categorie')
    if q:
        meds = meds.filter(Q(nom__icontains=q)|Q(nom_generique__icontains=q))
    if alerte:
        meds = [m for m in meds if m.en_rupture()]
    categories = CategorieMedicament.objects.all()
    return render(request, 'pharmacie/liste.html', {'medicaments': meds, 'q': q, 'categories': categories, 'alerte': alerte})

@login_required
@pharmacien_only
def creer_medicament(request):
    if request.method == 'POST':
        cat, _ = CategorieMedicament.objects.get_or_create(nom=request.POST.get('categorie_nom','Général'))
        Medicament.objects.create(
            nom=request.POST['nom'],
            nom_generique=request.POST.get('nom_generique',''),
            categorie=cat,
            forme=request.POST['forme'],
            dosage=request.POST['dosage'],
            stock=int(request.POST.get('stock',0)),
            stock_minimum=int(request.POST.get('stock_minimum',10)),
            prix_achat=request.POST.get('prix_achat',0),
            prix_vente=request.POST.get('prix_vente',0),
            date_expiration=request.POST.get('date_expiration') or None,
            fournisseur=request.POST.get('fournisseur',''),
        )
        messages.success(request, "Médicament ajouté au stock.")
        return redirect('liste_medicaments')
    categories = CategorieMedicament.objects.all()
    return render(request, 'pharmacie/form_medicament.html', {'categories': categories})

@login_required
@pharmacien_only
def mouvement_stock(request, pk):
    med = get_object_or_404(Medicament, pk=pk)
    if request.method == 'POST':
        MouvementStock.objects.create(
            medicament=med,
            type_mouvement=request.POST['type_mouvement'],
            quantite=int(request.POST['quantite']),
            motif=request.POST['motif'],
            utilisateur=request.user,
        )
        messages.success(request, f"Mouvement de stock enregistré. Nouveau stock : {med.stock}")
        return redirect('liste_medicaments')
    return render(request, 'pharmacie/mouvement.html', {'medicament': med})

@login_required
@pharmacien_only
def dispenser_ordonnance(request, ordonnance_pk):
    from apps.consultations.models import Ordonnance
    ordo = get_object_or_404(Ordonnance, pk=ordonnance_pk)
    if request.method == 'POST':
        total = 0
        for ligne in ordo.lignes.all():
            med = Medicament.objects.filter(nom__icontains=ligne.medicament.split()[0], actif=True).first()
            if med and med.stock >= ligne.quantite:
                MouvementStock.objects.create(
                    medicament=med, type_mouvement='sortie',
                    quantite=ligne.quantite, motif=f"Ordonnance #{ordo.pk}",
                    utilisateur=request.user,
                )
                total += float(med.prix_vente) * ligne.quantite
        DispensationMedicament.objects.create(
            ordonnance=ordo, pharmacien=request.user, montant_total=total
        )
        ordo.dispensee = True
        import django.utils.timezone as tz
        ordo.date_dispense = tz.now()
        ordo.save()
        messages.success(request, "Ordonnance dispensée avec succès.")
        return redirect('liste_medicaments')
    return render(request, 'pharmacie/dispenser.html', {'ordonnance': ordo})

@login_required
@personnel_only
def historique_mouvements(request):
    mouvements = MouvementStock.objects.select_related('medicament','utilisateur').all()[:100]
    return render(request, 'pharmacie/historique.html', {'mouvements': mouvements})
