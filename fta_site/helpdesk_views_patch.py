# helpdesk_views_patch.py
from helpdesk.views_staff import staff_create_ticket
from helpdesk.decorators import is_helpdesk_staff
from django.contrib.auth.decorators import user_passes_test
from .helpdesk_forms import CustomStaffTicketCreationForm

@user_passes_test(is_helpdesk_staff)
def patched_staff_create_ticket(request):
    # Import here to avoid circular imports
    from helpdesk.views_staff import staff_create_ticket
    # Monkey patch the form used in the original function
    import helpdesk.views_staff
    helpdesk.views_staff.StaffTicketCreationForm = CustomStaffTicketCreationForm
    return staff_create_ticket(request)

# Replace the original view
import helpdesk.urls
# You'll need to update the URL pattern to use this patched view