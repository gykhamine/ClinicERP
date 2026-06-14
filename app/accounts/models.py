from django.contrib.auth.models import AbstractUser
from django.db import models

ROLE_CHOICES = [
    ('chef', 'Chef / Directeur'),
    ('medecin', 'Médecin'),
    ('infirmier', 'Infirmier(e)'),
    ('pharmacien', 'Pharmacien(ne)'),
    ('laborantin', 'Laborantin(e)'),
    ('receptionniste', 'Réceptionniste'),
    ('comptable', 'Comptable'),
    ('patient', 'Patient'),
]

class Utilisateur(AbstractUser):
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
    telephone = models.CharField(max_length=20, blank=True)
    adresse = models.TextField(blank=True)
    photo = models.ImageField(upload_to='photos/', blank=True, null=True)
    date_naissance = models.DateField(null=True, blank=True)
    genre = models.CharField(max_length=10, choices=[('M','Masculin'),('F','Féminin'),('A','Autre')], blank=True)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_personnel(self):
        return self.role in ['medecin','infirmier','pharmacien','laborantin','receptionniste','comptable']

    def is_chef(self):
        return self.role == 'chef'

    def is_patient(self):
        return self.role == 'patient'

    def get_role_display_icon(self):
        icons = {
            'chef': '👑', 'medecin': '🩺', 'infirmier': '💉',
            'pharmacien': '💊', 'laborantin': '🔬', 'receptionniste': '📋',
            'comptable': '💰', 'patient': '🏥'
        }
        return icons.get(self.role, '👤')

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
