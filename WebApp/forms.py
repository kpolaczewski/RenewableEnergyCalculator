from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from rest_framework.exceptions import ValidationError

from WebApp.models import Turbine


class SelectTurbineForm(forms.Form):
    turbine = forms.ModelChoiceField(
        queryset=Turbine.objects.all(),
        required=True,
        label="Select a Turbine"
    )

class TurbineForm(forms.ModelForm):
    class Meta:
        model = Turbine
        fields = ['name', 'company_name', 'rotor_diameter', 'efficiency', 'nominal_power', 'startup_speed']


class WindDataForm(forms.Form):
    source_choice = forms.ChoiceField(
        choices=[('csv', 'Upload CSV'), ('meteostat', 'Use Meteostat')],
        widget=forms.RadioSelect,
        required=True
    )
    csv_file = forms.FileField(required=False)
    location = forms.CharField(required=False)
    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)


class EnergyConsumptionForm(forms.Form):
    consumption_file = forms.FileField(label="Upload Home Energy Consumption CSV", required=True)

class WindDataChoiceForm(forms.Form):
    DATA_SOURCE_CHOICES = [
        ('csv', 'Upload CSV File'),
        ('api', 'Use Meteostat API'),
    ]
    data_source = forms.ChoiceField(choices=DATA_SOURCE_CHOICES, widget=forms.RadioSelect, required=True)
    wind_data_file = forms.FileField(label="Upload Wind Data CSV", required=False)

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={
            'class': 'w-full p-2 mb-2 mt-1 outline-none ring-none focus:ring-2 focus:ring-indigo-500',
            'id': 'username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full p-2 mb-2 mt-1 outline-none ring-none focus:ring-2 focus:ring-indigo-500',
            'id': 'password'
        })
    )

class RegisterForm(UserCreationForm):
    email = forms.EmailField(label="E-mail", required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean(self):
        cleaned_data = super().clean()

        email = cleaned_data.get('email')

        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already in use. Please choose another.")

        return cleaned_data