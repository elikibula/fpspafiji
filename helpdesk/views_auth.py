# helpdesk/views_auth.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm
from .auth_utils import get_user_role

def role_redirect(request):
    """
    Redirect users to appropriate dashboard based on their role
    """
    if not request.user.is_authenticated:
        return redirect('helpdesk:login')
    
    role = get_user_role(request.user)
    
    if role == 'admin':
        messages.success(request, f"Welcome back, Administrator!")
        return redirect('helpdesk:staff_dashboard')
    elif role == 'staff':
        messages.success(request, f"Welcome back, Staff Member!")
        return redirect('helpdesk:staff_dashboard')
    elif role == 'member':
        messages.success(request, f"Welcome back, Member!")
        return redirect('helpdesk:member_dashboard')
    else:
        # Authenticated but no specific role - redirect to public dashboard
        messages.info(request, "Welcome! Please complete your profile.")
        return redirect('helpdesk:helpdesk_dashboard')

class CustomLoginView(LoginView):
    template_name = 'helpdesk/auth/login.html'
    
    def form_valid(self, form):
        """Security check complete. Log the user in."""
        user = form.get_user()
        
        # Check if user is active
        if not user.is_active:
            messages.error(self.request, 'Your account has been deactivated. Please contact support.')
            return self.form_invalid(form)
        
        login(self.request, user)
        
        # Get user role for personalized message
        role = get_user_role(user)
        role_display = {
            'admin': 'Administrator',
            'staff': 'Staff Member', 
            'member': 'Member'
        }.get(role, 'User')
        
        messages.success(self.request, f"Welcome back, {role_display}!")
        return redirect('helpdesk:role_redirect')