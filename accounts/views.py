from django.db import models
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db import IntegrityError
import logging
from .forms import MemberRegistrationForm, CustomUserCreationForm, CustomAuthenticationForm
from membership.models import Member, School
from django.contrib.auth import authenticate, login, logout
# Calculate statistics
from membership.models import Member, MemberCategory, School
from helpdesk.models import HelpdeskTicket, TicketStatus, TicketPriority
from django.utils import timezone
from datetime import timedelta
# Import models from other apps
from news.models import News
from events.models import Event
from documents.models import Document
from training.models import Course, CourseSchedule, Enrollment
from django.http import JsonResponse
from django.db.models import Q




# Get logger
logger = logging.getLogger(__name__)

def _auth_user_has_id(user_id):
    """
    Check if the user exists in the auth_user table.
    This is a safety check for database constraint issues.
    """
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.filter(id=user_id).exists()
    except Exception as e:
        logger.error(f"Error checking auth user: {e}")
        return False

@login_required
def complete_member_profile(request):
    user = request.user

    # Check if user already has a complete profile
    try:
        existing_member = Member.objects.get(user=user)
        messages.info(request, "Your member profile is already complete.")
        # Redirect based on role
        if user.role in ['admin', 'staff']:
            return redirect("staff_dashboard")
        else:
            return redirect("member_dashboard")
    except Member.DoesNotExist:
        existing_member = None

    if request.method == 'POST':
        form = MemberRegistrationForm(request.POST, request.FILES, instance=existing_member)
        if form.is_valid():
            try:
                with transaction.atomic():
                    member_obj = form.save(commit=False)
                    member_obj.user = user
                    
                    # Set email if not provided
                    if not getattr(member_obj, "email", None):
                        member_obj.email = user.email
                    
                    # Save the member object
                    member_obj.save()
                    
                    # Update user fields
                    user.first_name = form.cleaned_data.get("first_name", user.first_name)
                    user.last_name = form.cleaned_data.get("last_name", user.last_name)
                    user.save()

                messages.success(request, "Member profile saved successfully!")
                
                # FIX: Redirect based on user role
                if user.role in ['admin', 'staff']:
                    return redirect("staff_dashboard")
                else:
                    return redirect("member_dashboard")

            except IntegrityError as exc:
                if "auth_user" in str(exc):
                    # Specific handling for the foreign key constraint issue
                    logger.error(f"Foreign key constraint issue: {exc}")
                    messages.error(
                        request,
                        "There's a database configuration issue. Please contact the administrator. "
                        "Error: Foreign key constraint points to wrong table."
                    )
                    # Provide a way to continue without the profile for now
                    messages.info(
                        request, 
                        "You can continue to use the site, but please contact support to fix your profile."
                    )
                    # FIX: Redirect based on role even with errors
                    if user.role in ['admin', 'staff']:
                        return redirect("staff_dashboard")
                    else:
                        return redirect("member_dashboard")
                else:
                    # Other integrity errors
                    logger.error(f"IntegrityError saving member profile: {exc}")
                    messages.error(
                        request,
                        "There was a database error saving your profile. Please try again."
                    )
            except Exception as exc:
                logger.error(f"Unexpected error saving member profile: {exc}")
                messages.error(
                    request,
                    "An unexpected error occurred. Please try again."
                )
        else:
            logger.error(f"Form errors: {form.errors}")
            messages.error(request, "Please correct the errors below.")
    else:
        form = MemberRegistrationForm(instance=existing_member)

    return render(request, "accounts/complete_member_profile.html", {"form": form})

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            
            # FIX: Redirect based on role immediately after registration
            if user.role in ['admin', 'staff']:
                return redirect('staff_dashboard')
            else:
                messages.info(request, 'Please complete your member profile.')
                return redirect('complete_member_profile')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


