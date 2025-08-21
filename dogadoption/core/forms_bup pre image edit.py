from django import forms
from .models import FosterHome

class FosterHomeForm(forms.ModelForm):
    class Meta:
        model = FosterHome
        fields = '__all__'



# forms.py
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")



from django import forms
from .models import MedicalRecord

#class MedicalRecordForm(forms.ModelForm):
#    class Meta:
#        model = MedicalRecord
#        fields = ['checkup_date', 'vet_name', 'description', 'medication', 'vaccinations', 'follow_up_required', 'status']
class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ['checkup_date', 'vet_name', 'description', 'medication', 'vaccinations', 'follow_up_required', 'status', 'notes', 'last_update_date']
        widgets = {
            'checkup_date': forms.DateInput(attrs={'class': 'form-control w-auto', 'type': 'date'}),
            'vet_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'medication': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'vaccinations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'follow_up_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status': forms.Select(attrs={'class': 'form-control w-auto'}),  # <-- this makes it a pulldown
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'last_update_date': forms.DateInput(attrs={'class': 'form-control w-auto', 'type': 'date', 'disabled': True}),
        }




# core/forms.py
from django import forms
from .models import Dog

class DogUpdateForm(forms.ModelForm):
    class Meta:
        model = Dog
        fields = '__all__' # Specify fields you want to adisplay

        widgets = {
            #'update_date': forms.DateTimeInput(attrs={'class': 'form-control', 'style': 'width: 200px;',
            #    'readonly': 'readonly', 'disabled': True}),
            'update_date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                    'style': 'width: 200px;',  # Set exact width
                    'disabled': True
                },
                format='%Y-%m-%d'
            ),
            'creation_date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                    'style': 'width: 200px;',  # Set exact width
                    'disabled': False
                },
                format='%Y-%m-%d'
            ),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'url': forms.TextInput(attrs={'class': 'form-control', 'style': 'width: 500px'}),
            'age': forms.TextInput(attrs={'class': 'form-control'}),
            'status':  forms.Select(attrs={'class': 'form-control'}),
            #'notes' : forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(
                attrs={
                    'rows': 15,
                    'cols': 40,
                    'class': 'form-control',
                    'placeholder': 'Enter notes here...'
                },
            ),

            #'adoption_date': forms.DateTimeInput(attrs={'class': 'form-control', 'readonly': 'readonly', 'disabled': False}),
            'adoption_date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                    'style': 'width: 200px;',  # Set exact width
                    'disabled': False
                },
                format='%Y-%m-%d'
            ),
            'arrival_date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                    'style': 'width: 200px;',  # Set exact width
                    'disabled': False
                },
                format='%Y-%m-%d'
            ),
            'colour' : forms.TextInput(attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, readonly=False, **kwargs):
            super().__init__(*args,  **kwargs)
            self.fields['update_date'].initial = self.instance.update_date

            if readonly:
                for field in self.fields.values():
                    field.disabled = True

class DogReadonlyForm(forms.ModelForm):
    class Meta:
        model = Dog
        fields = '__all__' # Specify fields you want to adisplay

        widgets = {
            #'update_date': forms.DateTimeInput(attrs={'class': 'form-control', 'style': 'width: 200px;',
            #    'readonly': 'readonly', 'disabled': True}),
            'update_date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                    'style': 'width: 200px;',  # Set exact width
                    'disabled': True
                },
                format='%Y-%m-%d'
            ),
            'creation_date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                    'style': 'width: 200px;',  # Set exact width
                    'disabled': False
                },
                format='%Y-%m-%d'
            ),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'url': forms.TextInput(attrs={'class': 'form-control', 'style': 'width: 500px'}),
            'age': forms.TextInput(attrs={'class': 'form-control'}),
            'status':  forms.Select(attrs={'class': 'form-control'}),
            #'notes' : forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(
                attrs={
                    'rows': 15,
                    'cols': 40,
                    'class': 'form-control',
                    'placeholder': 'Enter notes here...'
                },
            ),

            #'adoption_date': forms.DateTimeInput(attrs={'class': 'form-control', 'readonly': 'readonly', 'disabled': False}),
            'adoption_date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                    'style': 'width: 200px;',  # Set exact width
                    'disabled': False
                },
                format='%Y-%m-%d'
            ),
            'arrival_date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                    'style': 'width: 200px;',  # Set exact width
                    'disabled': False
                },
                format='%Y-%m-%d'
            ),
            'colour' : forms.TextInput(attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, readonly=True, **kwargs):
            super().__init__(*args,  **kwargs)
            self.fields['update_date'].initial = self.instance.update_date

            if readonly:
                for field in self.fields.values():
                    field.disabled = True




from django import forms
from .models import DogWalker, DogWalk

class DogWalkerForm(forms.ModelForm):
    class Meta:
        model = DogWalker
        fields = '__all__'


class DogWalkForm(forms.ModelForm):
    class Meta:
        model = DogWalk
        fields = '__all__'
        widgets = {
            'walk_date': forms.DateInput(attrs={'type': 'date'}),
        }




from django import forms
from .models import DogFosterAssignment

class DogFosterAssignmentForm(forms.ModelForm):
    class Meta:
        model = DogFosterAssignment
        fields = ['dog', 'foster', 'start_date', 'end_date', 'notes']


