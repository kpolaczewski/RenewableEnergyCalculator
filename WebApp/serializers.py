from rest_framework import serializers
from .models import Turbine

class TurbineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Turbine
        fields = "__all__"