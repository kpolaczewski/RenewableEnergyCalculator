import csv
import logging
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.views.decorators.csrf import csrf_exempt

from WebApp.forms import RegisterForm, LoginForm, EnergyConsumptionForm, TurbineForm, WindDataChoiceForm, \
    SelectTurbineForm, WindDataForm
from WebApp.models import Turbine
from meteostat import Daily, Point, Stations

from WebApp.utils import turbine_to_dict


def home_view(request):
    return render(request, 'home.html')

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                form.add_error(None, "Invalid username or password.")
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

def dashboard_view(request):
    return render(request, 'dashboard.html')


def get_wind_data_from_meteostat(lat, lon, start_date, end_date):
    if end_date - start_date > timedelta(days=365):
        raise ValueError("The date range must not exceed 1 year.")

    stations = Stations()
    stations = stations.nearby(lat=lat, lon=lon)
    stations = stations.fetch(1)

    if stations.empty:
        return None

    station_id = stations.index[0]

    df = Daily(station_id, start=start_date, end=end_date)
    df = df.fetch()

    wind_speed = df['wspd'].mean() if not df.empty else None
    return wind_speed


def process_csv(file):
    data = []
    decoded_file = file.read().decode('utf-8').splitlines()
    csv_reader = csv.reader(decoded_file)

    for row in csv_reader:
        data.append({
            'date': row[0],
            'wind_speed': row[1]
        })
    return data


def turbine_selection_view(request):
    if request.method == 'POST':
        select_form = SelectTurbineForm(request.POST)
        turbine_form = TurbineForm(request.POST)

        if 'select_submit' in request.POST:
            if select_form.is_valid():
                turbine = select_form.cleaned_data['turbine']
                turbine_data = turbine_to_dict(turbine)
                request.session['turbine_data'] = turbine_data
                return redirect('wind_data_view')
            else:
                messages.error(request, "Please select a turbine.")

        elif 'create_submit' in request.POST:
            if turbine_form.is_valid():
                turbine_data = {
                    "rotor_diameter": turbine_form.cleaned_data['rotor_diameter'],
                    "efficiency": turbine_form.cleaned_data['efficiency'],
                    "nominal_power": turbine_form.cleaned_data['nominal_power'],
                    "startUp": turbine_form.cleaned_data['startup_speed'],
                }
                request.session['turbine_data'] = turbine_data
                return redirect('wind_data_view')
            else:
                messages.error(request, "Please fill all fields correctly.")

    else:
        select_form = SelectTurbineForm()
        turbine_form = TurbineForm()

    return render(request, 'turbine_selection.html', {
        'select_form': select_form,
        'turbine_form': turbine_form,
    })


def wind_data_view(request):
    if request.method == 'POST':
        form = WindDataForm(request.POST, request.FILES)
        if form.is_valid():
            source = form.cleaned_data['source_choice']
            if source == 'csv':
                csv_file = request.FILES['csv_file']
                # Process CSV here
                request.session['wind_data'] = csv_file.read().decode('utf-8')
            elif source == 'meteostat':
                location = form.cleaned_data['location']
                start_date = form.cleaned_data['start_date']
                end_date = form.cleaned_data['end_date']
                # Fetch data via meteostat
                # Save it into session
            return redirect('calculate_result_view')
    else:
        form = WindDataForm()

    return render(request, 'wind_data.html', {'form': form})

def calculate_result_view(request):
    return render(request, 'result.html')

