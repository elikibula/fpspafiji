# helpdesk_patch.py
from django.conf import settings
from django.contrib.auth import get_user_model

def patch_helpdesk():
    User = get_user_model()
    
    # Import helpdesk models after setting the user model
    from helpdesk import models
    
    # Update the user foreign key references
    for model_name in ['Ticket', 'FollowUp', 'PreSetReply', 'EscalationExclusion', 'EmailTemplate', 'KBCategory', 'KBItem', 'SavedSearch', 'UserSettings', 'IgnoreEmail']:
        model = getattr(models, model_name, None)
        if model and hasattr(model, 'user'):
            model.user.field.remote_field.model = User

# Apply the patch
patch_helpdesk()