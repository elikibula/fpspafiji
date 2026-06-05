# staff_members/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.db.utils import OperationalError, ProgrammingError
from .models import StaffMember

def staff_team(request):
    """Display all active staff members"""
    try:
        staff_members = list(StaffMember.objects.filter(is_active=True))
    except (OperationalError, ProgrammingError):
        staff_members = []
    
    context = {
        'staff_members': staff_members,
        'page_title': 'Our Leadership Team',
    }
    return render(request, 'staff_members/team.html', context)

def member_detail(request, pk):
    """Individual staff member detail page"""
    try:
        member = get_object_or_404(StaffMember, pk=pk, is_active=True)
    except (OperationalError, ProgrammingError):
        return redirect('staff_members:team')
    
    context = {
        'member': member,
        'page_title': f'{member.display_name} - {member.position}',
    }
    return render(request, 'staff_members/member_detail.html', context)
