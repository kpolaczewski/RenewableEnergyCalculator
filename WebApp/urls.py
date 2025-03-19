from django.urls import path
from .views import *


urlpatterns = [
    path('', home_view, name="home"),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('calculator/', calculator_view, name='calculator'),
]
