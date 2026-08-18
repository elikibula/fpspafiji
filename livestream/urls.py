from django.urls import path

from . import views

app_name = 'livestream'

urlpatterns = [
    path('', views.live, name='live'),
]
