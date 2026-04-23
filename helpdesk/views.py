# helpdesk/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import *
from .forms import TicketCreationForm, TicketResponseForm
# helpdesk/views.py (inside create_ticket view)
from membership.models import Member   # or wherever Member lives
from django.contrib.auth import get_user_model
User = get_user_model()
# make sure these imports exist in the module
from .forms import TicketCreationForm
from .models import HelpdeskTicket, TicketStream, TicketStatus

@login_required
def create_ticket(request):
    """Create a new support ticket - MEMBER STREAM"""
    if request.method == 'POST':
        form = TicketCreationForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            # created_by should be the authenticated CustomUser
            ticket.created_by = request.user

            # Set to member stream (defensive - use .first() rather than get to avoid exception)
            member_stream = TicketStream.objects.filter(slug='member').first()
            if member_stream:
                ticket.stream = member_stream

            # Set default status to Open (defensive)
            open_status = TicketStatus.objects.filter(name='Open').first()
            if open_status:
                ticket.status = open_status

            # IMPORTANT: HelpdeskTicket.member expects a CustomUser instance
            # Do NOT assign a Member model instance. Use the authenticated user (CustomUser).
            # If you need the Member record, access it via request.user.member_profile (related_name).
            ticket.member = request.user

            # If you need to access the Member profile for additional logic:
            member_profile = getattr(request.user, 'member_profile', None)
            # e.g. if you wanted to use member_profile.some_field to set other ticket attributes,
            # do it here — but do NOT set ticket.member = member_profile

            ticket.save()
            form.save_m2m()  # if form has m2m fields

            messages.success(
                request,
                f'Ticket created successfully! Your ticket number is: {ticket.ticket_number}'
            )
            return redirect('helpdesk:ticket_detail', ticket_number=ticket.ticket_number)
    else:
        form = TicketCreationForm()

    context = {
        'form': form,
        'page_title': 'Create Support Ticket'
    }
    return render(request, 'helpdesk/create_helpdesk.html', context)




def helpdesk_dashboard(request):
    """Main helpdesk dashboard with FAQs and ticket creation"""
    faq_categories = FAQCategory.objects.filter(is_active=True).prefetch_related('faq_set')
    
    if request.user.is_authenticated:
        user_tickets = HelpdeskTicket.objects.filter(created_by=request.user)[:5]
    else:
        user_tickets = []
    
    context = {
        'faq_categories': faq_categories,
        'user_tickets': user_tickets,
        'page_title': 'FTA Helpdesk - Get Support'
    }
    return render(request, 'helpdesk/dashboard.html', context)


@login_required
def ticket_list(request):
    """List user's tickets"""
    tickets = HelpdeskTicket.objects.filter(created_by=request.user).select_related(
        'category', 'priority', 'status'
    )
    
    # Filtering
    status_filter = request.GET.get('status')
    if status_filter:
        tickets = tickets.filter(status__name=status_filter)
    
    # Pagination
    paginator = Paginator(tickets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'page_title': 'My Support Tickets'
    }
    return render(request, 'helpdesk/ticket_list.html', context)

@login_required
def ticket_detail(request, ticket_number):
    """View ticket details and responses - MEMBER VIEW"""
    ticket = get_object_or_404(HelpdeskTicket, ticket_number=ticket_number)
    
    # Ensure user can only view their own tickets (unless staff)
    if not request.user.is_staff and ticket.created_by != request.user:
        messages.error(request, 'You do not have permission to view this ticket.')
        return redirect('helpdesk:ticket_list')
    
    if request.method == 'POST':
        response_form = TicketResponseForm(request.POST, request.FILES, user=request.user)
        if response_form.is_valid():
            response = response_form.save(commit=False)
            response.ticket = ticket
            response.author = request.user
            # Members can only send public replies
            response.visibility = 'public'
            response.response_type = 'reply'
            response.save()
            
            # Update ticket timestamp
            ticket.save()
            
            messages.success(request, 'Response added successfully!')
            return redirect('helpdesk:ticket_detail', ticket_number=ticket.ticket_number)
    else:
        response_form = TicketResponseForm(user=request.user)
    
    # Members can only see public responses and their own
    responses = ticket.responses.filter(
        Q(visibility='public') | Q(author=request.user)
    ).select_related('author').order_by('created_at')
    
    context = {
        'ticket': ticket,
        'response_form': response_form,
        'responses': responses,
        'page_title': f'Ticket {ticket.ticket_number}'
    }
    return render(request, 'helpdesk/ticket_detail.html', context)


def faq_list(request):
    """List all FAQs"""
    faq_categories = FAQCategory.objects.filter(is_active=True).prefetch_related(
        'faq_set'
    ).filter(faq__is_active=True).distinct()
    
    context = {
        'faq_categories': faq_categories,
        'page_title': 'Frequently Asked Questions'
    }
    return render(request, 'helpdesk/faq_list.html', context)