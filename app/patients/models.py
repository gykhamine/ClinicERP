from django.db import models
from apps.accounts.models import Utilisateur
import qrcode
import io
from django.core.files.base import ContentFile

class Patient(models.Model):
    GROUPE_SANGUIN = [('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),('AB+','AB+'),('AB-','AB-'),('O+','O+'),('O-','O-')]
    
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, related_name='profil_patient')
    numero_dossier = models.CharField(max_length=20, unique=True)
    groupe_sanguin = models.CharField(max_length=5, choices=GROUPE_SANGUIN, blank=True)
    allergies = models.TextField(blank=True)
    antecedents = models.TextField(blank=True, verbose_name="Antécédents médicaux")
    medecin_traitant = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='patients_traites')
    assurance = models.CharField(max_length=100, blank=True)
    numero_assurance = models.CharField(max_length=50, blank=True)
    contact_urgence_nom = models.CharField(max_length=100, blank=True)
    contact_urgence_tel = models.CharField(max_length=20, blank=True)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.numero_dossier:
            import random
            self.numero_dossier = f"PAT{random.randint(10000,99999)}"
        if not self.qr_code:
            self.generate_qr()
        super().save(*args, **kwargs)

    def generate_qr(self):
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(f"PATIENT:{self.numero_dossier}|{self.utilisateur.get_full_name()}")
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        self.qr_code.save(f'qr_{self.numero_dossier}.png', ContentFile(buffer.getvalue()), save=False)

    def __str__(self):
        return f"{self.utilisateur.get_full_name()} [{self.numero_dossier}]"

    class Meta:
        verbose_name = 'Patient'
        ordering = ['-created_at']


class DossierMedical(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='dossiers')
    titre = models.CharField(max_length=200)
    contenu = models.TextField()
    fichier = models.FileField(upload_to='dossiers/', blank=True, null=True)
    medecin = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(auto_now_add=True)
    confidentiel = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.patient} - {self.titre}"

    class Meta:
        ordering = ['-date']
