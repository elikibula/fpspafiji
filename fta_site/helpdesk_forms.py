# helpdesk_forms.py
from django import forms
from django.contrib.auth import get_user_model
from helpdesk.forms import StaffTicketCreationForm as BaseStaffTicketCreationForm

User = get_user_model()

class CustomStaffTicketCreationForm(BaseStaffTicketCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use custom user model for assigned_to field
        self.fields['assigned_to'].queryset = User.objects.filter(is_staff=True)