def custom_login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f'Welcome back, {username}!')
                
                # Redirect based on user role
                if user.role in ['admin', 'staff']:
                    return redirect('staff_dashboard')
                else:
                    return redirect('member_dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def custom_logout(request):
    logout(request)
    messages.info(request, 'You have been successfully logged out.')
    return redirect('home')

@login_required
def profile(request):
    context = {}
    if request.user.role == 'member':
        try:
            context['member'] = Member.objects.get(user=request.user)
        except Member.DoesNotExist:
            messages.warning(request, 'Please complete your member profile.')
            return redirect('complete_member_profile')
    return render(request, 'accounts/profile.html', context)

# Dashboard views
@login_required
def dashboard(request):
    if request.user.role in ['admin', 'staff']:
        return redirect('staff_dashboard')
    else:
        return redirect('member_dashboard')

@login_required
def staff_dashboard(request):
    if request.user.role not in ['admin', 'staff']:
        messages.error(request, 'Access denied.')
        return redirect('member_dashboard')

    # Member statistics
    total_members = Member.objects.count()
    active_members = Member.objects.filter(membership_status='active').count()
    pending_approvals = Member.objects.filter(membership_status='pending').count()

    # Helpdesk statistics
    total_tickets = HelpdeskTicket.objects.count()

    # Try to get active tickets (existing logic kept)
    try:
        active_tickets = HelpdeskTicket.objects.filter(
            status__is_resolved=False
        ).count()
    except Exception:
        try:
            active_tickets = HelpdeskTicket.objects.exclude(
                status__name__in=['Resolved', 'Closed', 'Completed']
            ).count()
        except Exception:
            active_tickets = HelpdeskTicket.objects.count()

    # ----------------------------
    # In-Progress tickets detection
    # ----------------------------
    in_progress_tickets = 0
    try:
        # Candidate status names that commonly represent "in progress"
        IN_PROGRESS_NAMES = [
            'In Progress', 'In-Progress', 'Ongoing', 'Assigned', 'Working', 'InProgress'
        ]

        # Build Q object to look for either a direct string status or status.name property
        q = Q()
        for name in IN_PROGRESS_NAMES:
            q |= Q(**{'status__iexact': name}) | Q(**{'status__name__iexact': name})

        # First try: tickets whose status field matches one of the candidate names
        in_progress_tickets = HelpdeskTicket.objects.filter(q).count()

        # Second fallback: if no matches, treat unresolved & assigned tickets as "in progress"
        if in_progress_tickets == 0:
            # check for common assignee field names
            assignee_field_candidates = ['assigned_to', 'assignee', 'owner', 'handler']
            has_assignee_field = False
            for field_name in assignee_field_candidates:
                try:
                    HelpdeskTicket._meta.get_field(field_name)
                    has_assignee_field = True
                    # count unresolved tickets that have an assignee
                    filter_kwargs = {
                        # unresolved detection: try common fields
                    }
                    # Try a few unresolved field patterns
                    try:
                        in_progress_tickets = HelpdeskTicket.objects.filter(
                            Q(status__is_resolved=False) & Q(**{f"{field_name}__isnull": False})
                        ).count()
                    except Exception:
                        # alternate unresolved pattern: status.name not in resolved set
                        in_progress_tickets = HelpdeskTicket.objects.filter(
                            ~Q(status__name__in=['Resolved', 'Closed', 'Completed']) & Q(**{f"{field_name}__isnull": False})
                        ).count()
                    break
                except Exception:
                    continue

            # Third fallback: if there's no assignee field or still zero, try a looser heuristic:
            if in_progress_tickets == 0:
                # Count tickets that are not resolved/closed (exclude common closed states).
                try:
                    in_progress_tickets = HelpdeskTicket.objects.exclude(
                        status__name__in=['Resolved', 'Closed', 'Completed']
                    ).count()
                except Exception:
                    # As ultimate fallback, use active_tickets (best-effort)
                    in_progress_tickets = active_tickets

    except Exception:
        # On any unexpected error, gracefully fall back to 0 or to active_tickets
        in_progress_tickets = active_tickets if 'active_tickets' in locals() else 0

    # Recent activity (last 7 days)
    one_week_ago = timezone.now() - timedelta(days=7)
    recent_members = Member.objects.filter(date_joined__gte=one_week_ago).count()
    # use 'created_at' or a safe fallback if your field differs
    try:
        recent_tickets = HelpdeskTicket.objects.filter(created_at__gte=one_week_ago).count()
    except Exception:
        # attempt common alternatives
        try:
            recent_tickets = HelpdeskTicket.objects.filter(created__gte=one_week_ago).count()
        except Exception:
            recent_tickets = HelpdeskTicket.objects.count()

    # School statistics
    total_schools = School.objects.count()

    # NEWS APP INTEGRATION - Recent News Articles
    recent_news = News.objects.all().order_by('-date_posted')[:5]
    total_news_articles = News.objects.count()
    recent_news_count = News.objects.filter(date_posted__gte=one_week_ago).count()

    # EVENTS APP INTEGRATION - Upcoming Events
    upcoming_events = Event.objects.filter(
        status='published',
        start__gte=timezone.now()
    ).order_by('start')[:5]
    total_upcoming_events = Event.objects.filter(
        status='published',
        start__gte=timezone.now()
    ).count()
    recent_documents = Document.objects.select_related('category', 'author').order_by('-date_posted')[:5]
    upcoming_qr_schedules = CourseSchedule.objects.select_related('course').filter(
        is_active=True,
        qr_checkin_enabled=True,
        start_datetime__gte=timezone.now(),
    ).order_by('start_datetime')[:5]
    training_courses_count = Course.objects.count()
    published_training_count = Course.objects.filter(is_published=True).count()
    active_training_enrollments = Enrollment.objects.exclude(status='cancelled').count()

    context = {
        'user': request.user,
        'stats': {
            'total_members': total_members,
            'active_members': active_members,
            'pending_approvals': pending_approvals,
            'total_tickets': total_tickets,
            'active_tickets': active_tickets,
            'in_progress_tickets': in_progress_tickets,
            'recent_members': recent_members,
            'recent_tickets': recent_tickets,
            'total_schools': total_schools,
            'total_news_articles': total_news_articles,
            'recent_news_count': recent_news_count,
            'total_upcoming_events': total_upcoming_events,
            'recent_documents': Document.objects.count(),
            'training_courses_count': training_courses_count,
            'published_training_count': published_training_count,
            'active_training_enrollments': active_training_enrollments,
        },
        'recent_news': recent_news,
        'upcoming_events': upcoming_events,
        'recent_documents': recent_documents,
        'upcoming_qr_schedules': upcoming_qr_schedules,
    }
    return render(request, 'accounts/staff_dashboard.html', context)

@login_required
def member_dashboard(request):
    try:
        member = Member.objects.get(user=request.user)
    except Member.DoesNotExist:
        messages.warning(request, 'Please complete your member profile.')
        return redirect('complete_member_profile')
    
    now = timezone.now()
    member_enrollments = Enrollment.objects.select_related(
        'course',
        'selected_schedule',
    ).filter(member=member).order_by('-last_accessed_at', '-enrolled_at')[:4]
    featured_courses = Course.objects.filter(is_published=True).order_by('-is_featured', 'title')[:3]
    latest_news = News.objects.filter(is_published=True).order_by('-date_posted')[:3]
    upcoming_events = Event.objects.filter(status='published', start__gte=now).order_by('start')[:3]
    recent_documents = Document.objects.select_related('category').order_by('-date_posted')[:4]
    open_tickets = HelpdeskTicket.objects.filter(created_by=request.user).filter(
        Q(status__isnull=True) | Q(status__is_resolved=False)
    ).order_by('-created_at')[:3]
    upcoming_training_schedules = CourseSchedule.objects.select_related('course').filter(
        is_active=True,
        start_datetime__gte=now,
    ).order_by('start_datetime')[:3]

    context = {
        'member': member,
        'member_enrollments': member_enrollments,
        'featured_courses': featured_courses,
        'latest_news': latest_news,
        'upcoming_events': upcoming_events,
        'recent_documents': recent_documents,
        'open_tickets': open_tickets,
        'upcoming_training_schedules': upcoming_training_schedules,
    }
    return render(request, 'accounts/member_dashboard.html', context)

def inprogress_trend(request):
    today = timezone.now().date()
    start_date = today - timedelta(days=29)
    data = []

    for i in range(30):
        date = start_date + timedelta(days=i)
        count = HelpdeskTicket.objects.filter(
        status__name__iexact='In Progress',  # assuming Status model has 'name' field
        created_at__date=date
        ).count()
        data.append({'date': date.strftime('%Y-%m-%d'), 'count': count})

    return JsonResponse({'data': data})
