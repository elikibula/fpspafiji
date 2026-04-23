# helpdesk_monkeypatch.py
from django.apps import apps
from django.contrib.auth import get_user_model

def patch_helpdesk():
    """Monkey patch helpdesk to use custom user model"""
    User = get_user_model()
    
    # Import helpdesk models after setting user model
    from helpdesk import models, forms
    
    # Patch the models to use custom user
    for model_name in ['Ticket', 'FollowUp', 'PreSetReply', 'EscalationExclusion', 
                      'EmailTemplate', 'KBCategory', 'KBItem', 'SavedSearch', 
                      'UserSettings', 'IgnoreEmail']:
        model = getattr(models, model_name, None)
        if model and hasattr(model, 'user'):
            model.user.field.remote_field.model = User
    
    # Patch the forms to use custom user
    if hasattr(forms, 'StaffTicketCreationForm'):
        original_init = forms.StaffTicketCreationForm.__init__
        
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            if 'assigned_to' in self.fields:
                self.fields['assigned_to'].queryset = User.objects.filter(is_staff=True)
        
        forms.StaffTicketCreationForm.__init__ = new_init

# Apply the patch when Django starts
patch_helpdesk()