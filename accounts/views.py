from django.db import models
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import transaction
from django.db import IntegrityError
import logging
from django.contrib.auth import get_user_model
from .forms import MemberRegistrationForm, CustomUserCreationForm, CustomAuthenticationForm
from membership.models import Member
from django.contrib.auth import authenticate, login, logout
from membership.models import Member, MemberCategory
from helpdesk.models import HelpdeskTicket, TicketStatus, TicketPriority
from django.utils import timezone
from datetime import timedelta
from news.models import News
from events.models import Event
from documents.models import Document
from training.models import Course, CourseSchedule, Enrollment
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from .notifications import send_user_registration_notification
from reps.models import District
from membership.models import MembershipApprovalAudit
from .permissions import get_staff_district, is_national_administrator, require_application_access
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from django.urls import reverse_lazy

logger = logging.getLogger(__name__)


def _auth_user_has_id(user_id):
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

    try:
        existing_member = Member.objects.get(user=user)
        messages.info(request, "Your member profile is already complete.")
        if user.role in ['admin', 'staff', 'district_staff']:
            return redirect("staff_dashboard")
        if existing_member.membership_status != 'active':
            return redirect("pending_approval")
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

                    if not getattr(member_obj, "email", None):
                        member_obj.email = user.email

                    member_obj.save()

                    user.first_name = form.cleaned_data.get("first_name", user.first_name)
                    user.last_name = form.cleaned_data.get("last_name", user.last_name)
                    user.save()

                messages.success(request, "Member profile saved successfully. Staff will review your registration.")

                if user.role in ['admin', 'staff', 'district_staff']:
                    return redirect("staff_dashboard")
                else:
                    return redirect("pending_approval")

            except IntegrityError as exc:
                if "auth_user" in str(exc):
                    logger.error(f"Foreign key constraint issue: {exc}")
                    messages.error(
                        request,
                        "There's a database configuration issue. Please contact the administrator. "
                        "Error: Foreign key constraint points to wrong table."
                    )
                    messages.info(
                        request,
                        "You can continue to use the site, but please contact support to fix your profile."
                    )
                    if user.role in ['admin', 'staff', 'district_staff']:
                        return redirect("staff_dashboard")
                    else:
                        return redirect("member_dashboard")
                else:
                    logger.error(f"IntegrityError saving member profile: {exc}")
                    messages.error(request, "There was a database error saving your profile. Please try again.")
            except Exception as exc:
                logger.error(f"Unexpected error saving member profile: {exc}")
                messages.error(request, "An unexpected error occurred. Please try again.")
        else:
            logger.error(f"Form errors: {form.errors}")
            messages.error(request, "Please correct the errors below.")
    else:
        form = MemberRegistrationForm(instance=existing_member)

    return render(request, "accounts/complete_member_profile.html", {"form": form})


def register(request):
    return registration_entry(request)


def registration_entry(request):
    if request.user.is_authenticated:
        return complete_member_profile(request)

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            transaction.on_commit(lambda: send_user_registration_notification(user, request))
            login(request, user)
            messages.success(request, 'Account created. Please complete your member profile.')
            return redirect('complete_member_profile')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {
        'form': form,
        'registration_step': 1,
    })


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

                if user.role in ['admin', 'staff']:
                    return redirect('staff_dashboard')
                else:
                    try:
                        member = Member.objects.get(user=user)
                    except Member.DoesNotExist:
                        messages.info(request, 'Please complete your member profile.')
                        return redirect('complete_member_profile')
                    if member.membership_status != 'active':
                        return redirect('pending_approval')
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
def pending_approval(request):
    if request.user.role in ['admin', 'staff', 'district_staff']:
        return redirect('staff_dashboard')

    member = None
    try:
        member = Member.objects.get(user=request.user)
    except Member.DoesNotExist:
        messages.info(request, 'Please complete your member profile before approval.')
        return redirect('complete_member_profile')

    if member.membership_status == 'active':
        return redirect('member_dashboard')

    return render(request, 'accounts/pending_approval.html', {'member': member})


@login_required
def profile(request):
    context = {}
    if request.user.role == 'member':
        try:
            member = Member.objects.get(user=request.user)
            if member.membership_status != 'active':
                return redirect('pending_approval')
            context['member'] = member
        except Member.DoesNotExist:
            messages.warning(request, 'Please complete your member profile.')
            return redirect('complete_member_profile')
    return render(request, 'accounts/profile.html', context)


@login_required
def dashboard(request):
    if request.user.role in ['admin', 'staff', 'district_staff']:
        return redirect('staff_dashboard')
    else:
        return redirect('member_dashboard')


