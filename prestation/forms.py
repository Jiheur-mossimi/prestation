from django import forms
from .models import Agent, Service, Cours, Classe, Fonction, Mois


class AgentForm(forms.ModelForm):
    class Meta:
        model = Agent
        fields = [
            'matricule', 'nom', 'postnom', 'prenom', 'sexe',
            'telephone', 'email', 'adresse', 'photo',
            'type_agent', 'etat', 'service',
            'date_naissance', 'lieu_naissance', 'nationalite',
            'province_origine', 'territoire_origine', 'secteur',
            'groupement', 'village_origine'
        ]
        widgets = {
            'matricule': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: AGT001', 'style': 'text-transform: uppercase;'}),
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de famille'}),
            'postnom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postnom'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'sexe': forms.Select(attrs={'class': 'form-select'}, choices=[('', 'Sélectionnez le sexe'), ('M', 'Masculin'), ('F', 'Féminin')]),
            'telephone': forms.TextInput(attrs={'class': 'form-control phone-input', 'placeholder': 'Ex: +243812345678'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'agent@ecole.cd'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Adresse complète'}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'type_agent': forms.Select(attrs={'class': 'form-select'}),
            'etat': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'service': forms.Select(attrs={'class': 'form-select'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'lieu_naissance': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lieu de naissance'}),
            'nationalite': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nationalité', 'value': 'Congolaise'}),
            'province_origine': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Province d\'origine'}),
            'territoire_origine': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Territoire'}),
            'secteur': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Secteur'}),
            'groupement': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Groupement'}),
            'village_origine': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Village d\'origine'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sexe'].choices = [('', 'Sélectionnez le sexe'), ('M', 'Masculin'), ('F', 'Féminin')]
        self.fields['service'].empty_label = 'Sélectionnez un service'
        self.fields['type_agent'].empty_label = 'Sélectionnez le type'


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['nom', 'description']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Enseignement'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Description du service...'}),
        }


class CoursForm(forms.ModelForm):
    class Meta:
        model = Cours
        fields = ['code', 'libelle', 'coefficient', 'enseignant_responsable', 'heures_ponderation', 'description', 'actif']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'style': 'text-transform: uppercase;', 'placeholder': 'Ex: MATH101'}),
            'libelle': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Mathématiques'}),
            'coefficient': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10, 'placeholder': 'Coefficient (1-10)'}),
            'enseignant_responsable': forms.Select(attrs={'class': 'form-select'}),
            'heures_ponderation': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'Ex: 60'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description du cours...'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ClasseForm(forms.ModelForm):
    class Meta:
        model = Classe
        fields = ['nom', 'niveau', 'effectif', 'status']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 6ème A'}),
            'niveau': forms.Select(attrs={'class': 'form-select'}),
            'effectif': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': "Nombre d'élèves"}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['niveau'].empty_label = 'Sélectionnez le niveau'
        self.fields['status'].empty_label = 'Sélectionnez le statut'


class FonctionForm(forms.ModelForm):
    class Meta:
        model = Fonction
        fields = ['libelle', 'description']
        widgets = {
            'libelle': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Professeur'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Description de la fonction...'}),
        }


class MoisForm(forms.ModelForm):
    class Meta:
        model = Mois
        fields = ['libelle', 'mois_num', 'annee']
        widgets = {
            'libelle': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Janvier 2025'}),
            'mois_num': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 12, 'placeholder': 'Numéro du mois (1-12)'}),
            'annee': forms.NumberInput(attrs={'class': 'form-control', 'min': 2020, 'max': 2100, 'placeholder': 'Ex: 2025'}),
        }