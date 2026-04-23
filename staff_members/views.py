# staff_members/views.py
from django.shortcuts import render, get_object_or_404
from .models import StaffMember

def staff_team(request):
    """Display all active staff members"""
    staff_members = StaffMember.objects.filter(is_active=True)
    
    context = {
        'staff_members': staff_members,
        'page_title': 'Our Leadership Team',
    }
    return render(request, 'staff_members/team.html', context)

def member_detail(request, pk):
    """Individual staff member detail page"""
    member = get_object_or_404(StaffMember, pk=pk, is_active=True)
    
    context = {
        'member': member,
        'page_title': f'{member.display_name} - {member.position}',
    }
    return render(request, 'staff_members/member_detail.html', context)