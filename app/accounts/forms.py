from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Utilisateur

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Nom d\'utilisateur'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control','placeholder':'Mot de passe'}))

class UtilisateurForm(forms.ModelForm):
    password1 = forms.CharField(label='Mot de passe', widget=forms.PasswordInput(attrs={'class':'form-control'}))
    password2 = forms.CharField(label='Confirmer', widget=forms.PasswordInput(attrs={'class':'form-control'}))

    class Meta:
        model = Utilisateur
        fields = ['username','first_name','last_name','email','role','telephone','adresse','genre','date_naissance','photo']
        widgets = {f: forms.TextInput(attrs={'class':'form-control'}) if f not in ['role','genre','adresse','date_naissance','photo'] else forms.Select(attrs={'class':'form-select'}) for f in ['username','first_name','last_name','email','role','telephone','adresse','genre','date_naissance']}

    def clean_password2(self):
        p1, p2 = self.cleaned_data.get('password1'), self.cleaned_data.get('password2')
        if p1 != p2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return p2
