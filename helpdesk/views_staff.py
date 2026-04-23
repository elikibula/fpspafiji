# helpdesk/views_staff.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from .models import HelpdeskTicket, TicketStream, TicketStatus, TicketResponse
from .forms import StaffTicketCreationForm, StaffTicketUpdateForm, TicketResponseForm

def staff_required(view_func):
    """Decorator to ensure user is staff"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            messages.error(request, "Staff access required.")
            return redirect('helpdesk:helpdesk_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@staff_required
def staff_dashboard(request):
    """Staff dashboard with overview of all tickets"""
    # Get ticket statistics
    total_tickets = HelpdeskTicket.objects.count()
    open_tickets = HelpdeskTicket.objects.filter(status__is_resolved=False).count()
    
    # Overdue tickets (no first response past due date)
    overdue_tickets = HelpdeskTicket.objects.filter(
        due_date__lt=timezone.now(),
        first_response_at__isnull=True,
        status__is_resolved=False
    ).count()
    
    # Tickets assigned to current staff
    my_tickets = HelpdeskTicket.objects.filter(
        assigned_to=request.user,
        status__is_resolved=False
    ).count()
    
    # Recent tickets
    recent_tickets = HelpdeskTicket.objects.select_related(
        'category', 'priority', 'status', 'assigned_to', 'created_by', 'stream'
    ).order_by('-created_at')[:10]
    
    # Ticket counts by status
    status_counts = HelpdeskTicket.objects.values(
        'status__name', 'status__color'
    ).annotate(count=Count('id'))
    
    context = {
        'total_tickets': total_tickets,
        'open_tickets': open_tickets,
        'overdue_tickets': overdue_tickets,
        'my_tickets': my_tickets,
        'recent_tickets': recent_tickets,
        'status_counts': status_counts,
        'page_title': 'Staff Dashboard'
    }
    return render(request, 'helpdesk/staff/dashboard.html', context)

@login_required
@staff_required
def staff_ticket_list(request):
    """Staff view of all tickets with filtering"""
    tickets = HelpdeskTicket.objects.select_related(
        'category', 'priority', 'status', 'assigned_to', 'created_by', 'stream'
    ).order_by('-created_at')
    
    # Filters
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    stream_filter = request.GET.get('stream')
    assigned_filter = request.GET.get('assigned')
    
    if status_filter:
        tickets = tickets.filter(status__name=status_filter)
    if priority_filter:
        tickets = tickets.filter(priority__name=priority_filter)
    if stream_filter:
        tickets = tickets.filter(stream__slug=stream_filter)
    if assigned_filter == 'me':
        tickets = tickets.filter(assigned_to=request.user)
    elif assigned_filter == 'unassigned':
        tickets = tickets.filter(assigned_to__isnull=True)
    
    # Pagination
    paginator = Paginator(tickets, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Available filters for template
    from .models import TicketStatus, TicketPriority, TicketStream
    statuses = TicketStatus.objects.all()
    priorities = TicketPriority.objects.all()
    streams = TicketStream.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'statuses': statuses,
        'priorities': priorities,
        'streams': streams,
        'filters': {
            'status': status_filter,
            'priority': priority_filter,
            'stream': stream_filter,
            'assigned': assigned_filter,
        },
        'page_title': 'All Tickets'
    }
    return render(request, 'helpdesk/staff/ticket_list.html', context)

@login_required
@staff_required
def staff_create_ticket(request):
    """Staff create ticket from various sources"""
    if request.method == 'POST':
        form = StaffTicketCreationForm(request.POST, request.FILES, request=request)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            
            # Set default status to Open
            try:
                open_status = TicketStatus.objects.get(name='Open')
                ticket.status = open_status
            except TicketStatus.DoesNotExist:
                pass
            
            # Set stream based on source
            if ticket.source in ['walkin', 'phone']:
                try:
                    reception_stream = TicketStream.objects.get(slug='reception')
                    ticket.stream = reception_stream
                except TicketStream.DoesNotExist:
                    pass
            else:
                try:
                    staff_stream = TicketStream.objects.get(slug='staff')
                    ticket.stream = staff_stream
                except TicketStream.DoesNotExist:
                    pass
            
            ticket.save()
            
            messages.success(request, f'Ticket created successfully! Ticket number: {ticket.ticket_number}')
            return redirect('helpdesk:staff_ticket_detail', ticket_number=ticket.ticket_number)
    else:
        form = StaffTicketCreationForm(request=request)
    
    context = {
        'form': form,
        'page_title': 'Create Ticket (Staff)'
    }
    return render(request, 'helpdesk/staff/ticket_create.html', context)

@login_required
@staff_required
def staff_ticket_detail(request, ticket_number):
    """Staff view of ticket details with management options"""
    ticket = get_object_or_404(
        HelpdeskTicket.objects.select_related(
            'category', 'priority', 'status', 'assigned_to', 'created_by', 'stream'
        ), 
        ticket_number=ticket_number
    )
    
    if request.method == 'POST':
        if 'update_ticket' in request.POST:
            update_form = StaffTicketUpdateForm(request.POST, instance=ticket)
            response_form = TicketResponseForm(user=request.user)
            
            if update_form.is_valid():
                old_assigned_to = ticket.assigned_to
                update_form.save()
                
                # Create system note about assignment changes
                if 'assigned_to' in update_form.changed_data:
                    new_assignee = ticket.assigned_to
                    if old_assigned_to and new_assignee:
                        note = f"Ticket reassigned from {old_assigned_to.get_full_name() or old_assigned_to.username} to {new_assignee.get_full_name() or new_assignee.username}"
                    elif new_assignee:
                        note = f"Ticket assigned to {new_assignee.get_full_name() or new_assignee.username}"
                    else:
                        note = "Ticket unassigned"
                    
                    TicketResponse.objects.create(
                        ticket=ticket,
                        author=request.user,
                        message=note,
                        response_type='system',
                        visibility='internal'
                    )
                
                messages.success(request, 'Ticket updated successfully!')
                return redirect('helpdesk:staff_ticket_detail', ticket_number=ticket.ticket_number)
        
        elif 'add_response' in request.POST:
            update_form = StaffTicketUpdateForm(instance=ticket)
            response_form = TicketResponseForm(request.POST, request.FILES, user=request.user)
            
            if response_form.is_valid():
                response = response_form.save(commit=False)
                response.ticket = ticket
                response.author = request.user
                
                # Set first response time if this is the first public response
                if not ticket.first_response_at and response.visibility == 'public':
                    ticket.first_response_at = timezone.now()
                    ticket.save()
                
                response.save()
                messages.success(request, 'Response added successfully!')
                return redirect('helpdesk:staff_ticket_detail', ticket_number=ticket.ticket_number)
    else:
        update_form = StaffTicketUpdateForm(instance=ticket)
        response_form = TicketResponseForm(user=request.user)
    
    # Get all responses (staff can see everything)
    responses = ticket.responses.select_related('author').order_by('created_at')
    
    context = {
        'ticket': ticket,
        'update_form': update_form,
        'response_form': response_form,
        'responses': responses,
        'page_title': f'Ticket {ticket.ticket_number}'
    }
    return render(request, 'helpdesk/staff/ticket_detail.html', context)

@login_required
@staff_required
def staff_my_tickets(request):
    """Tickets assigned to current staff member"""
    tickets = HelpdeskTicket.objects.filter(
        assigned_to=request.user
    ).select_related(
        'category', 'priority', 'status', 'created_by', 'stream'
    ).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        tickets = tickets.filter(status__name=status_filter)
    
    paginator = Paginator(tickets, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'page_title': 'My Assigned Tickets'
    }
    return render(request, 'helpdesk/staff/my_tickets.html', context)