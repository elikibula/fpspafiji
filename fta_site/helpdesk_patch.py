# fta_site/helpdesk_patch.py
from django.contrib.auth import get_user_model

def comprehensive_helpdesk_patch():
    """
    Comprehensive patch for helpdesk to work with custom user models
    """
    try:
        User = get_user_model()
        
        # Patch forms
        from helpdesk import forms
        
        # Patch StaffTicketCreationForm
        original_staff_init = forms.StaffTicketCreationForm.__init__
        def new_staff_init(self, *args, **kwargs):
            original_staff_init(self, *args, **kwargs)
            if hasattr(self, 'fields') and 'assigned_to' in self.fields:
                self.fields['assigned_to'].queryset = User.objects.filter(is_staff=True)
        forms.StaffTicketCreationForm.__init__ = new_staff_init
        
        # Patch other forms that might use User model
        if hasattr(forms, 'TicketForm'):
            original_ticket_init = forms.TicketForm.__init__
            def new_ticket_init(self, *args, **kwargs):
                original_ticket_init(self, *args, **kwargs)
                # Add any other field patches for TicketForm if needed
            forms.TicketForm.__init__ = new_ticket_init
        
        print("Comprehensive helpdesk patch applied successfully")
        return True
        
    except Exception as e:
        print(f"Error in comprehensive helpdesk patch: {e}")
        return False

# Apply the patch immediately
comprehensive_helpdesk_patch()