@login_required
def staff_dashboard(request):
    if request.user.role not in ['admin', 'staff', 'district_staff'] and not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('member_dashboard')

    staff_district = get_staff_district(request.user)
    district_unassigned = request.user.role == 'district_staff' and staff_district is None
    members_scope = Member.objects.none() if district_unassigned else Member.objects.all()
    if staff_district:
        members_scope = members_scope.filter(district=staff_district)
    total_members = members_scope.count()
    active_members = members_scope.filter(membership_status='active').count()
    pending_approvals = members_scope.filter(membership_status='pending').count()
    members_qs = members_scope.select_related('user', 'category', 'district').order_by(
        'district', 'last_name', 'first_name'
    )
    all_members = list(members_qs)
    pending_members = [
        member for member in all_members if member.membership_status == 'pending'
    ][:25]

    # Helpdesk statistics
    total_tickets = HelpdeskTicket.objects.count()

    try:
        active_tickets = HelpdeskTicket.objects.filter(status__is_resolved=False).count()
    except Exception:
        try:
            active_tickets = HelpdeskTicket.objects.exclude(
                status__name__in=['Resolved', 'Closed', 'Completed']
            ).count()
        except Exception:
            active_tickets = HelpdeskTicket.objects.count()

    in_progress_tickets = 0
    try:
        IN_PROGRESS_NAMES = [
            'In Progress', 'In-Progress', 'Ongoing', 'Assigned', 'Working', 'InProgress'
        ]
        q = Q()
        for name in IN_PROGRESS_NAMES:
            q |= Q(**{'status__iexact': name}) | Q(**{'status__name__iexact': name})

        in_progress_tickets = HelpdeskTicket.objects.filter(q).count()

        if in_progress_tickets == 0:
            assignee_field_candidates = ['assigned_to', 'assignee', 'owner', 'handler']
            for field_name in assignee_field_candidates:
                try:
                    HelpdeskTicket._meta.get_field(field_name)
                    try:
                        in_progress_tickets = HelpdeskTicket.objects.filter(
                            Q(status__is_resolved=False) & Q(**{f"{field_name}__isnull": False})
                        ).count()
                    except Exception:
                        in_progress_tickets = HelpdeskTicket.objects.filter(
                            ~Q(status__name__in=['Resolved', 'Closed', 'Completed']) &
                            Q(**{f"{field_name}__isnull": False})
                        ).count()
                    break
                except Exception:
                    continue

            if in_progress_tickets == 0:
                try:
                    in_progress_tickets = HelpdeskTicket.objects.exclude(
                        status__name__in=['Resolved', 'Closed', 'Completed']
                    ).count()
                except Exception:
                    in_progress_tickets = active_tickets
    except Exception:
        in_progress_tickets = active_tickets if 'active_tickets' in locals() else 0

    # Recent activity
    one_week_ago = timezone.now() - timedelta(days=7)
    recent_members = Member.objects.filter(date_joined__gte=one_week_ago).count()
    User = get_user_model()
    recent_accounts_qs = User.objects.filter(date_joined__gte=one_week_ago).order_by("-date_joined")
    recent_accounts = recent_accounts_qs[:5]

    try:
        recent_tickets = HelpdeskTicket.objects.filter(created_at__gte=one_week_ago).count()
    except Exception:
        try:
            recent_tickets = HelpdeskTicket.objects.filter(created__gte=one_week_ago).count()
        except Exception:
            recent_tickets = HelpdeskTicket.objects.count()

    # School and area statistics
    total_schools = Member.objects.exclude(school='').values('school').distinct().count()
    represented_districts = members_scope.exclude(district__isnull=True).values('district').distinct().count()

    members_with_age = [member.age for member in all_members if member.age is not None]
    principal_years = [member.years_as_principal for member in all_members if member.start_year]
    average_member_age = round(sum(members_with_age) / len(members_with_age), 1) if members_with_age else None
    average_principal_years = round(sum(principal_years) / len(principal_years), 1) if principal_years else None

    # Area groups (replaces district_groups)
    district_groups = []
    districts = District.objects.all() if is_national_administrator(request.user) else District.objects.filter(pk=getattr(staff_district, 'pk', None))
    for area_obj in districts:
        area_members = [m for m in all_members if m.district_id == area_obj.id]
        area_years = [m.years_as_principal for m in area_members if m.start_year]
        district_groups.append({
            'value': area_obj.id,
            'label': str(area_obj),
            'members': area_members,
            'total': len(area_members),
            'active': len([m for m in area_members if m.membership_status == 'active']),
            'pending': len([m for m in area_members if m.membership_status == 'pending']),
            'average_principal_years': round(sum(area_years) / len(area_years), 1) if area_years else None,
        })

    unassigned_members = [m for m in all_members if m.district_id is None]

    # News
    recent_news = News.objects.all().order_by('-date_posted')[:5]
    total_news_articles = News.objects.count()
    recent_news_count = News.objects.filter(date_posted__gte=one_week_ago).count()

    # Events
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
            'recent_accounts': recent_accounts_qs.count(),
            'recent_tickets': recent_tickets,
            'total_schools': total_schools,
            'represented_districts': represented_districts,
            'average_member_age': average_member_age,
            'average_principal_years': average_principal_years,
            'total_news_articles': total_news_articles,
            'recent_news_count': recent_news_count,
            'total_upcoming_events': total_upcoming_events,
            'recent_documents': Document.objects.count(),
            'training_courses_count': training_courses_count,
            'published_training_count': published_training_count,
            'active_training_enrollments': active_training_enrollments,
        },
        'recent_news': recent_news,
        'recent_accounts': recent_accounts,
        'upcoming_events': upcoming_events,
        'recent_documents': recent_documents,
        'upcoming_qr_schedules': upcoming_qr_schedules,
        'pending_members': pending_members,
        'all_members': all_members,
        'district_groups': district_groups,
        'unassigned_members': unassigned_members,
        'assigned_district': staff_district,
        'district_unassigned': district_unassigned,
        'returned_members': members_scope.filter(membership_status='returned')[:25],
        'rejected_members': members_scope.filter(membership_status='rejected')[:25],
        'recent_approval_activity': MembershipApprovalAudit.objects.filter(application__in=members_scope).select_related('acting_user', 'staff_district', 'application')[:10],
    }
    return render(request, 'accounts/staff_dashboard.html', context)


