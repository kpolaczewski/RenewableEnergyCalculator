from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from rest_framework.exceptions import ValidationError


class TurbineForm(forms.Form):
    rotor_diameter = forms.FloatField(label="Rotor Diameter (m)", required=True)
    efficiency = forms.FloatField(label="Efficiency (Cp)", required=True)
    nominal_power = forms.FloatField(label="Nominal Power (W)", required=True)
    startup_speed = forms.FloatField(label="Startup Speed (m/s)", required=True)

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