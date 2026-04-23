# staff_members/urls.py
from django.urls import path
from . import views

app_name = 'staff_members'

urlpatterns = [
    path('', views.staff_team, name='team'),
    path('member/<int:pk>/', views.member_detail, name='member_detail'),
]