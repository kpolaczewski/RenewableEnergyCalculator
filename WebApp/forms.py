from datetime import timedelta, datetime

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
    source_choice = forms.ChoiceField(choices=[('csv', 'CSV File'), ('meteostat', 'Meteostat API')], required=True)
    csv_file = forms.FileField(required=False)
    location = forms.CharField(max_length=100, required=False)
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))



class EnergyConsumptionForm(forms.Form):
    consumption_file = forms.FileField(label="Upload Home Energy Consumption CSV", required=True)

class WindCSVForm(forms.Form):
    csv_file = forms.FileField(label="Upload CSV File")


class WindAPIForm(forms.Form):
    location = forms.CharField(max_length=200, label="Location")
    latitude = forms.FloatField(widget=forms.HiddenInput())
    longitude = forms.FloatField(widget=forms.HiddenInput())
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        # Get the current date
        today = datetime.today().date()

        # Ensure that start_date and end_date are within 1 year from today
        if start_date and end_date:
            # Check that both dates are in the past (before today)
            if start_date >= today:
                raise ValidationError("Start date must be in the past.")
            if end_date >= today:
                raise ValidationError("End date must be in the past.")

            # Check that start_date is before end_date
            if start_date > end_date:
                raise ValidationError("Start date must be before end date.")

            # Check that the range is less than 1 year
            if (end_date - start_date).days > 365:
                raise ValidationError("The date range must be less than one year.")

        return cleaned_data

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

class EnergyAverageForm(forms.Form):
    average_consumption = forms.ChoiceField(
        choices=[
            ('low', 'Low (2000 kWh/year)'),
            ('medium', 'Medium (4000 kWh/year)'),
            ('high', 'High (6000 kWh/year)'),
        ],
        label="Select Average Consumption",
        widget=forms.RadioSelect
    )

class EnergyCSVForm(forms.Form):
    csv_file = forms.FileField(label="Upload CSV File")