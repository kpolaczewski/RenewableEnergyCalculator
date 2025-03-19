from django.db import models
import logging

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

    def save(self, *args, **kwargs):
        """
        Custom save method to ensure efficiency is within the valid range (0.0 - 0.6).
        """
        if self.efficiency > 0.6 or self.efficiency < 0:
            logging.warning(f"Efficiency value {self.efficiency} is out of bounds. Setting efficiency to 0.4.")
            self.efficiency = 0.4
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.company_name} {self.name} ({self.nominal_power} MW)"

    #def calculate_efficiency(self, wind_speed):
