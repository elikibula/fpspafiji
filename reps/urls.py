from django.urls import path
from . import views

app_name = "reps"

urlpatterns = [
    path("", views.district_representatives, name="district_representatives"),
    path("representatives/", views.district_representatives, name="reps_list"),
    path("districts/", views.district_representatives, name="areas"),
]
