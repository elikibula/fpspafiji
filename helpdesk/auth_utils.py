# helpdesk/auth_utils.py
from membership.models import Member
from staff_members.models import StaffMember
from django.contrib.auth import get_user_model
User = get_user_model()

def get_user_role(user):
    """
    Determine user role based on your existing models
    Priority: Admin -> Staff -> Member
    """
    if not user.is_authenticated:
        return None
    
    # Check if user is admin (Django superuser or staff)
    if user.is_superuser or user.is_staff:
        return 'admin'
    
    # Check if user is staff member
    try:
        staff_member = StaffMember.objects.get(user=user, is_active=True)
        return 'staff'
    except StaffMember.DoesNotExist:
        pass
    
    # Check if user is member
    try:
        member = Member.objects.get(user=user)
        if member.membership_status == 'active':
            return 'member'
    except Member.DoesNotExist:
        pass
    
    return 'guest'  # Authenticated but no specific role

def is_staff_user(user):
    """Check if user has staff privileges"""
    role = get_user_role(user)
    return role in ['staff', 'admin']

def is_admin_user(user):
    """Check if user has admin privileges"""
    return user.is_superuser or user.is_staff

def get_user_profile(user):
    """Get the user's profile based on their role"""
    role = get_user_role(user)
    
    if role == 'staff':
        try:
            return StaffMember.objects.get(user=user, is_active=True)
        except StaffMember.DoesNotExist:
            return None
    elif role == 'member':
        try:
            return Member.objects.get(user=user)
        except Member.DoesNotExist:
            return None
    
    return None