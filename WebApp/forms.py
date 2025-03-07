from django import forms


class TurbineForm(forms.Form):
    rotor_diameter = forms.FloatField(label="Rotor Diameter (m)", required=True)
    efficiency = forms.FloatField(label="Efficiency (Cp)", required=True)
    nominal_power = forms.FloatField(label="Nominal Power (W)", required=True)
    startup_speed = forms.FloatField(label="Startup Speed (m/s)", required=True)