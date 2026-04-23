from django.urls import path
from . import views

app_name = 'reps'

urlpatterns = [
    path('', views.areas, name='areas'),
    path('reps', views.reps_list, name='reps_list'),
    
]