@login_required
def member_dashboard(request):
    try:
        member = Member.objects.get(user=request.user)
    except Member.DoesNotExist:
        messages.warning(request, 'Please complete your member profile.')
        return redirect('complete_member_profile')

    if member.membership_status != 'active':
        return redirect('pending_approval')

    now = timezone.now()
    member_enrollments = Enrollment.objects.select_related(
        'course', 'selected_schedule',
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


@login_required
@require_POST
def approve_member(request, member_id):
    member = get_object_or_404(Member.objects.select_related('district', 'user'), pk=member_id)
    require_application_access(request.user, member)
    if not member.district_id:
        messages.error(request, 'Assign a district before approving this application.')
        return redirect('staff_dashboard')
    if member.user_id == request.user.id:
        raise PermissionDenied('You cannot approve your own application.')
    with transaction.atomic():
        previous = member.membership_status
        member.membership_status = 'active'
        member.save(update_fields=['membership_status'])
        MembershipApprovalAudit.objects.create(application=member, action='approved', acting_user=request.user, staff_district=get_staff_district(request.user), previous_status=previous, new_status='active', comment=request.POST.get('comment', '').strip())
    messages.success(request, f'{member.full_name} has been approved.')
    return redirect('staff_dashboard')


@login_required
@require_POST
def reject_member(request, member_id):
    member = get_object_or_404(Member.objects.select_related('district'), pk=member_id)
    require_application_access(request.user, member)
    reason = request.POST.get('comment', '').strip()
    with transaction.atomic():
        previous = member.membership_status
        member.membership_status = 'rejected'
        member.save(update_fields=['membership_status'])
        MembershipApprovalAudit.objects.create(application=member, action='rejected', acting_user=request.user, staff_district=get_staff_district(request.user), previous_status=previous, new_status='rejected', comment=reason)
    messages.success(request, f'{member.full_name} has been rejected.')
    return redirect('staff_dashboard')


@login_required
@require_POST
def return_member(request, member_id):
    member = get_object_or_404(Member.objects.select_related('district'), pk=member_id)
    require_application_access(request.user, member)
    comment = request.POST.get('comment', '').strip()
    with transaction.atomic():
        previous = member.membership_status
        member.membership_status = 'returned'
        member.save(update_fields=['membership_status'])
        MembershipApprovalAudit.objects.create(application=member, action='returned', acting_user=request.user, staff_district=get_staff_district(request.user), previous_status=previous, new_status='returned', comment=comment)
    messages.success(request, f'{member.full_name} has been returned for correction.')
    return redirect('staff_dashboard')


class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('password_change_done')


class CustomPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = 'accounts/password_change_done.html'


def inprogress_trend(request):
    today = timezone.now().date()
    start_date = today - timedelta(days=29)
    data = []

    for i in range(30):
        date = start_date + timedelta(days=i)
        count = HelpdeskTicket.objects.filter(
            status__name__iexact='In Progress',
            created_at__date=date
        ).count()
        data.append({'date': date.strftime('%Y-%m-%d'), 'count': count})

    return JsonResponse({'data': data})
