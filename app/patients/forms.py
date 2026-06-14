from django import forms
from apps.accounts.models import Utilisateur
from .models import Patient

class PatientForm(forms.Form):
    # User fields
    username   = forms.CharField(label="Nom d'utilisateur", widget=forms.TextInput(attrs={'class':'form-control'}))
    password   = forms.CharField(label="Mot de passe", widget=forms.PasswordInput(attrs={'class':'form-control'}), initial='patient123')
    first_name = forms.CharField(label="Prénom", widget=forms.TextInput(attrs={'class':'form-control'}))
    last_name  = forms.CharField(label="Nom", widget=forms.TextInput(attrs={'class':'form-control'}))
    email      = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class':'form-control'}))
    telephone  = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control'}))
    # Patient fields
    groupe_sanguin      = forms.ChoiceField(choices=[('','---')]+Patient.GROUPE_SANGUIN, required=False, widget=forms.Select(attrs={'class':'form-select'}))
    allergies           = forms.CharField(required=False, widget=forms.Textarea(attrs={'class':'form-control','rows':2}))
    antecedents         = forms.CharField(required=False, widget=forms.Textarea(attrs={'class':'form-control','rows':2}))
    medecin_traitant    = forms.ModelChoiceField(queryset=Utilisateur.objects.filter(role__in=['medecin','chef']), required=False, widget=forms.Select(attrs={'class':'form-select'}))
    assurance           = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control'}))
    contact_urgence_nom = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control'}))
    contact_urgence_tel = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control'}))

class DossierMedicalForm(forms.Form):
    titre      = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}))
    contenu    = forms.CharField(widget=forms.Textarea(attrs={'class':'form-control','rows':6}))
    confidentiel = forms.BooleanField(required=False)
