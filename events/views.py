from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.utils.text import slugify
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib import messages
from datetime import timedelta
from .models import Event
from .forms import EventForm


def is_event_admin(user):
    """Return True for staff users or users with the change_event permission."""
    return user.is_staff or user.has_perm('events.change_event')


def list_events(request):
    """
    Render a paginated list of upcoming published events with RSVP counts.
    """

    now = timezone.now()

    # Query upcoming published events
    events_qs = (
        Event.objects.filter(status='published')
        .filter(
            Q(end__gte=now) |
            Q(end__isnull=True, start__gte=now) |
            Q(start__gte=now)
        )
             
        .order_by('start')
    )

    # Pagination
    per_page = 8
    paginator = Paginator(events_qs, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'events': page_obj,       # your template loops over 'events'
        'page_obj': page_obj,
    }
    return render(request, 'events/list.html', context)


def calendar_events_json(request):
    """
    FullCalendar JSON feed for published events.
    """
    events = Event.objects.filter(status='published').order_by('start')
    data = [
        {
            'title': e.title,
            'start': e.start.isoformat(),
            'end': e.end.isoformat() if e.end else None,
            'url': e.get_absolute_url(),
            'allDay': bool(e.all_day),
        }
        for e in events
    ]
    return JsonResponse(data, safe=False)


def event_detail(request, slug):
    """
    Display event details.
    """
    event = get_object_or_404(Event, slug=slug, status__in=['published', 'draft'])
    return render(request, 'events/detail.html', {'event': event})


@login_required
def create_event(request):
    """
    Create an event. Only allowed for event admins (staff or users with permission).
    """
    if not is_event_admin(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            # generate unique slug if missing
            if not event.slug:
                base = slugify(event.title)[:50]
                slug = base
                counter = 0
                while Event.objects.filter(slug=slug).exists():
                    counter += 1
                    slug = f"{base}-{counter}"
                event.slug = slug
            event.created_by = request.user
            event.organizer = request.user
            event.save()
            return redirect(event.get_absolute_url())
    else:
        form = EventForm()

    return render(request, 'events/form.html', {'form': form, 'create': True})


@login_required
def update_event(request, slug):
    """
    Update an existing event (admins only).
    """
    event = get_object_or_404(Event, slug=slug)
    if not is_event_admin(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            return redirect(event.get_absolute_url())
    else:
        form = EventForm(instance=event)

    return render(request, 'events/form.html', {'form': form, 'event': event})


@login_required
def delete_event(request, slug):
    """
    Delete an event (admins only). Confirms via POST.
    """
    event = get_object_or_404(Event, slug=slug)
    if not is_event_admin(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        event.delete()
        return redirect('events:list')

    return render(request, 'events/confirm_delete.html', {'event': event})



@login_required
def events_dashboard(request):
    """
    Events management dashboard for staff members
    """
    if not is_event_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('member_dashboard')
    
    now = timezone.now()
    
    # Statistics
    total_events = Event.objects.count()
    published_events = Event.objects.filter(status='published').count()
    draft_events = Event.objects.filter(status='draft').count()
    
    # Upcoming events (next 30 days)
    upcoming_events = Event.objects.filter(
        status='published',
        start__gte=now,
        start__lte=now + timedelta(days=30)
    ).count()
    
    # Past events
    past_events = Event.objects.filter(
        status='published',
        start__lt=now
    ).count()
    
    # Recent events (last 7 days)
    recent_events = Event.objects.filter(
        created_at__gte=now - timedelta(days=7)
    ).count()
    
    # Events by status for chart
    events_by_status = Event.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Upcoming events list for quick access
    upcoming_events_list = Event.objects.filter(
        status='published',
        start__gte=now
    ).order_by('start')[:5]
    
    # Recent draft events
    recent_drafts = Event.objects.filter(
        status='draft'
    ).order_by('-created_at')[:5]
    
    # Events needing attention (drafts or events without end date)
    events_needing_attention = Event.objects.filter(
        Q(status='draft') | Q(end__isnull=True)
    ).count()
    
    context = {
        'total_events': total_events,
        'published_events': published_events,
        'draft_events': draft_events,
        'upcoming_events': upcoming_events,
        'past_events': past_events,
        'recent_events': recent_events,
        'events_by_status': list(events_by_status),
        'upcoming_events_list': upcoming_events_list,
        'recent_drafts': recent_drafts,
        'events_needing_attention': events_needing_attention,
        'now': now,
    }
    return render(request, 'events/dashboard.html', context)

@login_required
def events_analytics(request):
    """
    Detailed analytics for events
    """
    if not is_event_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('member_dashboard')
    
    now = timezone.now()
    
    # Time-based analytics
    last_30_days = now - timedelta(days=30)
    
    # Events created in last 30 days
    recent_events_trend = Event.objects.filter(
        created_at__gte=last_30_days
    ).extra({
        'date': "date(created_at)"
    }).values('date').annotate(count=Count('id')).order_by('date')
    
    # Events by month
    events_by_month = Event.objects.extra({
        'month': "EXTRACT(month FROM start)",
        'year': "EXTRACT(year FROM start)"
    }).values('month', 'year').annotate(count=Count('id')).order_by('-year', '-month')
    
    # Top organizers
    from django.contrib.auth import get_user_model
    User = get_user_model()
    top_organizers = User.objects.annotate(
        event_count=Count('created_events')
    ).filter(event_count__gt=0).order_by('-event_count')[:10]
    
    # Events without end date
    events_without_end = Event.objects.filter(end__isnull=True).count()
    
    # All-day events count
    all_day_events = Event.objects.filter(all_day=True).count()
    
    # Events with capacity set
    events_with_capacity = Event.objects.exclude(capacity__isnull=True).count()
    
    context = {
        'recent_events_trend': list(recent_events_trend),
        'events_by_month': list(events_by_month),
        'top_organizers': top_organizers,
        'events_without_end': events_without_end,
        'all_day_events': all_day_events,
        'events_with_capacity': events_with_capacity,
        'last_30_days': last_30_days,
    }
    return render(request, 'events/analytics.html', context)

@login_required
def events_admin_list(request):
    """
    Admin list view for managing all events
    """
    if not is_event_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('member_dashboard')
    
    events = Event.objects.all().order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter in ['published', 'draft']:
        events = events.filter(status=status_filter)
    
    context = {
        'events': events,
        'status_filter': status_filter,
    }
    return render(request, 'events/admin_list.html', context)