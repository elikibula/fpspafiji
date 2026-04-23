# helpdesk/forms.py
from django import forms
from django.contrib.auth import get_user_model
from .models import (
    HelpdeskTicket,
    TicketResponse,
    TicketCategory,
    TicketPriority,
    TicketStatus,
)


class TicketCreationForm(forms.ModelForm):
    """Main ticket creation form - used by members"""
    class Meta:
        model = HelpdeskTicket
        fields = ['title', 'description', 'category', 'priority', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#800000]',
                'placeholder': 'Brief description of your issue'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#800000]',
                'placeholder': 'Please provide detailed information about your issue...',
                'rows': 6
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#800000]'
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#800000]'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#800000]'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active categories (defensive: ensure field exists)
        if 'category' in self.fields:
            self.fields['category'].queryset = TicketCategory.objects.filter(is_active=True)
        # Set default priority to Medium
        if 'priority' in self.fields:
            try:
                medium_priority = TicketPriority.objects.get(name='Medium')
                self.fields['priority'].initial = medium_priority
            except TicketPriority.DoesNotExist:
                pass


class StaffTicketCreationForm(forms.ModelForm):
    """Form for staff to create tickets from various sources"""
    class Meta:
        model = HelpdeskTicket
        fields = ['title', 'category', 'priority', 'description', 'attachment', 'source', 'assigned_to']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Brief description of the issue'
            }),
            'description': forms.Textarea(attrs={
                'rows': 6,
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Detailed information about the issue...'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'source': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            })
        }

    def __init__(self, *args, **kwargs):
        # pop request if provided by views (kept as in original)
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        User = get_user_model()
        # Limit assignment to staff users only (defensive: ensure field exists)
        if 'assigned_to' in self.fields:
            try:
                self.fields['assigned_to'].queryset = User.objects.filter(is_staff=True)
            except Exception:
                # fall back to no queryset if something unexpected happens
                self.fields['assigned_to'].queryset = User.objects.none()
            # provide an empty label if the field is a ModelChoiceField
            if hasattr(self.fields['assigned_to'], 'empty_label'):
                self.fields['assigned_to'].empty_label = "Unassigned"

        # Only show active categories
        if 'category' in self.fields:
            self.fields['category'].queryset = TicketCategory.objects.filter(is_active=True)

        # Optionally set default status to Open if status is part of the form (kept defensive)
        if 'status' in self.fields:
            try:
                open_status = TicketStatus.objects.get(name='Open')
                self.fields['status'].initial = open_status
            except TicketStatus.DoesNotExist:
                pass


class StaffTicketUpdateForm(forms.ModelForm):
    """Form for staff to update ticket details"""
    class Meta:
        model = HelpdeskTicket
        fields = ['status', 'priority', 'assigned_to', 'category']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        User = get_user_model()
        # Limit assignment to staff users only (defensive)
        if 'assigned_to' in self.fields:
            try:
                self.fields['assigned_to'].queryset = User.objects.filter(is_staff=True)
            except Exception:
                self.fields['assigned_to'].queryset = User.objects.none()
            if hasattr(self.fields['assigned_to'], 'empty_label'):
                self.fields['assigned_to'].empty_label = "Unassigned"


class TicketResponseForm(forms.ModelForm):
    """Enhanced response form with visibility options"""
    class Meta:
        model = TicketResponse
        fields = ['message', 'attachment', 'visibility', 'response_type']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Type your response here...'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'visibility': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'response_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            })
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Set default values (defensive: only if fields exist)
        if 'visibility' in self.fields:
            self.fields['visibility'].initial = 'public'
        if 'response_type' in self.fields:
            self.fields['response_type'].initial = 'reply'

        # Staff can choose visibility, members can only send public messages
        if self.user and not self.user.is_staff:
            if 'visibility' in self.fields:
                self.fields['visibility'].widget = forms.HiddenInput()
            if 'response_type' in self.fields:
                self.fields['response_type'].widget = forms.HiddenInput()
