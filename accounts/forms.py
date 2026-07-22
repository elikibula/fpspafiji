from datetime import date
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from .models import CustomUser
from membership.models import Member
from reps.models import District

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'role' in self.fields:
            self.fields['role'].initial = 'member'
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.role = 'member'
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dob'].label = 'Date of Birth'
        self.fields['district'].label = 'District'
        self.fields['ftra_register_num'].label = 'FTRA Registration Number'
        self.fields['school'].label = 'School'
        self.fields['start_year'].label = 'Starting Year as Head Teacher'

        self.fields['district'].empty_label = 'Select District'
        self.fields['district'].queryset = District.objects.filter(is_active=True).order_by('order', 'name')

        for field_name in [
            'first_name', 'last_name', 'dob', 'tpf_number', 'ftra_register_num',
            'phone_number', 'residing_address', 'category', 'district',
            'school', 'position', 'start_year'
        ]:
            self.fields[field_name].required = True

    class Meta:
        model = Member
        fields = [
            'first_name', 'last_name', 'dob', 'tpf_number', 'ftra_register_num',
            'phone_number', 'residing_address', 'category', 'district',
            'school', 'position', 'start_year',
            'profile_photo', 'id_document'
        ]
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
            'residing_address': forms.Textarea(attrs={'rows': 3}),
            'school': forms.TextInput(attrs={'placeholder': 'Enter your school name'}),
            'start_year': forms.NumberInput(attrs={'min': 1900, 'max': date.today().year}),
        }
