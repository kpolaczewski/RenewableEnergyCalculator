import csv
import json
import logging
import uuid
from datetime import datetime, timedelta, time, date

from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.views.decorators.csrf import csrf_exempt

from WebApp.forms import RegisterForm, LoginForm, EnergyConsumptionForm, TurbineForm, \
    SelectTurbineForm, WindDataForm, WindCSVForm, WindAPIForm, EnergyCSVForm, EnergyAverageForm
from WebApp.models import Turbine, WindDataCSV, WindDataAPI
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


def get_wind_avg_from_meteostat(lat, lon, start_date, end_date):
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

    wind_avg = df['wspd'].mean() if not df.empty else None
    return wind_avg


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
        select_form = SelectTurbineForm(request.POST, user=request.user)
        turbine_form = TurbineForm(request.POST, user=request.user)

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
                turbine = turbine_form.save(commit=False)
                turbine.user = request.user
                turbine.save()

                turbine_data = turbine_to_dict(turbine)
                request.session['turbine_data'] = turbine_data
                return redirect('wind_data_view')
            else:
                messages.error(request, "Please fill all fields correctly.")

    else:
        select_form = SelectTurbineForm(user=request.user)
        turbine_form = TurbineForm(user=request.user)

    return render(request, 'turbine_selection.html', {
        'select_form': select_form,
        'turbine_form': turbine_form,
    })


def wind_data_view(request):
    if request.method == 'POST':
        if 'csv_submit' in request.POST:
            csv_form = WindCSVForm(request.POST, request.FILES)

            if csv_form.is_valid():
                wind_data_entry = WindDataCSV(
                    id=uuid.uuid4(),
                    source='csv'
                )
                csv_file = request.FILES['csv_file']
                wind_data_entry.csv_data = csv_file.read().decode('utf-8')
                wind_data_entry.save()
                request.session['wind_data_id'] = str(wind_data_entry.id)
                return redirect('energy_consumption_view')

        elif 'meteostat_submit' in request.POST:
            api_form = WindAPIForm(request.POST)

            if api_form.is_valid():
                wind_data_entry = WindDataAPI(
                    id=uuid.uuid4(),
                    latitude=api_form.cleaned_data['latitude'],
                    longitude=api_form.cleaned_data['longitude'],
                    location=api_form.cleaned_data['location'],
                    start_date=api_form.cleaned_data['start_date'],
                    end_date=api_form.cleaned_data['end_date'],
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
                avg_choice = avg_form.cleaned_data['average_consumption']
                avg_custom = avg_form.cleaned_data['custom_consumption']

                if avg_choice:
                    request.session['consumption_type'] = 'average'
                    request.session['average_consumption'] = avg_choice


                else:
                    request.session['consumption_type'] = 'custom'
                    request.session['custom_consumption'] = avg_custom

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
    turbine_data = request.session.get('turbine_data')
    wind_data_id = request.session.get('wind_data_id')

    turbine = Turbine(
        name=turbine_data['name'],
        company_name=turbine_data['company_name'],
        rotor_diameter=turbine_data['rotor_diameter'],
        efficiency=turbine_data['efficiency'],
        nominal_power=turbine_data['nominal_power'],
        startup_speed=turbine_data['startUp']

    )

    if not turbine_data or not wind_data_id:
        return render(request, 'result.html', {'error': 'Missing turbine or wind data information.'})

    wind_speeds = []
    dates = []

    # If data came from Meteostat
    try:
        wind_data_id_uuid = uuid.UUID(wind_data_id)
        wind_data_api = WindDataAPI.objects.get(id=wind_data_id_uuid)
        location = Point(wind_data_api.latitude, wind_data_api.longitude)

        if isinstance(wind_data_api.start_date, date):
            wind_data_api.start_date = datetime.combine(wind_data_api.start_date, time.min)

        if isinstance(wind_data_api.end_date, date):
            wind_data_api.end_date = datetime.combine(wind_data_api.end_date, time.min)

        df = Daily(location, wind_data_api.start_date, wind_data_api.end_date).fetch()

        if df.empty or 'wspd' not in df:
            raise ValueError("No wind speed data available.")

        wind_speeds = df['wspd'].tolist()
        dates = df.index.strftime('%Y-%m-%d').tolist()


    # If data came from CSV
    except WindDataAPI.DoesNotExist:
        try:
            wind_data_id_uuid = uuid.UUID(wind_data_id)
            wind_data_csv = WindDataCSV.objects.get(id=wind_data_id_uuid)
            csv_lines = wind_data_csv.csv_data.strip().splitlines()

            for line in csv_lines[1:]:  # Skip header
                date_str, speed = line.strip().split(',')
                dates.append(date_str)
                wind_speeds.append(float(speed))
        except Exception as e:
            return render(request, 'result.html', {'error': f"Error reading CSV data: {str(e)}"})

    power_outputs = turbine.calculate_annual_wind_power_output(wind_speeds)

    average_consumption_num = 0
    produced_energy = 0
    consumption_type = request.session['consumption_type']
    avg_output = 0

    if consumption_type == "custom":
        average_consumption_num = request.session['custom_consumption']
        for i in range(len(power_outputs)):
            power_outputs[i] = power_outputs[i] - average_consumption_num
            if power_outputs[i] > 0:
                produced_energy += power_outputs[i]
        avg_output = sum(power_outputs) / len(power_outputs) if power_outputs else 0

    elif consumption_type == "average":
        average_consumption = request.session['average_consumption']
        match average_consumption:
            case "low":
                average_consumption_num = 2000
            case "medium":
                average_consumption_num = 4000
            case "high":
                 average_consumption_num = 6000
        for i in range(len(power_outputs)):
            power_outputs[i] = power_outputs[i] - average_consumption_num
            if power_outputs[i] > 0:
                produced_energy += power_outputs[i]
        avg_output = sum(power_outputs) / len(power_outputs) if power_outputs else 0



    if consumption_type == "csv":
        csv_consumption = request.session['csv_consumption']
        lines = csv_consumption.strip().splitlines()
        consumption_day = []

        for line in lines[1:]:
            date_str, consumption = line.strip().split(',')
            consumption_day.append(float(consumption))
        print(consumption_day)
        for i in range(len(power_outputs)):
            power_outputs[i] = power_outputs[i] - consumption_day[i]
            if power_outputs[i] > 0:
                produced_energy += power_outputs[i]
        avg_output = sum(power_outputs) / len(power_outputs) if power_outputs else 0

    # Prepare data for chart
    chart_data = {
        'labels': dates,
        'data': power_outputs,
    }

    return render(request, 'result.html', {
        'chart_data': json.dumps(chart_data),
        'turbine': turbine,
        'average_output': avg_output,
        'produced_energy': produced_energy
    })
