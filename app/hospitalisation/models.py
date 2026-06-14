from django.db import models
from apps.accounts.models import Utilisateur
from apps.patients.models import Patient


class Batiment(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)

    def __str__(self):
        return self.nom


class Service(models.Model):
    nom = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    batiment = models.ForeignKey(Batiment, on_delete=models.SET_NULL, null=True, blank=True)
    chef_service = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='services_diriges'
    )
    description = models.TextField(blank=True)
    capacite = models.IntegerField(default=10)
    actif = models.BooleanField(default=True)

    def lits_disponibles(self):
        from .models import Lit
        return Lit.objects.filter(
            chambre__service=self,
            statut='libre'
        ).count()

    def taux_occupation(self):
        from .models import Lit

        total = Lit.objects.filter(chambre__service=self).count()
        if total == 0:
            return 0

        occupe = Lit.objects.filter(
            chambre__service=self,
            statut='occupe'
        ).count()

        return round((occupe / total) * 100, 2)

    def __str__(self):
        return f"{self.code} — {self.nom}"


class Chambre(models.Model):
    TYPE = [
        ('standard', 'Standard'),
        ('semi_prive', 'Semi-privée'),
        ('prive', 'Privée'),
        ('soins_intensifs', 'Soins intensifs'),
        ('isolation', 'Isolement')
    ]

    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='chambres')
    numero = models.CharField(max_length=20)
    type_chambre = models.CharField(max_length=20, choices=TYPE, default='standard')
    etage = models.IntegerField(default=1)
    actif = models.BooleanField(default=True)

    def __str__(self):
        return f"Ch.{self.numero} ({self.service})"

    class Meta:
        unique_together = ['service', 'numero']


class Lit(models.Model):
    STATUT = [
        ('libre', 'Libre'),
        ('occupe', 'Occupé'),
        ('nettoyage', 'En nettoyage'),
        ('hors_service', 'Hors service')
    ]

    chambre = models.ForeignKey(Chambre, on_delete=models.CASCADE, related_name='lits')
    numero = models.CharField(max_length=10)
    statut = models.CharField(max_length=15, choices=STATUT, default='libre')
    notes = models.TextField(blank=True)

    def service(self):
        return self.chambre.service

    def __str__(self):
        return f"Lit {self.numero} — {self.chambre}"

    class Meta:
        unique_together = ['chambre', 'numero']


class Hospitalisation(models.Model):
    STATUT = [
        ('en_cours', 'En cours'),
        ('sortie_prevue', 'Sortie prévue'),
        ('sorti', 'Sorti'),
        ('transfere', 'Transféré'),
        ('dcd', 'Décédé')
    ]

    MODE_ENTREE = [
        ('urgence', 'Urgences'),
        ('programmee', 'Programmée'),
        ('transfert', 'Transfert interne'),
        ('externe', 'Transfert externe')
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='hospitalisations')
    lit = models.ForeignKey(Lit, on_delete=models.PROTECT, related_name='hospitalisations')
    service = models.ForeignKey(Service, on_delete=models.PROTECT)

    medecin_responsable = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        related_name='hospitalisations_responsable'
    )

    mode_entree = models.CharField(max_length=15, choices=MODE_ENTREE, default='programmee')
    date_entree = models.DateTimeField()
    date_sortie_prevue = models.DateField(null=True, blank=True)
    date_sortie_reelle = models.DateTimeField(null=True, blank=True)

    statut = models.CharField(max_length=15, choices=STATUT, default='en_cours')

    motif_hospitalisation = models.TextField()
    diagnostic_entree = models.TextField(blank=True)
    diagnostic_sortie = models.TextField(blank=True)
    compte_rendu_sortie = models.TextField(blank=True)

    created_by = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        related_name='hospitalisations_creees'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def duree_jours(self):
        from django.utils import timezone
        fin = self.date_sortie_reelle or timezone.now()
        return (fin - self.date_entree).days

    def __str__(self):
        return f"Hosp. {self.patient} — {self.service} ({self.get_statut_display()})"

    class Meta:
        ordering = ['-date_entree']


class SuiviQuotidien(models.Model):
    hospitalisation = models.ForeignKey(Hospitalisation, on_delete=models.CASCADE, related_name='suivis')
    medecin = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)

    date = models.DateTimeField(auto_now_add=True)
    tension = models.CharField(max_length=20, blank=True)
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    poids = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    frequence_cardiaque = models.IntegerField(null=True, blank=True)
    saturation_o2 = models.IntegerField(null=True, blank=True)

    evolution = models.TextField()
    traitement_en_cours = models.TextField(blank=True)
    observations = models.TextField(blank=True)
    prescriptions_nouvelles = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']


class TransfertService(models.Model):
    hospitalisation = models.ForeignKey(Hospitalisation, on_delete=models.CASCADE, related_name='transferts')

    service_origine = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='transferts_depart')
    lit_origine = models.ForeignKey(Lit, on_delete=models.SET_NULL, null=True, related_name='transferts_depart')

    service_destination = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='transferts_arrivee')
    lit_destination = models.ForeignKey(Lit, on_delete=models.SET_NULL, null=True, related_name='transferts_arrivee')

    date = models.DateTimeField(auto_now_add=True)
    motif = models.TextField()

    medecin = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)
