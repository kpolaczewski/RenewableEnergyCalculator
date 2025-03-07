from django.contrib import admin

from .models import Turbine


# Register your models here.
class TurbineAdmin(admin.ModelAdmin):
    list_display = ("name", "company_name", "rotor_diameter", "efficiency", "nominal_power", "startup_speed")
    search_fields = ("name", "company")


admin.site.register(Turbine, TurbineAdmin)