# helpdesk/views_member.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import HelpdeskTicket
from .auth_utils import get_user_role

@login_required
def member_dashboard(request):
    """Member-specific dashboard"""
    # Verify user is actually a member
    role = get_user_role(request.user)
    if role not in ['member', 'guest']:
        messages.warning(request, "Redirected to member dashboard.")
    
    # Get member's tickets
    user_tickets = HelpdeskTicket.objects.filter(created_by=request.user)
    
    # Statistics
    total_tickets = user_tickets.count()
    open_tickets = user_tickets.filter(status__is_resolved=False).count()
    resolved_tickets = user_tickets.filter(status__is_resolved=True).count()
    
    # Recent tickets
    recent_tickets = user_tickets.order_by('-created_at')[:5]
    
    context = {
        'page_title': 'Member Dashboard',
        'total_tickets': total_tickets,
        'open_tickets': open_tickets,
        'resolved_tickets': resolved_tickets,
        'recent_tickets': recent_tickets,
    }
    
    return render(request, 'helpdesk/member/dashboard.html', context)