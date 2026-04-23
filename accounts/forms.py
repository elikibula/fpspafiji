from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from .models import CustomUser
from membership.models import Member

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    # Only allow admin to set roles during registration, or restrict to member only
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove role field from public registration or set default to 'member'
        if 'role' in self.fields:
            self.fields['role'].initial = 'member'
            # Optionally hide the role field for non-staff users
            # self.fields['role'].widget = forms.HiddenInput()
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.role = 'member'  # Default role for public registration
        if commit:
            user.save()
        return user

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'profile_picture')

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label='Username or Email')

class MemberRegistrationForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = [
            'first_name', 'last_name', 'tpf_number', 'phone_number', 'residing_address',
            'category', 'area', 'branch', 'school', 'position', 'start_year',
            'profile_photo', 'id_document'
        ]
        widgets = {
            'residing_address': forms.Textarea(attrs={'rows': 3}),
            'start_year': forms.NumberInput(attrs={'min': 1900, 'max': 2024}),
        }