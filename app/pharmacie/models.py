from django.db import models
from apps.accounts.models import Utilisateur

class CategorieMedicament(models.Model):
    nom = models.CharField(max_length=100)
    def __str__(self): return self.nom

class Medicament(models.Model):
    FORME = [('comprime','Comprimé'),('sirop','Sirop'),('injection','Injection'),('creme','Crème'),('gouttes','Gouttes'),('autre','Autre')]
    nom = models.CharField(max_length=200)
    nom_generique = models.CharField(max_length=200, blank=True)
    categorie = models.ForeignKey(CategorieMedicament, on_delete=models.SET_NULL, null=True)
    forme = models.CharField(max_length=20, choices=FORME)
    dosage = models.CharField(max_length=50)
    stock = models.IntegerField(default=0)
    stock_minimum = models.IntegerField(default=10)
    prix_achat = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    prix_vente = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date_expiration = models.DateField(null=True, blank=True)
    fournisseur = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)

    def en_rupture(self):
        return self.stock <= self.stock_minimum

    def __str__(self):
        return f"{self.nom} {self.dosage}"

    class Meta:
        ordering = ['nom']

class MouvementStock(models.Model):
    TYPE = [('entree','Entrée'),('sortie','Sortie'),('ajustement','Ajustement')]
    medicament = models.ForeignKey(Medicament, on_delete=models.CASCADE, related_name='mouvements')
    type_mouvement = models.CharField(max_length=15, choices=TYPE)
    quantite = models.IntegerField()
    motif = models.CharField(max_length=200)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(auto_now_add=True)
    stock_avant = models.IntegerField()
    stock_apres = models.IntegerField()

    def save(self, *args, **kwargs):
        self.stock_avant = self.medicament.stock
        if self.type_mouvement == 'entree':
            self.medicament.stock += self.quantite
        else:
            self.medicament.stock -= self.quantite
        self.stock_apres = self.medicament.stock
        self.medicament.save()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-date']

class DispensationMedicament(models.Model):
    from apps.consultations.models import Ordonnance
    ordonnance = models.ForeignKey('consultations.Ordonnance', on_delete=models.CASCADE, related_name='dispensations')
    pharmacien = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(auto_now_add=True)
    montant_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
