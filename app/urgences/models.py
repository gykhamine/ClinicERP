from django.db import models
from apps.accounts.models import Utilisateur
from apps.patients.models import Patient


TRIAGE_CHOICES = [
    (1, 'P1 — Rouge / Immédiat'),
    (2, 'P2 — Orange / Très urgent'),
    (3, 'P3 — Jaune / Urgent'),
    (4, 'P4 — Vert / Peu urgent'),
    (5, 'P5 — Blanc / Non urgent'),
]

TRIAGE_COLORS = {1:'#c62828', 2:'#e65100', 3:'#f9a825', 4:'#2e7d32', 5:'#546e7a'}


class PassageUrgence(models.Model):
    STATUT = [
        ('attente_triage','En attente triage'),
        ('triage_fait','Trié — attente prise en charge'),
        ('en_cours','Prise en charge en cours'),
        ('observation','En observation'),
        ('hospitalise','Hospitalisé'),
        ('sorti','Sorti'),
        ('dcd','Décédé'),
        ('parti_sans_soins','Parti sans soins'),
    ]
    MOTIF_SORTIE = [('domicile','Retour domicile'),('hospitalisation','Hospitalisation'),('transfert','Transfert établissement'),('dcd','Décès'),('pss','Parti sans soins')]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='passages_urgence')
    date_arrivee = models.DateTimeField(auto_now_add=True)
    date_triage = models.DateTimeField(null=True, blank=True)
    date_prise_en_charge = models.DateTimeField(null=True, blank=True)
    date_sortie = models.DateTimeField(null=True, blank=True)
    motif_venue = models.TextField()
    niveau_triage = models.IntegerField(choices=TRIAGE_CHOICES, null=True, blank=True)
    infirmier_triage = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='triages_effectues')
    medecin_prise_en_charge = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='urgences_prises_en_charge')
    statut = models.CharField(max_length=25, choices=STATUT, default='attente_triage')
    motif_sortie = models.CharField(max_length=20, choices=MOTIF_SORTIE, blank=True)
    # Constantes à l'arrivée
    tension = models.CharField(max_length=20, blank=True)
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    frequence_cardiaque = models.IntegerField(null=True, blank=True)
    saturation_o2 = models.IntegerField(null=True, blank=True)
    frequence_respiratoire = models.IntegerField(null=True, blank=True)
    glasgow = models.IntegerField(null=True, blank=True, help_text="Score de Glasgow 3-15")
    # Résumé clinique
    symptomes = models.TextField(blank=True)
    diagnostic = models.TextField(blank=True)
    traitement_urgence = models.TextField(blank=True)
    observations = models.TextField(blank=True)
    created_by = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='passages_crees')

    def get_triage_color(self):
        return TRIAGE_COLORS.get(self.niveau_triage, '#546e7a')

    def duree_attente_minutes(self):
        if self.date_prise_en_charge and self.date_arrivee:
            return int((self.date_prise_en_charge - self.date_arrivee).total_seconds() / 60)
        return None

    def duree_totale_minutes(self):
        from django.utils import timezone
        fin = self.date_sortie or timezone.now()
        return int((fin - self.date_arrivee).total_seconds() / 60)

    def __str__(self):
        return f"URG-{self.pk} {self.patient} ({self.get_statut_display()})"

    class Meta:
        ordering = ['niveau_triage', 'date_arrivee']


class ActeUrgence(models.Model):
    passage = models.ForeignKey(PassageUrgence, on_delete=models.CASCADE, related_name='actes')
    description = models.CharField(max_length=300)
    heure = models.DateTimeField(auto_now_add=True)
    realise_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['heure']
