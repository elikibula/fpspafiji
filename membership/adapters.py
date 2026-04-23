# membership/adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_username
from django.contrib.auth.models import User
from .models import Member
from django.urls import reverse
from django.http import HttpResponseRedirect

class CustomAccountAdapter(DefaultAccountAdapter):
    
    def save_user(self, request, user, form, commit=True):
        """
        Saves a new `User` instance using information provided in the signup form.
        """
        user = super().save_user(request, user, form, commit=False)
        user.username = user.email  # Set username to email
        if commit:
            user.save()
        return user
    
    def new_user(self, request):
        """
        Instantiate a new User instance.
        """
        user = super().new_user(request)
        user.username = user.email  # Ensure username is set to email
        return user
    

    def get_signup_redirect_url(self, request):
        # This ensures after social signup they go to your custom form
        return reverse('membership_register')