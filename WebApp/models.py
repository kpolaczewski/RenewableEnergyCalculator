import math
from argparse import ArgumentError
from django.db import models
import logging
from rest_framework.exceptions import ValidationError
from .utils import calculate_air_density
import uuid

# Create your models here.
class Turbine(models.Model):
    """
    A Django model representing a wind turbine
    """
    name = models.CharField(max_length=100, unique=True, db_index=True, help_text="The name of the turbine")
    company_name = models.CharField(max_length=50, help_text="The company name")
    rotor_diameter = models.FloatField(help_text="The rotor diameter in meters")
    efficiency = models.FloatField(help_text="Power coefficient (Cp), typically between 0.3 and 0.5")
    nominal_power = models.FloatField(help_text="Nominal power output in W (Watts)")
    startup_speed = models.FloatField(help_text="Minimum wind speed required for the turbine to start (m/s)")

    def clean(self):
        """
        Custom validation to ensure efficiency is within a valid range (0.0 - 0.6).
        """
        try:
            # Ensure the values are converted to float
            efficiency = float(self.efficiency)
            nominal_power = float(self.nominal_power)
            startup_speed = float(self.startup_speed)

            # Now perform the checks on floats
            if not (0.0 <= efficiency <= 0.6):
                raise ValidationError('Efficiency must be between 0.0 and 0.6.')

            if nominal_power <= 0:
                raise ValidationError('Nominal power must be a positive value.')

            if startup_speed <= 0:
                raise ValidationError('Startup speed must be a positive value.')

        except ValueError:
            raise ValidationError('Invalid value for one or more fields. Please ensure all values are numeric.')

    def save(self, *args, **kwargs):
        """
        Overrides save() to validate the model before saving.
        """
        try:
            self.clean()
        except ValidationError as e:
            logging.warning(f"Validation Error: {e}. Setting efficiency to 0.4.")
            self.efficiency = 0.4
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.company_name} {self.name} ({self.nominal_power} MW)"

    def calculate_daily_power_output(self, wind_speed : float, temp_celcius : float = 15.0, pressure_hpa : float = 1013.5) -> float:
        """
        Calculates the power output of the turbine given a wind speed.

        P = 0.5 * ρ * A * v^3 * Cp

        where:
        - ρ (air density) = 1.225 kg/m³ (default at sea level)
        - A (rotor swept area) = π * (D/2)^2
        - v (wind speed in m/s)
        - Cp (efficiency, self.efficiency)

        Returns: Power output in Watts
        """
        air_density = calculate_air_density(temp_celcius, pressure_hpa)

        if wind_speed < self.startup_speed:
            return 0

        swept_area = math.pi * (self.rotor_diameter / 2) ** 2
        power_output = 0.5 * air_density * swept_area * (wind_speed ** 3) * self.efficiency

        return min(power_output, self.nominal_power)

    def calculate_annual_wind_power_output(self, wind_speeds: [], temp_celcius: [] = None, pressure_hpa: [] = None) -> []:
        """
            Calculates the annual power output for the turbine given daily wind speed data.

            Parameters:
            - wind_speeds (list): A list of daily average wind speeds (m/s)
            - temp_celcius (list, optional): A list of daily temperatures (°C) or None (default 15°C)
            - pressure_hpa (list, optional): A list of daily pressures (hPa) or None (default 1013.5 hPa)

            Returns:
            - list: A list of daily power outputs in Watts
            """

        if not wind_speeds:
            raise ArgumentError(message ='No wind speed data provided')

            # Set default values if temperature or pressure data is not provided
        if temp_celcius is None:
            temp_celcius = [15.0] * len(wind_speeds)  # Default 15°C for all days
        if pressure_hpa is None:
            pressure_hpa = [1013.5] * len(wind_speeds)  # Default 1013.5 hPa for all days

        if len(wind_speeds) != len(temp_celcius) or len(wind_speeds) != len(pressure_hpa):
            raise ArgumentError(
                message ="Mismatched list lengths. Ensure wind_speeds, temp_celcius, and pressure_hpa are of the same length.")

        daily_outputs = []
        for i in range(len(wind_speeds)):
            power_output = self.calculate_daily_power_output(wind_speeds[i], temp_celcius[i], pressure_hpa[i])
            daily_outputs.append(power_output)

        return daily_outputs



class WindData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.CharField(max_length=20, choices=[('csv', 'CSV'), ('meteostat', 'Meteostat')])
    csv_data = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)