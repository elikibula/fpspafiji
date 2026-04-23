# news/dashboard_api.py  (or add to your existing views file)

from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.apps import apps

# Try to import Ticket model; change path if your app is different
try:
    Ticket = apps.get_model('helpdesk', 'Ticket')
except Exception:
    # try other common app name if needed, or set None
    try:
        Ticket = apps.get_model('tickets', 'Ticket')
    except Exception:
        Ticket = None

COMMON_DATE_FIELDS = [
    'created', 'created_at', 'created_on', 'date_created',
    'opened', 'opened_at', 'timestamp', 'date', 'posted_at'
]

def _get_ticket_date_field():
    """
    Return the best guess for a Ticket DateTimeField name, or None if not found.
    """
    if Ticket is None:
        return None
    field_names = [f.name for f in Ticket._meta.get_fields() if hasattr(f, 'get_internal_type')]
    for cand in COMMON_DATE_FIELDS:
        if cand in field_names:
            return cand
    # fallback: look for any DateTimeField in the model
    for f in Ticket._meta.get_fields():
        # get_internal_type exists on real fields
        try:
            if f.get_internal_type() in ('DateTimeField', 'DateField'):
                return f.name
        except Exception:
            continue
    return None


def tickets_trend(request):
    """
    Return daily ticket counts for the past 30 days.
    JSON: { data: [{date: 'YYYY-MM-DD', count: N}, ...], total_last_30, total_prev_30, field_used }
    """
    today = timezone.now().date()
    start = today - timedelta(days=29)
    dates = [(start + timedelta(days=i)) for i in range(30)]

    # default all zeros list
    data = [{'date': d.isoformat(), 'count': 0} for d in dates]
    field_used = None
    total_last_30 = 0
    total_prev_30 = 0

    if Ticket is None:
        return JsonResponse({'data': data, 'total_last_30': 0, 'total_prev_30': 0, 'field_used': None})

    # detect a field to use
    date_field = _get_ticket_date_field()
    if date_field:
        field_used = date_field
        # Build counts per day using simple filtering (robust, DB-agnostic)
        counts_map = {}
        for d in dates:
            # construct filter like {'created__date': d}
            lookup = f"{date_field}__date"
            counts_map[d.isoformat()] = Ticket.objects.filter(**{lookup: d}).count()

        data = [{'date': d.isoformat(), 'count': counts_map[d.isoformat()]} for d in dates]

        # compute totals for last 30 and previous 30 (for percent delta)
        total_last_30 = sum(counts_map[d.isoformat()] for d in dates)
        prev_start = start - timedelta(days=30)
        prev_dates = [(prev_start + timedelta(days=i)) for i in range(30)]
        total_prev_30 = 0
        for d in prev_dates:
            total_prev_30 += Ticket.objects.filter(**{f"{date_field}__date": d}).count()
    else:
        # no detectable date field: attempt to use 'pk' created ordering (best-effort)
        # fallback: split all tickets by created date via str(ticket.some_field) -- but better to return zeros
        # This fallback returns zero-series so the frontend still works.
        field_used = None

    return JsonResponse({
        'data': data,
        'total_last_30': total_last_30,
        'total_prev_30': total_prev_30,
        'field_used': field_used
    })


# Replace this import with your real Ticket model path if different
# from helpdesk.models import Ticket
try:
    from helpdesk.models import Ticket
except Exception:
    Ticket = None  # adjust import path above to your actual ticket model

def _date_list_and_counts(queryset_date_field_lookup, start_date, end_date, queryset=None):
    """
    Helper to build a list of date/count dicts for each day in [start_date, end_date].
    - queryset: optional queryset already filtered by model; if provided, the function expects
      queryset_date_field_lookup to be a field name like 'date_joined__date' and will
      annotate counts per day.
    """
    # Build empty dict for date -> 0
    days = []
    cur = start_date
    while cur <= end_date:
        days.append(cur)
        cur = cur + timedelta(days=1)

    # If a queryset is provided, use it to get counts per date
    counts_map = {d.isoformat(): 0 for d in days}
    if queryset is not None:
        # annotate by date (expects the lookup to be like 'date_joined__date')
        # We cannot use dynamic annotation easily here without Raw SQL, so we'll count per-day in Python (robust).
        for d in days:
            filter_kwargs = {queryset_date_field_lookup: d}
            counts_map[d.isoformat()] = queryset.filter(**filter_kwargs).count()
    return [{'date': d.isoformat(), 'count': counts_map[d.isoformat()]} for d in days]


def members_trend(request):
    """Return daily new member counts for the last 30 days."""
    User = get_user_model()
    today = timezone.now().date()
    start = today - timedelta(days=29)
    # Use per-day counting to avoid DB-specific GROUP BY complications
    data = _date_list_and_counts('date_joined__date', start, today, queryset=User.objects.all())
    return JsonResponse({'data': data})


def inprogress_trend(request):
    today = timezone.now().date()
    start = today - timedelta(days=29)
    data = []
    for d in range(30):
        day = start + timedelta(days=d)
        count = Ticket.objects.filter(status='In Progress', created__date=day).count()
        data.append({'date': day.isoformat(), 'count': count})
    return JsonResponse({'data': data})