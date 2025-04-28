import csv
import io
import requests



def turbine_to_dict(turbine):
    return {
        "rotor_diameter": turbine.rotor_diameter,
        "efficiency": turbine.efficiency,
        "nominal_power": turbine.nominal_power,
        "startUp": turbine.startup_speed,
    }

def calculate_air_density(temp_c, pressure_hpa):
    """
    Calculates air density using the ideal gas law.

    Parameters:
    - temp_c (float): Average air temperature in °C
    - pressure_hpa (float): Atmospheric pressure in hPa

    Returns:
    - float: Air density in kg/m³
    """
    R = 287.05  # Specific gas constant for dry air (J/kg·K)

    # Convert temperature to Kelvin
    temp_k = temp_c + 273.15

    # Convert pressure to Pascals
    pressure_pa = pressure_hpa * 100

    # Calculate air density
    air_density = pressure_pa / (R * temp_k)

    return air_density

