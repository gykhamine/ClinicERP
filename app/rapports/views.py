from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from apps.accounts.decorators import chef_only, personnel_only
import json

@login_required
@chef_only
def tableau_de_bord_stats(request):
    from apps.patients.models import Patient
    from apps.consultations.models import Consultation, RendezVous
    from apps.facturation.models import Facture, Paiement
    from apps.pharmacie.models import Medicament
    from django.utils import timezone
    from datetime import timedelta
    import pandas as pd

    today = timezone.now().date()
    last_30 = today - timedelta(days=30)

    # Consultations par jour (30 derniers jours)
    cons = Consultation.objects.filter(date__date__gte=last_30)
    cons_data = {}
    for c in cons:
        d = str(c.date.date())
        cons_data[d] = cons_data.get(d, 0) + 1

    # Recettes par jour
    paie = Paiement.objects.filter(date__date__gte=last_30)
    paie_data = {}
    for p in paie:
        d = str(p.date.date())
        paie_data[d] = paie_data.get(d, 0) + float(p.montant)

    # Stats générales
    stats = {
        'nb_patients': Patient.objects.count(),
        'nb_consultations_mois': cons.count(),
        'recettes_mois': sum(paie_data.values()),
        'nb_factures_impayees': Facture.objects.filter(statut__in=['emise','partiel']).count(),
        'nb_medicaments_alerte': sum(1 for m in Medicament.objects.filter(actif=True) if m.en_rupture()),
        'rdv_aujourd_hui': RendezVous.objects.filter(date_heure__date=today).count(),
    }

    # Distribution des rôles patients vs personnel
    from apps.accounts.models import Utilisateur
    roles_count = {}
    for u in Utilisateur.objects.all():
        roles_count[u.get_role_display()] = roles_count.get(u.get_role_display(), 0) + 1

    # Top médecins par nb consultations
    top_medecins = []
    for u in Utilisateur.objects.filter(role__in=['medecin','chef']):
        nb = Consultation.objects.filter(medecin=u, date__date__gte=last_30).count()
        if nb > 0:
            top_medecins.append({'nom': u.get_full_name(), 'nb': nb})
    top_medecins.sort(key=lambda x: x['nb'], reverse=True)

    ctx = {
        'stats': stats,
        'cons_data': json.dumps(cons_data),
        'paie_data': json.dumps(paie_data),
        'roles_count': json.dumps(roles_count),
        'top_medecins': json.dumps(top_medecins[:5]),
    }
    return render(request, 'rapports/dashboard_stats.html', ctx)

@login_required
@chef_only
def rapport_financier(request):
    from apps.facturation.models import Facture, Paiement
    from django.utils import timezone
    from datetime import timedelta

    periode = request.GET.get('periode', '30')
    jours = int(periode)
    debut = timezone.now().date() - timedelta(days=jours)

    factures = Facture.objects.filter(date_emission__date__gte=debut)
    paiements = Paiement.objects.filter(date__date__gte=debut)

    total_facture = sum(f.total() for f in factures)
    total_paye = sum(p.montant for p in paiements)
    total_impaye = total_facture - total_paye

    par_mode = {}
    for p in paiements:
        par_mode[p.mode] = float(par_mode.get(p.mode, 0)) + float(p.montant)

    ctx = {
        'total_facture': total_facture,
        'total_paye': total_paye,
        'total_impaye': total_impaye,
        'par_mode': json.dumps(par_mode),
        'factures': factures[:50],
        'periode': periode,
    }
    return render(request, 'rapports/financier.html', ctx)

@login_required
@chef_only
def rapport_activite(request):
    from apps.consultations.models import Consultation
    from apps.patients.models import Patient
    from django.utils import timezone
    from datetime import timedelta
    from apps.accounts.models import Utilisateur

    mois = {}
    for i in range(6):
        debut = timezone.now().date().replace(day=1) - timedelta(days=30*i)
        nb = Consultation.objects.filter(date__year=debut.year, date__month=debut.month).count()
        mois[debut.strftime('%b %Y')] = nb

    medecins_stats = []
    for m in Utilisateur.objects.filter(role__in=['medecin','chef']):
        nb = Consultation.objects.filter(medecin=m).count()
        medecins_stats.append({'nom': m.get_full_name(), 'consultations': nb})

    ctx = {
        'mois_data': json.dumps(dict(reversed(list(mois.items())))),
        'medecins_stats': medecins_stats,
        'nb_patients_total': Patient.objects.count(),
        'nb_consultations_total': Consultation.objects.count(),
    }
    return render(request, 'rapports/activite.html', ctx)

@login_required
@chef_only
def exporter_pdf(request, type_rapport):
    from io import BytesIO
    import PyPDF2
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    # Header
    c.setFillColorRGB(0.09, 0.47, 0.63)
    c.rect(0, h-80, w, 80, fill=1, stroke=0)
    c.setFillColorRGB(1,1,1)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, h-45, "ClinicERP – Rapport")
    c.setFont("Helvetica", 12)
    from datetime import date
    c.drawString(40, h-65, f"Généré le {date.today().strftime('%d/%m/%Y')}")

    c.setFillColorRGB(0,0,0)
    c.setFont("Helvetica-Bold", 14)
    titres = {'financier': 'Rapport Financier', 'activite': "Rapport d'Activité", 'patients': 'Rapport Patients'}
    c.drawString(40, h-120, titres.get(type_rapport, 'Rapport'))

    y = h - 160
    c.setFont("Helvetica", 11)

    if type_rapport == 'financier':
        from apps.facturation.models import Facture, Paiement
        factures = Facture.objects.all()[:20]
        c.drawString(40, y, f"Total factures : {len(factures)}")
        y -= 20
        for f in factures:
            if y < 80:
                c.showPage()
                y = h - 60
            c.drawString(50, y, f"  {f.numero} | {f.patient} | {f.total():,.0f} FCFA | {f.get_statut_display()}")
            y -= 18
    elif type_rapport == 'activite':
        from apps.consultations.models import Consultation
        cons = Consultation.objects.all()[:30]
        c.drawString(40, y, f"Total consultations : {Consultation.objects.count()}")
        y -= 20
        for con in cons:
            if y < 80:
                c.showPage()
                y = h - 60
            c.drawString(50, y, f"  {con.date.strftime('%d/%m/%Y')} | {con.patient} | Dr.{con.medecin.last_name}")
            y -= 18

    c.save()
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_{type_rapport}.pdf"'
    return response
