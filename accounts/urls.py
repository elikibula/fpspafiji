from django.urls import path
from . import views
from accounts.dashboard_api import members_trend, tickets_trend

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('complete-profile/', views.registration_entry, name='complete_member_profile'),
    path('pending-approval/', views.pending_approval, name='pending_approval'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('member-dashboard/', views.member_dashboard, name='member_dashboard'),
    path('api/dashboard/members-trend/', members_trend, name='api_members_trend'),
    path('api/dashboard/tickets-trend/', tickets_trend, name='api_tickets_trend'),
    path('api/inprogress/trend/', views.inprogress_trend, name='api_inprogress_trend'),
    path('staff-dashboard/approve-member/<int:member_id>/', views.approve_member, name='approve_member'),
    path('staff-dashboard/reject-member/<int:member_id>/', views.reject_member, name='reject_member'),
    
]
