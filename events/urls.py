from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    # Dashboard URLs - MUST COME BEFORE DETAIL URL
    path('dashboard/', views.events_dashboard, name='events_dashboard'),
    path('analytics/', views.events_analytics, name='events_analytics'),
    path('admin/list/', views.events_admin_list, name='events_admin_list'),
    
    # Your existing URLs
    path('', views.list_events, name='list'),
    path('create/', views.create_event, name='create_event'),
    path('calendar/events.json', views.calendar_events_json, name='calendar_events'),
    
    # This should be LAST - it will catch any slug
    path('<slug:slug>/', views.event_detail, name='detail'),
    path('<slug:slug>/edit/', views.update_event, name='update_event'),
    path('<slug:slug>/delete/', views.delete_event, name='delete_event'),
]