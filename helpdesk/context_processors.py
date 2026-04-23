# helpdesk/context_processors.py
from .auth_utils import get_user_role, is_staff_user, is_admin_user, get_user_profile

def user_role_context(request):
    context = {
        'user_role': None,
        'user_role_display': 'Guest',
        'is_staff_user': False,
        'is_admin_user': False,
        'user_profile': None,
    }
    
    if request.user.is_authenticated:
        role = get_user_role(request.user)
        role_display = {
            'admin': 'Administrator',
            'staff': 'Staff',
            'member': 'Member',
            'guest': 'Guest'
        }.get(role, 'Guest')
        
        context.update({
            'user_role': role,
            'user_role_display': role_display,
            'is_staff_user': is_staff_user(request.user),
            'is_admin_user': is_admin_user(request.user),
            'user_profile': get_user_profile(request.user),
        })
    
    return context