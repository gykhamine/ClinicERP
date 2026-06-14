from django.db import models
from apps.accounts.models import Utilisateur

class Departement(models.Model):
    nom = models.CharField(max_length=100)
    chef = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='departements_diriges')
    description = models.TextField(blank=True)
    def __str__(self): return self.nom

class FichePersonnel(models.Model):
    TYPE_CONTRAT = [('cdi','CDI'),('cdd','CDD'),('stage','Stage'),('consultant','Consultant'),('benevole','Bénévole')]
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, related_name='fiche_personnel')
    matricule = models.CharField(max_length=20, unique=True)
    departement = models.ForeignKey(Departement, on_delete=models.SET_NULL, null=True)
    poste = models.CharField(max_length=100)
    type_contrat = models.CharField(max_length=15, choices=TYPE_CONTRAT)
    date_embauche = models.DateField()
    salaire_base = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    diplome = models.CharField(max_length=200, blank=True)
    specialisation = models.CharField(max_length=200, blank=True)
    numero_ordre = models.CharField(max_length=50, blank=True, verbose_name="N° Ordre professionnel")
    actif = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.matricule:
            import random
            self.matricule = f"EMP{random.randint(1000,9999)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.utilisateur.get_full_name()} - {self.poste}"

class Conge(models.Model):
    STATUT = [('demande','Demandé'),('approuve','Approuvé'),('refuse','Refusé')]
    TYPE = [('annuel','Congé annuel'),('maladie','Congé maladie'),('maternite','Maternité'),('paternite','Paternité'),('autre','Autre')]
    personnel = models.ForeignKey(FichePersonnel, on_delete=models.CASCADE, related_name='conges')
    type_conge = models.CharField(max_length=15, choices=TYPE)
    date_debut = models.DateField()
    date_fin = models.DateField()
    motif = models.TextField()
    statut = models.CharField(max_length=10, choices=STATUT, default='demande')
    approuve_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def duree_jours(self):
        return (self.date_fin - self.date_debut).days + 1

class PlanningTravail(models.Model):
    JOUR = [(i, j) for i, j in enumerate(['Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche'])]
    personnel = models.ForeignKey(FichePersonnel, on_delete=models.CASCADE, related_name='plannings')
    jour_semaine = models.IntegerField(choices=JOUR)
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    semaine_type = models.CharField(max_length=20, default='normale')
