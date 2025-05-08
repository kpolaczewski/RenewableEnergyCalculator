from django.urls import path
from .views import *

urlpatterns = [
    path('', home_view, name="home"),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('calculate/step1/', turbine_selection_view, name='turbine_selection_view'),
    path('calculate/step2/', wind_data_view, name='wind_data_view'),
    path('calculate/step3/', energy_consumption_view, name='energy_consumption_view'),
    path('calculate/result/', calculate_result_view, name='calculate_result_view'),
]
