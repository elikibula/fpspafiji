# helpdesk/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, views_staff, views_auth, views_member

app_name = 'helpdesk'

urlpatterns = [
    # Authentication URLs
    path('login/', views_auth.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('redirect/', views_auth.role_redirect, name='role_redirect'),

    # Public/Member URLs
    path('', views.helpdesk_dashboard, name='helpdesk_dashboard'),
    path('create/', views.create_ticket, name='create_ticket'),
    path('tickets/', views.ticket_list, name='ticket_list'),
    path('tickets/<str:ticket_number>/', views.ticket_detail, name='ticket_detail'),
    path('faqs/', views.faq_list, name='faq_list'),


    # Member Dashboard
    path('member/dashboard/', views_member.member_dashboard, name='member_dashboard'),

    # Staff URLs
    path('staff_tickets/', views_staff.staff_dashboard, name='staff_dashboard'),
    path('staff/tickets/', views_staff.staff_ticket_list, name='staff_ticket_list'),
    path('staff/tickets/create/', views_staff.staff_create_ticket, name='staff_create_ticket'),
    path('staff/tickets/<str:ticket_number>/', views_staff.staff_ticket_detail, name='staff_ticket_detail'),
    path('staff/my-tickets/', views_staff.staff_my_tickets, name='staff_my_tickets'),

]