import csv
import logging
import uuid
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.views.decorators.csrf import csrf_exempt

from WebApp.forms import RegisterForm, LoginForm, EnergyConsumptionForm, TurbineForm, \
    SelectTurbineForm, WindDataForm, WindCSVForm, WindAPIForm, EnergyCSVForm, EnergyAverageForm
from WebApp.models import Turbine, WindData
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
        if 'csv_submit' in request.POST:
            csv_form = WindCSVForm(request.POST, request.FILES)
            api_form = WindAPIForm()

            if csv_form.is_valid():
                wind_data_entry = WindData(id=uuid.uuid4(), source='csv')
                csv_file = request.FILES['csv_file']
                wind_data_entry.csv_data = csv_file.read().decode('utf-8')
                wind_data_entry.save()
                request.session['wind_data_id'] = str(wind_data_entry.id)
                return redirect('energy_consumption_view')

        elif 'meteostat_submit' in request.POST:
            api_form = WindAPIForm(request.POST)
            csv_form = WindCSVForm()

            if api_form.is_valid():
                wind_data_entry = WindData(
                    id=uuid.uuid4(),
                    source='meteostat',
                    location=api_form.cleaned_data['location'],
                    start_date=api_form.cleaned_data['start_date'],
                    end_date=api_form.cleaned_data['end_date'],
                    csv_data='placeholder for fetched data'
                )
                wind_data_entry.save()
                request.session['wind_data_id'] = str(wind_data_entry.id)
                return redirect('energy_consumption_view')
    else:
        csv_form = WindCSVForm()
        api_form = WindAPIForm()

    return render(request, 'wind_data.html', {
        'csv_form': csv_form,
        'api_form': api_form,
    })


def energy_consumption_view(request):
    if request.method == 'POST':
        if 'average_submit' in request.POST:
            avg_form = EnergyAverageForm(request.POST)
            csv_form = EnergyCSVForm()

            if avg_form.is_valid():
                consumption = avg_form.cleaned_data['average_consumption']
                request.session['consumption_type'] = 'average'
                request.session['average_consumption'] = consumption
                return redirect('calculate_result_view')  # or next step

        elif 'csv_submit' in request.POST:
            csv_form = EnergyCSVForm(request.POST, request.FILES)
            avg_form = EnergyAverageForm()

            if csv_form.is_valid():
                csv_data = csv_form.cleaned_data['csv_file'].read().decode('utf-8')
                request.session['consumption_type'] = 'csv'
                request.session['csv_consumption'] = csv_data
                return redirect('calculate_result_view')  # or next step

    else:
        avg_form = EnergyAverageForm()
        csv_form = EnergyCSVForm()

    return render(request, 'energy_consumption.html', {
        'avg_form': avg_form,
        'csv_form': csv_form,
    })


def calculate_result_view(request):
    return render(request, 'result.html')

