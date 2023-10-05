from django.urls import path
from . import views

urlpatterns = [
    path('', views.vizual_home, name ='vizual-home'),
]