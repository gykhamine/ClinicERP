from django.db import models
from apps.patients.models import Patient
from apps.accounts.models import Utilisateur

class TypeAnalyse(models.Model):
    nom = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delai_heures = models.IntegerField(default=24)
    valeurs_normales = models.TextField(blank=True)
    def __str__(self): return f"{self.code} - {self.nom}"

class DemandeAnalyse(models.Model):
    STATUT = [('demande','Demandée'),('en_cours','En cours'),('termine','Terminée'),('annule','Annulée')]
    PRIORITE = [('normale','Normale'),('urgente','Urgente'),('tres_urgente','Très urgente')]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='analyses')
    medecin_prescripteur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='analyses_prescrites')
    laborantin = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='analyses_traitees')
    types_analyses = models.ManyToManyField(TypeAnalyse)
    date_demande = models.DateTimeField(auto_now_add=True)
    date_realisation = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=15, choices=STATUT, default='demande')
    priorite = models.CharField(max_length=15, choices=PRIORITE, default='normale')
    notes_cliniques = models.TextField(blank=True)
    consultation = models.ForeignKey('consultations.Consultation', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-date_demande']

class ResultatAnalyse(models.Model):
    demande = models.ForeignKey(DemandeAnalyse, on_delete=models.CASCADE, related_name='resultats')
    type_analyse = models.ForeignKey(TypeAnalyse, on_delete=models.CASCADE)
    valeur = models.TextField()
    unite = models.CharField(max_length=50, blank=True)
    interpretation = models.TextField(blank=True)
    anormal = models.BooleanField(default=False)
    laborantin = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(auto_now_add=True)
    fichier_pdf = models.FileField(upload_to='analyses/', blank=True, null=True)

    def __str__(self):
        return f"Résultat {self.type_analyse} - {self.demande.patient}"
