from django.urls import path
from . import views

urlpatterns = [
    path('', views.survey_home, name ='survey-home'),
    #path('<int:survey_id>/', views.survey_home, name='survey-home'),
    path('thank-you/', views.thank_you_view, name='thank_you'),
]